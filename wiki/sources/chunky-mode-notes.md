---
title: Chunky Graphics Mode — notes
type: source
urls:
  - http://modelb.bbcmicro.com/tech-chunky.html
author: [Tom Seddon, Julian Brown]
dates: [unknown, 2015-05-10]
local: raw/notes/chunky-mode.txt
tags: [chunky, video, mode-7, address-translation, ttxvdu, custom-modes]
updated: 2026-05-16
---

# Chunky Mode — Combined Notes

Two intertwined sources in `raw/notes/chunky-mode.txt`:

1. **Tom Seddon's page** (originally on modelb.bbcmicro.com) — describes the "mythical chunky mode" technique: drive a graphics mode but program R12/R13 as if for teletext (and reduce R9), giving a 40×25 or 80×25 1-byte-per-block display from just 1 KB of screen RAM. Plus a conjectured software workaround for the Model B's apparent inability to do high-res chunky directly.

2. **Julian Brown's 2015 Stardot post** — reports trying the technique on real hardware. Finds the Master partially works (low-speed CRTC clock only, high-speed gives a deterministic byte-interleave from the MA6/MA7 toggle), and the Model B exhibits a separate sync-corruption failure unrelated to the address interleave.

## Key technical claims

### The technique itself

- Set CRTC `R12 / R13` to point at the MODE 7 screen base (`&7C00`), with the high bit of `MA` set so the translator routes via TTX VDU instead of HI RES.
- Leave Video ULA configured for the graphics mode of your choice (so byte → pixel decoding is graphics, not teletext).
- Reduce `R9` so each byte's bitmap repeats N times in its character cell. For mode 2 + R9=4 → 80×25 square chunky pixels.
- Screen size shrinks to 1 KB (vs 10-20 KB for native graphics modes).

### What actually happens per mode (Julian on real hardware)

| Mode | CRTC clock | Master | Model B |
|---|---|---|---|
| 4, 5, 6 | low (1 MHz) | works as-is | works as-is |
| 0, 1, 2 | high (2 MHz) | every other byte from `addr XOR &40` or `XOR &80` (depends on RA0) | **sync corruption** — separate issue |

### Why the byte interleave happens (not a bug)

In TTX VDU mapping the translator XORs `MA6` with the 1 MHz clock — see [[hardware/address-translation]]. This fetches **two distinct bytes per microsecond**. In normal MODE 7 IC 15 routes one to the SAA 5050 and discards the other (which is what gives MODE 7 its uniquely good 88 µs DRAM refresh interval).

When you force TTX VDU mapping in a graphics mode, the Video ULA sees both bytes per µs. Every other byte arrives from `addr XOR &40`. This is **deterministic and exploitable**: arrange your back-buffer / draw routine with the EOR-64 interleave and a true high-res chunky display works on Model B in modes 0/1/2.

On the Master the interleave pattern is more elaborate — either MA6 or MA7 is toggled, depending on RA0 (Julian suspects this is because Master DRAM has more rows to refresh, requiring a different refresh strategy). The principle is the same: deterministic interleave, work the layout out and pre-pad accordingly.

### The Model B sync mystery (genuinely unsolved)

Julian's Model B-specific failure: simply asserting TTXVDU (programming R12/R13 to the teletext base) in a non-MODE-7 graphics mode breaks H/V sync. His monitor can't lock onto the signal at all. This is independent of the address interleave.

Speculated causes (no resolution in the thread):

- IC 5 (SAA 5050) emits non-zero RGB on its outputs and IC 6 (Video ULA) OR's them with its own output, expecting them to be zero outside MODE 7.
- IC 15 sinking all current from `D0-D7` leaves IC 6 in a strange state.
- Neither hypothesis really explains *sync* corruption (RGB ≠ sync).

This is captured as an open follow-up — anyone with a logic analyser and a Model B can probably nail it.

### Seddon's software workaround (stock Model B, conjectured)

Use a 10 KB back-buffer in regular graphics screen RAM; copy 40 bytes per row to the `&7C00` area as the raster passes. Per-row budget breakdown:

- 4 scanlines = 512 cycles available between when CRTC starts reading a row from `&7C00` and when it has finished.
- Unrolled `LDA abs : STA abs` per byte = 8c × 40 bytes = 320 cycles to refill.
- Slack: 192 cycles, padded out with a delay loop (`LDX #34 : DELAYLOOP DEX BNE DELAYLOOP` = 174c + small NOP trim).

Whole-screen draw routine size: 6 bytes per byte (LDA abs + STA abs) × 40 bytes × 25 rows + JSR overhead ≈ **6 KB of unrolled code**.

Caveats noted by Seddon himself:
- The 8c/byte budget assumes `LDA abs, STA abs` with both operands known at assemble time. Indexed mode (`LDA abs,X`) costs 9c/byte → 360c/row → too tight.
- The CRTC fetches `&7C00-&7FFF` then *wraps* to `&7C00`, so you need two routines: one to fill from the address that's about to be read past `&8000`, and one for `&7C00`. Or accept losing 13 150 bytes of RAM to alignment.
- **Vertical rupture** ([[techniques/vertical-rupture]]) would be a way to avoid the wrap-bookkeeping.

## Filed into

- [[techniques/chunky-mode]] — new entity page, framed as "high-res chunky IS achievable on Model B with the EOR-64 layout".
- [[hardware/address-translation]] — add a "why this matters" note that the MA6-XOR-clock fetch produces *two* exploitable bytes, normally one is discarded but you can sometimes use both.
- [[index]] / [[log]] — standard.

## Open follow-ups

- **The Model B sync-corruption mystery** — why does asserting TTXVDU (R12/R13 → teletext base) in a graphics mode break H/V sync on Model B but not Master? Real-hardware scope investigation needed.
- Working chunky-mode demo source — Tom Seddon's page promises one but the modelb.bbcmicro.com site is gone (web archive may have a copy).
- Master high-speed chunky: derive the exact `(MA6, MA7)` toggle table as a function of RA0, so the screen-buffer-pre-interleave can be implemented portably across Model B and Master.
- Cross-check Bitshifters / Stardot demos that have *actually shipped* a chunky-mode effect on real hardware to confirm whether the Model B sync issue has a known workaround (e.g. specific Video ULA control register dance, or a particular order of CRTC writes).
