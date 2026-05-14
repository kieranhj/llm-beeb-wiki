---
title: "SAA5050 — Combined References"
type: source
tags: [saa5050, teletext, video, mode-7]
file: raw/manuals/SAA5050.pdf
updated: 2026-05-14
---

# SAA5050 — Combined References

The primary Mullard SAA5050 datasheet (`raw/manuals/SAA5050.pdf`, 3.3 MB from `bitshifters/bbc-documents/ICs/SAA5050`) is an **image-only scan** with no extractable text. Alternative scans from stardot.org.uk, vd-view, and datasheet aggregators were checked — all image-only.

This source page consolidates **four text-bearing alternatives** that together cover the chip's behaviour, plus notes about the unread primary datasheet. The wiki's [[hardware/saa5050]] entity page is synthesised from these.

## Sources used

### 1. `raw/manuals/SAA5050.pdf` — Mullard 1982 datasheet (UNREAD)

Image-only PDF. 16 pages. Contains the canonical pinout, control code table, character ROM layout, electrical specs, and timing diagrams. **Marked as a long-term TODO**: needs OCR. Until OCR'd, treat the items below as authoritative.

### 2. Wikipedia: Mullard SAA5050

URL: https://en.wikipedia.org/wiki/Mullard_SAA5050

- 480 × 500 pixel full-screen resolution; 40 × 25 character grid.
- Character cell: 12 × 20 pixels.
- Internal character ROM: 5 × 9 pixel grid (Signetics 2513-derived), interpolated by diagonal smoothing to 10 × 18 pixels.
- 2 × 3 block graphics: 6×6 top, 6×8 middle, 6×6 bottom blocks.
- Implements World System Teletext **Level 1**.
- Limitation: "no provision to set black for the foreground text colour" (control codes `&80` for "alpha black" don't actually produce visible text — black-on-black).
- Language variants: SAA5050 (UK), SAA5051 (DE), SAA5052 (SE), SAA5053 (IT), SAA5054 (BE), SAA5055 (US ASCII), SAA5056 (HE), SAA5057 (CY).
- Successor: SAA5243 CCT (integrates teletext decoder + timing + video, I²C-controlled).
- Used in: BBC Micro (1982), Acorn System 2 (1980), Philips P2000 (1980), teletext TVs, viewdata terminals, Prestel adapters.

### 3. HandWiki: Engineering: Mullard SAA5050

URL: https://handwiki.org/wiki/Engineering:Mullard_SAA5050

Largely overlaps Wikipedia. Confirms 5×9 internal grid derived from Signetics 2513 character generator. Same 12×20 cell, 480×500 resolution.

### 4. mdfs.net: Teletext Control Characters

URL: http://mdfs.net/Info/Comp/Teletext/Controls (redirected from `/SAA5050/Controls`)

Authoritative control-code table for the BBC's MODE 7. Maintained by J.G. Harston (same as AllMem).

**Control codes (BBC stores them with bit-7 set in screen RAM at `&7C00`):**

| Code | Function | Line-start default? |
|---|---|---|
| `&80` | Alpha black (text) | — |
| `&81` | Alpha red | — |
| `&82` | Alpha green | — |
| `&83` | Alpha yellow | — |
| `&84` | Alpha blue | — |
| `&85` | Alpha magenta | — |
| `&86` | Alpha cyan | — |
| `&87` | Alpha white | **yes** |
| `&88` | Flash on | — |
| `&89` | Flash off (steady) | **yes** |
| `&8A` | End box | — |
| `&8B` | Start box | — |
| `&8C` | Normal height (1×1) | **yes** |
| `&8D` | Double height (1×2) | — |
| `&8E` | Double width (2×1) | — |
| `&8F` | Double size (2×2) | — |
| `&90` | Mosaic black (graphics) | — |
| `&91` | Mosaic red | — |
| `&92` | Mosaic green | — |
| `&93` | Mosaic yellow | — |
| `&94` | Mosaic blue | — |
| `&95` | Mosaic magenta | — |
| `&96` | Mosaic cyan | — |
| `&97` | Mosaic white | — |
| `&98` | Conceal display | — |
| `&99` | Contiguous graphics | — |
| `&9A` | Separated graphics | — |
| `&9B` | Toggle G0 character sets | — |
| `&9C` | Black background | **yes** |
| `&9D` | New background (use current fg as new bg) | — |
| `&9E` | Hold graphics | — |
| `&9F` | Release graphics | **yes** |

**Hold graphics semantics:** when active (`&9E`), subsequent control characters (except `&9E` itself) display as the most recent graphics character on the line — including any joined/separated and colour state. Does NOT apply to text (alpha) characters.

**Double-height rule:** any character on the second row of a double-height pair that is *not also* marked double-height becomes invisible. So you cannot mix single and double heights vertically within such a pair.

### 5. BeebFpga `saa5050.vhd` (Hoglet67)

URL: https://github.com/hoglet67/BeebFpga/blob/master/src/common/saa5050.vhd

VHDL behavioural model of the SAA5050 as used in the BBC. Reveals signal-level and timing details.

**Entity ports:**
- `DI[6:0]` — 7-bit character input from CRTC-fetched screen byte (bit 7 strips off).
- `DEW` — Data Entry Window (synchronised to VSYNC; falling edge resets line counters and flash counter).
- `LOSE` — Load Output Shift register Enable (active during visible video).
- `CRS` — Character Rounding Select (tied to FIELD signal — picks even/odd-field rounding).
- `GLR` — General Line Reset (not utilised in BBC integration).
- `R, G, B` — single-bit colour outputs.
- `Y` — monochrome luminance.

**Set-after vs Set-at:**
- **Set-after** (control takes effect on the *next* character cell): Flash (`&88`), Steady... wait, actually per the VHDL — Flash is set-after, Steady is set-at. Double-height is set-after. Release Graphics is set-after.
- **Set-at** (control takes effect immediately, in the current cell — which is consequently rendered as a space): Colour changes (alpha and mosaic), Conceal, Graphics Hold, Steady.

Practical implication: when you change colour mid-line in MODE 7, the control character *itself* occupies a cell rendered as background-colour space.

**Hold-graphics bug** (per VHDL comment):
> "SAA5050 hold bug: control codes outside of hold clear the held character (apart from `&9E`=HOLD)"

i.e. when in hold-graphics mode, any control code OTHER than `&9E` itself clears the held character — even though the cell still renders. This is a chip quirk, not a spec feature.

**Flash rate:** ~0.78 Hz, with a 3:1 on/off ratio (cell visible for 3/4 of cycle, dark for 1/4).

**Character rounding:** the chip applies morphological smoothing to alphanumeric characters only — comparing the current ROM row with the adjacent row to fill in diagonal "stairsteps", producing the characteristically angular SAA5050 typeface.

**Not implemented in BeebFpga's model** (and likely not present in the BBC's wiring either):
- No `/SI` pin — TEXT mode is permanently enabled.
- No remote control features.
- No large-character support.
- No box overlay.

## Filed into

- Created: [[hardware/saa5050]] (new entity page).
- Updated: [[hardware/crtc-6845]], [[hardware/crtc-6845-advanced]], [[hardware/video-ula]], [[hardware/address-translation]], [[video/modes]] — all gained inbound link to [[hardware/saa5050]].

## TODO

When the primary Mullard datasheet PDF is OCR'd, revisit this and verify:
- Exact pinout (number / function of each of 28 pins).
- Electrical specs (Vcc range, Icc, capacitances, propagation delays).
- Timing diagrams (CLK to DI setup, LOSE-to-RGB latency).
- Set-after vs set-at table for all control codes (BeebFpga gives some; the datasheet has the full table).
- Conceal/reveal behaviour formally.
- "End box / start box" semantics (mdfs.net lists them but doesn't define).
