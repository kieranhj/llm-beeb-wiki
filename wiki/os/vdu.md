---
title: VDU Control Codes
type: os
tags: [vdu, control-codes, ascii, mos, screen]
sources: [bbc-user-guide]
updated: 2026-05-16
---

# VDU Control Codes

ASCII codes 0-31 (plus 127) are interpreted by the MOS **VDU driver** as control codes, not printable characters. `VDU n` in BASIC is equivalent to `PRINT CHR$(n);`. Sending a control code to `OSWRCH` (or `OSASCI`) triggers the same dispatch — this is how all high-level languages (BASIC, Pascal, COMAL, FORTRAN) and assembly code paint the screen, draw graphics, scroll, change colours, set windows, switch modes.

Many control codes require **additional parameter bytes** that follow the code. The MOS VDU driver counts those bytes via the **VDU queue** at `&31F-&323` (5 bytes) — see [[memory/os-workspace]] page 3 layout. The driver only acts when all expected bytes have arrived.

## Quick reference (VDU 0-31 + 127)

| Dec | Hex | Ctrl | Bytes | Effect |
|---|---|---|---|---|
| 0 | `&00` | `@` | 0 | NUL — does nothing |
| 1 | `&01` | `A` | 1 | Send next character to **printer only** |
| 2 | `&02` | `B` | 0 | **Enable printer** (all output → printer too) |
| 3 | `&03` | `C` | 0 | **Disable printer** |
| 4 | `&04` | `D` | 0 | Write text at **text cursor** (default) |
| 5 | `&05` | `E` | 0 | Write text at **graphics cursor** |
| 6 | `&06` | `F` | 0 | **Enable** VDU drivers (re-enables after VDU 21) |
| 7 | `&07` | `G` | 0 | **BEEP** — short tone via sound channel 1 |
| 8 | `&08` | `H` | 0 | **Backspace** cursor (no delete) |
| 9 | `&09` | `I` | 0 | **Forward-space** cursor (TAB) |
| 10 | `&0A` | `J` | 0 | **Line feed** (cursor down 1) |
| 11 | `&0B` | `K` | 0 | Cursor **up** 1 |
| 12 | `&0C` | `L` | 0 | **Clear text area** (CLS) |
| 13 | `&0D` | `M` | 0 | Carriage return — cursor to start of current line |
| 14 | `&0E` | `N` | 0 | **Paged mode ON** |
| 15 | `&0F` | `O` | 0 | Paged mode OFF |
| 16 | `&10` | `P` | 0 | **Clear graphics area** (CLG) |
| 17 | `&11` | `Q` | 1 | **Define text colour** (`COLOUR n`) |
| 18 | `&12` | `R` | 2 | **Define graphics colour** (`GCOL mode, colour`) |
| 19 | `&13` | `S` | 5 | **Define logical colour** (palette) — see below |
| 20 | `&14` | `T` | 0 | **Restore default** logical colours |
| 21 | `&15` | `U` | 0 | **Disable** VDU drivers (silence screen output) |
| 22 | `&16` | `V` | 1 | **Select screen MODE** (`MODE n`) |
| 23 | `&17` | `W` | 9 | **Re-program character / CRTC / extended ops** — see below |
| 24 | `&18` | `X` | 8 | Define **graphics window** (4 × 2-byte coords) |
| 25 | `&19` | `Y` | 5 | **PLOT k, x, y** — graphics primitive |
| 26 | `&1A` | `Z` | 0 | **Restore default windows** (full-screen text + graphics) |
| 27 | `&1B` | `[` | 0 | ESC — does nothing in VDU driver (handled by OSRDCH) |
| 28 | `&1C` | `\` | 4 | Define **text window** |
| 29 | `&1D` | `]` | 4 | Define **graphics origin** |
| 30 | `&1E` | `^` | 0 | **Home text cursor** (top-left of text window) |
| 31 | `&1F` | `_` | 2 | **Move text cursor** to (x, y) char position |
| 127 | `&7F` | DEL | 0 | **Backspace and delete** character |

## VDU 17 — text colour

```
VDU 17, c
```

`c` < 128: foreground; `c` ≥ 128: background. `c` is **modulo number of colours** in the current mode (so `c=4` in MODE 5 = `c=0`). Equivalent to BASIC `COLOUR c`.

## VDU 18 — graphics colour (GCOL)

```
VDU 18, mode, colour
```

`mode` selects the plotting operation:

| Mode | Action |
|---|---|
| 0 | **Plot** the colour (overwrite) |
| 1 | **OR** with existing |
| 2 | **AND** with existing |
| 3 | **EOR** with existing — useful for XOR sprites |
| 4 | **Invert** existing (colour byte ignored) |

`colour` ≥ 128 sets the graphics background; < 128 sets foreground.

EOR mode (3) is the classic technique for **non-destructive sprites** — XOR a sprite onto the screen, do whatever, XOR again to remove it cleanly. Master adds modes 5 (leave unchanged) and ECF patterns (16n+0..5).

## VDU 19 — logical → physical colour

```
VDU 19, logical, physical, 0, 0, 0
```

Sets logical colour `logical` to show as physical colour `physical`. The three trailing zeros are reserved (future expansion never used). Equivalent to BASIC `VDU 19,L,P,0,0,0` or via OSWORD `&0C`.

For the underlying Video ULA mechanism (8 palette entries written per 2-colour mode, etc.) see [[hardware/video-ula]] "Logical colour matching" section.

Physical colour codes:

| Code | Colour | Code | Colour |
|---|---|---|---|
| 0 | Black | 8 | Flash 0↔7 |
| 1 | Red | 9 | Flash 1↔6 |
| 2 | Green | 10 | Flash 2↔5 |
| 3 | Yellow | 11 | Flash 3↔4 |
| 4 | Blue | 12 | Flash 4↔3 |
| 5 | Magenta | 13 | Flash 5↔2 |
| 6 | Cyan | 14 | Flash 6↔1 |
| 7 | White | 15 | Flash 7↔0 |

## VDU 23 — extended commands

`VDU 23,n,b1,b2,b3,b4,b5,b6,b7,b8` (always 9 parameter bytes). `n` selects the sub-function:

| n | Function |
|---|---|
| 0 | **Write CRTC register**: `VDU 23,0, R, X, 0,0,0,0,0,0` → register R ← X. See [[hardware/crtc-6845]]. |
| 1 | **Cursor on/off**: `VDU 23,1, n, 0,0,0,0,0,0,0` — n=0 off, n=1 default. Master adds n=2 (steady) and n=3 (flash) |
| 2-5 | **ECF pattern set** (Master only — per [[sources/master-arm]] App 2). Patterns 1-4 = VDU 23,2 to 5 |
| 6 | **Dotted-line pattern** (Master only) |
| 7 | **Direct window scroll** (Master only) |
| 8 | **Clear block of text** (Master only) |
| 9 | First flash period (Master adds VDU form — `*FX 9` on Model B) |
| 10 | Second flash period (Master — `*FX 10` on Model B) |
| 11 | Set default ECF patterns (Master) |
| 12-15 | Set simple ECF pattern (Master) |
| 16 | Cursor movement control (Master) |
| 17-26 | Reserved (Master) |
| 27 | Acornsoft sprites |
| 28-31 | Application-reserved — routed through `VDUV` (`&226/&227`) |
| 32-255 | **Define user character**: `VDU 23, char, b0,b1,b2,b3,b4,b5,b6,b7` — 8 bytes of 8 pixels each. Top row first, MSB = leftmost pixel. |

User-definable character range: **224-255** on Model B (32 chars; per [[sources/bbc-user-guide]] Ch 34). Master can also define 128-159 (per [[sources/master-arm]]). The character data lives at `&0C00-&0CFF` on Model B (Page C) and at `&8900-&8FFF` on Master (second 32 KB — see [[memory/os-workspace]]).

## VDU 25 — PLOT (graphics primitive)

```
VDU 25, k, xlo, xhi, ylo, yhi
```

Equivalent to BASIC `PLOT k, x, y`. Coordinates are in **external graphics coordinates** (0-1279 × 0-1023). `k` selects the operation (256 codes); see [[video/plot-codes]] for the full table.

The `;` punctuation in `VDU 25, k, x;y;` form sends the X and Y values as 2-byte pairs (low byte first). The two forms are equivalent:
- `VDU 25, 4, 100; 500;` ↔ `VDU 25, 4, 100, 0, 244, 1` (500 = `&01F4` → `244, 1`).

## VDU 24 / 28 / 29 — windows

```
VDU 24, leftX;bottomY;rightX;topY;   ; graphics window (8 bytes)
VDU 28, leftX, bottomY, rightX, topY  ; text window (4 bytes; char units)
VDU 29, originX; originY;             ; graphics origin (4 bytes)
```

Text-window coords are in **character cells**; max depends on mode (39 × 31 in MODE 0/1, 19 × 31 in MODE 2/5, 39 × 24 in MODE 3/6/7). Graphics-window coords are 16-bit external graphics units.

`VDU 26` restores both windows to full screen and resets the graphics origin to (0,0) at bottom-left.

## VDU 31 — text cursor positioning

```
VDU 31, x, y
```

Move text cursor to character position (x, y) within the **current text window**. Equivalent to BASIC `PRINT TAB(x, y);`.

## Programmatic invocation

### From BASIC

```basic
VDU 22, 1                  : REM MODE 1
VDU 23, 240, 24,24,24,255,255,24,24,24      : REM define char 240 (+)
VDU 19, 1, 4, 0,0,0        : REM set logical 1 to physical 4 (blue)
VDU 25, 4, 100; 500;       : REM PLOT 4, 100, 500
```

### From assembly via OSWRCH

```asm
LDA #22 : JSR &FFEE        ; VDU 22 (mode select)
LDA #1  : JSR &FFEE        ; mode 1
```

Each byte of the VDU sequence goes through `OSWRCH` (`&FFEE`). The VDU queue at `&31F-&323` buffers incoming parameters until the count for the active control code is reached, then dispatches.

### Bulk VDU sequences

For long sequences (e.g. CRTC reprogramming), each VDU byte still costs an OSWRCH (`&FFEE`) dispatch unless you're willing to bypass the driver. For tight inner loops the BBC convention is either: (a) accept the OSWRCH cost (still much faster than BASIC `VDU`), or (b) write directly to the chip you're targeting (CRTC at `&FE00/&FE01`, ULA at `&FE20/&FE21`) and skip the VDU driver altogether — the [[techniques/custom-modes]] pattern.

## What changes between models

- Model B / B+ / Master: VDU 0-31 + 127 all behave identically (compatibility-critical).
- Master adds many VDU 23,n sub-functions (ECF patterns, direct scroll, clear block, cursor options).
- Master extends VDU 18 with `mode = 5` (leave unchanged) and ECF modes (16n+).
- VDU 23 char defs land at different addresses depending on model — see [[synthesis/model-differences]].

## See also

- [[video/plot-codes]] — full PLOT k=0-255 reference.
- [[hardware/video-ula]] — palette mechanics behind VDU 19.
- [[hardware/crtc-6845]] — CRTC register reference behind VDU 23,0.
- [[memory/os-workspace]] — Page 3 VDU workspace layout.
- [[os/calls]] — OSWRCH / OSWORD entry points.
- [[techniques/custom-modes]] — bypassing VDU for direct CRTC + ULA control.
- [[sources/bbc-user-guide]] — Ch 34, the canonical primary source.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
