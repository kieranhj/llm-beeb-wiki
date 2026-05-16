---
title: '"MODE 8" — 16-colour low-frequency mode'
type: synthesis
tags: [custom-mode, mode-8, 16-colour, low-frequency, crtc, video-ula]
sources: [naug-ch13-video, naug-ch22-vias]
updated: 2026-05-13
---

# "MODE 8" — 16-colour low-frequency mode

"MODE 8" is community jargon — Acorn never defined a MODE 8. The most common interpretation: **MODE 2's 16-colour pixel format running on MODE 5's CRTC timing**, yielding 80×256 at 16 colours in 10 KB. Same palette as MODE 2 with half the screen RAM (and double-wide chunky pixels).

See [[techniques/custom-modes]] for the general custom-mode recipe.

## The trick

The Video ULA's bits-per-pixel is implicitly set by the ratio **R1 ÷ ULA-displayed-chars**:

| R1 / ULA chars | bpp |
|---|---|
| 1 | 1 (2-colour) |
| 2 | 2 (4-colour) |
| 4 | 4 (16-colour) |

MODE 5 has R1=40 and ULA chars=20 → bpp=2. To get bpp=4 without changing the CRTC (and keeping the 10 KB screen), **halve the ULA chars setting** from 20 to 10. R1/chars becomes 40/10 = 4 → 16-colour interpretation, MODE 2 byte layout.

## Setup procedure

```asm
; Start from MODE 5 — sets all CRTC, palette mechanics, 22 KB wrap addend, 10 KB screen at &5800
LDA #22 : JSR &FFEE         ; VDU 22
LDA #5  : JSR &FFEE         ; ,5

; Switch the Video ULA control register from MODE 5 (&C4) to "MODE 8" (&E0)
LDA #&9A : LDX #&E0 : JSR &FFF4   ; OSBYTE &9A — Tube-safe write
```

For maximum speed in a game (no Tube), the direct path:

```asm
LDA #&E0 : STA &FE20
; OS shadow at the relevant page-3 byte goes stale — patch if mixing with MOS later
```

## All-register summary

### 6845 CRTC — unchanged from MODE 5

| Reg | Unit | Value | Note |
|---|---|---|---|
| R0  | chars       | 63 | LF total scanline |
| R1  | chars       | 40 | 40 bytes per scanline |
| R2  | chars       | 49 | hsync position |
| R3  | mixed       | `&24` | LF: 4-char hsync + 2-scanline vsync |
| R4  | char rows   | 38 | (38+1) × 8 = 312 scanlines @ 50 Hz |
| R5  | scanlines   | 0  | no fractional adjust |
| R6  | char rows   | 32 | 32 × 8 = 256 scanlines displayed |
| R7  | char rows   | 34 | vsync position |
| R8  | bits        | **0** for games (non-interlaced) / 1 for MODE-5-default | see [[techniques/custom-modes]] |
| R9  | scanlines-1 | 7  | 8 scanlines per char row |
| R12 | addr hi/8   | `&0B` | (&5800 / 8) >> 8 |
| R13 | addr lo/8   | `&00` | (&5800 / 8) & &FF |

### Video ULA control register `&FE20`

**`&E0` = `1110 0000`** (flash bit X)

| Bits | Field | Setting | Effect |
|---|---|---|---|
| 7-5 | Cursor width | `111` (4 char-times wide) | MODE-2-style wide cursor — matches the chunky pixels |
| 4 | 6845 clock | `0` (LF) | inherited from MODE 5 |
| 3-2 | Chars per displayed line | `00` (10 cells) | **the key change** vs MODE 5's `01` (20 cells) |
| 1 | Teletext | `0` | normal serialiser |
| 0 | Flash | X | OS-toggled |

