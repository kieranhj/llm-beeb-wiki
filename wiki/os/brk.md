---
title: BRK & Error Handling
type: os
tags: [brk, brkv, errors]
sources: [naug-ch08-interrupts]
updated: 2026-05-13
---

# BRK & Error Handling

BRK is opcode `&00`. It's a 1-byte instruction that:

1. Pushes PC+2 onto the stack (yes, +2 — skips a byte!).
2. Pushes P with B=1.
3. Sets I.
4. (On 65C12, also clears D. NMOS does *not*.)
5. JMPs via `(&FFFE)` (shared IRQ/BRK vector).

The MOS handler tests the pushed P for B=1 and diverts to **BRKV** at `&202/&203`.

## Acorn BRK convention

Used as an error-raising mechanism in BASIC and other languages:

```asm
BRK
EQUB &10           ; error number
EQUS "Out of range"
EQUB 0             ; null terminator
```

After BRK:
- `&FD/&FE` = address of the byte *after* BRK (so points to the error number — useful for indexed addressing).
- A, X, Y = unchanged from before BRK.
- RTI returns to **PC+2** (the byte after the error number) — i.e. skips the error number but lands inside the message. So BRK handlers never `RTI` back to the error data — they reset the stack and jump to the language's command-line prompt.

## Standard handler pattern

```asm
.my_brk_handler
    LDX #&FF           ; reset stack pointer
    TXS
    ; print error: &FD points to error number byte, &FE/+1 is high byte
    ; ... use OSWRCH to print bytes from &FD/&FE pointer until terminator
    JMP (language_entry)  ; or jump to command prompt
```

## Installing a BRK handler

```asm
SEI
LDA &202 : STA old_brkv
LDA &203 : STA old_brkv+1
LDA #my_brk_handler MOD 256 : STA &202
LDA #my_brk_handler DIV 256 : STA &203
CLI
```

Restore the old vector before exiting your program.

## BRK from a paged ROM

When BRK fires, MOS swaps the current **language ROM** back in (because that's where BASIC's BRK handler lives). If your service ROM wants to raise an error, the literal BRK+message bytes in your ROM are no longer addressable when the handler runs — the language ROM occupies `&8000-&BFFF` instead.

Solution: copy the BRK + error number + message + 0 into RAM (commonly `&0100` — the bottom of the stack page, safe because the handler resets SP) and JMP to the RAM copy. The handler then reads from the RAM address via `&FD/&FE`.

## OSBYTE `&BA` — ROM active at last BRK

After MOS records which paged ROM was active at the moment BRK fired, this OSBYTE returns it in X. Useful in debugging:

```asm
LDA #&BA : LDX #0 : LDY #&FF : JSR &FFF4
; X = ROM number that was paged in when BRK happened
```

## Debugging use — BRK as breakpoint

A BRK in the middle of your assembly is a one-byte "stop here" — combined with a custom BRK handler that prints A/X/Y and waits for a keypress, it's a poor-man's debugger. NAUG §8.13 p133-134 gives a worked example (BASIC + inline assembler) that does exactly this; the routine prints `A:&xx X:&xx Y:&xx`, then `OSRDCH` waits, then RTI continues.

Caveat on the byte-after-BRK skip: if you don't follow the BRK with a dummy byte, RTI will return into the middle of your next instruction. So always:

```asm
BRK
EQUB 0           ; dummy / RTI lands here, falls through to next insn
LDA something    ; this is where execution continues
```

Or use the dummy byte as a 0-255 breakpoint ID that your handler prints.

## NMOS D-flag trap

The 65C12 (Master) clears D on BRK entry. The NMOS 6502 (Model B / B+ / Electron / 6502 second processor) **does not** — if D was set when BRK fired, your handler runs with D set, and any ADC/SBC inside the handler does BCD arithmetic. Always start a BRK handler with `CLD` on NMOS to be safe.

```asm
.my_brk_handler
    CLD            ; mandatory on NMOS
    LDX #&FF : TXS
    ; ...
```
