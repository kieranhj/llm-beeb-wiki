---
title: Acorn Video ULA
type: hardware
tags: [video, ula, palette, sheila]
sources: [naug-ch13-video, beebwiki-video-ula, master-arm, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
sheila: ["&FE20", "&FE21"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-11-18
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

**Why, measured** ([[sources/beeb-port-kit-hardware-facts-2026-11]] §2; KC's real Master, phX hwtest card K, no wrong pixel; and jsbeeb's `table4bpp`, 2026-11-15): **the ULA indexes the 16-entry palette with bits 7, 5, 3, 1 of the byte as it shifts out, and shifts in 1s.** So in MODE 1 a byte's 2nd-4th pixels look up entries other than a naive reading of their two bits gives — which is why all four entries of a colour must be set. A program can use it: phX's MODE 1 Bobs encode their colours in it (cell bytes `&0F`, `&AF`, `&07`, `&2F`, with pens on entries 3/7 and 1/15).

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
- Direct `&FE20`/`&FE21` writes are 4 cycles (STA abs) — **measured on real Masters 2026-11, see below**; OSBYTE round-trip costs hundreds of cycles. For raster-tight work, save the OS copy yourself and use direct STA inside an SEI/CLI window — but only when you control the whole machine state (no Tube).

The user-level palette workflow (VDU 19, OSWORD `&0C`, expansion rules) is fully captured on this page above. For mid-frame palette change techniques, see [[techniques/raster-splits]].

## Hardware history

- Original Acorn part: Ferranti ULA 5C094. Runs hot — needs a heatsink. Effectively overclocked at the standard 16 MHz; sensitive to temperature.
- Second source: VLSI Technologies VIDPROC VC 2023, later VC 2069 (Acorn part 201,647).
- Some Model A units shipped with Video ULAs that failed the high-resolution-mode acceptance test (Model A's 16 KiB RAM cannot drive MODES 0-2, so the bad parts were "good enough"). Owners who upgraded to 32 KiB sometimes saw bad MODES 0/1/2.
- **VideoNuLA** (Rob Coleman) is a modern drop-in replacement at IC 6 with 12-bit colour depth (16 from 4096), pixel-by-pixel hardware horizontal scrolling, and attribute modes — samples A1 via flying lead.

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up.

### Palette register

- **`&FE21` takes `(logical << 4) OR (physical EOR 7)`, and the logical field is a content-addressable match**: in a 4-colour mode only bits 7 and 5 are compared, so bits 6 and 4 must be written in every combination (four entries per logical colour) or the colour comes out split — exactly the expansion rule tabulated above, confirmed with output identical to the `VDU 19` version (Paradroid Layer 3, jsbeeb).
- **The MOS's default MODE 2 palette is logical n → physical n for all sixteen**, and `(n << 4) OR (n EOR 7)` reproduces it exactly (the `F8 E9 … 07` sequence above). Logical 8-15 can be mapped back onto 0-7 *without* the flash bit, giving a second black that a sprite engine using logical 0 as its transparency key can use (Edge, 2026-09-05, jsbeeb; [layer-8b-nula.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-8b-nula.md)).
- **A `&FE21` write from main-loop code lands wherever the raster is.** If a panel has its own palette applied at VSync, a mid-frame write leaves the panel in the wrong palette for the rest of the field: a one-frame flash, about one transition in three in Paradroid (2026-08-31, jsbeeb, stepping a field at a time).
- A palette write can glitch a few displayed pixels at the beam position on the write line (short dashes at flash peaks, over black) — *stated* in Paradroid's intro write-up as real-hardware behaviour shared with every mid-frame palette split; not separately measured (unverified — [[sources/beeb-port-kit-hardware-facts]] §2).
- **Settled 2026-11 — `&FE21` is a 2 MHz access.** Edge Grinder's title-page write-up had said a per-scanline loop that *opens* with a write to `&FE21` is phase-stable because the write is "on the 1 MHz bus"; this wiki (from BeebWiki, [[timing/cycle-stretching]]) said 2 MHz, unstretched, 4c, and flagged it to measure ([[sources/beeb-port-kit-hardware-facts]] §2, §12). Measured now: **on both of KC's real Masters a back-to-back `STA`/`STX &FE21` run changed colour every 4 cycles** (stripes on the ticks' spacing, phX hwtest card 6 band C), and a palette write landed the same way at an odd (C0 43) and an even (C0 54) character (bands B, B') — not stretched to a 1 MHz cycle. jsbeeb agrees (its `is1MHzAccess` makes `&FE20-&FE3F` 2 MHz on the Master too; `STA &FE21` 4c, `LDA # : STA` 6c). So about 21 independent palette writes fit a 128-cycle line, 32 of preloaded values. Edge's loop is only as stable as its passes are equal: a pass a cycle longer (an indexed load crossing a page) carries into every later write on the line; Edge's comment was corrected (`7363c8b`). ([[sources/beeb-port-kit-hardware-facts-2026-11]] §2.)

### Where a mid-line palette or `&FE20` write lands (open disagreement)

**A palette (`&FE21`) or ULA control (`&FE20`) write takes effect EARLY on a real Master**, and the two measurements of how early disagree. Recorded both, per [[sources/beeb-port-kit-hardware-facts-2026-11]] §2:

| Measurement | How early | Source |
|---|---|---|
| **KC's eye**, both real Masters, 2026-11-14 | about **one MODE 2 pixel (0.25 µs, half a character)** before the character it is written in, the same at odd and even C0; `&FE20` the same (card B: the mode change a little left of the tick, as beebjit shows it) | phX hwtest cards 6 (B, B'), B |
| **jsbeeb main 2.22.1** (#1868, from the jsbeeb maintainer's own Master) | `4 - p` texels (1/16 µs) into the character BEFORE the one written, p the pixel width — **MODE 2 a whole character, MODE 1 three pixels, MODE 0 five texels**. phX's sine scrollers calibrate to it: their expected pictures shifted 3 MODE 1 pixels give 632 of 632 fields on 2.22.1 | phX `BUGS.md` #1, #2, #7 |
| jsbeeb 2.10.2 and 2.21.1 (the pinned versions) | offset 0: at the character written | phX probe test 4 |

**Unresolved**: phX's second hardware-test disc (card N) was built to settle it and has no recorded result. Either way, **a write meant for the blanking just after the display can recolour the last displayed character**: start such writes a character or two later (phX's logo moved its writes from C0 100 to 102: 0 of 400 fields right on 2.22.1 before, 400 of 400 after), or write an entry that character cannot show.

By contrast **ACCCON's D bit (`&FE34` bit 0) mid-line acts AT the character written**, odd or even C0, cleanly, on both real Masters and in jsbeeb (card A) — it changes which memory the fetch reads, so it is character-aligned ([[memory/shadow-ram]]).

### Other 2026-11 additions

- **The teletext bit (`&FE20` bit 1, e.g. `&F6`) delays display enable by 2 characters while it is on** (jsbeeb, phX) — usable as a short blank, e.g. to hide RVI strays ([[techniques/rvi]]).
- **The MOS keeps its copy of the control register at `&0248`, and its flash timer EORs the flash bit into it and writes `&FE20` from it.** A program that writes `&FE20` itself while the MOS's IRQ still runs (a loader, a title screen) must write `&0248` too, or the next flash tick puts the old mode's byte back (1942-beeb, 2026-09; [[sources/beeb-port-kit-hardware-facts-2026-11]] §2).

### Byte layouts (as exported and plotted)

- **MODE 1**: pixel n takes bit `7-n` (high colour bit) and bit `3-n` (low bit); solid colour 0/1/2/3 = `&00`/`&0F`/`&F0`/`&FF`; **adjacent 4-pixel columns are 8 bytes apart, not 1** — this cost Paradroid a build (Layer 3, jsbeeb). Agrees with the layout on [[video/modes]].
- **MODE 2**: the **left** pixel of a byte is bits 7, 5, 3, 1 and the **right** pixel bits 6, 4, 2, 0; 640 bytes per character row (`R1 = 80`), a CRTC unit is 2 px (Edge Layer 1, 2026-09-02).

### VideoNuLA (Edge Grinder's `-Nula` build)

- **By default the NuLA composes both tables**: logical → `&FE21` → physical → `&FE23` → 12-bit RGB. **`&FE22 = &11`** (control 1, parameter 1) selects logical colour mapping and makes `&FE21` ignored. Without it a title screen's per-scanline `&FE21` pulses wrecked the game's colours (a blue background instead of black). Measured 2026-09-05 on **real hardware first** (KC), then jsbeeb; encoding cross-checked against the VideoNuLA User Guide's worked example ([layer-8b-nula.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-8b-nula.md)).
- **Palette entries go to `&FE23` as two bytes each, `[index<<4 | red]` then `[green<<4 | blue]`, in that order**; `&FE22 = &40` resets the extended features first (2026-09-05, jsbeeb, against the reference library's default table byte for byte).
- **jsbeeb emulates the NuLA palette** (`?&FE23=&78 : ?&FE23=&88` gives mid grey; sixteen distinct entries come back under logical mapping) but **not its scrolling or attribute modes**. See [[tools/emulators]].

### VideoNuLA for an Amstrad CPC original (2026-11, emulator only)

From Isometrikum's port ([[sources/beeb-port-kit-hardware-facts-2026-11]] §2; jsbeeb 2.10.2, 2026-11-07/08; **no real NuLA has seen any of this**):

- **Palette mode 1 shows a CPC mode 0 screen byte for byte.** `&FE22 = &40` (reset, which also resets the two-write protocol), then `&FE22 = &11`, then 16 entries to `&FE23`: entry L = the CPC colour of pen `swap03(L)` (bits 0 and 3 swapped — CPC mode 0 and MODE 2 order a pixel's bits differently), CPC levels 0/1/2 as NuLA 0, 8, 15. Disable interrupts between an entry's two bytes if an IRQ also writes the palette.
- **CPC mode 0 is MODE 2's pixel format** (same pixel clock and shape, left pixel in bits 7, 5, 3, 1; masks `&AA`/`&55` carry over); one CRTC character is 2 bytes on the CPC and 1 on the BBC.
- **Detecting a NuLA by timing.** A stock ULA decodes only A0, so `&FE22` is `&FE20`. Count MODE 7 fields with ULA control `&10`, write `&44` to `&FE22`, count again: a NuLA takes it as a reset and the rate holds; a stock ULA takes `&44` as control with the clock bit clear and runs at half rate (jsbeeb: stock 9,452 then 18,909 loops; `video_nula` 9,453 then 9,452). Decide NuLA when 4E ≥ 3G. **Interrupts off, polling the CA1 flag** — with the MOS running, its own `&FE20` writes made a NuLA read 29/57.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