If you don't care about cursor width (which you won't in a game), `&C0` works too (keeps MODE 5's 2-char cursor `110` but switches chars to `00`).

### Pixel layout

Each byte holds **2 pixels**, MODE 2 interleaved layout (NAUG §13.3.12):

```
bit:    7   6   5   4   3   2   1   0
pixel:  P2d P1d P2c P1c P2b P1b P2a P1a
```

Where `P1a..P1d` = pixel 1's 4-bit colour (a=LSB), `P2a..P2d` = pixel 2's 4-bit colour. See [[video/modes]] for the per-pixel mask patterns.

### Palette

16-colour rules ([[hardware/video-ula]]): every palette entry has a unique logical colour selector — write 16 distinct entries, no expansion. Use `OSWORD &0C` (a parameter block per logical colour) or `VDU 19`.

```basic
VDU 19,0,0,0,0,0          : REM logical 0 = black
VDU 19,1,1,0,0,0          : REM logical 1 = red
...
VDU 19,15,15,0,0,0        : REM logical 15 = flashing white-black
```

### Screen memory

`&5800-&7FFF` (10 KB) — same as MODE 5. Hardware-scroll wrap addend (22 KB) already set by `VDU 22,5`. No System VIA latch changes needed.

## Display geometry

- **Resolution**: 80 horizontal pixels × 256 vertical
- **Pixels per byte**: 2 (4 bpp)
- **Bytes per scanline**: 40 (R1)
- **Pixel aspect**: extremely chunky — each pixel is 8 dots wide horizontally (LF clock + 10 displayed cells × 8 dots = 80 dots = 80 pixels at 1 dot/pixel, but LF dots are twice as wide as HF dots). Effectively each pixel is ~8× as wide as it is tall. Art / sprites need to compensate.

## Why this matters

- **Half the RAM of MODE 2** for the same colour count. 10 KB vs 20 KB → 10 KB more free for code, sprites, level data.
- **MODE 2's byte-aligned sprite trick still works** ([[techniques/fast-animation]]): moving 1 byte = moving 2 pixels. The smaller pixel count means less data to push per frame.
- **Hardware scrolling**: identical to MODE 5 (10 KB window, 22 KB addend). 8-dot horizontal step per byte-step in R12/R13 = effectively a 1-pixel horizontal jump (since pixels are 8 dots wide). Smoothest hardware scrolling of any 16-colour mode on the BBC.

## Gotchas

- **MOS doesn't know about it** — page-3 VDU workspace still reads as MODE 5 (4 colours, 4 pixels/byte). `OSWRCH` will render text at MODE 5's byte stride but with MODE 2's pixel interpretation, producing garbled glyphs. Render text yourself.
- **Cursor**: if you want a visible text cursor, the 4-char-wide setting (`111`) is right for the chunky pixels. Otherwise hide it (set bits 5-7 to 0).
- **Pixel aspect**: 80×256 with 8:1 pixel aspect is extremely chunky. Visually like an Atari 2600 or Spectrum-attribute-mode look. Art has to be designed for this — sprites that look fine at 1:1 will appear severely vertically stretched.
- **Light pen, OSWORD `&09` (read pixel)**: broken in this mode for the usual MOS-bypass reasons.
- **`VDU 22,n` resets it.** Any soft BREAK reverts to MODE 5. Hook BREAK intercept (`OSBYTE &F7-&F9`) to re-apply.

## Alternative interpretations

Some sources use "MODE 8" to mean different things:

- **160×256 16-colour at LF** would need R1=80 and ULA chars=20 → bpp=4. But LF clock R0=63 caps R1 at 63 chars/scanline. **Not achievable** in a standard LF custom mode.
- **80×256 4-colour at LF** would just be a half-width MODE 5 (R1=20, ULA chars=10). Sometimes called "MODE 8" too. Less interesting since MODE 5 gives more pixels at the same colour depth.

The 80×256 16-colour interpretation above is the most common when people say "MODE 8" in scene context, because it's the one that buys you something MODE 2/5 don't: cheap 16-colour graphics.

## Derivation log

This synthesis was generated from the wiki on 2026-05-13. Key insight (the bpp = R1 / ULA-displayed-chars relationship) was derived from NAUG §13.3.13 p213 ("each character is 8 dots wide, video data clock must have 8, 16 or 32 cycles per character width") combined with the per-mode R1 and ULA chars-per-line values in [[hardware/video-ula]] and §13.3.3 p191.

The bpp-from-ratio derivation isn't called out explicitly in NAUG — it's inferable from the per-mode tables. Worth verifying on real hardware before relying on this mode's exact behaviour.

## See also

- [[techniques/custom-modes]] — General custom-mode recipe.
- [[hardware/crtc-6845]] — CRTC register reference.
- [[hardware/video-ula]] — Video ULA control register + palette mechanics.
- [[video/modes]] — MODE 2 pixel layout (which "MODE 8" inherits).
- [[techniques/fast-animation]] — MODE-2-byte-aligned sprite techniques.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
