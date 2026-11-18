---
title: Interrupts (MOS IRQ chain)
type: os
tags: [interrupts, irq, irq1v, irq2v, vsync, nmi]
sources: [naug-ch08-interrupts, naug-ch22-vias, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# Interrupts — MOS IRQ Chain

How an IRQ flows from chip to handler, what MOS does, and where user code intercepts.

## Hardware → vector

```
Chip raises IRQ line --> 6502 finishes current insn --> push PC, push P (B=0)
                    --> set I flag --> JMP (&FFFE)
```

`(&FFFE)` points into MOS. The MOS handler:

1. Save A into zero page `&FC`. (X, Y not touched.)
2. Test the pushed P (B flag bit 4) on stack:
   - **B=1 (BRK)** → divert to `BRKV` (`&202`).
   - **B=0 (real IRQ)** → proceed.
3. **`JMP (&204)` — IRQ1V hook.** Default points to the MOS dispatcher; user can intercept here for highest-priority work.
4. **MOS poll** — in order:
   - 6850 status `&FE08` bit 7 → handle RS423/cassette.
   - System VIA IFR `&FE4D` bit 7 → handle VIA sources (apply mask `OSBYTE &E9`).
   - User VIA IFR `&FE6D` bit 7 → handle CA1 (printer); mask `OSBYTE &E7`.
5. **`JMP (&206)` — IRQ2V hook** — called even if MOS handled something, to give user code a final intercept and any unrecognised IRQs.
6. Restore A from `&FC`, `RTI`.

## User entry state (at either IRQ1V or IRQ2V)

- Stack: P, then PC (return address).
- **X, Y**: unchanged from interrupted code.
- **A**: in zero page `&FC` (NOT in the A register).
- D flag: undefined on NMOS — `CLD` first if you do BCD.

```asm
.my_irq2v
    LDA &FE6D       ; user VIA IFR — test our source
    AND #&20        ; e.g. T2 of user VIA
    BEQ pass_through
    ; ... handle T2 IRQ, clear flag (read T2C-L or write T2C-H)
    LDA &FC         ; restore A from MOS save
    RTI

.pass_through
    LDA &FC
    JMP (old_irq2v) ; chain to whatever was there before us
```

**Clearing IFR flags without clobbering A**: the read-to-clear mechanism in the VIA is triggered by the bus access, not the opcode. So `BIT &FE61` (User VIA ORA) is functionally identical to `LDA &FE61` for clearing the CA1 flag, but preserves A. Same 4 cycles. Same for `BIT &FE48` to read T2C-L and clear the T2 flag. Use BIT in IRQ handlers wherever you don't need the value in A.

## Hooking IRQ2V (recommended pattern)

```asm
SEI
LDA &206 : STA old_irq2v        ; preserve old vector
LDA &207 : STA old_irq2v+1
LDA #my_irq2v MOD 256 : STA &206
LDA #my_irq2v DIV 256 : STA &207
CLI
```

Always save the old vector — other ROMs may have hooked it. Always SEI/CLI around vector writes.

To unhook: SEI, restore from `old_irq2v`, CLI.

## IRQ1V — when

Use **IRQ1V** if you need to run *before* MOS — typical reasons:
- You're hooking T2 of the System VIA for raster timing and need to react within a few µs of the timer firing.
- You're providing a custom RS423 driver and want first crack at the 6850.
- You're disabling certain MOS interrupt behaviour (e.g. suppressing the keyboard scan).

Cost: you have to either replicate MOS's dispatch yourself, or test the source you care about and immediately fall through to the original IRQ1V handler. Mis-hooking IRQ1V is the most common way to crash a BBC.

## MOS IRQ bit masks

The MOS keeps software shadow copies of "interrupts to handle" per chip. **Setting a bit in the mask makes MOS skip that source**, so the IRQ falls through to IRQ2V. The chip flag stays set until cleared — *you* must clear it in your IRQ2V handler.

| OSBYTE | Chip | Notes |
|---|---|---|
| `&E7` | User VIA | Default `&FF` — MOS only watches CA1 (printer) |
| `&E8` | 6850 | Default `&FF` — MOS owns all unless you mask |
| `&E9` | System VIA | Default `&FF` — typical user trick: mask T1 if you want sole control of 100Hz |
| `&CB` | Electron ULA | Default `&0C` |

Standard `<NEW>=(<OLD> AND Y) EOR X` call:
```asm
; Make MOS ignore System VIA T2 (bit 5), keep everything else
LDA #&E9 : LDX #&20 : LDY #&FF : JSR &FFF4
```

The flag at IFR doesn't move — you must still **read T2-L or write T2-H** in your handler to clear it, or the CPU will re-IRQ immediately.

## 50 Hz vs 100 Hz — which is which

| Source | Frequency | What MOS uses it for |
|---|---|---|
| **System VIA CA1** (vsync) | 50 Hz | Flash colour swap, 6850 RS423/cassette timeout, event 4 |
| **System VIA T1** (timer) | 100 Hz | TIME update, interval timer, INKEY countdown, sound envelope, key-buffer servicing |

If you want a "fire every frame" hook, hook **CA1 via IRQ2V** with the System VIA mask updated to **un-mask** bit 1 — but then *you* must clear bit 1 by reading `&FE41` (ORA). Or just leave MOS handling it and use the lower-priority side-effect: insert your code *after* MOS's flash update.

If you want "do something every 10 ms (centi-second)" — hook **T1 via IRQ2V** (mask MOS off bit 6, take ownership).

## Maximum SEI window

> Disabling interrupts for longer than ~2 ms causes undefined behaviour (NAUG §8.5 p129).

2 ms = 4000 CPU cycles @ 2 MHz. The 100 Hz handler must run; missing one tick drops a sound-envelope step, a TIME increment, possibly a key. Keep SEI windows < 1 ms (2000 cycles) for routine work; only exceed for absolutely necessary atomicity (and accept the consequences).

## NMI

NMI is non-maskable (SEI doesn't block it). Vector `&FFFA` points to MOS code that jumps to **`&0D00`** — a one-page RAM area where the NMI handler lives. Filing systems (DFS, Econet) install their NMI handlers here and chain.

Under the MOS, user code generally doesn't touch NMI — it's reserved for disc/network. See [[sources/naug-ch17-paged-roms]] for the NMI claim/release protocol via paged-ROM service calls (`OSBYTE &8F` with reason `&0B`/`&0C`).

**But a program can own the NMI** ([[sources/beeb-port-kit-hardware-facts-2026-11]] §6):

- **A loader** claims it without detaching the filing system: `OSBYTE 143,12,255` (service call `&0C`, NMI claim) and `RTI` at `&0D00`, then runs no OS code at all until it is done.
- **After `OSBYTE 140`** (the filing system detaches and tells its hardware to stop raising NMIs) the NMI is the program's for good, and zero page `&A0-&A7` (the MOS's NMI-owner workspace) with it. 1942 and phX then put their own 1770 driver's routine at `&0D00` and load with interrupts on; phX's NMI page holds its routine at `&0D00`, its BREAK intercept at `&0D20` and overlay code at `&0D40-&0D9E`. Both played on real Masters. See [[hardware/wd1770]].
- **`SEI` does not mask it**: a 1770 transfer runs on through a masked section, which is how a DFS `*LOAD` under `SEI` works at all (kit `lib/qdisc.6502`).
- **Disc NMIs delay IRQs**: at ~35 cycles a byte, a disc NMI can push an IRQ past what a stable-raster slide absorbs (phX: fields entered 0-35 cycles late behind its loading card, jsbeeb). A line-exact part must not run while the disc loads.
- **NMIs nest** (a late 1770 INTRQ inside the byte routine): keep A on the stack, not in zero page. See [[hardware/wd1770]].

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Both ports take IRQ1V outright: VSync (CA1) and System VIA T1 only, no MOS tick, no OS sound, keyboard read direct from the VIA.

- **The entry state above is right as measured: the MOS saves the interrupted A in `&FC` and not X or Y** (Paradroid Layer 3, jsbeeb).
- **Taking IRQ1V outright**: disable every interrupt source on both VIAs except System VIA CA1 and T1, or anything unserviced holds the IRQ line asserted forever (Paradroid Layer 3; [layer-3-scroll.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-3-scroll.md)).
- ~~**Every `*LOAD`/OSFILE must happen before you take IRQ1V**: taking it stops the MOS servicing the filing system~~ (Paradroid Layer 3 — **assumed, never tested; replaced**, see the next entry). And **the MOS's disc code needs VSync** — with the CRTC's R7 parked where VSync never fires, the second `*LOAD` hung forever in DFS's 8271 status poll at `&ACAE`; bisecting the CRTC writes one at a time showed R7 was the trigger (Paradroid Layer 3, jsbeeb; [bug-map-corruption.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/bug-map-corruption.md)). **Not reproducible on later jsbeeb**: re-tested 2026-09-09 (jsbeeb-mcp 3.4.0 / jsbeeb 1.25.0), R7 = 34 against R4 = 30 in MODE 7 stopped VSync (IFR bit 1 never set again) and an 8 KB `*LOAD` still completed. That was R7 alone in a full-length frame, not Paradroid's rupture shape: treat the hang as real but not pinned to VSync ([[sources/beeb-port-kit-hardware-facts-2026-11]] §6). See [[os/filing-systems]].
- **What a filing-system call needs from the IRQ, measured** ([[sources/beeb-port-kit-hardware-facts-2026-11]] §6):
  - **Model B, 8271, DFS 1.20** (kit, 2026-09-09, jsbeeb 1.25.0, `B-DFS1.2`): an 8 KB 32-sector `*LOAD` completed byte-for-byte with IRQ1V on a handler that only clears both VIAs' flags (`TIME` unmoved), with `SEI` across the whole call, and with both plus VSync stopped. The 8271 transfers on NMI.
  - **Master 128, MOS 3.20, Acorn 1770 DFS** (1942, 2026-09-13, jsbeeb; `docs/note-to-kit.md`), across a 26-sector `*LOAD`:

    | IRQ state during the call | result |
    |---|---|
    | MOS running normally | checksum `&7B0F` |
    | `SEI` … `CLI` around the call | `&7B0F`, byte-identical |
    | IRQ1V on a **null** handler (clears both VIAs' flags, `RTI`) | **hung**: MOS spinning in its service-call dispatcher `&EE72-&EE9C`, `JSR &8003` round every bank |
    | IRQ1V on a **chaining** handler (`JMP (old)`), MOS VIA state untouched | `&7B0F`; the MOS wrote 35 bytes of `&0800-&08FF` |
    | chaining + System VIA T1's latch changed | **hung**, the same `&8003` spin |
    | chaining + T1's interrupt disabled (IER `&40`) | **hung**, inside the DFS ROM at `&8673` |

    So on a Master: **either mask, or chain and change nothing**; a rupture's own T1 cadence cannot run across a filing-system call, and a chaining handler hands the 100 Hz tick back, so the MOS sound driver writes `&0800-&08FF` again. The three hangs are jsbeeb results, not hardware, and want a b2 or real-Master run before anything is designed against them. **Cost of a call:** ~15 cs fixed plus ~4 cs a sector, so a one-sector call already blocks for nine fields (1/18 cs, 2/20, 3/38, 26/120) — chunking a load to service a player between chunks does not work.
- **Chaining to the MOS loses VSyncs.** A handler that finds no VSync and chains the interrupt (the 100 Hz tick, a User VIA timer) to the MOS can have VSync arrive in the ~30 cycles before the MOS's dispatcher reads the VIA; the dispatcher tests VSync first, acknowledges it, and the game never sees that field. Stryker's Run's original lost 12 fields of 1,000. Fix: clear bit 1 of the MOS's System VIA IRQ mask (`&0279`, OSBYTE `&E9`) while the game owns VSync — take VSync before masking, unmask before handing it back: 0 of 1,000 lost since (2026-10-16, jsbeeb 2.5.0; [strykers-run BUGS.md #3](https://github.com/kieranhj/strykers-run/blob/main/BUGS.md), decision 14).
- **An interrupt the MOS does not recognise is offered to every paged ROM** (service call 5, `&EE72`) before IRQ2V: a User VIA T1 palette split cost **1,165 cycles a field** that way. Service your own timers and `RTI` yourself; never chain them (Stryker's Run decision 15, 2026-10-16, jsbeeb 2.5.0, Master MOS 3.20).
- **What the MOS's IRQ costs a game that keeps it (MOS 3.20):** the 100 Hz tick takes ~16% of the CPU in play — 3,240 cycles a tick in Stryker's Run's original, mostly sound queues and envelopes (6.8% of all cycles) and, while any key is held, a full keyboard-matrix scan every tick (6.3%). **The tick re-enables interrupts** (`CLI` at `&E720` around its sound processing), so interrupts nest and a profiler must keep a stack. The whole interrupt budget went 21.0% → 10.6% once the game owned VSync → 2.2% with its own 50 Hz sound driver (2026-10-16, jsbeeb 2.5.0, `tools/irqprofile.mjs`).
- **An interrupt entry with System VIA T1's flag up is not one MOS tick**: counting them gave 3,192 entries for 1,176 ticks from BASIC — interrupts nest and re-enter. Place ticks on a 20,000-cycle grid (kit `sfxcapture.mjs`, 2026-10-25; gotchas class 5).
- **Replacing a MOS call means returning everything it returns, documented or not**: MOS 3.20's OSBYTE 19 falls out of its wait through `LDY &0301,X : LDA &0300,X : TAX` (`&F0FF`), and Stryker's Run kept Y from it across a screen clear; a replacement field-counter wait that didn't put text on the wrong screen (BUGS #5, jsbeeb 2.5.0).
- **The MOS's 100 Hz T1 tick is 20,000 CPU cycles, exactly half a frame** — which is why a `&FE44` read at a fixed point in a VSync-locked loop is near-constant, not random (Paradroid, 2026-08-26). Consistent with the 50 Hz / 100 Hz table above.
- **IRQ latency swings by more than a few cycles**: the 6502 finishes the instruction it is on, and a `SEI` window in the foreground (17 cycles in Paradroid's CRTC-start write) adds to it. A CRTC write with 3-7 cycles of margin to the end of horizontal blanking overran intermittently and showed a character of the next row in the bottom-left corner (Paradroid, 2026-09-06, jsbeeb, phase of the `STA &FE01` against a `run_frames` anchor, differenced mod 128). The VSync CA1 interrupt itself is serviced about 4 scanlines after the edge. See [[timing/field-timing]].
- **Hand IRQ1V back with your data over `&0800-&08FF` and the MOS plays it as notes** — flush every buffer (`OSBYTE &0F, X=0`) before uninstalling (Paradroid, 2026-08-26). See [[memory/os-workspace]], [[os/sound]].
- **On the Master, `&FFFE` reads `&E59E`**, above HAZEL, so paging HAZEL in cannot break the dispatch at the top of this page (Edge, 2026-09-04, jsbeeb). See [[memory/shadow-ram]].
- **An IRQ fires with whatever sideways bank the foreground has paged**; an IRQ that needs a bank saves `&F4`, pages, and restores both (Paradroid's sound tick, 2026-08-21). See [[memory/paged-rom]].

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
