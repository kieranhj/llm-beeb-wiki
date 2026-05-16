---
title: VDU Control Codes
type: os
tags: [vdu, control-codes, ascii, mos, screen]
sources: [bbc-user-guide, master-rm]
updated: 2026-05-16
---

# VDU Control Codes

ASCII codes 0-31 (plus 127) are interpreted by the MOS **VDU driver** as control codes, not printable characters. `VDU n` in BASIC is equivalent to `PRINT CHR$(n);`. Sending a control code to `OSWRCH` (or `OSASCI`) triggers the same dispatch — this is how all high-level languages (BASIC, Pascal, COMAL, FORTRAN) and assembly code paint the screen, draw graphics, scroll, change colours, set windows, switch modes.

Many control codes require **additional parameter bytes** that follow the code. The MOS VDU driver counts those bytes via the **VDU queue** at `&31F-&323` (5 bytes) — see [[memory/os-workspace]] page 3 layout. The driver only acts when all expected bytes have arrived. The byte count for the current pending command can be read via `OSBYTE &DA` (218).

Interpretation by character range (per [[sources/master-rm]] Ch E.1):

| ASCII | Modes 0-6 (and 128-134) | Mode 7 (and 135) |
|---|---|---|
| 0-31 | VDU commands | VDU commands |
| 32-126 | Characters to display | Characters to display |
| 127 | Backspace + delete | Backspace + delete |
| 128-159 | Characters to display | **Teletext control codes** |
| 160-255 | Characters to display | Characters to display |

The process of splitting the byte stream into commands and characters is called **parsing**. For graphics-window-pinned commands (PLOT, MOVE), the byte stream is queued via the VDU queue; once enough bytes are received, the command is dispatched.

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
| 4 | **Invert** existing (colour = EOR with `(num_colours - 1)`) |
| 5 | **Leave** screen colour unchanged (Master only) |

`colour` ≥ 128 sets the graphics background; < 128 sets foreground. Out-of-range values are reduced MOD (number of available colours).

EOR mode (3) is the classic technique for **non-destructive sprites** — XOR a sprite onto the screen, do whatever, XOR again to remove it cleanly.

### Master ECF (Extended Colour Fill) patterns

Per [[sources/master-rm]] Ch E.3, VDU 18 on the Master also accepts **mode = 16n+offset** to select one of four programmable ECF patterns instead of a solid colour:

| `mode` byte | Effect |
|---|---|
| `16+n` | ECF pattern 1 with sub-mode n (n = 0..5 = plot/OR/AND/EOR/invert/leave) |
| `32+n` | ECF pattern 2 with sub-mode n |
| `48+n` | ECF pattern 3 with sub-mode n |
| `64+n` | ECF pattern 4 with sub-mode n |

When using an ECF mode, `colour = 0` selects the pattern as foreground; `colour = 128` selects it as background. The patterns themselves are set via VDU 23,2..5 (full row definition) or VDU 23,12..15 (simple 2×4) — see below.

ECF gives you 4-bit dithering effects (greys, hatches, gradients) without burning a custom mode. Defaults per mode are listed under VDU 23,11 below.

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

`VDU 23,n,b1,b2,b3,b4,b5,b6,b7,b8` (always 9 parameter bytes after the leading `23`). `n` selects the sub-function:

| n | Function |
|---|---|
| 0 | **Write CRTC register**: `VDU 23,0, R, X, 0,0,0,0,0,0` → register R ← X. See [[hardware/crtc-6845]]. |
| 1 | **Cursor on/off**: n2=0 off, n2=1 on (default), n2=2 steady, n2=3 flash slow (Master) |
| 2 | Set ECF pattern 1 (8 row bytes; see below) |
| 3 | Set ECF pattern 2 |
| 4 | Set ECF pattern 3 |
| 5 | Set ECF pattern 4 |
| 6 | Set **dotted-line pattern**: 1 byte, MSB-first 8-bit pattern. `&FF`=solid, `&AA`=dot-space (default), `&EE`=dash-space |
| 7 | **Direct window scroll**: see "VDU 23,7" section below |
| 8 | **Clear block of text** (rectangular subregion): see below |
| 9 | First flash period (same as `*FX 9`) — 1 byte |
| 10 | Second flash period (same as `*FX 10`) — 1 byte |
| 11 | Set default ECF patterns for current mode (0 params) |
| 12-15 | Set **simple ECF** pattern 1..4 — 8 logical-colour bytes, paired in 2×4 grid |
| 16 | **Cursor movement control flags** — see below |
| 17-26 | Reserved (Master treats as user calls) |
| 27 | Reserved for Acornsoft sprites |
| 28-31 | **Application-reserved** — routed through `VDUV` (`&226/&227`) with C=1, A=23-sub-code |
| 32-255 | **Define user character**: 8 bytes of 8 pixels. Top row first; MSB = leftmost pixel. |

User-definable character range: **224-255** on Model B (32 chars; per [[sources/bbc-user-guide]] Ch 34). Master can also define 128-159 (per [[sources/master-arm]]). On Model B character data lives at `&0C00-&0CFF` (Page C); on Master at `&8900-&8FFF` in the second 32 KB (see [[memory/os-workspace]]).

### VDU 23,2..5 — ECF row-by-row pattern

