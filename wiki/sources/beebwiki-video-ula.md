---
title: "BeebWiki: Video ULA"
type: source
tags: [video, ula, palette]
url: https://beebwiki.mdfs.net/Video_ULA
updated: 2026-05-14
---

# BeebWiki — Video ULA

**URL:** https://beebwiki.mdfs.net/Video_ULA

## Summary

BBC-specific reference for the Acorn Video ULA. Adds: per-mode default palette tables, low-level shift-register / palette-CAM mechanics, undefined-behaviour gotchas (80 cols at 1 MHz, 10 cols at 2 MHz), the unofficial extra-mode control values, and historical / hardware notes (Ferranti heatsink, Model A failed-test units, VideoNuLA replacement).

## Key technical claims

### Manufacturing / hardware

- Acorn part 201,647. Original Ferranti ULA 5C094; second source VLSI Tech VIDPROC VC 2023, later VC 2069.
- IC 6 on the motherboard. Connected to DRAM data bus at 4 MHz (multiplexed: 2 MHz CPU access + 2 MHz video access).
- Pin 8 = 16 MHz input. Pins 7/6/5/4 output divided clocks: 8/4/2/1 MHz.
- Pin 26 = DISEN (CRTC blanking → forces RGB low).
- Pin 27 = INVERT (linked to S26 — selects normal or reverse video).
- Pins 14/12/10 = R/G/B output.
- Original Ferranti part runs warm — needs heatsink; effectively overclocked at the standard 16 MHz.
- Model A units sometimes shipped with Video ULAs that failed the high-resolution-mode acceptance test (acceptable because Model A's 16 KiB RAM cannot drive MODES 0-2). Owners who upgraded to 32 KiB sometimes saw bad MODES 0/1/2.

### Operation

- Each fetched byte clocked into a shift register. Bits 1, 3, 5, 7 of the shift register address the 16-entry × 4-bit palette CAM.
- Palette outputs `~R, ~G, ~B, flash` (bits 0-3).
- If `flash bit ∧ control_reg[0]` = 1, inverted RGB passes through; otherwise re-inverted to true RGB. Net effect: palette stores inverted RGB; flash bit toggles inversion.
- Effective 4 bits per pixel in all modes (extras may belong to following pixels — palette must be programmed to cover all combinations).
- Cursor: CRTC's CURSOR pin → temporarily inverts the RGB output stream during the configured cursor segments.

### Shift register clock rates

| Modes | Shift clock |
|---|---|
| 0, 3 | 16 MHz |
| 1, 4, 6 | 8 MHz |
| 2, 5 | 4 MHz |

### Control register `&FE20` (write-only, MOS RAM copy `&248`)

| Bits | Field |
|---|---|
| 7-5 | Cursor segments 0, 1, 2 |
| 4 | Clock rate: 0 = 1 MHz (40 bytes/scanline); 1 = 2 MHz (80 bytes/scanline) |
| 3-2 | Number of columns |
| 1 | Teletext select (0 = serialiser, 1 = SAA 5050) |
| 0 | Flash enable |

**Preferred update path:** OSBYTE 154 (`&9A`) with X = new value. Direct STA bypasses MOS shadow.

**Cursor segment widths:** segment 0 and 1 are each 1/40 or 1/80 of display width (per bit 4). Segment 2 is twice segment 1's width.
- ASCII modes: segment 0 always enabled (left column edge of cursor)
- MODE 7: only segment 1 enabled (compensates 1-char Teletext pipeline delay)

### Column-count field (bits 3-2)

| b3 | b2 | Columns | Pixel rate |
|---|---|---|---|
| 0 | 0 | 10 | 2 MHz |
| 0 | 1 | 20 | 4 MHz |
| 1 | 0 | 40 | 8 MHz |
| 1 | 1 | 80 | 16 MHz |

**Undefined-but-observed cases:**
- **80 columns selected with 1 MHz clock (bit 4 clear, bits 3-2 = 11)**: shift register empties partway through each character. Every other text column is blank (logical colour 15).
- **10 columns selected with 2 MHz clock (bit 4 set, bits 3-2 = 00)**: only odd bits of each fetched byte affect the display.

These would be useful for some custom-mode effects but rarely seen in software.

### Default per-mode control register values (MOS 1.20 `&C3F7-&C3FE`)

| MODE | Hex | Binary |
|---|---|---|
| 0 | `&9C` | `1001 1100` |
| 1 | `&D8` | `1101 1000` |
| 2 | `&F4` | `1111 0100` |
| 3 | `&9C` | `1001 1100` |
| 4 | `&88` | `1000 1000` |
| 5 | `&C4` | `1100 0100` |
| 6 | `&88` | `1000 1000` |
| 7 | `&4B` | `0100 1011` |

### Unofficial / extra MODE control values

| MODE | Hex | Binary |
|---|---|---|
| 8 | `&E0` | `1110 0000` |
| 9 | `&80` | `1000 0000` |
| 10 | `&84` | `1000 0100` |

(Not the same as the BBC community's "MODE 8" 16-colour LF mode synthesised in `[[synthesis/mode-8-16colour-lf]]` — see notes there.)

### Palette register `&FE21` (write-only, MOS RAM copy `&249`)

| Bits 7-4 | Bits 3 | 2 | 1 | 0 |
|---|---|---|---|---|
| Logical-colour selector | Flash | ~Blue | ~Green | ~Red |

**Preferred update path:** OSBYTE 155 (`&9B`). Pass real (un-inverted) colour in low 4 bits of X; OSBYTE inverts bits 0/1/2 before writing.

Internal CAM: 16 × 4-bit fast static RAM. Write stores bits 3-0 in the word addressed by bits 7-4. When the same word is later addressed by shift register bits 7/5/3/1, the stored 4 bits drive the output (bits 0-2 inverted again unless flash-and-control-bit-0 conspire to keep them inverted).

### Default palette write sequences (after VDU 20)

**MODES 0, 3, 4, 6:** `80 90 A0 B0 C0 D0 E0 F0 07 17 27 37 47 57 67 77`

**MODES 1, 5:** `A0 B0 E0 F0 84 94 C4 D4 26 36 66 76 07 17 47 57`

**MODE 2:** `F8 E9 DA CB BC AD 9E 8F 70 61 52 43 34 25 16 07`

These are the actual `&FE21` byte streams MOS issues — useful when bypassing OSBYTE `&9B` / VDU 19 entirely.

### Third-party hardware

- **Palettemate** (1986, Wild Vision): 4096 colours, up to 16 on screen.
- **Chameleon** (1990, Mike Cook): post-ULA RGB → user-port-controlled 4096 palette.
- **VideoNuLA** (Rob Coleman): drop-in replacement at IC 6, samples A1 via flying lead. 12-bit colour depth (16 from 4096), pixel-by-pixel horizontal hardware scrolling, attribute modes.

## Cross-check against existing wiki

All defaults and bit assignments match our existing `[[hardware/video-ula]]` page. Material to add:
- 80@1MHz / 10@2MHz observed undefined behaviour
- Default palette write-sequence tables (3 mode groups)
- Clock divider output pin numbers (8/4/2/1 MHz on pins 7/6/5/4)
- Shift register clock rate per MODE (16/8/4 MHz)
- VideoNuLA mention

## Filed into

- Updated: `[[hardware/video-ula]]` (added gotchas, default palette tables, clock-pin notes, second-source citation).
