---
title: Screen Modes
type: video
tags: [modes, screen-memory, pixel-format]
sources: [naug-ch13-video, master-arm]
updated: 2026-05-13
---

# Screen Modes

Eight MODEs (0-7) on BBC Model B / B+ / Master. Each is a particular combination of resolution, colour depth, screen RAM base, and 6845/Video-ULA register settings.

## Summary

| Mode | Graphics | Text | Colours | Bits/pixel | Screen base | Screen size | Bytes/row | Bytes/screen |
|---|---|---|---|---|---|---|---|---|
| 0 | 640×256  | 80×32 | 2  | 1 | `&3000` | 20 KB | 640  | 20480 |
| 1 | 320×256  | 40×32 | 4  | 2 | `&3000` | 20 KB | 640  | 20480 |
| 2 | 160×256  | 20×32 | 16 | 4 | `&3000` | 20 KB | 640  | 20480 |
| 3 | (text)   | 80×25 | 2  | 1 | `&4000` | 16 KB | 640  | 16000 |
| 4 | 320×256  | 40×32 | 2  | 1 | `&5800` | 10 KB | 320  | 10240 |
| 5 | 160×256  | 20×32 | 4  | 2 | `&5800` | 10 KB | 320  | 10240 |
| 6 | (text)   | 40×25 | 2  | 1 | `&6000` | 8 KB  | 320  | 8000  |
| 7 | (text)   | 40×25 | teletext | — | `&7C00` | 1 KB | 40 | 1000 |

Screen always ends at `&7FFF` on a non-shadow Model B. On B+/Master in shadow mode the screen lives at `&3000-&7FFF` in the shadow bank regardless of MODE (see [[memory/shadow-ram]]).

## Shadow modes (128-135) on B+/Master

Per [[sources/master-arm]] Ch 6, modes 128-135 are MOS-managed shadow variants of modes 0-7. They use the same VIDPROC and CRTC programming as their 0-7 counterparts, but the screen RAM lives in LYNNE rather than main memory — so user code retains `&3000-&7FFF` in the main map for code/data.

| Mode | Equivalent of | Notes |
|---|---|---|
| 128 | MODE 0 | 20 KB in LYNNE |
| 129 | MODE 1 | 20 KB in LYNNE |
| 130 | MODE 2 | 20 KB in LYNNE |
| 131 | MODE 3 | 20 KB reserved in LYNNE (16 KB used) |
| 132 | MODE 4 | 20 KB reserved in LYNNE (10 KB used) |
| 133 | MODE 5 | 20 KB in LYNNE (10 KB used) |
| 134 | MODE 6 | 20 KB reserved (8 KB used) |
| 135 | MODE 7 | 20 KB reserved (1 KB used; MOS may reuse the spare 19 KB for inter-FS transfers) |

The "20 KB reserved" rows show LYNNE's fixed allocation — even modes 3/4/5/6/7 that "use" less still occupy a 20 KB slot in shadow. This matters when calculating how much shadow you have available for double-buffering (see [[memory/shadow-ram]]).

Source: NAUG §13.4 p210-217 (per-mode diagrams), §13.2 page-3 `&356` "Size of screen memory: 20K=0,16K=1,10K=2,8K=3,1K=4".

## Byte → pixel layout (modes 0-6)

The screen is laid out in **character cells of 8 scan lines**. Within a cell, 8 bytes occupy 8 consecutive memory addresses (one byte per scan line). Cells are laid out **left-to-right then top-to-bottom in rows of cells**. This is why hardware scrolling is in character-row units — see [[video/hardware-scrolling]].

Pixel bit assignment within a byte:

### MODE 0, 3, 4, 6 (2-colour, 1 bit/pixel)

```
bit:    7  6  5  4  3  2  1  0
pixel:  P0 P1 P2 P3 P4 P5 P6 P7   (leftmost = bit 7)
```

### MODE 1, 5 (4-colour, 2 bits/pixel)

**Four pixels per byte.** Pixel 0 is leftmost (highest-priority bits), pixel 3 rightmost. The 2-bit colour index for each pixel is **split across the two nibbles** of the byte: high nibble holds the four MSBs (in pixel order), low nibble holds the four LSBs (in pixel order).

```
bit:    7   6   5   4   3   2   1   0
pixel:  M0  M1  M2  M3  L0  L1  L2  L3

       \_______________/\_______________/
            MSB nibble       LSB nibble
            (pixels 0-3)     (pixels 0-3)
```

