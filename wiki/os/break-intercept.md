---
title: BREAK Intercept & Reset Handling
type: os
tags: [break, reset, intercept, osbyte, startup]
sources: [naug-ch24-misc, bbc-service-manual]
updated: 2026-05-13
---

# BREAK Intercept & Reset Handling

How to survive — or take over — the BREAK / reset sequence.

## Reset types

| Type | Trigger | `OSBYTE &FD` returns |
|---|---|---|
| Soft BREAK | BREAK key alone | 0 |
| Power-on reset | Power-up; or software-triggered by masking System VIA IRQs (`STA &FE4E` with `&7F`) then forcing reset | 1 |
| Hard BREAK | CTRL + BREAK | 2 |

A **hard BREAK** clears memory and reinitialises everything from scratch (MOS reads the keyboard PCB links / `*FX 255` byte). A **soft BREAK** preserves user memory (`&E00`+) and just re-enters the current language. A **power-on reset** does the most aggressive init.

After any reset, `OSBYTE &FD` returns the type — useful for "skip init the second time" logic.

### How MOS distinguishes cold-start from BREAK at the hardware level

Per [[sources/bbc-service-manual]] §3.1, the BBC's reset circuitry has two paths:

- A **555 timer** (IC16 on a Model B) drives the general `RESET` line, asserted both at power-on and on BREAK.
- A separate **RC network** (C10 + R20 + D1) feeds the System VIA's `RESET A` input on power-up *only* — the time constant is long enough that the BREAK key's reset pulse doesn't trigger it.

Power-on therefore latches an extra interrupt source in the System VIA IFR that BREAK does not. MOS's startup code polls the IFR to set the cold-start / warm-start flag that `OSBYTE &FD` later surfaces. On a **Master 128 + Compact**, the equivalent latching is done by the Memory Controller IC rather than discrete RC components, but the IFR-polling pattern is the same. This is why `OSBYTE &FD` reliably differentiates cold-start across all BBC models.

You cannot easily "fake" a cold-start from software — the only reliable software path to value `1` is via the documented "mask all System VIA IRQs then jump to `&FFFC` indirect" sequence, which is a brittle hack. Just use `OSBYTE &FD` to read the type and branch.

## OSBYTE `&F7-&F9` — install a BREAK intercept

These three bytes hold a **JMP instruction** that MOS calls during every reset. By default they're `00 00 00` (no JMP, no intercept). Install:

```asm
; Install a JMP to my_handler at &F7-&F9
LDA #&F7 : LDX #&4C : LDY #0 : JSR &FFF4              ; JMP opcode (&4C)
LDA #&F8 : LDX #my_handler MOD 256 : LDY #0 : JSR &FFF4   ; lo byte
LDA #&F9 : LDX #my_handler DIV 256 : LDY #0 : JSR &FFF4   ; hi byte
```

MOS calls your JMP **twice per BREAK**:

1. **First call: C=0** — before the OS startup message, before Tube init.
2. **Second call: C=1** — after the startup message and Tube init.

Handler skeleton:

```asm
.my_break_handler
    BCC .first_call

; ----- second call (C=1) -----
    ; OS message printed, Tube init done.
    ; Re-install your IRQ vectors, custom mode, palette, etc.
    LDA #ivec_lo : STA &204                ; IRQ1V or whatever
    LDA #ivec_hi : STA &205
    ; ... etc ...
    RTS                                    ; or JMP to your reset entry

.first_call
    ; Pre-message work.
    ; Clear pending IRQs, restore default state.
    RTS
```

## Why intercept BREAK

- **Game / demo persistence**: if a user accidentally presses BREAK during your game, re-set up the custom mode + load resume state instead of dropping to BASIC.
- **Protected environments**: a service ROM can re-claim NMI/IRQ vectors that BASIC would otherwise reset.
- **Custom startup**: silent boot directly into your application (set `OSBYTE &D7` bit 7 to suppress the BBC startup message, then your BREAK handler runs into your app entry).

## OSBYTE summary

| OSBYTE | Function |
|---|---|
| `&C8` (200) | R/W escape-disable + BREAK-clears-memory flags |
| `&D7` (215) | R/W startup message + boot-error suppression |
| `&F7` (247) | R/W BREAK intercept byte 0 (JMP opcode = `&4C`) |
| `&F8` (248) | R/W BREAK intercept byte 1 (handler low byte) |
| `&F9` (249) | R/W BREAK intercept byte 2 (handler high byte) |
| `&FD` (253) | Read last-BREAK type (0/1/2) |
| `&FF` (255) | R/W start-up options byte |

### `OSBYTE &C8` — ESCAPE + BREAK behaviour

```
bit 0:   0 = normal ESCAPE,  1 = ESCAPE disabled
bits 1-7: 0 = preserve memory on BREAK,  non-zero = clear memory on BREAK
```

`*FX 200,1` = "ESCAPE disabled, memory preserved on soft BREAK" — the canonical game-launcher setting.

### `OSBYTE &D7` — message suppression

```
bit 7: 0 = suppress startup message, 1 = print message (default)
bit 0: 0 = boot-file errors cause lock-up if !BOOT in *ROM,
       1 = boot-file errors continue if !BOOT in *ROM but lock-up on disc
```

Set bit 7 = 0 for a silent boot.

### `OSBYTE &FF` — start-up options byte

On Model B, set by 8 keyboard PCB links read at hard BREAK. On Electron / Master, programmable via `*FX 255,n`:

| Bits | Function |
|---|---|
| 0-2 | Initial MODE after reset |
| 3 | If clear, SHIFT+BREAK swapped (auto-boot vs no-boot) |
| 4-5 | Disc-drive timings (depends on FDC) |
| 6 | Reserved |
| 7 | 0 = boot to NFS, 1 = boot to DFS |

## Triggering a reset programmatically

```asm
LDA #&7F : STA &FE4E         ; mask System VIA IRQs
JMP (&FFFC)                  ; vector via reset → power-on reset path
```

The IRQ-mask + reset combo causes MOS to detect a power-on reset (return `OSBYTE &FD` = 1) rather than soft BREAK. Useful when you want full re-initialisation rather than language re-entry.

## See also

- [[os/escape]] — ESCAPE handling (separate from BREAK).
- [[os/osbyte]] — All BREAK-related OSBYTE entries.
- [[os/calls]] — BRKV (`&202`) vs the `&F7-&F9` intercept (different mechanisms).
- [[os/paged-roms]] — Service ROMs use their own service-call &27 reset notification (Master) in addition to the BREAK intercept.
- [[sources/naug-ch24-misc]] — Full source page with worked examples.
