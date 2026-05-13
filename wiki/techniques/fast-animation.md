---
title: Fast Animation
type: technique
tags: [sprites, animation, mode-2, mode-0, scrolling]
sources: [naug-ch13-video]
updated: 2026-05-13
---

# Fast Animation

NAUG §13.3.12 (p202-204) summarises why most fast-action BBC games use **MODE 2**: the interleaved 4-bits-per-pixel layout means a sprite is just a sequence of bytes, and moving it by **one byte = two pixels** is a simple memory copy. No bit-shifting, no masking.

## Why MODE 2 is the sweet spot

MODE 2 byte layout (NAUG §13.3.12 p202):
```
bit:    7   6   5   4   3   2   1   0
pixel:  P2d P1d P2c P1c P2b P1b P2a P1a
```

- Two pixels per byte. Pixel 1's 4 colour bits are scattered across odd positions; pixel 2's across even positions. The interleaving is invisible to you when manipulating whole bytes — both pixels move together.
- 16 colours available (the 4 bpp lets you index all 16 ULA palette entries directly).
- Sideways hardware scrolling moves by **2 pixels per char-step** — finest of any colour mode.

The cost: 20 KB screen RAM, 160 horizontal pixels (chunky compared to MODE 1's 320), 80 columns of cells per row.

## The basic sprite copy

For a `W`-byte-wide, `H`-row-tall sprite in MODE 2 (each row is 8 scan lines, since cells are 8 scan-lines tall):

```asm
; src = source sprite data
; dst = top-left destination char-cell address
; H = number of cell rows
; W = width in bytes (= width in cell-columns)
; bytes_per_row = 640 in modes 0-3, 320 in modes 4-6

    ldy #0
.row_loop
    .col_loop_unrolled  ; repeat W times:
        lda (src),y
        sta (dst),y
        iny             ; 2c
    ; ... unrolled W*8 times (8 scan lines per cell, each is a byte)
    ; advance to next cell row: add (bytes_per_row - W*8) to dst
```

For a 16×16 pixel sprite in MODE 2 (8 bytes wide, 2 cell rows tall):
- 128 bytes to move per frame.
- Naive `LDA (zp),Y / STA (zp),Y` loop: 5c + 6c + 2c (INY) + 2c (BNE) = 15c per byte = ~1920 cycles ≈ 960 µs at 2 MHz.
- Unrolled, with cached pointers: ~9c per byte = 1152 cycles ≈ 580 µs.

That fits comfortably in a single 20 ms frame, so dozens of sprites per frame are tractable.

## Masking / per-pixel writes

If sprites need transparency, you need a mask:

```asm
    lda (dst),y         ; existing background
    and (mask),y        ; mask out sprite shape — needs a different pointer
    ora (src),y         ; or in sprite pixels
    sta (dst),y
```

Each masked byte is now ~16-20c — still ~1 ms per 16×16 sprite. The challenge: 6502 only has 3 pointer-able indexed-indirect modes, so you need to manage three zero-page pointers (mask, sprite, dst) and reload them or use absolute,X with self-modified addresses.

## MODE 0 — bit-shifting cost

MODE 0 is 1 bpp; moving by 1 byte = 8 pixels (a whole character cell of horizontal motion). For finer motion you must **shift bits** across byte boundaries (`ROR` carry chain). Each pixel-shifted version of a sprite is a full re-render, so pre-shifted sprite tables are common:

- 8 pre-shifted copies for 1-pixel granularity in MODE 0.
- 4 pre-shifted copies for MODE 1 (2 bpp = 4 pixel positions per byte, but pixels also interleave — typically 4 copies suffice).
- 2 pre-shifted copies for MODE 2 (because hardware scrolling already gives 2-pixel granularity).

Pre-shifted tables trade ROM/RAM for cycles. For a 16×16 MODE 2 sprite at 2 pre-shifted positions, you need 256 bytes of sprite data; for MODE 0 at 8 shifts, 2 KB.

## Hardware scroll as foundation

For **scrolling games** (Planetoid, Frak!, anything with a horizontally-moving world), don't redraw the screen — use `[[video/hardware-scrolling]]` to slew the 6845 screen-start register, and only redraw the **leading edge** column each frame.

A common pattern in MODE 2:
- Maintain an off-screen "compose" column one cell-row tall, one cell wide (8 bytes).
- Each frame: advance the 6845 screen start by 8 bytes (left scroll) or -8 (right).
- Update the cells that *now* sit at the rightmost (or leftmost) edge with new world content.
- All other pixels move "for free" via the screen-start shift.

This reduces work-per-frame from "draw the world" to "draw one column" — a 30×-100× win.

## Vsync sync

To avoid tearing, do **all** screen writes during vertical blanking. Two ways:

- `OSBYTE &13` (call &FFF4 with A=&13) — blocks until vsync.
- Hardware: poll System VIA `IFR` (`&FE4D`) bit 1 for the CA1 (vsync) interrupt, or hook IRQ2V.

Vsync is ~50 Hz on UK BBC, giving ~20 ms per frame. The visible-screen period is ~16 ms (320 scan lines × 64 µs); blanking is ~4 ms. Schedule **fast** writes for the blanking window; long writes can spill into visible scan but should land at lines below where the user is looking.

See `[[techniques/raster-splits]]` (planned, after Ch8 ingest) for techniques that *exploit* mid-frame timing rather than fight it.

## Don't bother with MODE 7 for animation

Teletext mode is 1 byte = 1 character, and the SAA5050 turns those bytes into glyphs. There's no per-pixel addressing. Use MODE 7 for HUDs / status displays / text-heavy screens where you want 25×40 character text in 1 KB of screen RAM — but not for sprite movement.
