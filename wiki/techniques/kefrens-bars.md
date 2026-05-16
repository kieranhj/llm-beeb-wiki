---
title: Kefrens Bars (single-scanline beam race)
type: technique
tags: [crtc, single-rasterline, beam-race, kefrens, alcatraz, mode-1, sine]
sources: [twisted-brain]
updated: 2026-05-16
---

# Kefrens Bars (Alcatraz Bars)

The classic demoscene Kefrens-bars effect — diagonal coloured bars cascading down the screen with no overdraw — done at **true single-scanline resolution** on the BBC. The chip displays the same 80-byte buffer on **every one of 256 visible scanlines**, and the CPU **mutates 4 bytes of the buffer between each scanline** to "add" one new bar's worth of pixels onto the visible image.

The result: the displayed image at scanline N is the accumulation of bars 0..N drawn on top of each other, but only 4 bytes of memory writes per scanline made it that way.

From Twisted Brain Part 10 ([[sources/twisted-brain]]). "I have been on a quest to produce true single scanline Kefrens bars on the Beeb for quite a while" — kieran.

## How it works

Conceptually, a Kefrens bar effect is: for each scanline, draw a bar at sine-table-derived X position, on top of all previous bars. With a real frame buffer you'd plot 256 bars into 256 × 80 = ~20 KB. With single-scanline rupture, you plot 256 bars into a *single shared 80-byte buffer*, with the CRTC reading it after every plot.

The catch: each plot can only **add** to what's already on the buffer — you never get to clear, because the previous scanlines have already been displayed and you'd erase them. So the bars must be drawn in z-order top-to-bottom, with each new one painted on top of the previous accumulation.

