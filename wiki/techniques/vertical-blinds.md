---
title: Vertical Blinds (double-buffered 160-byte mini-frame)
type: technique
tags: [crtc, single-rasterline, vertical-rupture, mode-2, double-buffer, sine, stipple]
sources: [twisted-brain]
updated: 2026-05-16
---

# Vertical Blinds

A full-screen MODE 2 animation of "bars" sweeping left/right, drawn into a **160-byte mini-frame buffer** that the CRTC re-displays 128 times across the screen. The whole effect's framebuffer is one character row × 2 scanlines, double-buffered so the CPU can update one copy while the other is being shown.

From Twisted Brain Part 9 ([[sources/twisted-brain]]).

## The CRTC config

128 cycles per frame = 127 two-scanline display cycles + 1 final rebalance cycle = 256 visible scanlines. See [[techniques/single-rasterline-rupture]] for the framework-entered + looped + final accounting.

```
R9 = 1   (2 scanlines per char row)
R4 = 0   (1 char row per cycle)
R6 = 1   (display that row)
R7 = &FF (no VSync this cycle)
R12/R13 → fixed (points at one of the two 160-byte buffers)
```

Final rebalance cycle: `R4 = 28` (29 rows × 2 scanlines = 58 raster lines, of which only 2 are displayed thanks to R6=1; the other 56 hide VSync). `R7 = 13` for VSync at scanline 280. Total raster lines = 127×2 + 58 = 312 ✓.

The CRTC reads the same 160 bytes 128 times during display. The CPU's job during the FX draw function is to **redraw that buffer between frames** with the next frame's content.

## Double buffering

Why double-buffer when the buffer is only 160 bytes?

Because the draw work (compute 14 sine-bar positions + plot pixels + copy line buffer → screen) takes ~250 raster lines, far more than the 18-line vblank budget for `update`. So the draw function does its work **during** display — while the CRTC is showing buffer A, the CPU is writing buffer B for next frame. At frame boundary the update function swaps which buffer the CRTC reads from.

```asm
FX_update:
    LDX which_buffer
    BEQ use_A
    ; show row 0, write to row 1
    LDA #row0_addr_div_8 / 256 : STA &FE01 (via R12)
    LDA #row0_addr_div_8 MOD 256 : STA &FE01 (via R13)
    STA write_ptr -> row 1 base
    JMP swap
.use_A
    ; show row 1, write to row 0
    LDA #row1_addr_div_8 / 256 : STA &FE01 (via R12)
    ...
.swap
    EOR #1 : STA which_buffer
    RTS
```

Each buffer is 80 bytes (one MODE 2 character row). Total RAM cost: 160 bytes + the line buffer (256 bytes) + some constants.

## The line buffer

Bars are drawn into a **256-byte linear line buffer**: one byte per pixel-position-on-screen, with 15 colour values that get mapped to MODE 2 pixel-pairs in the copy loop.

Why a linear intermediate?

1. **Plotting is simple** — write byte N for pixel N. No MODE-2 nibble shuffling at draw time.
2. **Clipping is free** — the line buffer is wider than the visible screen (256 vs ~160 pixels of plot), so bars that extend off-screen are just written to clipped positions that the copy loop skips. No per-bar bounds checks.
3. **Stipple is cheap** — at copy time, each linear byte expands to a MODE 2 pixel pair, possibly stippling odd/even pixels for the appearance of more colours than the 8-colour palette allows.
4. **Constant-time copy** — the copy is always the same size (160 pixels = 80 MODE 2 bytes), regardless of how many bars are visible or where they are. Predictable raster cost.

## Constant-time discipline — the sink loop

The draw function plots **14 bars** of varying widths. Naively that's a variable amount of work per frame, which would shift the visible content horizontally on every frame.

The trick: each bar's plot consists of two loops with **identical cycle cost per iteration**:

1. The "real" loop writes `width` colour values into the line buffer at the bar's X position.
2. The "sink" loop writes `(max_width - width)` colour values to a throwaway sink address.

Total iterations = `max_width`, always. The combined cost is the same whether the bar is 1 pixel wide or 50 pixels wide.

```asm
; real plot
LDA bar_colour
LDX bar_width
.plot
    STA line_buffer, Y      ; 5c
    INY
    DEX
    BNE plot                ; 3c (taken) / 2c (final)

; sink to balance
LDX bar_max_minus_width
.sink
    STA sink_byte           ; 4c
    DEX
    BNE sink                ; (matched cycle count to plot)
```

(Exact cycle balancing requires the sink loop's per-iteration cost equal the plot loop's; pad with NOPs if needed.)

## Frame anatomy (FX draw)

The 256-raster-line draw function does roughly:

| Raster lines | Work |
|---|---|
| 0 | Reprogram CRTC for 2-scanline cycles |
| 1-83 | Copy 80 bytes (160 pixels) from line buffer to **the buffer NOT being displayed**, with stipple/colour-pair expansion |
| 84-161 | For each of 14 bars: update X (sine table), update width (sine table), plot to line buffer with sink-balanced loop |
| 162-254 | Wait until cycle #128 reached (timing pad) |
| 255+ | Restore CRTC for VSync rebalance cycle |

The exact line counts are budgets, not hard boundaries — the work just has to complete before the next FX update fires.

## Why it works

CRTC reads the same 160 bytes 128 times. Between every 2-scanline display, the CPU has 256 cycles to do *something* — but in this effect, the CPU isn't trying to change the buffer per-strip (which would be Kefrens-bars style; see [[techniques/kefrens-bars]]). It just changes the buffer **once per frame**, then lets the same content show 128 times for a 256-scanline "fill" of identical bars at consistent vertical position.

The bars move per-frame, not per-scanline. So a single buffer mutation per frame gives full-screen bar motion at 50 Hz.

The double-buffering matters because the FX draw budget (256 raster lines) overruns the vblank budget (18 lines) by an order of magnitude — couldn't possibly do the work in vblank with single buffer.

## Builds on / used by

- [[techniques/single-rasterline-rupture]] — 2-scanline-cycle chassis.
- [[techniques/fx-framework]] — the update/draw function split that makes the double-buffer arrangement work.
- [[hardware/crtc-6845]] — R12/R13 latch (changed once per frame, in update, not in draw).
- Memory cost: 160 bytes (two 80-byte buffers) + 256 bytes (line buffer) + tables.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
