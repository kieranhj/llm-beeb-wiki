---
title: Single-Rasterline Vertical Rupture
type: technique
tags: [crtc, vertical-rupture, raster, single-scanline, beam-race, demo]
sources: [twisted-brain]
updated: 2026-05-16
---

# Single-Rasterline Vertical Rupture

The extreme version of [[techniques/vertical-rupture]]: instead of splitting a PAL frame into 2-3 CRTC cycles for status panels, split it into **64, 128 or 256 cycles** — each cycle only 1, 2 or 4 scanlines tall — and feed the CRTC a tiny buffer (one character row, or one scanline) which gets displayed once then either re-pointed (R12/R13 latch) or mutated (chase the beam) before the next cycle starts.

Pioneered on the BBC by [[sources/twisted-brain|Twisted Brain]] (Bitshifters Collective, 2018). Most of the demo's effects rely on this pattern.

## The core CRTC config

The smallest meaningful CRTC cycle:

| Register | Value | Effect |
|---|---|---|
| R9 (Scanlines per Row) | 0, 1, or 3 | 1, 2, or 4 scanlines per character row |
| R4 (Vertical Total) | 0 | 1 character row per cycle |
| R6 (Vertical Displayed) | 1 | display that 1 row |
| R7 (Vertical Sync Position) | `&FF` | VSync suppressed this cycle |

Cycle duration = `(R9+1) × (R4+1) = (1, 2, or 4)` scanlines. Repeat across the frame, then **one final cycle** with VSync embedded that consumes the remaining scanlines to bring the frame to 312.

Worked numbers for each granularity. **The FX framework calls draw at the start of cycle 1**, so the loop only sets up cycles 2 through N (loop = total − 2):

| Scanlines/cycle | Display cycles | Loop iterations | Total cycles | Visible scanlines | Final-cycle R4 | Final-cycle R7 |
|---|---|---|---|---|---|---|
| 1 (R9=0) | 255 | 254 | **256** | 256 | `((312-255)/1) - 1 = 56` (57 rows) | `(280-255)/1 = 25` |
| 2 (R9=1) | 127 | 126 | **128** | 256 | `((312-254)/2) - 1 = 28` (29 rows) | `(280-254)/2 = 13` |
| 4 (R9=3) | 63 | 62 | **64** | 256 | `((312-252)/4) - 1 = 14` (15 rows) | `(280-252)/4 = 7` |

For each row: "Display cycles" run at the single-scanline rate (each displays R6=1 row). The "Final cycle" is one of the total cycles but consumes more raster lines (its R4 padding hides VSync). All three configurations give exactly 312 raster lines and 256 visible scanlines — the screen looks like a continuous 256-line image.

(Numbers match the worked examples in [[techniques/kefrens-bars]], [[techniques/vertical-blinds]], and [[techniques/copper-bars]] respectively.)

## Two patterns of use

### 1. Re-point R12/R13 per cycle (frame-coherent)

The CRTC fetches from a different screen address every cycle. The screen RAM is the full pre-rendered buffer; you just choose which row to show on each raster.

Used by: [[techniques/copper-bars]] (Parts 6+7), [[techniques/parallax-bars]] (Part 8 with ACCCON tricks), [[techniques/twister]] (Part 13 with R1 narrow-screen), Bitshifters logo (Part 12).

The R12/R13 write must happen during the *previous* cycle so the value is latched when the new cycle begins. With only 1-4 scanlines per cycle, that's 64-512 cycles to do everything: read sine table, compute address, write R12, write R13. Tight but achievable.

```asm
; inside a 4-scanlines-per-row cycle (512c budget):
; ... per-row sine math (~40c)
LDA #12 : STA &FE00 : LDA new_addr_hi : STA &FE01    ; 18c
LDA #13 : STA &FE00 : LDA new_addr_lo : STA &FE01    ; 18c
; ... pad to 512c
```

### 2. Beam-race a tiny buffer (mutate-as-displayed)

R12/R13 stays constant — the same memory is shown every cycle. The CPU races the beam to **rewrite the buffer between fetches**, so each visible 2- or 4-scanline strip on screen shows a *different* version of the buffer.

