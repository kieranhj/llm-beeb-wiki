---
title: Raster Splits (overview)
type: technique
tags: [raster, crtc, video-ula, palette, mode-split, vertical-rupture, single-rasterline]
sources: [naug-ch13-video, twisted-brain]
updated: 2026-05-16
---

# Raster Splits

"Raster split" is the umbrella term for **changing CRTC or Video ULA state mid-frame, in sync with the beam position**, to make different parts of the screen behave differently. The BBC has no hardware sprite, no scrolling layers, no per-pixel attributes — but a 2 MHz CPU racing a 50 Hz raster can substitute for all of those, given precise enough timing.

This page is an index of the specific raster-split families documented on the wiki. Each family is its own technique page; this page exists so readers entering with "I want to do a raster split" land somewhere useful.

## The split levers

Five things can be changed mid-frame, each with its own latency and visible cost:

| Lever | Where to write | Latency | Visible cost | Typical use |
|---|---|---|---|---|
| **Palette colour** | Video ULA `&FE21` | 4c (stretched) | 1 entry per write; in MODE 1 you must write 4 entries to fully change a colour ([[hardware/video-ula]]) | Per-raster hue rotation, copper bars |
| **ULA flash bit** | `&FE20` bit 0 | 4c (stretched) | 1 cycle | Per-raster colour inversion of all flash-coded palette entries — see [[techniques/checkerboard-zoom]] |
| **ULA mode bits** | `&FE20` bits 2-4 | 4c (stretched) | One char of horizontal smear at the transition | Mid-frame MODE width change (rarely worth it on real hardware) |
| **CRTC screen start** | `&FE00`/`&FE01` R12/R13 | 8c per byte | Pre-latched, applies to *next* CRTC cycle | Hardware-scroll position, per-cycle screen-address selection in [[techniques/single-rasterline-rupture]] |
| **CRTC cycle shape** | `&FE00`/`&FE01` R4/R6/R7/R5 | 4c each | Read on the cycle they govern (R4/R6/R7) or applied at cycle end (R5) | Vertical rupture, smooth vertical scroll |
| **ACCCON video source** | `&FE34` bit `D` | 4c (stretched) | Immediate — affects the *next* CRTC fetch | Mid-frame main↔SHADOW swap in [[techniques/parallax-bars]] |

The CRTC's R12/R13 latch and R4/R6/R7 sample timing are documented on [[hardware/crtc-6845-advanced]].

## Split families

### Per-frame splits (rupture)

Split the frame into N CRTC cycles, each with its own screen-start address. Foundation for everything below.

- [[techniques/vertical-rupture]] — the 2-3-cycles-per-frame case used for status panels and game playfields.
- [[techniques/single-rasterline-rupture]] — the 64-256 cycles per frame extreme, each cycle 1-4 scanlines tall. Foundation for modern Beeb demos.
- [[techniques/smooth-vertical-scroll]] — two-cycle rupture + R5 trick for 1-scanline vertical motion.

### Per-raster palette changes

Cycle-counted writes to `&FE21` inside horizontal blanking, looping per scanline.

- [[sources/twisted-brain]] Part 3 (Text Screens) — MODE 1 palette swap per raster, ~26c per colour, ~128c/raster budget. Cheapest possible raster split.
- [[techniques/copper-bars]] — palette change per CRTC cycle (4-scanline granularity), in horizontal blanking, only when solid colour is on screen (avoids partial-palette artefacts).
- [[techniques/checkerboard-zoom]] — per-raster flash-bit toggle instead of palette write. 4 cycles vs ~26 cycles for the equivalent palette change.

### Per-cycle screen-start changes

R12/R13 latched once per CRTC cycle, picking a different screen address each time.

- [[techniques/copper-bars]] + [[techniques/parallax-bars]] — pre-rendered buffer, per-cycle address selection by sine-table lookup.
- [[techniques/twister]] — narrow-screen variant via R1=20, packing 128 ribbon rotations into a standard MODE 1 buffer.

### Beam-raced buffer mutation

R12/R13 stays fixed; CPU rewrites the buffer between scanlines so each visible strip is freshly drawn.

- [[techniques/vertical-blinds]] — 2-scanline-per-cycle, double-buffered 160-byte mini-frame.
- [[techniques/kefrens-bars]] — 1-scanline-per-cycle, additive 80-byte buffer mutation (4 bytes per scanline budget).

### Mid-frame video-source switches

ACCCON `D` bit toggle on the boundary between CRTC cycles.

- [[techniques/parallax-bars]] — main↔SHADOW swap to access a 64-row pre-rendered buffer larger than one MODE 1 screen.
- [[techniques/twister]] — alternate-scanline main↔SHADOW swap for a fourth-colour stipple.

## Prerequisites

All raster splits depend on knowing what raster the beam is on, accurate to within a few cycles. Three approaches:

1. **System VIA T1 free-run** in continuous mode, polled with `BIT &FE4D` (~8c jitter due to cycle stretching). Used by [[techniques/fx-framework]] / Twisted Brain.
2. **CRTC vsync interrupt** via IRQ1V — same jitter problem as 1, plus IRQ entry latency variability.
3. **hexwab's stable raster** — initial narrowing-loop sync + T1 free-run + per-IRQ jitter compensation via latch read. 2-cycle precision. See [[techniques/hexwab-stable-raster]].

For most effects, (1) is good enough. (3) is for sub-pixel-precise effects where the residual 8c jitter would be visible.

## Why the BBC is well-suited to this

The CRTC's R12/R13 latch-once-per-cycle behaviour ([[hardware/crtc-6845-advanced]]) is the lever. The Video ULA's separation of "byte fetch" (CRTC) from "byte→pixel decoding" (ULA mode setting) is the second lever. The System VIA's free-run timer + cycle stretching that aligns reads to 1 MHz boundaries is the third.

Other 8-bit machines have some of these (the C64's VIC-II is generally more raster-friendly out of the box; the Spectrum's ULA is more rigid). The BBC's discrete-logic implementation means *more* of the chip state is poke-able mid-frame and the timing is more deterministic. That's why the BBC demo scene is what it is.

## Builds on

- [[hardware/crtc-6845]] / [[hardware/crtc-6845-advanced]] — register-rewrite semantics.
- [[hardware/video-ula]] — palette write protocol, ULA control register layout.
- [[hardware/system-via]] / [[hardware/user-via]] — T1 continuous mode for sync.
- [[timing/cycle-stretching]] — why VIA reads quantise to 1 MHz boundaries.
- [[techniques/fx-framework]] — the standard "8c jitter is fine" sync chassis.
- [[techniques/hexwab-stable-raster]] — the "2c jitter, full beam race" chassis.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
