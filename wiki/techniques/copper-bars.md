---
title: Copper Bars / Plasma
type: technique
tags: [crtc, vertical-rupture, single-scanline, mode-0, palette, dither, sine, copper, plasma]
sources: [twisted-brain]
updated: 2026-05-16
---

# Copper Bars and Plasma

Two related effects from Twisted Brain (Parts 6 and 7), built on the same single-rasterline-rupture chassis: **a pre-rendered MODE 0 dither buffer + per-row R12/R13 selection + per-row palette change**. The two effects differ only in what's in the pre-rendered buffer and how it's indexed.

## Common chassis

CRTC config: 64 cycles × 1 character row × 4 scanlines = 256 visible scanlines (see [[techniques/single-rasterline-rupture]]).

```
R9 = 3   (4 scanlines per char row)
R4 = 0   (1 char row per cycle)
R6 = 1   (display that row)
R7 = &FF (no VSync this cycle)
R12/R13 → varies per cycle (picked from lookup)
```

Final 64th cycle restores VSync: `R4 = 14` (15 char rows), `R7 = 7` for VSync at line 280 (= `(280-252)/4`).

Pre-rendered buffer: 17 dither patterns from a **4×4 ordered (Bayer) dithering matrix**, each pattern stored as one MODE 0 character row. Patterns go pure-black → 4×4-Bayer-fades → pure-white. With ordered dithering the patterns are static, so motion doesn't scintillate.

## Copper Bars (Part 6)

Each cycle picks a screen address pointing at one of the 17 dither rows. Stepping through the table white → black → white → black gives copper-style horizontal bands.

```asm
.loop                       ; 64 iterations, must total 512c each
    LDA addr_table_HI, X
    STA &FE00 = 12          ; via prior LDA #12 / STA
    ; ... R12 + R13 writes
    LDA palette_table, X
    STA &FE21               ; palette change in horizontal blank
    ; ... pad to 512c
    INX
    BNE loop
```

Three things layered on the per-row R12/R13 selection:

1. **Hue rotation** — palette colour 1 (the dither's "white" lane) is cycled through the colour wheel: red → magenta → blue → cyan → green → yellow → red. Because MODE 0 only has colours 0 and 1, this is 8 palette writes per change. Writes are scheduled for horizontal blank periods so partial-palette frames aren't visible. Only update palette when a *solid* colour is on screen — never mid-dither — so a partially-programmed palette doesn't bleed across pixels.

2. **Scroll** — index into the screen-address lookup is incremented per frame so bars scroll up.

3. **Sine-stretch** — an accumulator adds a per-row delta to the lookup index. Small delta → bars stretched (slow advance through the table); large delta → squashed. The delta is itself a sine wave per frame, so the bars zoom in and out as they scroll.

## Plasma (Part 7)

Same CRTC config, same palette tricks, different pre-rendered buffer: instead of 17 black-to-white dither levels, the buffer contains **gradient rows of increasing frequency** — 1 white-black-white cycle in the top rows, then 2, then 4, then 8 in the bottom rows.

The per-cycle screen-address lookup picks rows by frequency, and each row can be **shifted horizontally** by adjusting the low bits of R12/R13 (offsetting within the pre-rendered char row).

Animation:

- Shift all rows by the same delta → horizontal scroll.
- Apply a sine wave to per-row shifts → "bend" the bars.
- Add a second sine wave at a different frequency → interfering ripples.
- Vary phase rate per character row → vertical motion of the ripples.

Two colours only, chosen to be close in hue (red/magenta, white/yellow) so the dither blends cleanly to the eye.

No multiplication needed at runtime — everything is sine-table lookup + ADC. Just be careful: it's easy to produce static-looking patterns; pleasing motion is a black art of phase/frequency tweaking.

## Why it works

The trick is the **separation of "what content"** (pre-rendered dither in screen RAM) **from "where on screen each chunk lands"** (per-cycle R12/R13). Once you accept that the screen-RAM-to-display mapping is yours to choose, the 2 MHz CPU has plenty of time to update *which* rows are picked and *which* palette they use — without ever redrawing a pixel.

A 256-line MODE 0 screen has 20 480 bytes. Filling that at 2 MHz costs **10 240 cycles** of pure writes — about 80 raster lines just to clear, never mind drawing. Per-row R12/R13 reuse means we display all 64 character rows from just a 1 KB pre-rendered buffer, and the per-frame work is < 1 KB of CRTC + palette register writes.

## Constant-time discipline

Each of the 64 cycles must consume **exactly 4 raster lines = 512 cycles**. The per-iteration work (compute address, write R12/R13, optionally write palette) takes ~50-100c; the rest is NOP padding or `BIT 0` (3c) fillers. See [[techniques/single-rasterline-rupture]] for the general patterns.

## Variants

- **Different dither matrix** — Bayer 4×4 is the obvious choice; 8×8 would give finer gradients but cost a larger pre-rendered buffer.
- **MODE 1 or MODE 2** — would give more palette colours per buffer entry, but bigger pre-rendered buffer and you'd need to be cleverer about which colours to dither. The MODE 0 + hue-rotation combo is the cheapest path to "copper" look.
- **Text mode with palette-only effect** — see [[sources/twisted-brain]] Part 3 (Text Screens). Per-raster palette swap without any vertical rupture, MODE 1. Cheaper but limited to colour effects only.

## Builds on / used by

- [[techniques/single-rasterline-rupture]] — the 4-scanlines-per-cycle chassis.
- [[techniques/vertical-rupture]] — the general technique.
- [[hardware/video-ula]] — palette register layout, MODE 0 colour encoding.
- [[hardware/crtc-6845]] — R12/R13 latch timing.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