Used by: [[techniques/vertical-blinds]] (Part 9), [[techniques/kefrens-bars]] (Part 10), [[techniques/checkerboard-zoom]] (Part 11).

This is the genuinely head-scratching mode. The TV shows a 256-line tall image, but at any moment the chip is reading just 80 bytes of RAM, and those 80 bytes have just been overwritten by the CPU with the content for the next 2-4 scanlines.

```asm
; 1-scanline rupture (128c budget):
; - chip is reading scanline N from the 80-byte buffer
; - meanwhile, CPU prepares scanline N+1's content into the same buffer
; - the write must complete before chip starts reading scanline N+1
```

The 128c budget per scanline is enough to update a handful of bytes (e.g. Kefrens bars draws ~4 bytes per scanline to "accumulate" one new bar onto the existing pattern). It is not enough to redraw the entire 80-byte buffer per scanline — for that you need the 2-scanline variant (Vertical Blinds) and a double-buffer arrangement.

## Constant-time discipline

Every loop iteration must take **exactly the same number of cycles**, regardless of inputs. The CRTC doesn't wait for you; if your loop takes 10c longer one iteration, that 10c shows up as a horizontal shift on the affected raster.

Standard idioms:

- **Branch both ways equally**: pad the shorter branch with NOPs so both paths take the same total cycles.
- **Dual-loop sink writes**: for variable-iteration work (e.g. "draw N pixels into a buffer for varying N"), follow the real loop with a sink-write loop targeting a throwaway address, sized so `(real_iterations + sink_iterations) = constant`. See [[techniques/vertical-blinds]] for a worked example.
- **Mid-block delay calls**: a `JSR cycles_wait_128` is a clean way to spend exactly one raster line. Standardise a library of these.

## R12/R13 update jitter

R12/R13 are latched at the start of each CRTC cycle (see [[hardware/crtc-6845]]). With cycles only 1-4 scanlines tall, the latch happens every 128-512 cycles. **Write R12 before R13** (or vice versa, consistently) and ensure both bytes are committed before the cycle boundary — otherwise the chip catches one byte from this frame's intended value and one from the previous one, giving a one-cycle "jump" in the displayed image.

## Real-hardware quirks

- **Vertical Total R4 rewrites in 1-scanline cycles have ambiguous timing on real HD6845SP**. The chip samples R12/R13 on the "last raster period" and compares R4/R7 each cycle — operations whose relative ordering within a single scanline isn't specified by the datasheet. Normal-cycle usage never exposes the ambiguity (there are 7 non-last rasters where the sequence is unambiguous), but in a 1-scanline cycle every raster IS the last raster. Symptom: R4 written for the rebalance cycle takes effect one cycle late, frame becomes 313 lines. Fix via 311-line rebalance frame — see [[techniques/kefrens-bars]].
- **BeebEm cycle inaccuracy** — single-rasterline effects don't behave the same on BeebEm as on real hardware or b-em / jsbeeb. Always test on the cycle-accurate emulators (b-em, jsbeeb) and ideally on hardware.
- **Master vs Model B vs B+** — generally consistent for these effects (all use HD6845SP) but the address-translator differences ([[hardware/address-translation]]) can bite if you combine single-rasterline rupture with TTX VDU routing (see [[techniques/chunky-mode]]).

## What it enables

Anything that looks like "256 lines of full-screen animation from a CPU that can't fill a 20 KB buffer in 20 ms" — copper bars, plasmas, twisters, parallax scrolls, Kefrens bars, blind/curtain effects, checkerboards, sprite reveals at sub-row granularity, etc. The whole "Amiga demo" aesthetic on a 2 MHz 6502.

## Builds on / used by

- [[techniques/vertical-rupture]] — the 2-3-cycle case this generalises from.
- [[techniques/fx-framework]] — provides the stable-raster + module structure that makes per-frame cycle-counting tractable.
- [[hardware/crtc-6845]] / [[hardware/crtc-6845-advanced]] — register latching behaviour is the whole substrate.
- Effect pages: [[techniques/copper-bars]], [[techniques/parallax-bars]], [[techniques/vertical-blinds]], [[techniques/kefrens-bars]], [[techniques/checkerboard-zoom]], [[techniques/twister]].
