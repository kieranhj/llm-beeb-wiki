---
title: Hardware Scrolling
type: video
tags: [scrolling, crtc, raster, vsync]
sources: [naug-ch13-video, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# Hardware Scrolling

Changing the **6845 screen start register** (R12, R13) moves the entire display by a chosen offset, no memory copies. This is the BBC's most powerful video technique — without it, scrolling a MODE 0 screen would require moving 20 KB per frame, far beyond 2 MHz throughput.

## The lever

`R12` (high) + `R13` (low) form a 14-bit value = **`screen_address / 8`** (modes 0-6). The divisor of 8 reflects 8 scan lines per character cell.

Writing the register pair via the OS (Tube-safe):
```basic
VDU 23;12, start DIV 2048; 0; 0; 0   : REM R12 = (addr DIV 8) DIV 256
VDU 23;13, start MOD 2048 DIV 8; 0; 0; 0  : REM R13 = (addr DIV 8) MOD 256
```

Direct (I/O processor only, faster, must guard against tearing — see vsync below):
```asm
LDA #12
STA &FE00     ; address register = R12
LDA hi_div256 ; (addr DIV 8) >> 8
STA &FE01
LDA #13
STA &FE00
LDA lo_byte   ; (addr DIV 8) & 0xFF
STA &FE01
```

## Vertical scroll

- **Up by one char row**: add `bytes_per_row` to the screen start (640 for modes 0-3, 320 for 4-6).
- **Down by one char row**: subtract.

Result: an entire 8-scanline row of cells shifts. Sub-row vertical scrolling (1-7 scanlines) is **not possible** via R12/R13 alone, but it *is* achievable via a two-cycle [[techniques/vertical-rupture]] + R5 abuse — see [[techniques/smooth-vertical-scroll]].

## Sideways scroll

- **Left by one 6845 char** (8 dots / 4 dots / 2 dots depending on MODE): add 8 to screen start.
- **Right by one 6845 char**: subtract 8.

Caveat: each char that "moves off the left" reappears one cell-row up on the right (because hardware just decrements the start of a continuous memory image — the wrap is per-row of cells, not per displayed scanline). For a clean horizontal scroll, you must software-fix-up the rightmost column each frame.

Pixel-step granularity:
- MODE 0: 8 pixels per step (chunky)
- MODE 1: 4 pixels per step
- MODE 2: **2 pixels per step** — best for smooth horizontal motion
- MODE 4: 8 pixels per step
- MODE 5: 4 pixels per step

For sub-character horizontal smoothness, use mode 2 hardware scroll combined with byte-shifted pre-rendered sprites — see [[techniques/fast-animation]].

## Hardware wrap-around

When the 6845's fetch address hits `≥ &8000`, dedicated logic **subtracts** a mode-dependent amount to bring the address back into screen RAM. The subtract amount is selected by 2 bits on the **System VIA addressable latch (IC 32)**, programmed at MODE-set time. Full mechanism (subtract amounts `&4000`/`&2000`/`&5000`/`&2800` for MODES 3/6/0-2/4-5, restart addresses `&4000`/`&6000`/`&3000`/`&5800`) is documented in [[hardware/address-translation]].

Practical implication: provided your `R12,R13` value stays within `[screen_base, screen_base + screen_size)`, you can scroll indefinitely and the screen image wraps cleanly through screen RAM.

If your computed start drifts above `&7FFF`, subtract the screen size. If below `screen_base`, add the screen size. BASIC example from NAUG §13.3.12 p203:

```basic
IF START >= &8000 THEN START = START - &5000   : REM MODE 0: 20K screen
IF START <  &3000 THEN START = START + &5000
```

## MODE 7 — different correction

MODE 7 stores screen at `&7C00-&7FFF` and the 6845 uses a teletext-friendly addressing scheme. The correction (§13.3.11 p202):

```
R12 = (high_byte - &74) EOR &20
R13 =  low_byte
```

Where `high_byte:low_byte` is the desired screen-start RAM address. The same correction must be applied to R14, R15 (cursor position) in MODE 7.

## Timing

R12/R13 are **latched** by the 6845 and applied at the next CRTC frame cycle — writes don't cause mid-frame tearing of the scrolled image (see [[hardware/crtc-6845#register-latching]]). What *can* go wrong: R12 and R13 form a 14-bit value across two writes, so if the chip samples between your two writes the result is one frame at a "half-updated" address. To avoid this, either write both bytes within a single frame (well within 20 ms), or synchronise to vsync so both writes land in the same blanking window:

- Wait via OS: `*FX 19` / `OSBYTE &13` (`JSR &FFF4` with A=&13).
- Wait via hardware: poll the System VIA IFR for the CA1 vsync edge — bit 1 of `&FE4D`. Or hook IRQ2V (`&206/&207`) on that bit. Latency to first vsync edge is up to 20 ms; budget accordingly.

Detailed timing of R12/R13 update semantics will be expanded in [[hardware/crtc-6845-advanced]] (planned).

## A note about the OS shadow copy

The OS keeps the screen-start copy at `&350/&351` (page 3 — see [[memory/os-workspace]]). When you scroll directly via `&FE00/&FE01`, the OS's idea of the screen origin is now stale — character output (`OSWRCH`) will write to the wrong line. Either:

- Sync the OS copy after each scroll: write your computed `(addr DIV 8) MOD 256` to `&350` and `(addr DIV 8) DIV 256` to `&351`.
- Or only do hardware scrolling in code that doesn't rely on OSWRCH afterwards (i.e., the game owns the screen).

OSBYTE `&A0` with X=&50 will read these back if you need to recover the current value (R12/R13 are write-only on the chip).

## Measured in practice — two C64 → BBC ports (2026)

*Later addition (2026-11):* one CRTC character is one byte on the BBC (two on the Amstrad CPC), so a MODE 2 horizontal scroll steps one byte (2 pixels) natively with R12/R13 — the CPC needs an R3 half-step for the same; Isometrikum's port (MODE 2, R1 = 96) relies on it ([[sources/beeb-port-kit-hardware-facts-2026-11]] §2). For the R5 single-scanline vertical scroll, see the displayed-adjust facts on [[techniques/vertical-rupture]].

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Paradroid scrolls a 10K MODE 1 strip in both axes; Edge Grinder scrolls a 16K MODE 2 play area 1 px a frame by alternating two shadow banks half a byte out of phase.

- **CRTC start address = screen address / 8** — a buffer at `&5800` is `R12/R13 = &0B00` (Paradroid Layer 3, jsbeeb).
- **One CRTC address unit is 8 bytes, one byte per scanline of an 8-scanline cell**: 8 px in MODE 0, 4 in MODE 1, 2 in MODE 2. Horizontal hardware scroll granularity is therefore half a MODE 1 character (4 px), not a whole one — the "6845 char" step tabulated above (Paradroid Layer 3, 10 steps in 10 frames at 4 px).
- **A hardware-scrolled area is a one-dimensional ring through memory, not a 2-D grid.** A character leaving the left edge reappears one row up on the right (the caveat above). Drawn as a flat grid it is corruption that scales with the offset; treated as a circular strip the redraw per step collapses to one column or one row (Paradroid Layer 3: at 80 px offset the right quarter showed the wrong rows; [layer-3-scroll.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-3-scroll.md)).
- **The half-updated-address frame is real**: R12/R13 form one 14-bit value across two writes, and if the CRTC samples between them the display shows one frame at a half-updated address. Write both in vertical blanking (Paradroid Layer 3, jsbeeb). Both ports write them in the VSync handler.
- **The display window must fit inside ONE hardware wrap** — the translator subtracts once and does not iterate. Larger windows fetch from `&8000` upward at some scroll positions (Paradroid Layer 3). And on the Master **the wrap applies inside whichever bank is displayed** (Edge, 2026-09-04, jsbeeb). See [[hardware/address-translation]], [[memory/shadow-ram]].
- The "wait for vsync" idiom above: the CA1 interrupt is serviced about 4 scanlines after the edge, and polling `&FE4D` bit 1 races the MOS's own handler while the MOS is alive — see [[hardware/system-via]].

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