Where `Mn` = MSB of pixel n's 2-bit colour, `Ln` = LSB. So the colour index for pixel 0 is `(M0 << 1) | L0` = `((byte & &80) >> 6) | ((byte & &08) >> 3)`.

To plot a single pixel without disturbing the others, you mask with the **two-bit pair pattern** for that pixel position:

| Pixel | Mask (colour=11, both bits set) | Mask (colour=10, MSB only) | Mask (colour=01, LSB only) |
|---|---|---|---|
| 0 | `%10001000` (`&88`) | `%10000000` (`&80`) | `%00001000` (`&08`) |
| 1 | `%01000100` (`&44`) | `%01000000` (`&40`) | `%00000100` (`&04`) |
| 2 | `%00100010` (`&22`) | `%00100000` (`&20`) | `%00000010` (`&02`) |
| 3 | `%00010001` (`&11`) | `%00010000` (`&10`) | `%00000001` (`&01`) |

NAUG §13.3.12 p202 only gives the MODE 2 layout explicitly. The MODE 1/5 layout above follows from how the Video ULA serialises pixel data: in 4-colour modes the ULA emits 2 bits per "dot" (NAUG §13.3.13 p213 — "in the four colour modes each dot is represented by two bits"), and Acorn keeps the high-nibble/low-nibble = MSB/LSB convention consistent across all multi-colour modes.

### MODE 2 (16-colour, 4 bits/pixel)

**Two pixels per byte**, each defined by 4 interleaved bits (NAUG §13.3.12 p202):

```
bit:    7   6   5   4   3   2   1   0
pixel:  P2d P1d P2c P1c P2b P1b P2a P1a
```

- `P1a..P1d` = pixel 1's 4-bit colour (a=LSB).
- `P2a..P2d` = pixel 2's 4-bit colour.

Same interleaving principle as MODE 1/5 but with 4 bits per pixel instead of 2: every odd bit position carries pixel-1's bits, every even bit position carries pixel-2's bits. The byte-aligned sprite movement performance win in [[techniques/fast-animation]] comes from this layout — moving a whole byte moves both pixels together.

### MODE 7 (teletext)

1 byte per character. Screen RAM is `&7C00-&7FFF` (1 KB, but only `&7C00-&7FE7` is displayed). Characters are interpreted by the [[hardware/saa5050]] teletext chip, not the Video ULA serialiser. Hardware scrolling uses a different correction — see [[video/hardware-scrolling#mode-7]].

## "6845 chars" vs "displayed chars"

The 6845 always emits 80 chars/line in modes 0-3 and 40 chars/line in modes 4-7 (R1). The Video ULA stretches each char to occupy more pixels in lower-colour modes — see [[hardware/video-ula]] bits 2-3 of `&FE20`. This is why **all 0-6 modes use 640 bytes per scanline-row** but show different pixel counts.

Important consequence: hardware-scrolling sideways moves by **1 byte = 1 6845 char**. The pixel cost per byte-step depends on how many pixels the ULA stretches one 6845 char into:

| Mode | 6845 chars / line | Displayed pixels | Pixels per 6845-char step |
|---|---|---|---|
| 0 | 80 | 640 | **8 pixels** |
| 1 | 80 | 320 | **4 pixels** |
| 2 | 80 | 160 | **2 pixels** |
| 4 | 40 | 320 | **8 pixels** |
| 5 | 40 | 160 | **4 pixels** |

For smooth horizontal hardware scrolling, MODE 2 wins (2-pixel jumps); MODE 5 is the cheapest middle ground (4-pixel jumps in 10 KB of screen RAM).

## Address arithmetic

To find the byte address of pixel (x, y) in modes 0-6:

```
char_x  = x DIV pixels_per_char   ; 8, 4, 2 for 1/2/4 bpp
char_y  = y DIV 8
scan    = y MOD 8
addr    = screen_base + char_y * bytes_per_row + char_x * 8 + scan
```

Where `bytes_per_row` is the screen width in bytes (640 for 80-col modes, 320 for 40-col modes 4-6).

This 2D-into-1D layout is unusual — the screen is **column-major within a row of cells, row-major over rows**. Per-pixel plotting touches 8 bytes for the cell. See [[techniques/pixel-plot]] (planned).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
