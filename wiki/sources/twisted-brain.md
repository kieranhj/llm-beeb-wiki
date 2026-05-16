---
title: Twisted Brain — Bitshifters demo write-up
type: source
url: https://stardot.org.uk/forums/viewtopic.php?t=15300
demo: https://bitshifters.github.io/posts/prods/bs-twisted-brain.html
source_code: https://github.com/bitshifters/twisted-brain
author: kieran (kieranhj)
collective: Bitshifters Collective (kieran, simonm, sbadger, Dethmunk)
date: 2018-06-27
local: raw/articles/twisted-brain-writeup.md
tags: [demo, crtc, raster, vertical-rupture, single-rasterline, kefrens, twister, parallax, copper, smooth-scroll]
updated: 2026-05-16
---

# Twisted Brain — Write-up

Kieran's 15-part technical write-up of the Bitshifters Collective's 2018 demo *Twisted Brain*. Demo by kieran/simonm/sbadger/Dethmunk. The first BBC demo to make extensive use of **single-rasterline CRTC vertical rupture** — pushing the rupture technique from the 2-3 cycles per frame used for status splits (see [[techniques/vertical-rupture]]) to **128-256 cycles per frame** where each cycle is just 1-2 scanlines tall.

Posted to Stardot 2018-06-27 onwards. Source code on GitHub. Demo video: <https://bitshifters.github.io/posts/prods/bs-twisted-brain.html>.

## Why this matters

Every effect in the demo shares the same underlying idea: a tiny pre-rendered or beam-raced buffer (one character row, or one scanline) displayed many times via vertical rupture, then mutated either at render time (chase the beam) or at vblank (frame-coherent). The 6502 cannot fill 20 KB at 50 Hz; it *can* fill 80 bytes per scanline and let the CRTC do the rest. The write-up is a comprehensive recipe for that whole class of techniques.

## Part index

