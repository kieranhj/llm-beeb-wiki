---
title: Chunky Graphics Mode
type: technique
tags: [chunky, video, mode-7, custom-modes, address-translation, ttxvdu, raster]
sources: [chunky-mode-notes, beebwiki-address-translation, naug-ch13-video, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# Chunky Graphics Mode

A **chunky** display has one byte per pixel-block, arranged linearly (left to right, top to bottom). It's the natural format for sprite-driven games, palette animation, and "blit" workflows — and it's exactly what the BBC's standard graphics modes *don't* give you. Modes 0-6 are planar bitmaps: a single byte is *eight* pixels in MODE 0, *four* in MODE 1/4, *two* in MODE 2/5. Editing one logical pixel means a read-modify-write across 1-3 bits inside a byte.

There's a way to coerce the BBC into a true chunky display anyway: program the [[hardware/crtc-6845|CRTC]] to fetch from the **MODE 7 1 KB screen** (`&7C00-&7FFF`) while leaving the [[hardware/video-ula|Video ULA]] configured for a graphics mode. Each byte fetched becomes one chunky cell repeated N scanlines tall. Trick originally documented by Tom Seddon ([[sources/chunky-mode-notes]]).

The technique has real-hardware quirks the original write-up didn't fully untangle. This page covers what actually works.

## What you get

| Setup | Resolution | Screen RAM | Pixel aspect |
|---|---|---|---|
| MODE 4/5/6 + R9=7 | 40×25 | 1 KB | tall (8×N) |
| MODE 4/5/6 + R9=3 | 40×50 | 1 KB | square-ish |
| **MODE 2 + R9=4** | **80×25** | **1 KB** | **square** ← Seddon's sweet spot |
| MODE 0/1 + tweaks | 80×25 | 1 KB | square (high CRTC clock — see below) |

In every case **the screen is 1 KB**. A full-screen blit costs 1 000 byte writes. Double-buffering becomes trivial. You can clear the entire screen in under 4 ms.

## Setup

```basic
10 MODE 2
20 VDU 23,0,12,&28,0,0,0,0,0,0   : REM R12 = &28 (screen base = &7C00)
30 VDU 23,0,13,0,0,0,0,0,0,0     : REM R13 = 0
40 VDU 23,0,9,4,0,0,0,0,0,0      : REM R9 = 4 (5 scanlines per char row)
50 REM Now writes to &7C00..&7FE7 produce chunky blocks
```

In asm:

```asm
LDA #12 : STA &FE00 : LDA #&28 : STA &FE01   ; R12 = teletext-style base
LDA #13 : STA &FE00 : LDA #0   : STA &FE01   ; R13 = 0
LDA #9  : STA &FE00 : LDA #4   : STA &FE01   ; R9 = 4 → 80×25 square in MODE 2
```

What's happening: `R12/R13 = &2800` programs the CRTC start address with **`MA13 = 1`** (R12 bit 5) — the bit that makes the [[hardware/address-translation|address translator]] route via **TTX VDU** — and `MA11 = 1, MA12 = 0` (MA11 picks the `&7C00` block on a Model B). *Corrected 2026-11-18:* this sentence used to credit `MA12=0, MA11=1` with the switch; MA13 is the flag. The translator routes via **TTX VDU** instead of HI RES, regardless of which graphics mode the Video ULA thinks it's in. Fetches come from the 1 KB MODE 7 RAM window. The ULA still decodes each byte as graphics pixels.

## High-speed CRTC clock (modes 0/1/2) — the EOR-64 interleave

Naïvely, MODE 2 + the above setup *looks* broken on real hardware — every other byte is "scrambled". It isn't scrambled, it's coming from `addr XOR &40`.

The reason is in the translator (see [[hardware/address-translation]]): TTX VDU mapping XORs `MA6` with the 1 MHz clock so two bytes are fetched per microsecond. In MODE 7, IC 15 routes one byte to the [[hardware/saa5050|SAA 5050]] and discards the other — this is the trick that gives MODE 7 its 88 µs DRAM refresh interval. When you force TTX VDU mapping in a graphics mode, the **Video ULA sees both bytes** per µs. Every other byte arrives from `addr XOR &40`.

**The fix is not a fix — it's a layout decision.** Lay out your back-buffer with the EOR-64 interleave so each byte ends up at the address the chip will actually read it from:

```
display_position N writes to:
    base + ((N AND ~1)) + ((N AND 1) << 6)        ; even N at low half, odd N at +64
```

Equivalently, treat `&7C00-&7C3F` and `&7C40-&7C7F` as two interleaved 64-byte half-rows. Plot to the right one. Or pre-shuffle at write time with a 256-byte lookup; the cost is one indexed LDA per pixel.

**Result: a working 80×25 chunky display in MODE 2 on Model B and Master.** The "impossible on real hardware" status the original write-up implied is wrong — it's just a buffer-layout problem.

### Master complication

On the Master the toggle pattern is more elaborate, and it has now been **measured on a real Master** (KC, phX hwtest card J, 2026-11-15; [[sources/beeb-port-kit-hardware-facts-2026-11]] §1):

- MODE 1 with MA13 set (R12/R13 `&2028`, MA11 clear) reads the 1K at **`&7C00`**, RA ignored — the Master's MA13 fetches come from `&7C00`, not `&3C00`.
- The characters of one 1 MHz phase read `&7C00 + (MA AND &3FF)`; the others the same address **`XOR &40` on one scanline and `XOR &C0` on the next** (MA6, then MA6 and MA7) — **never MA7 alone**. Bits 8-9 never flip. Which RA parity takes `XOR &C0` was not read.
- **The phase follows the 1 MHz clock, not C0**: every odd-length CRTC line since the boot swaps which characters flip, so a layout that depends on it needs a known 1 MHz phase (phX locks the 6845 to it at boot with R0 = 0, then keeps every line even).
- jsbeeb 2.10.x and b2 model neither flip; beebjit models MA6 only; jsbeeb main 2.22.0 (#1859) models both.

So a Master layout needs the `XOR &40` interleave on one scanline parity and `XOR &C0` on the other. *Superseded:* this section said "either `MA6` or `MA7` is XOR'd depending on `RA0`", from [[sources/chunky-mode-notes]] (Julian Brown, second-hand); the measured form is above. Details on [[hardware/address-translation]].

## Low-speed CRTC clock (modes 4/5/6) — works as-is

Modes 4/5/6 run the CRTC at 1 MHz, so only one byte is fetched per microsecond. No interleave. The setup above gives a clean 40×25 display with no buffer pre-shuffling. This is the easy version and a fine starting point.

## The Model B sync mystery

Reported by Julian Brown (2015 Stardot post, captured in [[sources/chunky-mode-notes]]): on a Model B, simply setting R12/R13 to the teletext base in a graphics mode breaks **H/V sync** entirely. The monitor can't lock. The Master doesn't exhibit this.

This is **separate from the address interleave** — sync is independent of which RAM byte is fetched.

Hypotheses without confirmation:
- IC 5 (SAA 5050) emits non-zero RGB which IC 6 (Video ULA) OR's with its own output (expecting zero outside MODE 7).
- IC 15 sinking current from `D0-D7` puts IC 6 in an undefined state.
- Neither cleanly explains a *sync* failure — both should affect colour only.

Workarounds people have tried (per the thread, none confirmed):
- Specific Video ULA control register dance before the R12/R13 write.
- Particular ordering of `*FX 144` border control plus the R12/R13 write.
- Putting the BBC into MODE 7 first, then reprogramming the Video ULA to graphics mode *after* R12/R13 is set.

**This is the open question.** Real-hardware scope work would resolve it. If you have a working chunky-mode demo on a Model B, the sequence used to avoid the sync break is the missing recipe.

## Software workaround — chase-the-raster blit

Seddon's conjectured workaround for the Model B sync issue: don't use TTX VDU mapping at all. Stay in MODE 4 (or whatever), keep a 1 KB "logical chunky" buffer somewhere convenient, and **copy 40 bytes per row to `&7C00` as the raster scans past**, exploiting the fact that you've got 4 scanlines of warning before the CRTC reads each next row.

Per-row budget at 2 MHz:

```
4 scanlines × 128 cycles = 512 cycles available
40 bytes × (LDA abs + STA abs) = 40 × 8c    = 320 cycles
Slack to absorb: 192 cycles
```

Slack absorbed via a tuned delay loop:

```asm
.DELAY
    LDX #34            ; 2c
.DELAYLOOP
    DEX                ; 2c
    BNE DELAYLOOP      ; 3c (taken), 2c (final)  → 5×34 + 4 = 174c
    NOP                ; 2c
    NOP                ; 2c
    RTS                ; 6c → ~192c total when called via JSR
```

**Memory cost**: 6 bytes per byte (LDA abs + STA abs both have 3-byte encoding) × 40 bytes/row × 25 rows = 6 000 bytes of unrolled blit code, + 3 bytes per row for the `JSR DELAY` = **6 075 bytes**.

**Caveats**:
- The 8c/byte budget *requires* absolute (not indexed) addressing — `LDA abs,X` costs 9c → 360c/row, breaking the budget.
- The CRTC wraps `&7FFF → &7C00` mid-frame, so two routines are needed (one for the pre-wrap rows, one for post-wrap), or accept the loss of 13 150 bytes of RAM to alignment.
- [[techniques/vertical-rupture]] is a cleaner way to handle the wrap — split into two CRTC cycles, each with its own R12/R13.

This whole workaround is moot if you can get TTX VDU mapping working in graphics modes on your Model B. Solve the sync mystery and you save 6 KB of code.

## Why it's worth doing

- **Sprites become memcpy.** No bit-shifting, no read-modify-write, no per-mode pixel layout.
- **Whole-screen redraws fit in a frame.** 1 KB at 2 MHz worst case = 0.5 ms unrolled, ~2 ms with addressing overhead. Double-buffer with hardware page-flip or vertical rupture.
- **Pixel art is straightforward.** Each cell is one byte = one colour (in the relevant mode's palette).
- **80×25 in MODE 2 looks period-correct.** Visually similar to C64 multicolour or Spectrum attribute-grid (without the colour clash, since each cell holds its colour locally in the byte).

## Builds on / related

- [[hardware/address-translation]] — the TTX VDU mapping and MA6-XOR-clock fetch are the foundation of why this works.
- [[hardware/crtc-6845]] — R9 (scanlines per row) reduction for square pixels; R12/R13 for the screen base.
- [[hardware/video-ula]] — the consumer of the fetched bytes; its mode setting determines pixel layout per byte.
- [[techniques/custom-modes]] — the broader "reprogram the CRTC to taste" pattern.
- [[techniques/vertical-rupture]] — cleaner solution to the CRTC wrap problem in the software workaround.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
