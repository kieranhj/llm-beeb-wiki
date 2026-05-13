---
title: OS Calls (entry points + vectors)
type: os
tags: [mos, vectors, oswrch, osrdch, oscli, osword, osbyte]
sources: [naug-ch06-os-introduction]
updated: 2026-05-13
---

# OS Calls — Entry Points & Vectors

The MOS exposes its API through fixed entry points in high ROM (`&FF**`). Most of them JMP-indirect through a vector in page 2, allowing interception.

| Routine | Entry | Vector | A holds | Function |
|---|---|---|---|---|
| OSCLI   | `&FFF7` | `&208` CLIV | — | Execute *-command (X+Y = command address) |
| OSBYTE  | `&FFF4` | `&20A` BYTEV | call # | OSBYTE dispatcher |
| OSWORD  | `&FFF1` | `&20C` WORDV | call # | OSWORD dispatcher |
| OSWRCH  | `&FFEE` | `&20E` WRCHV | char | Write char to current output stream |
| OSNEWL  | `&FFE7` | — | — | Write LF+CR (calls OSWRCH twice) |
| OSASCI  | `&FFE3` | — | char | Write char; if `&D` writes LF+CR |
| OSRDCH  | `&FFE0` | `&210` RDCHV | — | Read char from current input stream → A; C=1 if error |
| OSFILE  | `&FFDD` | `&212` FILEV | op | File load/save (param block in X+Y) |
| OSARGS  | `&FFDA` | `&214` ARGSV | op | File arguments |
| OSBGET  | `&FFD7` | `&216` BGETV | — | Get byte from file (Y=handle) → A |
| OSBPUT  | `&FFD4` | `&218` BPUTV | byte | Put byte to file (Y=handle) |
| OSGBPB  | `&FFD1` | `&21A` GBPBV | op | Multi-byte file I/O |
| OSFIND  | `&FFCE` | `&21C` FINDV | op | Open/close file |
| NVWRCH  | `&FFCB` | — | char | Non-vectored OSWRCH (faster, no Tube) |
| NVRDCH  | `&FFC8` | — | — | Non-vectored OSRDCH |
| GSREAD  | `&FFC5` | — | — | Read char from GSINIT string |
| GSINIT  | `&FFC2` | — | — | Init for GSREAD |
| OSEVEN  | `&FFBF` | — | event # | Generate an event |
| OSRDSC  | `&FFB9` | — | — | Read byte from screen / paged ROM |
| OSWRSC  | `&FFB3` | — | val | Write byte to screen |

Plus interceptable vectors with no fixed entry point:

| Vector | Address | Triggered by |
|---|---|---|
| USERV | `&200` | Unknown OSWORD `&E0-&FF`, custom user use |
| BRKV | `&202` | BRK instruction |
| IRQ1V | `&204` | All maskable IRQs (high priority) |
| IRQ2V | `&206` | MOS-unrecognised IRQs (low priority) |
| FSCV | `&21E` | Filing-system control entry |
| EVNTV | `&220` | Event dispatch |
| UPTV | `&222` | User print |
| NETV | `&224` | Econet |
| VDUV | `&226` | Unrecognised VDU command (e.g. `VDU 23,17..31`) |
| KEYV | `&228` | Keyboard |
| INSV | `&22A` | Insert into buffer |
| REMV | `&22C` | Remove from buffer |
| CNPV | `&22E` | Count / purge buffer |
| IND1V/IND2V/IND3V | `&230`/`&232`/`&234` | Spare |

## Calling conventions

- **A**: primary parameter / call selector.
- **X, Y**: secondary parameters, or parameter-block address LSB+MSB.
- **C, N, V, Z**: undefined on return unless the call specifies otherwise.
- **A, X, Y**: preserved on return for most calls (OSWRCH preserves all three). OSCLI and OSEVEN are exceptions.
- **Interrupt status**: preserved on return, but **may be enabled during the call**. So you cannot call OS routines from inside an IRQ handler — the inner CLI will re-enable IRQs and a nested interrupt will overwrite zp `&EF-&F1`, `&FC` etc.
- **D flag must be clear** before any OS call.

## OSWRCH details

```asm
LDA #'A'
JSR &FFEE       ; or JMP (&20E) from your own re-implementation
```

Writes to the **currently selected output stream(s)**. Default: VDU + printer (if `VDU 2`) + spool (if `*SPOOL`). Controlled by OSBYTE `&03` mask.

Cost varies widely:
- VDU only, plain ASCII to MODE 7: ~400 cycles
- VDU only, MODE 0 with 1bpp pixel rendering: ~1500 cycles (font lookup + 8 byte writes)
- Multi-stream (printer + spool): add the printer driver overhead

For **fast text output** in MODE 0/1/2/4/5: render glyphs yourself by reading the font definitions from MOS ROM (or your own font) and `STA` to screen RAM directly. OSWRCH is the slowest possible way to put a character on screen.

## OSRDCH details

```asm
JSR &FFE0
BCS error       ; C=1 means read error (ESCAPE etc.)
; A = character read
```

Blocks until a character is available. To poll instead, use OSBYTE `&81` with a timeout, or read `&FF` (Escape flag) and the key buffer directly.

## OSCLI details

```asm
LDX #cmd_str MOD 256
LDY #cmd_str DIV 256
JSR &FFF7

.cmd_str
EQUS "FX 15,0"
EQUB &0D        ; CR terminator
```

Equivalent to typing the command at the BASIC prompt. Slow (parser overhead) but powerful — any `*` command works.

## Non-vectored variants

`NVWRCH` (`&FFCB`) and `NVRDCH` (`&FFC8`) skip the indirection through `&20E`/`&210`. Save 3 cycles per call. **But**: not available across the Tube (second processors require the vectored version to forward I/O over the Tube link). Useful in time-critical I/O loops where you're sure no Tube is present.

## Bypassing OSWRCH entirely

For a tight character-printing loop, OSWRCH overhead dominates. Three faster paths:

1. **Pre-render strings**: build the screen-RAM byte sequence once at startup, `STA`/`LDA` directly each frame.
2. **Inline glyph writer**: JSR to a routine that does font-lookup + 8× STA to screen RAM. Skip MOS entirely.
3. **VDU queue stuffing**: write directly into the VDU queue at `&323` and decrement `&DA` (VDU queue count) — bypasses dispatcher cost. Rarely worth it; #1 or #2 wins.

In hot game loops, #1 (precompose) is almost always the right answer.

## See also

- `[[os/osbyte]]` and `[[os/osword]]` — directory tables.
- `[[os/interrupts]]` — IRQ vector chain.
- `[[os/brk]]` — BRK protocol.
- `[[memory/os-workspace]]` — Page 2 vector table + OS variables.