| # | Part | Wiki coverage |
|---|---|---|
| 1 | FX Framework & Main Loop | [[techniques/fx-framework]] |
| 2 | Da Brain Picture | covered here — trivial palette anim |
| 3 | Text Screens | covered here — per-raster palette swap, technique is a simpler form of [[techniques/copper-bars]] |
| 4 | A brief introduction to CRTC registers | reference, see [[hardware/crtc-6845]] |
| 5 | Vertical Rupture | covered by [[techniques/vertical-rupture]] (kieran credits RTW's earlier write-up) |
| 6 | Copper Colours | [[techniques/copper-bars]] |
| 7 | Plasma | covered on [[techniques/copper-bars]] (same CRTC config, varies in screen-address offsets) |
| 8 | Parallax Bars | [[techniques/parallax-bars]] |
| 9 | Vertical Blinds | [[techniques/vertical-blinds]] |
| 10 | Kefrens / Alcatraz bars | [[techniques/kefrens-bars]] |
| 11 | Checkerboard Zoom | [[techniques/checkerboard-zoom]] |
| 12 | Bitshifters "MODE 7" logo | covered here — applied case of [[techniques/single-rasterline-rupture]] |
| 13 | Twister | [[techniques/twister]] |
| 14 | Smiley Drop | application of [[techniques/smooth-vertical-scroll]] |
| 15 | Miscellaneous Debris (memory stats) | covered here |

## Key technical claims

### The FX framework (Part 1)

- Interrupts disabled (`SEI`) throughout the demo. IRQ flags polled via `&FE4D` instead.
- Stable raster sync at boot via narrowing-loop on `BIT &FE4D` for vsync (code attributed by kieran to Tom Seddon + tricky originally, later corrected — credit hexwab for the `Mode 7 stable raster` code).
- System VIA Timer 1 in free-run mode, latched to `FramePeriod = 312*64 - 2` so it fires at the same scanline every frame.
- Initial T1 value: `32*64 - 2*64 - 22 - 2 = 1896 µs` = (32 lines to end of frame) - (2 lines vsync pulse) - (22 µs framework code) - (2 µs latch trim).
- ~8-cycle jitter on T1-poll due to cycle stretching on `&FE4D`. Truly-stable-raster (hexwab's technique) is possible but more code; not used in Twisted Brain.
- Effect modules expose 4 entry points: `init` (called at raster 0, display off), `update` (vblank, ≤18 raster lines budget), `draw` (called at raster 0, typically runs ~256 raster lines), `kill` (vblank, restores known state).
- Every module must leave system in MODE 2 + ULA `&F4` + default palette + main RAM displayed/visible on exit.
- Every module's draw function must produce **exactly 312 raster lines** (so T1 stays in phase next frame).

### Per-effect highlights

- **Part 2 — Da Brain Picture**: 3 lines per frame copied from SHADOW to main RAM. Palette animation on colours 8-15. The simplest possible effect; included for the init/update/draw/kill module pattern.
- **Part 3 — Text Screens**: MODE 1, palette swapped every raster line in horizontal blanking. 4 palette writes per colour. "Copper" hue table (red → magenta → blue → cyan → green → yellow → red) + "pastel" black-and-white-stipple variant. Confession: the loop was 127 cycles not 128, didn't noticeably break anything because palette only updated every ~20 lines.
- **Part 12 — Bitshifters "MODE 7" logo**: MODE 1 image of a teletext-style logo. Single-scanline rupture displays each of 15 logo "sixel" rows for 16 raster lines. Pre-shifted 2-pixel offsets stored in 2 sets of 16 scanlines. Palette swap every 64 raster lines for red/green/yellow/blue colours.
- **Part 14 — Smiley Drop**: smooth vertical scroll used as a sprite reveal. `Vertical Displayed R6` is set larger than scrolling-window's `Vertical Total R4` so the VADJ scanlines are visible — the bit on top of the scrolling-window cycle that shows the partial-row content. CRTC R8 used as blank/unblank lever (`&00`/`&30` — non-interlace + display delay).
- **Part 15 — Memory budget**: main 7 KB, 4 SWRAM banks each ~16 KB (effects packed tightly), music 24 KB (~16K SWRAM + spills into HAZEL `&C000`). The demo runs at PAGE `&1900` for legacy DFS compatibility.

### Music (Part 15-ish, simonm)

- Pre-decompressed packet stream: 11 bytes per packet, one packet per 50 Hz frame, all SN76489 register writes pre-computed.
- Music data comes from converted Atari ST YM2149F tunes (very close cousin to the BBC's SN76489). simonm wrote a YM→SN converter — see <https://github.com/simondotm/ym2149f>.
- Tune is Mad Max — "There aren't any sheep in outer Mongolia".

## Real-hardware quirks the write-up uncovers

- **Kefrens bars** — Vertical Total R4 rewrites on the final scanline of a 1-scanline CRTC cycle don't take effect until the *next* scanline on real HD6845SP. Causes the frame to be 313 lines long for one frame after the effect starts. Now understood (see [[techniques/kefrens-bars]]): in a 1-scanline cycle, *every* scanline is the "last raster" window the chip uses for register sampling, so R12/R13 sample, R4 compare and R7 compare operations overlap ambiguously — the datasheet doesn't specify their relative timing within a single scanline because normal-cycle usage never exposes the question. Fix: a 311-line "rebalance" frame in the kill function.
- **Parallax bars + 64 µs T1 drift** — sensitive to the Kefrens timing bug above. If T1 is one raster line off, the main/SHADOW RAM switch in mid-frame happens at the wrong line and you get single-pixel-row "glitch" lines at the boundary.
- **BeebEm cycle inaccuracy** — Twisted Brain only runs cleanly on b-em (in 2018, when b-em was the gold standard) and was later validated on jsbeeb. BeebEm gets the cycle stretching wrong. Documented in follow-up posts. (As of 2026 the canonical-accurate emulators are jsbeeb, b2 and beebjit — b-em was the historical leader but has not kept up.)

## Filed into

New foundation pages: [[techniques/fx-framework]], [[techniques/single-rasterline-rupture]].

New per-effect technique pages: [[techniques/copper-bars]], [[techniques/parallax-bars]], [[techniques/vertical-blinds]], [[techniques/kefrens-bars]], [[techniques/checkerboard-zoom]], [[techniques/twister]].

Updated: [[techniques/vertical-rupture]] (link to single-rasterline extension), [[techniques/smooth-vertical-scroll]] (Smiley Drop as applied case), [[hardware/crtc-6845-advanced]] (the Kefrens R4-on-final-scanline mystery).

## Open follow-ups

- Truly-stable-raster (hexwab's technique) — referenced but not used in Twisted Brain. Now documented in [[techniques/hexwab-stable-raster]] (resolved).
- The R4-rewrite-on-final-scanline behaviour: now understood as a consequence of overlapping register-sample windows in 1-scanline cycles (see [[techniques/kefrens-bars]] for the explanation). Still no chip-internal phase-by-phase diagram; would be nice if anyone has scoped which clock edge each register's compare actually happens on.
- Twister "stable rotation parameters" (Spin / Twist / Knot) are a black-art parameter search; could be derived analytically.
- BeebEm modernisation — Kevin Edwards is in the thread asking if BeebEm could fix its cycle timings to be like b-em. Worth tracking if it ever lands.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