8 bytes `n1..n8`, each defining one row top-to-bottom. The bit pattern of each byte (MSB → LSB) maps to logical colours of pixels left-to-right *depending on the colour depth of the current mode*:

| Mode bpp | Pixel-to-bit mapping (left → right) |
|---|---|
| 1 (2-colour) | bit7, bit6, bit5, bit4, bit3, bit2, bit1, bit0 (8 pixels) |
| 2 (4-colour) | bits7,3; bits6,2; bits5,1; bits4,0 (4 pixels) |
| 4 (16-colour) | bits7,5,3,1; bits6,4,2,0 (2 pixels) |

So one ECF row byte encodes 8 / 4 / 2 pixels depending on mode — matching exactly the screen-byte format of [[video/modes]].

### VDU 23,6 — dotted-line pattern

```
VDU 23,6, n, 0,0,0,0,0,0,0
```

`n` is read MSB→LSB; each `1` bit = dot, each `0` bit = space. Default `&AA`. Used by all dotted-line PLOT codes (16-23, 24-31, 48-55, 56-63 — see [[video/plot-codes]]).

### VDU 23,7 — direct window scroll

```
VDU 23,7, m, d, z, 0,0,0,0,0
```

| param | values |
|---|---|
| `m` | 0=text window, 1=entire screen |
| `d` | 0=right, 1=left, 2=down, 3=up, 4=+X (per cursor-direction flags), 5=-X, 6=+Y, 7=-Y |
| `z` | 0=1 character cell, 1=1 cell vertically + 1 byte horizontally (8/4/2 pixels by mode) |

Cursor is never moved. Useful for marquee effects and arcade-style sideways scrolling without burning the hardware-scroll lever (which moves the whole screen, not a window — see [[video/hardware-scrolling]]).

### VDU 23,8 — clear rectangular text block

```
VDU 23,8, t1, t2, x1, y1, x2, y2, 0, 0
```

`t1` and `t2` are **base-position codes** (start and end of block respectively):

| code | base |
|---|---|
| 0 | top-left of window |
| 1 | top of cursor column |
| 2 | off top-right of window |
| 4 | left end of cursor line |
| 5 | cursor position |
| 6 | off right of cursor line |
| 8 | bottom-left of window |
| 9 | bottom of cursor column |
| 10 | off bottom-right of window |

`x1,y1` and `x2,y2` are signed displacements (-128..+127) from those bases. Block is cleared to text background colour. Useful for partial clears without losing the rest of the window.

### VDU 23,11 — default ECF patterns

Resets all 4 ECF patterns to their per-mode defaults. The defaults differ between MODE 0 and MODE 4 (despite both being 1bpp) to avoid TV interference patterns — Mode 0 uses interlaced single-pixel dithers, Mode 4 uses 2-pixel-wide dithers.

Default pattern table per [[sources/master-rm]] Ch E.3 (full hex values listed in the source page):

| Mode | Pattern 1 | Pattern 2 | Pattern 3 | Pattern 4 |
|---|---|---|---|---|
| 0/128 | Dark grey | Grey | Light grey | Hatching |
| 1/5/129/133 | Red-orange | Orange | Yellow-orange | Cream |
| 2/130 | Orange | Pink | Yellow-green | Cream |
| 4/132 | Dark grey | Grey | Light grey | Hatching |

### VDU 23,12..15 — simple ECF pattern

```
VDU 23, 12+i, a, b, c, d, e, f, g, h
```

Lays out a 2×4 logical-colour grid: top row (a,b), then (c,d), (e,f), (g,h). Easier than computing the bit-pattern form when you just want a small repeat. Mode 0 doubles each pixel horizontally to avoid TV patterning.

### VDU 23,16 — cursor movement control flags

```
VDU 23, 16, x, y, 0,0,0,0,0,0
```

Cursor-direction byte is updated: `new = (old AND y) EOR x`. Affects all cursor-movement-after-print behaviour. Bit field:

| bit | 0 | 1 |
|---|---|---|
| 7 | normal | (undefined) |
| 6 | VDU 5: cursor-off-window triggers carriage-return | VDU 5: cursor-off-window does nothing |
| 5 | cursor moves after print | cursor doesn't move after print |
| 4 | VDU 4: cursor-off-Y scrolls; VDU 5: wraps to opposite edge | always wraps to opposite edge |
| 3-1 | direction encoding | (8 possible right/left/up/down orientations) |
| 0 | "scroll-protect off" — wrap eagerly | "scroll-protect on" — defer wrap until next char (pending CR/LF) |

Bits 3-1 encode 8 possible (X-direction, Y-direction) orientations:

| b3 b2 b1 | X direction | Y direction |
|---|---|---|
| 0 0 0 | right | down (default) |
| 0 0 1 | left | down |
| 0 1 0 | right | up |
| 0 1 1 | left | up |
| 1 0 0 | down | right |
| 1 0 1 | down | left |
| 1 1 0 | up | right |
| 1 1 1 | up | left |

Useful for vertical-text effects, RTL languages, and unusual layouts without writing custom output code. The "pending CR/LF" mode (bit 0 = 1) is what BBC scene calls "81-column mode" — you can print to the rightmost cell without immediately scrolling.

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
