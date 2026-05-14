---
title: "Hitachi HD6845R/HD6845S Datasheet"
type: source
tags: [crtc, 6845, hitachi, datasheet, video]
file: raw/manuals/hd6845sp.pdf
updated: 2026-05-14
---

# Hitachi HD6845R/HD6845S — CRT Controller (CRTC) Datasheet

**File:** `raw/manuals/hd6845sp.pdf` (482 KB, 20-page Hitachi datasheet, full text)
**Online mirror:** `http://andercheran.aiind.upv.es/~amstrad/docs/hd6845s/hd6845sp.htm` (HTML version)

## Summary

Primary chip-level reference for the BBC's exact CRTC variant (HD6845**S**). Authoritative for every register, every encoding, every programming restriction, every "anomalous behaviour" when rewriting registers during display, and the differences between HD6845R and HD6845S. Where BeebWiki / NAUG / our derived pages disagree, **this is the primary source.**

Key surprise: contradicts our existing R10 BLK encoding (which we recently re-derived from BeebWiki). See contradiction section below.

## Variant identification

| Part | Bus timing | CRT display timing |
|---|---|---|
| HD6845S | 1.0 MHz | 3.7 MHz max |
| HD68A45S | 1.5 MHz | 3.7 MHz max |
| HD68B45S | 2.0 MHz | 3.7 MHz max |
| HD6845R | 1.0 MHz | 3.0 MHz max |
| HD68A45R | 1.5 MHz | 3.0 MHz max |
| HD68B45R | 2.0 MHz | 3.0 MHz max |

BBC uses the **HD68B45S** (2 MHz bus, 3.7 MHz CRT). The "S" variant is required — see HD6845S-vs-HD6845R section below.

## Pin / interface summary

**To MPU:**
- D0-D7 (33-26): bi-directional data, tristate.
- /W/R (22): direction (high = CRTC → MPU, low = MPU → CRTC).
- /CS (25): chip select (low = enable).
- RS (24): register select (low = address register, high = control registers).
- E (23): enable strobe (derived from MPU Φ2).
- /RES (?): reset (active low; only effective while LPSTB is low).

**To CRT:**
- CLK (21): character clock (input).
- HSYNC (39), VSYNC (40), DISPTMG (18), CUDISP (19): outputs.
- MA0-MA13 (4-17): refresh memory address (14-bit = 16K words max).
- RA0-RA4 (38-34): raster address (5 bits).
- LPSTB (3): light-pen strobe (input).

## Register conventions

**Written-value vs specified-value:**

| Register | Programmed value |
|---|---|
| R0 (Horizontal Total) | `Nht - 1` |
| R2 (Horizontal Sync Position) | `Nhsp - 1` |
| R4 (Vertical Total) | `Nvt - 1` |
| R7 (Vertical Sync Position) | `Nvsp - 1` |
| R9 (Max Raster) — Non-Interlace / Interlace Sync | `Nr - 1` |
| R9 (Max Raster) — **Interlace Sync & Video** | `Nr - 2` |
| All other registers | as-specified |

The Interlace-Sync-&-Video `-2` for R9 is easy to miss — relevant to BBC MODE 7 which uses this mode (R8 = 3).

## Programming restrictions (must hold)

- `0 < Nhd < Nht+1 ≤ 256`
- `0 < Nvd < Nvt+1 ≤ 128`
- `0 ≤ Nhsp ≤ Nht`
- `0 ≤ Nvsp ≤ Nvt`
- `0 ≤ Ncstart ≤ Ncend ≤ Nr` (Non-Interlace, Interlace Sync)
- `0 ≤ Ncstart ≤ Ncend ≤ Nr+1` (Interlace Sync & Video)
- `2 ≤ Nr ≤ 30` (Interlace Sync & Video mode only)
- `3 ≤ Nht` (except non-interlace)
- `5 ≤ Nht` (non-interlace mode)
- **In interlace mode, `R0` must be programmed to an even number** (Nht must be odd, so R0 = Nht-1 is even).

These are silent failures — violating them produces undefined display.

## R3 — Sync widths

