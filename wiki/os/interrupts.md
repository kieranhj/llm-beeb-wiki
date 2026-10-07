---
title: Interrupts (MOS IRQ chain)
type: os
tags: [interrupts, irq, irq1v, irq2v, vsync, nmi]
sources: [naug-ch08-interrupts, naug-ch22-vias, beeb-port-kit-hardware-facts]
updated: 2026-09-07
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

User code generally doesn't touch NMI — it's reserved for disc/network. See [[sources/naug-ch17-paged-roms]] for the NMI claim/release protocol via paged-ROM service calls (`OSBYTE &8F` with reason `&0B`/`&0C`).

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Both ports take IRQ1V outright: VSync (CA1) and System VIA T1 only, no MOS tick, no OS sound, keyboard read direct from the VIA.

- **The entry state above is right as measured: the MOS saves the interrupted A in `&FC` and not X or Y** (Paradroid Layer 3, jsbeeb).
- **Taking IRQ1V outright**: disable every interrupt source on both VIAs except System VIA CA1 and T1, or anything unserviced holds the IRQ line asserted forever (Paradroid Layer 3; [layer-3-scroll.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-3-scroll.md)).
- **Every `*LOAD`/OSFILE must happen before you take IRQ1V**: taking it stops the MOS servicing the filing system (Paradroid Layer 3). And **the MOS's disc code needs VSync** — with the CRTC's R7 parked where VSync never fires, the second `*LOAD` hung forever in DFS's 8271 status poll at `&ACAE`; bisecting the CRTC writes one at a time showed R7 was the trigger (Paradroid Layer 3, jsbeeb; [bug-map-corruption.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/bug-map-corruption.md)). See [[os/filing-systems]].
- **The MOS's 100 Hz T1 tick is 20,000 CPU cycles, exactly half a frame** — which is why a `&FE44` read at a fixed point in a VSync-locked loop is near-constant, not random (Paradroid, 2026-08-26). Consistent with the 50 Hz / 100 Hz table above.
- **IRQ latency swings by more than a few cycles**: the 6502 finishes the instruction it is on, and a `SEI` window in the foreground (17 cycles in Paradroid's CRTC-start write) adds to it. A CRTC write with 3-7 cycles of margin to the end of horizontal blanking overran intermittently and showed a character of the next row in the bottom-left corner (Paradroid, 2026-09-06, jsbeeb, phase of the `STA &FE01` against a `run_frames` anchor, differenced mod 128). The VSync CA1 interrupt itself is serviced about 4 scanlines after the edge. See [[timing/field-timing]].
- **Hand IRQ1V back with your data over `&0800-&08FF` and the MOS plays it as notes** — flush every buffer (`OSBYTE &0F, X=0`) before uninstalling (Paradroid, 2026-08-26). See [[memory/os-workspace]], [[os/sound]].
- **On the Master, `&FFFE` reads `&E59E`**, above HAZEL, so paging HAZEL in cannot break the dispatch at the top of this page (Edge, 2026-09-04, jsbeeb). See [[memory/shadow-ram]].
- **An IRQ fires with whatever sideways bank the foreground has paged**; an IRQ that needs a bank saves `&F4`, pages, and restores both (Paradroid's sound tick, 2026-08-21). See [[memory/paged-rom]].

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
