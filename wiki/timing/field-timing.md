---
title: Field and scanline timing — measured constants
type: timing
tags: [timing, scanline, field, vsync, irq-latency, t1, rupture, cycles]
sources: [beeb-port-kit-hardware-facts, naug-ch13-video, naug-ch22-vias, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# Field and scanline timing — measured constants

The numbers a raster-timed program is built from, **as counted in the emulator** during Kieran Connell's two ports — [Paradroid](https://github.com/kieranhj/paradroid-beeb) (Model B, MODE 1, three-cycle rupture) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (Master 128, MODE 2, two-cycle rupture). Source: [[sources/beeb-port-kit-hardware-facts]] §8 and §1. For the VIA timer mechanics see [[timing/via-timers]]; for what stretches a cycle see [[timing/cycle-stretching]]; for the CRTC's own field anatomy see [[hardware/crtc-6845-advanced]].

## The constants

| Quantity | Value | How it was measured |
|---|---|---|
| One scanline | **128 CPU cycles at 2 MHz** (64 µs) — *not 64 cycles* | Paradroid, 2026-08-15; corrected a wrong earlier figure that had cost a build |
| One field | 312 scanlines = **39,936 cycles** | 1,000 fields in 39,936,000 cycles exactly (Paradroid Layer 3, VSync count) |
| One 25 Hz pass (two fields) | 79,872 cycles | 128 passes in 10,223,616 cycles |
| MODE 1 scanline, display vs blanking | display is cycles **0-79**, blanking **80-127** | Paradroid, 2026-09-06, phase of a `STA &FE01` against a `run_frames` anchor, differenced mod 128 |
| MODE 1 blanking window for a CRTC write | ~24 µs | Paradroid Layer 3 |
| System VIA T1 tick | 1 MHz; **`SL = 64` ticks a scanline** | Edge, 2026-09-02 |
| A 25 Hz frame in T1 ticks | 39,936 µs | arithmetic from the above |
| Rows in a rupture | must sum to **39** (× 8 scanlines = 312) or the picture rolls | Paradroid Layer 3 |
| One CRTC character | **0.5 µs in MODEs 0-3** (128 a line), 1 µs in MODEs 4-7 (64 a line) | per-mode R0 ([[hardware/crtc-6845]]); phX's probe counts 128 characters a line, jsbeeb Master ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1) |
| CRTC write slot | every CRTC write lands at an even C0 (1 MHz); back-to-back `STA &FE01` 6 cycles | phX, jsbeeb 2.10.2, 2026-11-14 |
| 272 lit lines in a field | unchanged 39,936.00 cycles a field (3,993,600 over 100) | 1942, jsbeeb, 2026-09-07/08; played on a real Master ([[video/monitor-crt]]) |

## VSync and interrupt latency

- **The VSync CA1 interrupt is serviced about 4 scanlines after the VSync edge.** The timer chain itself is exact — breakpoint bisection put Paradroid's fire 1 at 78.3-79.3 scanlines after handler entry against a design figure of 78 — so the whole error is in where VSync itself sits. The scanline component cannot be read from screenshots better than ±2; KC spotting two wrong lines on b-em is what pinned it. (Paradroid Layer 3, [`docs/layer-3-scroll.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-3-scroll.md).)
- **IRQ latency swings by more than a few cycles**: the 6502 finishes the instruction it is on, and a `SEI` window in the foreground (17 cycles in Paradroid's `SetCRTCStart`) adds to it. A CRTC write with 3-7 cycles of margin to the end of horizontal blanking overran intermittently and showed a character of the next row in the bottom-left corner. (Paradroid, 2026-09-06, [`docs/raster-timing.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/raster-timing.md).)
- **Timer fires that must land in a CRTC cycle should overshoot the boundary by a few rows.** Sized to reach the boundary exactly, IRQ latency alone carried them into the previous cycle. (Paradroid Layer 3, with a `DEBUG_RASTER` tint at each interrupt entry.)
- **Erring late on the top edge is harmless; erring early shows content from the bottom of the window at the top.** Bias late if in doubt. (Paradroid Layer 3, jsbeeb and b-em.)

## The two ruptures' T1 constants

Both ports drive their ruptures from System VIA T1 in continuous mode, restarted at VSync (see [[timing/via-timers]] for why not T2). The constants, for calibration against your own:

| Port | Constant | Value | What it gives |
|---|---|---|---|
| Paradroid (three cycles, MODE 1) | `T1_I1` | `(84 + FRAME_DROP_ROWS * 8) * SL - 2 + T1_TUNE` | VSync handler to fire 1; VSync and this move together |
| Paradroid | `T1_TUNE` | `-4 * SL - 32` (was `-22`) | `-4 * SL` for the ~4-scanline CA1 service latency; the sub-scanline part centres fires 2 and 3 in blanking (writes at cycles ~93-99 of 128, 29 cycles of margin, against 116-124 before) |
| Edge Grinder (two cycles, MODE 2) | `T1_I1` | `56*SL - 4*SL - 2` | VSync handler to fire 1 = 6,802 cycles = 53.1 scanlines |
| Edge Grinder | `T1_I2` | `40*SL - 2` | fire 1 to fire 2 = 5,122 cycles = 40.0 scanlines |

The `-2` is the `(N+2) µs` load-and-underflow anatomy on [[timing/via-timers]]. **Take the phase from the emulator, not from the arithmetic**: the phase is a property of the whole IRQ path and drifted ~6 µs later than the calibration as the handler changed. (Paradroid Layer 3 and 2026-09-06, breakpoint bisection and a `T1_PROBE` screenshot method; Edge 2026-09-02, breakpoints on the two handlers and `elapsed_cycles`; [`docs/layer-2-display.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-2-display.md).)

## Measuring a frame

- **VSync quantises a step to whole frames**: a redraw a few thousand cycles over the line costs a whole extra frame, so a small optimisation can move nothing and the next one everything. (Paradroid Layer 3: vertical scroll 4 → 5 → 10 steps in 10 frames.)
- **A phase maximum includes any interrupt that landed inside it.** With six interrupts a frame, a 644-cycle phase showed a 3,632-cycle maximum. Take worst cases from maxima and typical costs from a single-frame sample. (Edge, 2026-09-04, [`docs/performance.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/performance.md).)
- **A T1 difference used as a stopwatch is only modular while the counter does not pass zero between the reads**; when it does, the sample gains ~65,536 ticks, and because the reload point drifts slowly the bad readings come in consecutive runs. Paradroid's `DEBUG_TIME` reported 2,903 cycles for code measured at 1,009 by breakpoints. (2026-08-26.) **T2's two bytes are read one after the other and the counter can roll between them**; reject a sample whose subtraction borrows. (Edge 2026-09-04: three readings of three were junk before the fix.) See [[timing/via-timers]].
- Malformed fields when switching CRTC shapes are on [[hardware/crtc-6845-advanced]]; they show up here as fields of 38,378 / 49,154 / 6,168 cycles instead of 39,936.

## See also

- [[timing/via-timers]] — T1/T2 mechanics, the `+2`, T1 vs T2 for raster work.
- [[hardware/crtc-6845-advanced]] — field anatomy, write windows.
- [[techniques/vertical-rupture]] — where these constants are used.
- [[tools/emulators]] — how the measurements were taken.


## Later measurements (2026-09 to 2026-11)

From [[sources/beeb-port-kit-hardware-facts-2026-11]] §8 and §11. Isometrikum and Square Roots are CPC demos ported to the BBC (Model B + sideways RAM and Master; **jsbeeb only**, not yet b2 or hardware); phX is a CPC demo ported to the Master and played on KC's real Masters.

### T1 fires and the stable raster (CPC demo ports, jsbeeb)

- **A fire's first CRTC write lands 4 lines after its nominal line** with no correction (the CA1 flag's timing, the IRQ path, the slide) — the same ~4-scanline VSync service latency as above. `T1_SYNC_TUNE = -3*SL`, applied to the next field, puts every write 1 line + 5 characters after its line: fire 0's R4 at 3:9 in 6,384 of 6,399 fields, fire 1's at 49:9 in 6,383; the rest up to 54 characters late, each because a bass interrupt was already running (Isometrikum, MODE 2, R1 = 96, 2026-11-07).
- **A stable-raster NOP slide of 80 µs holds one write position in 2,994 of 2,999 fields; 64 µs splits the writes between two positions 2 cycles apart.** Page-aligned (`ASSERT HI(slide) = HI(slide_end)`), entered by a self-modified low byte from `loaded - T1CL`. Only worth it where a write window is narrow: Square Roots' windows were whole 512 µs rows and its slide was removed (2026-11-07/08). See [[techniques/hexwab-stable-raster]].
- **Re-arming T1 from a constant drifts; chaining its latch does not.** A fire-0 restart drifted 70 µs a field; each fire loading the latch for the next interval, T1 locked once at install, held (Square Roots, 2026-11-08). Same conclusion as the T1-not-T2 rule on [[timing/via-timers]].
- **A frame need not be 312 lines.** Square Roots' CPC frame is 304 lines (51.4 Hz, measured on the reference CPC model); the BBC runs it as R4 = 37 with a T1 field of 19,456 µs (304 × 64) — 312 would make the demo 2.7% slower. A harness counting jsbeeb's frames drifts against such a frame.
- **A software bass on User VIA T1 is only as punctual as the interrupts in front of it**: Isometrikum's VSync music costs 2,337 cycles a field (5.9%), the bass 1.95 interrupts a field at 152 cycles; toggles within 8 cycles of the period 85.5% with two raster fires, 77.5% with five, worst ±4,700 cycles (jsbeeb).

### One cadence for a whole demo (phX, Master)

- **One T1 chain, two latches, a 0-14-cycle slide**: phX's draw is entered at the same beam position (C0 0) every field of 16,302, every field 39,936 cycles, VSync once a field (jsbeeb, `verify_frame.mjs`, 2026-11-15). Only fields with disc NMIs enter late (0-35 cycles behind the loading card, 0-67 in all four load windows), because an NMI (35 cycles a byte) can delay the IRQ beyond what the slide absorbs — a line-exact part must not run while the disc loads.

### Counting fields in jsbeeb

- **jsbeeb's `frameCount` counts C4 = R6 matches and nothing else** — not VSync, not the frame's end. A field whose display is cut by R8 and never reaches R6 does not count; one that meets R6 twice counts two. jsbeeb's web display decays its phosphor by that count, so a demo whose frames never reach R6 turns white on bbc.xania.org while headless harnesses pass. A real 6845 needs no R6 match. phX's rule: meet C4 = R6 exactly once a field inside lines R8 already blanks, and fail a frame check unless the count steps one a field (jsbeeb 2.10.2 and main 2.21.1, 2026-11-14). More on [[tools/emulators]].
- **Sample a harness at the port's own tick, not jsbeeb's frame**, when the port's frame is not 312 lines (Square Roots' 304-line frame drifted against it).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
