---
title: Retrosoftware — Smooth Vertical Scrolling
type: source
url: http://www.retrosoftware.co.uk/wiki/index.php/How_to_do_the_smooth_vertical_scrolling
author: Richard Talbot-Watkins (Richtw)
date: 2008-07-11
local: raw/articles/retrosoftware-smooth-vscroll.md
code: [raw/code/vrupt.6502, raw/code/smoothscroll.bas]
tags: [crtc, scrolling, vertical-rupture, raster, smooth-scroll, mode-2]
updated: 2026-05-16
---

# Retrosoftware — "How to do the smooth vertical scrolling"

Tutorial by **Richard Talbot-Watkins**, hosted at retrosoftware.co.uk (2008). Practical introduction to two related raster techniques:

1. **Vertical rupture** — split a single TV frame into two or more CRTC cycles, each with its own screen-start address. Foundation for split-screen and status panels.
2. **Smooth vertical scrolling** — abuse R5 (vertical total adjust) across two CRTC cycles to add 0-7 extra scanlines to the top border, shifting the displayed screen by sub-character-row amounts while keeping the PAL total at 312 lines.

Accompanying source:
- `raw/code/vrupt.6502` — BeebASM source for the rupture demo (annotated rework by jbnbeeb, 2015, of Talbot-Watkins's original BBC-ASM listing).
- `raw/code/smoothscroll.bas` — BBC BASIC + inline assembler source for the smooth-scroll demo (Talbot-Watkins's original).

## Key technical claims

- **PAL frame = 39 character rows.** Default MODE 2 has `R7 = 34` (vertical sync at row 34), so **5 character rows remain after VSync** before the cycle ends.
- **Total scanlines formula**: `(R4+1) * (R9+1) + R5 = 39 * 8 + 0 = 312`. Any change to R5 must be compensated for in another cycle's R5 to keep the total at 312.
- **R4, R6, R7 are read each cycle** (not pre-latched). Reprogramming them mid-frame, during a CRTC cycle, affects the *next* read of those registers — i.e. immediately for R4 (cycle length), and for the field's R7 (VSync position).
- **R12/R13 are latched** at the start of each CRTC cycle. Writing them mid-cycle changes the address used by the *next* cycle, not the current one. This is the lever rupture relies on.
- **R5 (vertical total adjust)** is added to the cycle's row count as a number of extra scanlines after VSync — practically, extra top-border scanlines from the viewer's perspective.
- **VSync interrupt fires after the VSync pulse-width period** (default 2 scanlines), not at the exact VSync edge. Timer setups for screen-on must account for this offset.
- **R7 mid-frame rewrite "works"** in this technique despite the Hitachi datasheet classifying it as NG. The trick is that rewrites happen during the *previous* CRTC cycle and settle before the new cycle samples them. NG applies to rewrites *during* the cycle whose VSync would be affected. See note in [[techniques/vertical-rupture]].
- **Rupture worked example geometry (MODE 2)**:
  - Top window: 16 rows, hardware-scrolled, screen address in range `&5800-&7FFF` (uses hardware wraparound at `&8000` — requires 10K screen latched via `&FE40` bit 4/5).
  - Bottom window: 16 rows, stationary, start `&3000`.
  - Cycle 1 (top): R4=15 (16 rows), R6=16, R7=255 (no VSync this cycle).
  - Cycle 2 (bottom): R4=22 (23 rows), R6=16, R7=18 (VSync at `23-5=18` to match normal MODE 2 position).
- **Smooth-scroll geometry** (24 displayed rows, MODE):
  - Cycle with VSync: `R5 = 8 - line`, `R4 = 39 - 24 - 1 - 1 = 13` (rows count includes one extra row to absorb the two R5 fractions).
  - Cycle with playing area: `R5 = line`, `R4 = 24 + 1 - 1 = 24` (so 25 rows of which 24 displayed + 'line' extra scanlines).
  - Screen disabled via Video ULA after VSync; re-enabled by System VIA T2 timer set at VSync IRQ, giving rock-steady visible top edge.
  - The timer load value compensates for `R5` so the screen-on point is always at the same physical scanline.
- **Why the lower status window matters**: with two CRTC cycles, the bottom cycle naturally provides a visible "status" area. This gives the timer interrupt some slack — it can fire anywhere within the status row's display and you'll still hit the cycle-switch correctly. Without it, R6=0 with imperfect timing would let the CRTC briefly send display data to the TV.

## Filed into

- [[techniques/vertical-rupture]] — new entity page; foundational technique.
- [[techniques/smooth-vertical-scroll]] — new entity page; builds on rupture.
- [[hardware/crtc-6845]] — augmented practical-rewrite note: R4/R6/R7 mid-frame rewrites are safe when done *during the cycle preceding* the one they govern (the technique's whole basis).
- [[video/hardware-scrolling]] — cross-link added to smooth-scroll page.
- [[index]] / [[log]] — standard updates.

## Notes from the smoothscroll.bas listing

Initial CRTC register table (line 310 `crtcvals`):

| R0 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 | R11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 127 | 80 | 98 | `&28` | 38 | 0 | **26** | **31** | `&F0` | 7 | 32 | 8 |

Note divergence from default MODE 2: **R6=26** (not 32 — gives total displayed of 26 rows split as 25 scroll + 1 status), **R7=31** (not 34 — VSync shifted), **R8=`&F0`** (display delay=3, cursor delay=3, non-interlaced, no skew). Addressable latch (`&FE40`) is set to select the **20K screen** (`&3000-&7FFF`) with `LDX #4 : STX &FE40 : INX : STX &FE40` (clearing bit 4 then setting bit 5 — see [[hardware/system-via]] for latch wraparound bits).

Variables (zp): `addr` (R12/R13 word), `line` (sub-row 0-7), `iline` (latched copy used in the timer ISR), `vsync`/`vsync2` (frame-count flags), `irqcount` (which IRQ next), `delay` (timer compensator).

## Open follow-ups

- "Vertical rupture" terminology originates in the **Amstrad CPC scene** per the article — would be worth a brief etymology note if we ever add a cross-platform-techniques page.