- Low 4 bits (HSW): horizontal sync pulse width in character clocks. **"0" cannot be programmed** (would be undefined).
- High 4 bits (VSW): vertical sync pulse width in raster periods. **"0" means 16 raster periods** (special-case wraparound, unlike HSW).

## R8 — Interlace and Skew

Bit layout:
- bits 0-1 (V, S): raster scan mode.
- bits 4-5 (D1, D0): DISPTMG (display) skew.
- bits 6-7 (C1, C0): CUDISP (cursor) skew.

**Scan mode (V S):**
| V S | Mode |
|---|---|
| 0 0 | Non-Interlace |
| 1 0 | Non-Interlace (duplicate encoding) |
| 0 1 | Interlace Sync |
| 1 1 | Interlace Sync & Video |

**Skew (each pair):**
| Bits | Effect |
|---|---|
| 00 | Non-skew (immediate) |
| 01 | 1-character skew |
| 10 | 2-character skew |
| 11 | **Non-output** (the signal is disabled entirely) |

So `C1 C0 = 11` disables CUDISP, and `D1 D0 = 11` disables DISPTMG.

**Critical:** "Dynamic rewrite into scan mode bit and skew bit is **prohibited**" — R8 cannot be safely written during display. Schedule R8 changes only during reset or full reprogramming.

## R10 — Cursor Start Raster + Cursor Display Mode

**Datasheet Table 7 (BP = bits 6-5):**

| B (bit 6) | P (bit 5) | Cursor display mode |
|---|---|---|
| 0 | 0 | **Non-blink** (cursor displayed, steady) |
| 0 | 1 | **Cursor-non-display** (cursor off) |
| 1 | 0 | Blink 16 Field Period |
| 1 | 1 | Blink 32 Field Period |

Lower 5 bits (bits 0-4): cursor start raster scan line.

**Logical reading:**
- B (bit 6) = blink-enable.
- P (bit 5) = when B=1, blink period; when B=0, toggles steady-on vs steady-off.
- A "Field Period" is the cycle length — 16-field period at 50 Hz field rate = ~3 Hz blink (faster); 32-field period = ~1.5 Hz (slower).

⚠️ **Contradicts BeebWiki and our existing wiki page.** See "Contradictions" below.

## R12/R13 — Start Address (rewriteable safely)

- **R12** holds high byte (top 2 bits always read as 0 — so effective range is 14-bit).
- **R13** holds low byte.
- **R12/R13 are sampled in the last raster period of the field** — i.e., during the bottom of the screen.
- Safe to rewrite at any other time. A rewrite during the *last raster period* of a field can result in a "split start address" display for one frame.
- Note: datasheet explicitly recommends rewriting *during* horizontal/vertical display period (i.e., NOT in retrace), the opposite of common folklore.

## R14/R15 — Cursor Position

Same format as R12/R13. Rewrite during retrace for stable cursor; during display gives one frame of temporary glitch.

## R16/R17 — Light Pen

Read-only. Captured on LPSTB rising edge. Address is the MA that was on the bus at strobe — software must correct for display pipeline + LPSTB detector delays.

## Anomalous register-rewrite behaviour during display

The datasheet provides an explicit "what happens if you rewrite register N during display" table:

| Reg | Safe? | Notes |
|---|---|---|
| R0 (HTC) | **NG** | Horizontal scan disturbed |
| R1 (HDC) | OK | DISPTMG width may be temporarily shortened (one raster) |
| R2 (HSP) | **NG** | HSYNC misplaced or noisy |
| R3 (sync widths) | conditional | Pulse width can be cut short if rewritten during HSYNC/VSYNC pulse |
| R4 (VTC) | conditional | Avoid the last raster period of the line |
| R5 (VTA) | conditional | Avoid the last char time of the raster — adjust may not apply |
| R6 (VDC) | OK | Display can briefly inhibit until next field |
| R7 (VSP) | **NG** | VSYNC misplaced or noisy |
| R8 (interlace & skew) | **NG (prohibited)** | Scan-mode + skew bits must not be dynamically rewritten |
| R9 (NSL) | **NG** | Internal operation disordered |
| R10 (cursor start) | conditional | Avoid last char time of raster — jitter / wrong blink rate |
| R11 (cursor end) | conditional | Same as R10 |
| R12/R13 (start) | **OK** | Sampled in last raster period of field — see above |
| R14/R15 (cursor) | OK | Brief glitch if rewritten during display |
| R16/R17 (light pen) | read-only | — |

