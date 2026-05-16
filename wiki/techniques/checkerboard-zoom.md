---
title: Checkerboard Zoom (ULA flash-bit toggle per raster)
type: technique
tags: [crtc, single-rasterline, ula, flash, mode-1, checkerboard, animation]
sources: [twisted-brain]
updated: 2026-05-16
---

# Checkerboard Zoom

A zooming, scrolling MODE 1 checkerboard. The CRTC displays the same 80-byte scanline buffer on every raster line; the CPU **toggles bit 0 of the Video ULA control register (`&FE20`)** per scanline to invert colours 8-15, producing the checker's vertical alternation for free.

The horizontal alternation is in the pre-drawn scanline buffer (done in `update`); the vertical alternation is per-raster ULA-flash toggling (done in `draw`).

From Twisted Brain Part 11 ([[sources/twisted-brain]]).

## The ULA flash bit

[[hardware/video-ula]] register at `&FE20` bit 0 is the **"selected flash colour"** bit. It only affects palette entries that have been programmed with a **flash physical-colour code** (`&08`-`&0F` — see the physical colour table on the Video ULA page). For those entries, the ULA picks one of two physical colours depending on bit 0 of `&FE20`: e.g. `&08` is "black ↔ white", `&0B` is "yellow ↔ blue", and so on. Non-flash entries (physical codes `&00`-`&07`) are unaffected by bit 0.

MOS normally toggles bit 0 at the standard flash rate (default 25/25 fifty-Hz frames, ~1 Hz). For the checkerboard effect, the **init function programs colours 8-15 as flash entries** so the demo can repurpose this single bit as a per-raster colour-flip lever; then the draw function writes bit 0 of `&FE20` per scanline to invert all "flashing" colours simultaneously.

Each toggle costs **one `STA &FE20`** = 4 cycles (stretched on SHEILA). Vastly cheaper than rewriting palette entries (which would take 8 writes per affected colour in MODE 1).

## CRTC config

256 cycles per frame, 1 scanline per cycle = 256 visible scanlines. Same chassis as [[techniques/kefrens-bars]] — 255 display cycles + 1 final rebalance cycle, with the draw function entering on cycle 1 and the loop iterating 254 times to set up cycles 2..255:

```
R9 = 0   (1 scanline per char row)
R4 = 0   (1 char row per cycle)
R6 = 1   (display)
R7 = &FF (no VSync)
R12/R13 → &3000 (fixed)
```

Final rebalance cycle: `R4 = 56` (57 rows), `R7 = 25`.

R12/R13 never changes — the same scanline of memory is shown 256 times. What changes is the ULA flash bit.

## The draw loop (per scanline)

```asm
.loop                          ; 254 iterations, 128c each
    ; pad until horizontal blank (94c)
    FOR n,1,45 : NOP : NEXT
    BIT 0                      ; 3c

    ; --- ULA flash bit = parity bit ---
    LDA flash_register_value   ; 4c
    AND #&FE                   ; 2c
    ORA checker_parity         ; 4c   ← bit 0 of parity
    STA &FE20                  ; 4c (stretched)

    ; --- update checker parity ---
    INC checker_y_in_cell      ; 5c
    LDA checker_y_in_cell      ; 3c
    CMP checker_N              ; 3c   ← N = current cell size in pixels
    BCC no_invert              ; 2c/3c
    LDX #0 : STX checker_y_in_cell
    LDA checker_parity : EOR #1 : STA checker_parity
.no_invert
    ; ... pad to 128c
    DEX
    BNE loop                   ; 3c
```

So every `N` raster lines, the parity flips, and consequently every block of `N` raster lines on screen shows the opposite colour pattern from the previous block. Combined with the horizontal alternation already in the buffer, this produces the checker.

## Drawing the scanline buffer (the *real* hard bit)

This is done in **`update`** during vblank, so it's not raster-bound but it *is* bound by the vblank budget — roughly **18 raster lines = 2 304 cycles** when the music player has just had a heavy frame.

Filling 80 bytes in 2 304 cycles = **28.8 cycles/byte**. Sounds generous. But every byte (4 MODE 1 pixels) may contain a parity flip *anywhere within it*, depending on the current X-offset modulo N. So you can't just write solid bytes — you have to handle the partial-byte transition.

