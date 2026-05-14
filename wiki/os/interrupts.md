---
title: Interrupts (MOS IRQ chain)
type: os
tags: [interrupts, irq, irq1v, irq2v, vsync, nmi]
sources: [naug-ch08-interrupts, naug-ch22-vias]
updated: 2026-05-13
---

# Interrupts — MOS IRQ Chain

How an IRQ flows from chip to handler, what MOS does, and where user code intercepts.

## Hardware → vector

```
Chip raises IRQ line ─→ 6502 finishes current insn ─→ push PC, push P (B=0)
                    ─→ set I flag ─→ JMP (&FFFE)
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