The scanline buffer is cleared **once per frame in the update function** (it's vblank then, no display happening). The draw function never clears it.

## CRTC config

256 cycles per frame = 255 single-scanline display cycles + 1 final cycle with embedded VSync (see [[techniques/single-rasterline-rupture]] for the accounting). The draw function enters with cycle 1 already underway and the loop iterates **254 times** to set up cycles 2 through 255:

```
R9 = 0   (1 scanline per char row)
R4 = 0   (1 char row per cycle)
R6 = 1   (display)
R7 = &FF (no VSync)
R12/R13 → &3000 (fixed for all 256 cycles)
```

Final cycle: `R4 = 56` (57 rows × 1 scanline = 57 raster lines, of which only 1 is displayed thanks to R6=1; the other 56 hide the VSync pulse and rebalance the frame back to 312 raster lines). `R7 = 25` for VSync inside that cycle. **But see the real-hardware quirk below — this R4 write doesn't always behave as expected in 1-scanline cycles.**

## Per-scanline plot (128c budget)

Each iteration must complete in 128 cycles (one raster line). The plot writes **4 bytes** = 1 MODE 1 character (8 pixels) of bar, using ORA-masking so the pixels overlay rather than overwrite the existing accumulation.

```asm
.write_pixels
    LDA kefrens_addr_table_LO, Y    ; 4c   ← Y indexes pre-shifted addr table
    STA writeptr                    ; 3c
    LDA kefrens_addr_table_HI, Y    ; 4c
    STA writeptr+1                  ; 3c

    TYA : LSR A
    BCS right                       ; 2c+3c   pixel parity by Y bit 0

    ; --- Left-aligned bar (4 bytes, full + 3 + final partial) ---
    LDA #PIXEL_LEFT_7 OR PIXEL_RIGHT_3   ; white/yellow
    LDY #0 : STA (writeptr), Y           ; 8c
    LDA #PIXEL_LEFT_6 OR PIXEL_RIGHT_2   ; cyan/green
    LDY #8 : STA (writeptr), Y
    LDA #PIXEL_LEFT_5 OR PIXEL_RIGHT_1   ; magenta/red
    LDY #16 : STA (writeptr), Y
    LDY #24
    LDA (writeptr), Y                    ; 6c   read current byte
    AND #&55                             ; 2c   keep right pixel
    ORA #PIXEL_LEFT_4                    ; 2c   mask in blue on left
    STA (writeptr), Y
    BRA continue                         ; 3c

.right
    ; --- Right-aligned bar (mirrored) ---
    LDY #0
    LDA (writeptr), Y                    ; mask in screen, fold in PIXEL_RIGHT_7
    AND #&AA : ORA #PIXEL_RIGHT_7 : STA (writeptr), Y
    LDA #PIXEL_LEFT_3 OR PIXEL_RIGHT_6 : LDY #8 : STA (writeptr), Y
    LDA #PIXEL_LEFT_2 OR PIXEL_RIGHT_5 : LDY #16 : STA (writeptr), Y
    LDA #PIXEL_LEFT_1 OR PIXEL_RIGHT_4 : LDY #24 : STA (writeptr), Y
    NOP                                  ; ← balances cycle cost vs left path
.continue
```

Both left and right branches must take **exactly the same number of cycles** so the next scanline lands at the same horizontal phase. The `NOP` at the end of the right branch is the cycle-balancing pad.

Pre-shifted address tables (`kefrens_addr_table_LO/HI`) save runtime arithmetic — Y is the X-position from the sine table, looked up directly.

The four pixels in the bar are pre-coloured to a gradient: white/yellow → cyan/green → magenta/red → blue. This gives the bars their characteristic look without any per-frame palette work.

## Real-hardware behaviour — the 313-line frame

> "Whilst the effect does work on the BBC Master machines that I've had access to (all sporting the apparently common Hitachi HD6845SP CRTC chip) there is definitely some not-quite-fully-understood behaviour when it comes to setting certain registers on the final scanline of a CRTC display cycle. Given that with this particular arrangement we have 256 'final scanlines' it's not clear that this should work at all..!"
> — kieran, [[sources/twisted-brain]] Part 10

**Symptom**: setting `R4 = 56` for the final (rebalance) cycle doesn't take effect immediately on real HD6845SP. The frame ends up **313 raster lines long instead of 312**, putting Timer 1 64 µs out of phase with raster line 0 for the rest of the demo.

**Why it happens** (precise mechanism, per [[sources/accc-compendium]] §13.2.1): the 6845 evaluates the "Last Line" condition (`C9=R9 AND C4=R4`) **only when C0<2** — the first 2 µs of every scanline. After C0=2, the verdict is locked for that scanline; R4 writes that land after C0≥2 are stored but cannot change the Last-Line state.

In a 1-scanline cycle (R9=0) every scanline has `C9=R9=0` always, so the Last-Line state is purely determined by whether `C4=R4` at C0<2. Kieran's rebalance cycle is supposed to be the scanline where `R4 = 56`: he wants the chip to *not* treat this as a Last Line, so it counts up through 57 rasters before wrapping. But his R4 write happens during the loop body, *after* C0=2 of the line that should have been the rebalance. The chip's Last-Line test at C0<2 saw the old R4 (=0) — `C4=R4=0` is still true — Last-Line is still armed — the chip resets C4/C9 at end of scanline as before.

So that scanline runs as another 1-scanline cycle (display only 1 raster), then the *next* scanline finally sees the new R4=56 at C0<2, no Last-Line arming, the chip counts up through 57 rasters as the rebalance. Net effect: **one extra single-scanline cycle (1 raster) inserted before the rebalance**, so the frame is 1 raster too long.

This is precisely documented in the ACCC compendium as the R.L.A.L. ("rupture ligne à ligne" — line-to-line rupture) recipe (§12.2.1): on CRTC 0, exiting from a single-scanline-rupture-mode requires that R4 (or R9) be set to its new value **before C0=0 of the rebalance scanline**, not during it. The BBC scene's rebalance frame works around this without requiring the cycle-exact precision of the R.L.A.L. recipe.

See [[hardware/crtc-internal-counters]] for the full counter model, and [[hardware/crtc-6845-advanced]] for the per-register write-window summary.

**Knock-on effect**: subsequent effects (especially [[techniques/parallax-bars]]) see the wrong ACCCON-switch timing and exhibit single-pixel glitch rows. The drift pollutes the next effect's timing too.

**Fix**: the `kill` function for Kefrens emits a single **311-raster-line frame** to rebalance Timer 1 back to where it should be. Done by resetting the CRTC to MODE 2 defaults but with one character row set to 7 scanlines instead of 8 (so total = `31×8 + 1×7 + 8 + remainder = 311`). When the user selects "Real Hardware" in the BASIC loader, this rebalance is enabled.

## What the rebalance frame looks like

| Frame | Raster lines | Effect |
|---|---|---|
| Last Kefrens frame | **313** | Bug — frame is one line too long |
| Rebalance frame in `kill` | **311** | Compensates by removing one line |
| First frame of next effect | **312** | Back in phase ✓ |

The drift accumulates to zero across the effect transition.

## Variants and limits

- **MODE 2 version**: would give 16-colour bars in only 2 bytes per character cell. Lower resolution (40 px wide instead of 80) so half the bars per screen. Worth investigating if you want flashier colours per bar.
- **More than 4 bytes per bar**: each extra byte costs cycles in the inner loop. With 4 bytes you've got ~30c left over per scanline for the sine-table lookup and bookkeeping. Going to 5 or 6 bytes would risk overrunning 128c/scanline.
- **Hexwab's stable-raster boot** would eliminate the 8c jitter that makes the rebalance frame less precise. Twisted Brain doesn't use it; could be a future tightening.

## Builds on / used by

- [[techniques/single-rasterline-rupture]] — the 1-scanline-cycle chassis (this is the most-extreme form).
- [[techniques/fx-framework]] — Timer 1 phase management, including the 311-line rebalance pattern.
- [[techniques/parallax-bars]] — receives the Kefrens timing bug if rebalance is skipped.
- [[hardware/crtc-6845-advanced]] — R4 mid-cycle rewrite semantics (the C0<2 evaluation window).
- [[hardware/crtc-internal-counters]] — the C0/C4/C9 counter model that explains why this happens.
- [[sources/accc-compendium]] §12.2.1 / §13.2.1 — primary documentation of the R4 rewrite mechanism and the R.L.A.L. exit recipe.