Worst case: with N small (a few pixels), every byte has a transition in it.

The solution: an **unrolled loop with a short and long path per byte**:

```asm
\\ X = pixels remaining until next flip
\\ A = current solid byte value (0 or &FF)

FOR c, 0, 79     ; one block per output byte
{
    CPX #4              ; 2c   need at least 4 pixels of same colour to write a solid byte?
    BCS write_byte      ; 3c

    ; --- LONG PATH: byte contains a colour transition ---
    EOR #&FF            ; 2c   flip bits
    TAY                 ; 2c   save flipped value
    EOR checker_left_mask, X  ; 4c   compose partial byte (X = pixels of OLD colour at left)
    STA &3000 + c*8     ; 4c   write
    LDA checkzoom_N     ; 3c   reset pixel counter
    SBC checker_lazy_table, X  ; 4c
    TAX                 ; 2c
    TYA                 ; 2c   restore A as new colour
    BRA done            ; 3c

.write_byte
    ; --- SHORT PATH: solid byte ---
    STA &3000 + c*8     ; 4c
    DEX:DEX:DEX:DEX     ; 8c   consume 4 pixels
.done
}
NEXT
```

Long path: 30c. Short path: 17c. **Worst case = 80 × 30 = 2 400c = 18.75 scanlines.** Just inside the vblank budget on a heavy music frame.

`checker_left_mask` is a 4-entry table giving the AND mask for "the leftmost X pixels of a MODE 1 byte". `checker_lazy_table` is a tiny lookup that handles the "remaining pixels after the transition" arithmetic without a multiply.

## The high-frequency clock detour

MODE 4/5/6 use the [[hardware/crtc-6845|6845]]'s low-frequency clock (1 MHz CRTC). The original Checkerboard prototype was in MODE 4 (40 chars wide, half the byte writes), but switching from MODE 0/1/2 (2 MHz CRTC) to MODE 4 mid-frame means the CRTC's horizontal counters shift their meaning mid-line. Painful: if you don't reprogram R0/R2 within the right window, the line is the wrong length or hsync lands in the wrong place.

Quote from the write-up:

> "Say we're at Horizontal Character = 30 in high frequency clock then suddenly we switch to low frequency clock and reduce the Horizontal Total from 127 to 63. Our Horizontal Counter now says we've only got 34 more characters to go but this feels like we've 'lost' some characters."

Decision: stay in high-frequency clock the whole demo. MODE 1 throughout, accept the higher per-frame byte-write cost. Cleaner timing across effects, no clock-mode switching brittleness.

## Why this works

Two cheap operations combine:

1. **Per-scanline ULA flash toggle** = 4 cycles. Inverts colours 8-15 instantly.
2. **Per-frame buffer redraw** = 2 400 cycles in vblank. The horizontal pattern.

The CRTC supplies the "show this scanline 256 times" repetition for free. So we get a 320×256 MODE 1 checkerboard, fully animated (per-pixel X and Y position, per-pixel size of check), for ~3 KB of work per frame. A regular per-pixel checker render in a 20 KB MODE 1 buffer would cost ~60 KB of writes per frame — impossible.

## Could it be even better?

> "Given that the vast majority of the FX draw function is spent in NOPs (94 cycles / raster line) I guess I could have used the double buffer technique from the Vertical Blinds effect and moved the work here. The challenge then becomes how to interleave work for the next frame whilst still inverting colour parity at the right time."
> — kieran

So: move the buffer redraw out of `update` and into `draw`, splitting it across the 94c/raster spare time per cycle. This would free up vblank for other modules' setup. Not implemented in the shipped demo; viable for a future optimisation.

## Builds on / used by

- [[techniques/single-rasterline-rupture]] — the 1-scanline-cycle chassis (shared with [[techniques/kefrens-bars]]).
- [[hardware/video-ula]] — the flash bit at `&FE20` bit 0.
- [[techniques/fx-framework]] — the update budget constraint and the draw raster timing.
- Pattern is reusable wherever per-raster colour inversion is wanted at near-zero cycle cost.