**Key takeaway for raster-tight code:** R8 is essentially write-once. R0/R2/R7/R9 should be considered write-once or only-during-reset. R12/R13 are the *only* freely-rewriteable major timing register. Cursor registers (R10/R11/R14/R15) tolerate rewrite with care.

## Reset behaviour

`/RES` active-low:
- All counters cleared, display halts.
- All outputs go low.
- **Control registers are NOT affected** (retain values).
- `/RES` only works while LPSTB is low.
- After /RES release: HD6845S starts display immediately. **First field is anomalous:**
  - DISPTMG and CUDISP not output (display inhibited).
  - Start Address register (R12/R13) is **not used** at first field — MA starts at 0.
  - From the second field onward, the start address is used.

## HD6845S vs HD6845R differences

The BBC uses HD6845**S**. The 'S' variant adds:

1. **Vertical character count programming**: HD6845R counts in 2-line units (only even vertical totals possible); HD6845S counts in 1-line units (both even and odd vertical totals — needed for `Nvd = 25` in BBC MODES 3/6/7).
2. **VSYNC pulse width** (R3 high nibble): HD6845R has fixed 16-raster VSYNC; HD6845S has programmable 1-16 raster.
3. **SKEW function**: HD6845R has no DISPTMG/CUDISP skew; HD6845S adds it (R8 bits 4-7) — needed for MODE 7's SAA5050 pipeline alignment.
4. **Start Address Register readable**: HD6845R = write-only; HD6845S = read-write.
5. **Cursor in Interlace Sync & Video**: HD6845R shows cursor in both fields; HD6845S shows in either even OR odd field only.
6. **Reset signal behaviour**: HD6845R's MA/RA outputs synchronously go low; HD6845S's go low asynchronously immediately.

The BBC requires features 1, 2, 3 above — explaining why "HD6845S" is the spec'd variant.

## Cross-check against existing wiki

### Major contradiction: R10 BLK encoding

Our existing [[hardware/crtc-6845]] page (updated 2026-05-14 from [[sources/beebwiki-crtc]]) currently says:

| BLK | Effect (our wiki / BeebWiki) | Effect (THIS DATASHEET) |
|---|---|---|
| `00` | Cursor off | **Non-blink (steady cursor displayed)** |
| `01` | Cursor on, steady | **Cursor not displayed (off)** |
| `10` | Blink slow (1/16 field) | Blink 16-field period (~3 Hz — faster of the two) |
| `11` | Blink fast (1/32 field) | Blink 32-field period (~1.5 Hz — slower of the two) |

**Both 00/01 are inverted, and the slow/fast labels on 10/11 are inverted.**

The primary chip datasheet is authoritative. BeebWiki appears wrong. Our wiki currently follows BeebWiki and is also wrong.

The internal logic of the datasheet is self-consistent: B = blink enable; with B=0, P picks steady-on vs steady-off; with B=1, P picks the 16- or 32-field period. "16 field period" is one full blink cycle every 16 fields = 3.1 Hz at 50 Hz — i.e. faster, not slower.

### Minor additions to add

- R9 Interlace Sync & Video uses `Nr - 2`, not `Nr - 1`. Currently we say only `-1`.
- R0 must be even in interlace mode (programming restriction).
- The full anomalous-register-rewrite table — particularly that R8 is "prohibited" for dynamic rewrite, and R12/R13 are sampled in the last raster period of the field (refines our "applies at next CRTC frame cycle" claim).
- HD6845S vs HD6845R differences — explains *why* the BBC requires the 'S' variant in concrete terms.
- Reset first-field behaviour (R12/R13 ignored on field 0).

## Filed into

- Updated: [[hardware/crtc-6845]] (R10 BLK encoding fix, R9 -2 in interlace-sync-&-video, programming restrictions, anomalous-rewrite summary, HD6845S features list, reset behaviour).
- The advanced register-rewrite table is the natural body for the long-planned [[hardware/crtc-6845-advanced]] stub.
