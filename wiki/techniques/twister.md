---
title: Twister (narrow-screen via R1 + 128 prerendered rotations)
type: technique
tags: [crtc, single-rasterline, mode-1, twister, sine, r1, r2, narrow-screen, dither]
sources: [twisted-brain]
updated: 2026-05-16
---

# Twister

A real-time rotating-ribbon "twister" demoscene effect in MODE 1, using **40 KB of pre-rendered single-scanline ribbon-rotation art** and per-raster R12/R13 selection. Two extras make it work: a **narrow CRTC display** (R1 + R2) so 128 rotations can be packed 4-to-a-scanline into a standard MODE 1 screen, and a **dual-buffer alternate-scanline stipple** for a fourth visual colour.

From Twisted Brain Part 13 ([[sources/twisted-brain]]). "Probably the most technically complex effect."

## The ribbon

For each of 128 angles θ, draw 4 vertical lines on a black background:

```basic
x1 = 40 + 38*SIN(θ + 0°)
x2 = 40 + 38*SIN(θ + 90°)
x3 = 40 + 38*SIN(θ + 180°)
x4 = 40 + 38*SIN(θ + 270°)
draw bar from x1..x2 (col 1, front)
draw bar from x2..x3 (col 2, side)
draw bar from x3..x4 (col 3, back)
draw bar from x4..x1 with bg colour (clear)
```

Each angle gives one 80-pixel-wide "ribbon slice". For 128 angles that's 128 slices.

## The packing trick — narrow CRTC display

A standard MODE 1 screen is **80 CRTC characters wide × 32 rows = 2 560 characters = 20 KB**. We need 128 slices, not 32, so the natural per-row layout doesn't fit.

Solution: **reduce R1 (Characters per Line) from 80 to 20** so the CRTC only displays 20 characters per scanline. The pre-rendered screen is then **20 chars wide × 128 rows = 2 560 chars = 20 KB** — same memory, different shape.

```
R1 = 20   ; display only 20 chars per scanline (instead of 80)
R2 = ?    ; reduce so display centres on screen
```

The horizontal timing is unaffected — the CRTC still runs 128 character periods per scanline (R0 = 127). It just stops fetching after 20 of them. The remaining 108 are dead time (horizontal border).

Use **R2 (Horizontal Sync Position)** — normally 98 in MODE 0/1/2 — to slide the 20-character display window into the middle of the screen instead of jammed against the left edge. Reduce R2 to give more time after hsync before the next line starts, which shifts the display right on screen.

Now each scanline of memory holds one ribbon-rotation slice, 80 pixels wide, but only 20 CRTC characters' worth. 128 rotations × 80 bytes = 10 KB stored as 32 rows of 80 bytes in a regular MODE 1 screen — but the CRTC's narrow display unpacks it as 128 rows.

Actually since 4 rotations are stored per visible scanline (each one fills 20 of the 80 chars), it's even denser: the prerender uses the full standard MODE 1 buffer and the CRTC's narrow display crops 20 chars out of every scanline.

## CRTC config

Same 1-scanline-per-cycle chassis as [[techniques/kefrens-bars]] / [[techniques/checkerboard-zoom]]:

```
R9 = 0   (1 scanline per char row)
R4 = 0   (1 char row per cycle)
R6 = 1   (display)
R7 = &FF (no VSync)
R1 = 20  (narrow display)
R2 = adjusted to centre horizontally
R12/R13 → varies per cycle, picked by rotation
```

For 254 visible cycles + final rebalance: `R4 = 56`, `R7 = 25`.

## Per-scanline rotation lookup (the parameter dance)

Pick the rotation angle for scanline N. The interesting question is what function of N you use.

A "straight" twister is `θ(N) = N * twist + spin*t`, where:

- **spin** = global rotation per frame (`spin*t` shifts all scanlines together)
- **twist** = rotation delta per scanline (the "twistiness")

Both are 8.8 fixed-point, manipulated per frame to give pleasing animation.

But this is boring. Kieran adds two more parameters that animate via sine tables:

| Parameter | Effect |
|---|---|
| **spin** | Top-line angle increment per frame. Sine-modulated → twister rotates and pauses |
| **twist** | Per-scanline angle increment. Sine-modulated → "tightness" of twist varies, can even flip direction |
| **knot** | Adds a spike (peak in middle of a 256-entry lookup table) to per-scanline rotation. Sine-modulated phase → knot moves up/down screen. Gives the "pinched" appearance |

All parameter changes are sine-table lookup + ADC — no runtime multiplication. The "black art" is choosing sine wavelengths and amplitudes that compose into visually pleasing motion. Lots of trial and error per the write-up.

## Multiple twisters from the same memory

Once the memory layout is "128 rotations packed 4 per visible scanline", changing R1 between 20, 40, 80 unpacks differently:

| R1 | Display |
|---|---|
| 20 | One twister column (slices 0, 4, 8, ... of the 128 rotations) |
| 40 | Two twister columns side by side (slices offset by 1/128 of a rotation — visually identical to a single twister to the eye) |
| 80 | Four twister columns (each offset by 1/128 — perceptually a wider twister field) |

Same screen RAM, three completely different visual effects, by changing one register.

## The fourth-colour stipple

MODE 1 has 4 logical colours. The ribbon uses 3 (front, side, back) on a black background. To make the fourth colour useful, kieran adds a stipple: alternate scanlines display from main RAM and SHADOW RAM, with the SHADOW copy having pixels for "colour 4" inverted between scanlines 0 and 1.

Result: where main RAM shows colour 1 on even scanlines, SHADOW shows colour 2 — and the eye blends them into the "fourth" colour (colour 1+2 combined).

This is implemented via per-scanline ACCCON `D` bit toggle in the draw loop, alternating which screen the CRTC reads from on odd vs even rasters. Costs ~10c per scanline.

## Memory budget

- Main RAM screen: 20 KB (the prerendered base)
- SHADOW screen: 20 KB (the same buffer with alternate-scanline stipple variation)
- Per-frame param tables: ~1 KB

40 KB of pre-rendered art. Generation can be done offline in BASIC (the listing in the write-up uses standard `MOVE`/`DRAW`).

## Builds on / used by

- [[techniques/single-rasterline-rupture]] — 1-scanline cycle chassis.
- [[techniques/fx-framework]] — Timer 1 stable raster.
- [[hardware/crtc-6845]] — R1 (chars per line) and R2 (hsync position) are independent of horizontal total R0, so reducing R1 doesn't break horizontal timing.
- [[memory/shadow-ram]] — ACCCON D bit for per-scanline main↔SHADOW toggle.
- The "narrow CRTC display via R1" trick is reusable wherever you need to pack more rows into a fixed memory budget.
