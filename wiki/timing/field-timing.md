---
title: Field and scanline timing — measured constants
type: timing
tags: [timing, scanline, field, vsync, irq-latency, t1, rupture, cycles]
sources: [beeb-port-kit-hardware-facts, naug-ch13-video, naug-ch22-vias]
updated: 2026-09-06
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

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
