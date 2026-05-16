---
title: FX Framework (stable-raster demo runtime)
type: technique
tags: [framework, raster, timing, vsync, t1, sei, demo, fx-modules]
sources: [twisted-brain]
updated: 2026-05-16
---

# FX Framework

The runtime architecture used by [[sources/twisted-brain|Twisted Brain]] (and reusable for any raster-tight demo). Solves two problems:

1. **Make the same chunk of code run at the same physical scanline every frame**, so cycle-counted raster tricks land on the same line consistently.
2. **Provide a module interface** so effects can swap in/out cleanly without each one having to re-solve the timing problem.

## The stable-raster trick

The entire demo runs with **interrupts disabled** (`SEI`). IRQs are not used — System VIA flags are polled via `BIT &FE4D` instead. This lets you put cycle-counted code anywhere without worrying about an IRQ stealing 7+ cycles unpredictably.

Synchronisation to the TV signal uses **System VIA Timer 1 in free-run mode**, latched to *exactly* one PAL frame (`312 × 64 − 2 = 19 966 µs`). T1 then fires at the same scanline every frame for as long as the program runs. The 2 µs subtracted is the latch-load delay observed by RTW.

The boot-time setup positions T1 zero-cross to coincide with the start of raster line 0:

```
T1_initial = 32*64 - 2*64 - 22 - 2 = 1896 µs
             |       |       |    |
             |       |       |    └─ 2 µs latch trim
             |       |       └────── 22 µs of framework code that runs after T1 fires
             |       └────────────── VSync IRQ arrives 2 raster lines after the actual VSync edge
             └────────────────────── 32 raster lines between VSync (line 280) and end of frame (line 312)
```

After the first T1 fire, T1 reloads to `312*64 - 2` and free-runs forever — every subsequent fire is exactly one frame later, locked to whatever absolute scanline you chose.

### Cycle-stretching jitter

Polling `&FE4D` involves [[timing/cycle-stretching|cycle stretching]] on SHEILA accesses, giving up to **8 cycles of jitter** on the moment the wait-loop exits. Visually invisible at this scale. Truly 2-cycle-precise raster is possible via [[techniques/hexwab-stable-raster]] (narrowing-loop initial sync + T1 free-run + per-IRQ latch-read jitter compensation). Twisted Brain doesn't use it — see that page for when the extra precision is worth the code complexity.

### Initial sync

Before T1 takes over you need to know *which* cycle T1 was loaded on. This is done with a one-shot narrowing loop:

```asm
LDA #2
.vsync1
BIT &FE4D
BEQ vsync1                ; wait for vsync flag to rise

; we're now within 10 cycles of vsync edge
.syncloop
STA &FE4D                 ; ack vsync (stretched STA)
; loop for one frame minus a small tail
LDX #142
.deloop
  LDY #55
  .innerloop
    DEY
    BNE innerloop
  DEX
  BNE deloop
; nop slide
NOP:NOP:NOP:NOP:NOP:NOP:NOP:NOP:NOP
BIT &FE4D                 ; stretched BIT
BNE syncloop              ; if vsync hit during nop slide, narrow
; → exit when vsync edge falls inside the nop slide
```

The narrowing loop reduces uncertainty to a few cycles. Credit: hexwab (kieran originally misattributed to Tom Seddon + tricky — later corrected in the thread).

Note: the framework can't re-sync mid-demo because the music player takes a variable number of cycles per call. So if T1 drifts (e.g. because an effect produces 313 raster lines instead of 312 — see [[techniques/kefrens-bars]]) the only fix is for the offending effect's `kill` function to produce a balancing 311-line frame.

## The module interface

Each effect is a module with 4 entry points:

| Entry | When called | Budget | Purpose |
|---|---|---|---|
| `init` | first frame of effect, called at raster 0 with display **off** | unbounded (display blanked) | Set up screen buffers, decompress images, change MODE if needed |
| `update` | every frame, in vblank after music player + script | ~18 raster lines (= 2 304 cycles @ 2 MHz) | Per-frame logic. Safe to write to visible screen buffer (in vblank, no tearing) |
| `draw` | every frame, called at the start of raster line 0 | typically 256 raster lines | Per-raster cycle-counted CRTC programming. The hot path |
| `kill` | last frame of effect, in vblank | ~18 raster lines | Restore "known state" (MODE 2 CRTC, ULA `&F4`, default palette, main RAM displayed) |

### Required "known state" on exit

Every `kill` function must leave:

- Standard MODE 2 CRTC registers — 32 visible char rows × 8 scanlines each
- ULA Control Register = `&F4` (MODE 2)
- ULA palette = MODE 2 defaults (no flashing colours)
- Main RAM paged in for read/write via ACCCON
- Main RAM displayed by CRTC via ACCCON

The next module's `init` can then assume that starting state.

### The 312-line invariant

**Every `draw` function MUST produce exactly 312 raster lines of CRTC output** — otherwise T1 zero-cross drifts out of phase with the start of raster line 0 next frame. Most effects ensure this by ending in a "rebalance" CRTC cycle that takes (312 − previously consumed raster lines).

If you somehow produce 313 or 311 lines for one frame (as the Kefrens-bars effect does on real hardware — see [[techniques/kefrens-bars]]), the cleanest fix is a single deliberately-off-by-one rebalance frame in `kill` to put T1 back where it belongs.

## Why this matters

Without the framework, every effect would have to re-solve the boot-sync + per-frame-timing problem in its own way, and the inter-effect transitions would be brittle. With it, each effect is just a triple `(init, update, draw, kill)` with a known calling convention and a fixed contract about the system state at entry/exit. That's what makes a 14-effect demo with multiple loaders / SWRAM banks tractable.

## Builds on / used by

- [[timing/via-timers]] — T1 free-run mode and latch reload mechanism.
- [[timing/cycle-stretching]] — the 8-cycle jitter on `&FE4D` polls.
- [[os/interrupts]] — why this framework needs interrupts off (variable IRQ entry cost would destroy the cycle counting).
- Every per-effect page in [[sources/twisted-brain]] builds on this framework.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
