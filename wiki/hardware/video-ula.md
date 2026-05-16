---
title: Acorn Video ULA
type: hardware
tags: [video, ula, palette, sheila]
sources: [naug-ch13-video, beebwiki-video-ula]
sheila: ["&FE20", "&FE21"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-05-14
---

# Acorn Video ULA

Custom Acorn chip — partner to the [[hardware/crtc-6845]]. Responsibilities:

- Generate the pixel clock (low-frequency / high-frequency) and supply it to the 6845.
- Serialise video data fetched from RAM into RGB output streams.
- Hold the 16-entry × 4-bit **palette** (logical → physical colour map).
- Control horizontal cursor width.
- Switch between in-chip serialiser and the [[hardware/saa5050]] teletext chip (MODE 7).

Two write-only Sheila registers (with MOS RAM shadows):

| Sheila | Name | MOS shadow (zero page) |
|---|---|---|
| `&FE20` | Video Control Register | `&248` |
| `&FE21` | Palette Register | `&249` |

**Clock-divider outputs**: pin 8 receives 16 MHz; output pins 7/6/5/4 supply divided 8/4/2/1 MHz to the rest of the board.

**Always write via OSBYTE `&9A` (control) and OSBYTE `&9B` (palette)** rather than direct STA. This keeps the OS's shadow copies consistent so Tube and other system services see the right state. OSBYTE `&9B` XORs the value with 7 internally — see palette section below.

## Video Control Register (`&FE20`)

| Bit | Field |
|---|---|
| 0 | Selected flash colour (toggled by OS at the flash rate) |
| 1 | 0=in-chip serialiser, 1=teletext input (SAA5050) |
| 2-3 | Number of displayed chars per line: `00`=10, `01`=20, `10`=40, `11`=80 |
| 4 | Clock rate: 0 = LF (1 MHz, 40 bytes/scanline); 1 = HF (2 MHz, 80 bytes/scanline) |
| 5-7 | Cursor segment enables (see below) |

### Shift-register clock rate per MODE

| Modes | Shift clock |
|---|---|
| 0, 3 | 16 MHz (1 bit/pixel) |
| 1, 4, 6 | 8 MHz (2 bits/pixel) |
| 2, 5 | 4 MHz (4 bits/pixel) |

(Effectively 4 bits per pixel always pass through the palette CAM — the lower-resolution modes simply hold each shift state for more dot-clocks.)

### Undefined-but-observed combinations

The chars-per-line bits (2-3) and the clock-rate bit (4) are independent — but two combinations behave oddly:

- **80 columns + 1 MHz** (bits 3-2 = `11`, bit 4 = 0): shift register empties partway through each character; every other text column displays as logical colour 15.
- **10 columns + 2 MHz** (bits 3-2 = `00`, bit 4 = 1): only odd bits of each fetched byte affect the display.

Both are useful curios for custom-mode work; not used by any standard MODE.

### Per-mode control register values (NAUG §13.3.13 p206)

Bit-field decode for the value MOS writes on each `VDU 22,n`. `X` marks the flash bit (bit 0), which the OS toggles continuously at the flash rate.

| Mode | Hex | Bin (b7..b0) | Cursor width (b7-5) | Clock (b4) | Chars/line (b3-2) | Teletext (b1) | Flash (b0) |
|---|---|---|---|---|---|---|---|
| 0 | `&9C` | `1001 110X` | `100` = 1 char (8 dots) | `1` HF | `11` = 80 | `0` serialiser | X |
| 1 | `&D8` | `1101 100X` | `110` = 2 chars (16 dots) | `1` HF | `10` = 40 | `0` serialiser | X |
| 2 | `&F4` | `1111 010X` | `111` = 4 chars (32 dots) | `1` HF | `01` = 20 | `0` serialiser | X |
| 3 | `&9C` | `1001 110X` | `100` = 1 char (8 dots) | `1` HF | `11` = 80 | `0` serialiser | X |
| 4 | `&88` | `1000 100X` | `100` = 1 char (8 dots) | `0` LF | `10` = 40 | `0` serialiser | X |
| 5 | `&C4` | `1100 010X` | `110` = 2 chars (16 dots) | `0` LF | `01` = 20 | `0` serialiser | X |
| 6 | `&88` | `1000 100X` | `100` = 1 char (8 dots) | `0` LF | `10` = 40 | `0` serialiser | X |
| 7 | `&4B` | `0100 101X` | `010` = 1 char (delayed) | `0` LF | `10` = 40 | `1` **teletext** | X (set in MODE 7 by default) |

Observations:

- **Bit 7 = 1 in all modes 0-6**, **0 only in MODE 7** — bit 7 is essentially "first 8 dots of cursor enabled". MODE 7's cursor is *delayed* by one character (driven by bit 6 alone) because the SAA5050 character generator pipelines its output one character behind the 6845's emitted address.
- **Cursor width scales with bpp**: 1 char in 1-bpp modes, 2 chars in 2-bpp, 4 chars in 4-bpp. Same on-screen physical width regardless of pixel depth, because each pixel occupies more dots in the lower-resolution modes.
- **HF/LF clock (bit 4) tracks** the 80-displayed-char vs 40-displayed-char split exactly: modes 0-3 use HF (`R0=127`), modes 4-7 use LF (`R0=63`).
- **Chars/line (bits 2-3) and 6845 R1 don't have to match**: this field tells the ULA how to serialise each fetched byte into pixels. R1 controls how many bytes per scanline get fetched. For a custom mode you set R1 to your byte width but pick the ULA bits 2-3 from `{10, 20, 40, 80}` based on your pixel-stretch goal. See [[techniques/custom-modes]].
- **MODE 7** is the only entry with teletext bit set (bit 1 = 1), routing RGB from the SAA5050 chip instead of the ULA serialiser. The "chars per line = 40" setting on bits 2-3 still applies but is largely cosmetic since the teletext chip drives video data anyway.
- **MODE 3 and MODE 0** have identical control-register values (`&9C`). They differ only in CRTC settings (R6, R5, R9) — both are 1 bpp, 80 displayed chars, HF clock. Same goes for MODE 4 and MODE 6 (both `&88`). The CRTC and the ULA are independent — the ULA doesn't know whether the framebuffer is 32 rows tall or 25 rows with padding.

### Cursor width (bits 5-7)

Bits enable cursor for the 1st 8 / 2nd 8 / last 16 video-data clock cycles per character:

| Bit 7 | Bit 6 | Bit 5 | Width | Used for |
|---|---|---|---|---|
| 1 | 0 | 0 | 1 char (8 dots) | MODE 0, 3, 4, 6 |
| 1 | 1 | 0 | 2 chars (16 dots) | MODE 1, 5 |
| 1 | 1 | 1 | 4 chars (32 dots) | MODE 2 |
| 0 | 1 | 0 | 1 char (delayed) | MODE 7 (teletext) |

Setting bits 5,6,7 = 0 hides the cursor in **all** conditions.

## Palette Register (`&FE21`)

16 entries × 8 bits. Writing to `&FE21` doesn't directly index — it writes one entry of a 64-bit content-addressable map. Format of the byte:

| Bits 7-4 | Bits 3-0 |
|---|---|
| Logical colour selector | Physical colour (EOR 7) |

The value sent to `&FE21` is `(logical << 4) | (physical EOR 7)`. OSBYTE `&9B` does the EOR for you when given the documented colour numbers.

### Logical colour matching

Only the **significant** logical-colour bits are compared against the screen pixel — the rest must be programmed to *all combinations* or you get split colours. Significant bits per mode:

| Mode | Significant logical bit(s) |
|---|---|
| 2-colour (0, 3, 4, 6) | Bit 7 only — must write 8 palette entries (bits 4,5,6 = all combos) |
| 4-colour (1, 5) | Bits 7 & 5 — must write 4 palette entries (bits 4 & 6 = all combos) |
| 16-colour (2) | Bits 7, 5, 3, 1 — every byte indexes uniquely (16 entries, one each) |

(For a 16-colour mode at the 1 MHz LF clock — the community-named "MODE 8" — see [[synthesis/mode-8-16colour-lf]].)

Using `VDU 19` or `OSWORD &0C` from the OS handles this expansion automatically — only relevant if you write `&FE21` directly via OSBYTE `&9B`.

### Physical colour table

| Code | Colour |
|---|---|
| `&00` | Black |
| `&01` | Red |
| `&02` | Green |
| `&03` | Yellow |
| `&04` | Blue |
| `&05` | Magenta |
| `&06` | Cyan |
| `&07` | White |
| `&08` | Flash black ↔ white |
| `&09` | Flash red ↔ cyan |
| `&0A` | Flash green ↔ magenta |
| `&0B` | Flash yellow ↔ blue |
| `&0C` | Flash blue ↔ yellow |
| `&0D` | Flash magenta ↔ green |
| `&0E` | Flash cyan ↔ red |
| `&0F` | Flash white ↔ black |

Flash duration: `OSBYTE 9` sets mark (1st colour), `OSBYTE 10` sets space (2nd colour); both in 50ths of a second. Default 25/25. Setting to 0 forces the opposite colour.

### Default palette write sequences (MOS, after `VDU 20`)

For when you bypass `VDU 19` / OSBYTE `&9B` and write `&FE21` directly. From [[sources/beebwiki-video-ula]]:

| Modes | Sequence (16 bytes, written in order) |
|---|---|
| 0, 3, 4, 6 | `80 90 A0 B0 C0 D0 E0 F0 07 17 27 37 47 57 67 77` |
| 1, 5 | `A0 B0 E0 F0 84 94 C4 D4 26 36 66 76 07 17 47 57` |
| 2 | `F8 E9 DA CB BC AD 9E 8F 70 61 52 43 34 25 16 07` |

## Performance notes

- The palette is the cheapest way to "change colours" mid-frame: a single write to `&FE21` retints all pixels of the affected logical entry going forward. Timed against the raster (via System VIA CA1 = vsync, or T1 timer for line-rate splits), this is the basis of **raster colour splits** beyond the 2/4/16-colour limit.
- Switching the chars-per-line bits (bits 2-3) mid-frame at the right horizontal time changes MODE width without a full mode reset — used for split-mode tricks.
- Direct `&FE20`/`&FE21` writes are 4 cycles (STA abs); OSBYTE round-trip costs hundreds of cycles. For raster-tight work, save the OS copy yourself and use direct STA inside an SEI/CLI window — but only when you control the whole machine state (no Tube).

The user-level palette workflow (VDU 19, OSWORD `&0C`, expansion rules) is fully captured on this page above. For mid-frame palette change techniques, see [[techniques/raster-splits]].

## Hardware history

- Original Acorn part: Ferranti ULA 5C094. Runs hot — needs a heatsink. Effectively overclocked at the standard 16 MHz; sensitive to temperature.
- Second source: VLSI Technologies VIDPROC VC 2023, later VC 2069 (Acorn part 201,647).
- Some Model A units shipped with Video ULAs that failed the high-resolution-mode acceptance test (Model A's 16 KiB RAM cannot drive MODES 0-2, so the bad parts were "good enough"). Owners who upgraded to 32 KiB sometimes saw bad MODES 0/1/2.
- **VideoNuLA** (Rob Coleman) is a modern drop-in replacement at IC 6 with 12-bit colour depth (16 from 4096), pixel-by-pixel hardware horizontal scrolling, and attribute modes — samples A1 via flying lead.
