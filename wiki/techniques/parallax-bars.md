---
title: Parallax Bars (64-row buffer via mid-frame ACCCON switch)
type: technique
tags: [crtc, single-rasterline, parallax, mode-1, shadow-ram, acccon, dither]
sources: [twisted-brain]
updated: 2026-05-16
---

# Parallax Bars

Vertical parallax-scrolling bars in MODE 1, inspired by Rebels' *Total Triple Trouble* on the Amiga. Built on [[techniques/single-rasterline-rupture]] with one extra ingredient: a **64-character-row pre-rendered buffer split across main RAM and SHADOW RAM**, switched mid-frame via ACCCON (`&FE34`) — see [[memory/shadow-ram]].

From Twisted Brain Part 8 ([[sources/twisted-brain]]).

## The problem

7 layers of bars at decreasing distance from a virtual "camera". The top layer is 32 px wide × 32 px apart = 5 bars across a 320-pixel MODE 1 screen. Move the camera 1 pixel right and the bars all shift by amounts proportional to their distance. After 64 single-pixel camera-shifts the front layer wraps and we're back where we started.

So we need **64 character rows** of pre-rendered bars (each row is one camera-position snapshot). The CRTC then picks the right row for each scanline and the user sees parallax motion as the row choice scrolls.

## Why two screens

MODE 1 screen = 32 character rows × 80 bytes = 20 KB. Our 64-row buffer needs **40 KB** — too big for one screen.

Solution: split the buffer across two MODE 1 screens, one in main RAM (rows 0-31) and one in SHADOW RAM (rows 32-63). Switch which the CRTC reads from per cycle.

## The mid-frame switch

CRTC R12/R13 is **latched** at the start of each cycle (see [[hardware/crtc-6845]]). ACCCON `D` bit (display source) takes effect **immediately**. So the sequence per cycle is:

1. During this cycle: write the *next* cycle's R12/R13 (latched).
2. **Immediately before the next cycle starts**: write ACCCON to switch main↔SHADOW.

Timing has to be sharp — ACCCON is read by the address translator on the very next CRTC fetch. If you write it too early, the *current* cycle's display flips mid-fetch. If you write it too late, the new cycle starts with the wrong RAM source.

The window: the end of the **4th scanline (horizontal blank)** of the current cycle. By then all displayable bytes for the current cycle have been fetched, and the next cycle's first fetch hasn't happened yet.

## The per-cycle loop

CRTC config: 64 cycles per frame = 63 four-scanline display cycles + 1 final rebalance cycle (same chassis as [[techniques/copper-bars]] — see [[techniques/single-rasterline-rupture]] for the accounting). The draw function enters with cycle 1 already underway and the loop iterates **62 times** to set up cycles 2 through 63.

Per-iteration work (must fit in 4 raster lines = 512c):

```asm
.loop                       ; 62 iterations
    ; --- per-frame sine math ---
    TXA                     ; 2c
    CLC                     ; 2c
    ADC parallax_wavey      ; 3c
    TAX                     ; 2c
    LDA sine_table, X       ; 4c
    CLC                     ; 2c
    ADC parallax_x          ; 3c
    AND #&3F                ; 2c   wrap to 0..63
    TAY                     ; 2c   Y indexes the buffer-row table

    ; pad until horizontal blank
    FOR n,1,23 : NOP : NEXT : BIT 0   ; 49c

    JSR cycles_wait_128     ; +128c   wait one raster line
    JSR cycles_wait_128     ; +128c   wait another

    ; --- write R12/R13 for next cycle ---
    LDA #12 : STA &FE00 : LDA vram_hi, Y : STA &FE01   ; 18c
    LDA #13 : STA &FE00 : LDA vram_lo, Y : STA &FE01   ; 18c

    JSR cycles_wait_128     ; +128c   one more raster line

    ; --- write ACCCON for next cycle (in 4th hsync) ---
    LDA &FE34               ; 4c (stretched)
    AND #&FE                ; 2c   clear D bit
    ORA vram_page, Y        ; 4c   set D bit if row >= 32
    STA &FE34               ; 4c (stretched)

    DEC parallax_crtc_row   ; 5c
    BNE loop                ; 3c
```

The three `JSR cycles_wait_128` calls span the three "passive" raster lines per cycle. The fourth raster line ends in the ACCCON write.

## Animation

- Per character row: index into the buffer is `(parallax_x + sine_table[parallax_wavey + row]) & 63`. So bars at different rows are offset by a sine wave — gives the wavy parallax-with-curvature look.
- Per frame: increment `parallax_x` (horizontal scroll) and `parallax_wavey` (phase of the wave).
- All offsets are sine-table lookup + ADC — no runtime multiplication.

## Why it's the most timing-sensitive effect in Twisted Brain

If Timer 1 fires even **one raster line early or late**, the ACCCON write lands one raster line off, and the main↔SHADOW switch happens *during* the wrong cycle. Result: single-pixel "glitch" rows at the main/SHADOW boundary. Particularly visible at the row 31→32 transition (where the buffer source actually changes).

This is the canonical failure mode that exposes the Kefrens-bars 313-line frame bug — see [[techniques/kefrens-bars]] for why that bug propagates here and how the `kill` function uses a 311-line rebalance frame to put Timer 1 back where it should be.

## The pre-rendered buffer

Each of the 64 rows is one "camera offset" with all 7 bar layers drawn. Generated with a BASIC program that:

1. Draws each layer from back to front at the appropriate distance-scaled offset.
2. Uses **ordered dither inside each bar** to give a smooth gradient, with the dither pattern keyed to pixel coordinates within the bar (not screen coordinates) — so the dither stays attached to the bar and doesn't scintillate as bars move.

40 KB of pre-rendered art is a lot of memory, but it's only paid once at init time.

## Variants worth knowing

- **MODE 0 version**: would let you have 80-pixel-wide bars with finer dither, but doubles the per-row buffer size — would need 80 KB pre-rendered. Doesn't fit.
- **Procedural bars** at runtime: in principle possible if you can compute one row's pixels in <512c. With 80 bytes to write per row, you'd have ~6 cycles/byte budget — feasible for plain colour bars, but no dithering.
- **More layers**: each additional layer doubles the camera-offset cycle, so 8 layers would need 128 buffer rows / 80 KB. Not viable in 64 KB main + 64 KB SHADOW.

## Builds on / used by

- [[techniques/single-rasterline-rupture]] — the 4-scanlines-per-cycle chassis (same as [[techniques/copper-bars]]).
- [[memory/shadow-ram]] — ACCCON bit layout, D vs E vs X bits.
- [[hardware/crtc-6845]] — R12/R13 latch timing relative to ACCCON immediate effect.
- [[techniques/fx-framework]] — Timer 1 stable raster (the parallax effect would be impossible without it).
