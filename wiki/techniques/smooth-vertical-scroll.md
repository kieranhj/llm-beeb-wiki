---
title: Smooth Vertical Scrolling (1-scanline granularity)
type: technique
tags: [crtc, scrolling, raster, vertical-rupture, mode-2, smooth-scroll]
sources: [retrosoftware-smooth-vscroll, hd6845sp-hitachi-datasheet, naug-ch13-video]
updated: 2026-05-16
---

# Smooth Vertical Scrolling

R12/R13 alone gives 8-scanline vertical scroll steps (one character row at a time — see [[video/hardware-scrolling]]). To scroll by **single scanlines**, exploit **R5 (vertical total adjust)** to shift the visible screen down 0-7 scanlines, then advance R12/R13 by one row each time R5 wraps. Foundation is [[techniques/vertical-rupture]] — two CRTC cycles per frame.

Source: Talbot-Watkins, [[sources/retrosoftware-smooth-vscroll]]; code in `raw/code/smoothscroll.bas`.

## The R5 lever

Total scanlines per PAL frame:

```
total = (R4 + 1) × (R9 + 1) + R5
      = 39 × 8 + 0
      = 312
```

R5 (0-31) adds extra scanlines after the cycle's last row — physically, these land in the **top border** of the next field. Setting R5=3 pushes the displayed screen down 3 scanlines relative to a fixed reference point on the TV.

But naively setting R5=3 gives **315** scanlines total — TV unlocks. Solution: **two CRTC cycles per frame** with `R5_a + R5_b = 8` (or any multiple of 8). Total stays at `38×8 + 8 = 312`.

So with a `line` variable in 0..7 (the desired sub-row offset):

| Cycle | Role | R5 setting |
|---|---|---|
| A | VSync cycle (above the playfield) | `8 − line` |
| B | Playfield cycle (the scrolling window) | `line` |

When `line=0`, R5_A=8 / R5_B=0 — playfield starts on its own row-0 boundary.
When `line=7`, R5_A=1 / R5_B=7 — playfield starts 7 scanlines into its row.

## Keeping the visible top edge rock-steady

Even with the total at 312, varying R5 shifts the *top of the playfield* on screen by 0-7 scanlines. To keep the visible top boundary stable, **turn the screen off via the Video ULA** after VSync, then re-enable via a System VIA T2 timer set to fire at the same physical scanline every frame.

### Why the timer can be a single constant

Walk the timeline with cycle A start as T=0 (units: scanlines). R4_A=13 (14 rows), R7_A = 9 − V%, R5_A = 8 − line:

| Event | T (scanlines) |
|---|---|
| Cycle A starts | 0 |
| VSync edge (start of R7_A's row) | `(9 − V%) × 8` |
| Cycle A's nominal 14 rows done | `14 × 8 = 112` |
| Cycle A actually ends (after R5_A) | `112 + (8 − line) = 120 − line` |
| Cycle B starts; chip fetches from new R12/R13 | `120 − line` |
| Scanline `line` of cycle B's row 0 — **visible top edge** | `(120 − line) + line = 120` |

The `line` cancels — visible top edge is always at **T=120** regardless of scroll position. That's the whole reason this technique works.

### Deriving the compensator

Wait needed from VSync IRQ entry to visible top edge:

```
T_visible_top  = 120                       (cycle-A scanlines)
T_vsync_edge   = (9 − V%) × 8 = 72 − 8·V%
T_irq_entry    = T_vsync_edge + 2          (VSync pulse width from R3 high nibble = 2)
               = 74 − 8·V%

wait_scanlines = T_visible_top − T_irq_entry
               = 120 − (74 − 8·V%)
               = 46 + 8·V%
```

Each scanline is **64 1MHz cycles** (the BBC's video bandwidth), so:

```
wait_ticks_raw = (46 + 8·V%) × 64
               = (5 + V%) × 512  +  6 × 64
                 |--rows-after-VSync--|   |--R5_max − pulse_width--|
                 = (R4_A + 1 − R7_A) × 8 × 64
```

Rearranging in row+scanline form makes the two physical quantities explicit:

- **`(5 + V%) × 512`** = `(R4_A + 1 − R7_A) × scanlines_per_row × ticks_per_scanline` — wait from VSync edge to the end of cycle A's nominal 14 rows. V% slides this by one char row per unit.
- **`6 × 64`** = `(R5_A_baseline − VSync_pulse_width) × ticks_per_scanline` = `(8 − 2) × 64`. The R5 max is 8 (when `line=0`); subtract the 2 scanlines already burned by the VSync pulse before the IRQ fires.

Finally subtract the **IRQ dispatch overhead** — the cycles between the VSync edge and our handler actually writing `STA &FE48`:

```
6502 IRQ sequence              7c
MOS save-A (STA &FC)           3c
MOS JMP (&204)                 5c   (assumes IRQ1V intercepted directly)
handler prologue:
  LDA &FE4D                    4c
  AND #2                       2c
  BEQ timerirq                 2c   (branch not taken)
  STA &FE4D                    4c
  LDA #<latch_lo : STA &FE48   2+4
  LDA #<latch_hi : STA &FE49   2+4
  (T2 is armed when high byte is written)
                              ----
                              ≈ 39c instructions + 7c interrupt seq
                              + cycle-stretching on &FE4D/&FE48/&FE49 accesses
```

The empirically tuned **−93** absorbs all of this. The exact number is platform-sensitive (cycle-stretching on the System VIA varies by 1c depending on the 2 MHz/1 MHz bus phase at IRQ entry — see [[timing/cycle-stretching]]), which is why it's calibrated rather than computed.

Putting it together:

```
timer_load = (5 + V%) × 512  +  6 × 64  −  93
```

V%=0 → 2851 ticks → fires 44.55 scanlines after IRQ entry → screen-on at the same physical TV scanline every frame, regardless of `line`.

### Generalising

If you change the cycle-A geometry (different R4_A or R7_A) the compensator's structure becomes:

```
timer_load = (R4_A + 1 − R7_A) × 512                  ; rows after VSync × ticks/row
           + (R5_A_max − VSync_pulse_width) × 64      ; partial-row residue
           − IRQ_dispatch_cycles                      ; tune empirically
```

Result: the visible top edge is determined by the timer, not by R5. R5 controls only which **scanline of the character row** appears first.

## Frame anatomy (24-row playfield + 1-row status)

```
Cycle A (VSync, above playfield + status)
    R4 = 13      → 14 rows
    R5 = 8-line
    R7 = 9-V%    → VSync inside this cycle
    Bottom 1 row visible = status panel @ &7B00 (R12/R13 = &0760)

Cycle B (playfield)
    R4 = 23      → 24 rows
    R5 = line
    R6 = 25      → display 25 rows (24 playfield + 1 fractional from R5)
    R7 = 255     → no VSync this cycle
    R12/R13 = scrolling base address
```

Row budget: `14 × 8 + (8 − line) + 24 × 8 + line = 112 + 8 − line + 192 + line = 312 ✓`

## Walk-through (`smoothscroll.bas` line numbers)

### On VSync IRQ (line 670-810)

1. Set T2 to fire at the screen-on point: `((5+V%)*512 + 6*64 − 93)` ticks (line 700-710).
2. Enable VSync IRQ only on the System VIA: `LDA #&A0 : STA &FE4E` (line 720).
3. Latch `iline ← line` so the playfield doesn't tear if `line` is updated mid-frame (line 730).
4. Write **R5 = 8 − iline** for cycle A (line 740-750).
5. Write **R6 = 25**, **R7 = 255**, **R8 = `&F0`** (display delay 3, cursor delay 3, non-interlace) — config for the playfield cycle that's about to start at next CRTC cycle (line 760-780).
6. Latch new playfield `addr` into R12/R13 (line 790-800).

### On first timer fire — screen-on, queue cycle-A shape (line 470-650)

1. Clear T2 flag (line 490).
2. **Unblank the screen** by writing `&C0` to CRTC R8 (line 510-520). This is the BBC's standard mid-frame blank/unblank trick — see [below](#screen-blank-via-crtc-r8).
3. Set next T2 timer to fire near the end of the playfield cycle: `24*512 − 3` ticks (line 530-540). 512 = 8 scanlines × 64 ticks.
4. Write **R4 = 23** (24 rows for playfield) and **R5 = iline** (line 560-580).
5. Latch status-panel address into R12/R13 (line 590-600) for cycle A which begins after cycle B ends.

### Screen blank via CRTC R8

The demo blanks the screen at VSync (`STA &FE01` with `&F0`, line 780) and re-enables at the timer fire (`&C0`, line 520). Both writes go to **CRTC R8**, not the Video ULA. The mechanism is R8's skew field (see [[hardware/crtc-6845]]):

| R8 value | Bits 4-5 (display skew) | Bits 6-7 (cursor skew) | Effect |
|---|---|---|---|
| `&F0` | `11` = **disable video** | `11` = cursor off | Screen blanked |
| `&C0` | `00` = no skew | `11` = cursor off | Screen on, no hardware cursor |

The `11` encoding in either skew field is documented as "non-display" on the HD6845S — the chip gates DISPTMG / CUDISP off rather than delaying them. It produces a clean borderless blank with **no visible artefact at the transition** because it's the chip's own display-enable that's being toggled, not the ULA's serialiser mid-byte.

This contradicts the Hitachi datasheet's blanket "R8 dynamic rewrite prohibited" verdict (see [[hardware/crtc-6845-advanced]]) — in practice, the **skew bits** are safe to rewrite mid-frame on the HD6845S; only the **interlace-mode bits 0-1** are the truly-don't-touch part. This page is one of two known real-world examples (the other being R7 mid-frame rewrites in [[techniques/vertical-rupture]]).

### On second timer fire — cycle-A setup (line 380-450)

1. **R4 = 13** (14 rows for the VSync cycle), **R6 = 1** (display 1 row = the status panel), **R7 = 9 − V%** (VSync near top of this short cycle) (line 390-420).
2. Re-enable T2 IRQ (line 430).

The 1-row status panel is **not optional padding** — it gives the timer a wide tolerance window to fire in. Without it, sub-µs jitter would leak playfield data into the wrong region.

## Updating the scroll position

Main loop (line 850-1020) reads `*` and `/` (BBC keyboard scan codes 72 and 104 via `&FE4F`) and Shift state. Without Shift: scroll by full 8-scanline rows. With Shift: scroll by 1 scanline.

```basic
DEC line : BPL notup            \ subtract 1 scanline
LDA #7   : STA line             \ wrapped; advance R12/R13 by one row
LDA addr : SEC : SBC #80 : STA addr        \ 80 = MODE 2 row stride DIV 8
LDA addr+1 : SBC #0 : CMP #&40/8           \ wraparound at &4000
BCS *+4   : ADC #&40/8 : STA addr+1
```

The 80-byte stride is `bytes_per_row (640) ÷ 8` because R12/R13 stores `addr DIV 8`. Wraparound check uses the 20K-screen-base `&4000` (DIV 8 = `&40/8 = 8`).

## CRTC + ULA + System VIA setup (line 170-300)

| Reg | Value | Effect |
|---|---|---|
| R0-R11 | from `crtcvals` table | see source page |
| R6 (init) | 26 | overrides MODE-2-default 32; total displayed = 25 playfield + 1 status |
| R7 (init) | 31 | shifts VSync 3 rows earlier than MODE 2 default |
| R8 (init) | `&F0` | display delay=3, cursor delay=3, non-interlaced, no skew |
| System VIA `&FE4E` | `&7F` then `&82` | disable all then enable CA1 (vsync) + T2 |
| System VIA `&FE4C` (ACR) | 4 | T2 one-shot mode (PB7 disabled) |
| Addressable latch `&FE40` | bit 4 cleared, bit 5 set | selects **20K screen** wraparound at `&4000` |
| User VIA `&FE43` | `&7F` | DDR for keyboard scan |
| IRQ1V `&204/5` | `irqhandler` | take all IRQs ourselves (MOS bypassed) |

## Why this can be done at all

The technique relies on the same three CRTC properties as [[techniques/vertical-rupture]] — R12/R13 latched per cycle, R4/R6/R7 read per cycle, R5 added per cycle — plus one extra: **the Video ULA can be re-enabled mid-frame** without disturbing the CRTC or the TV's sync lock. The chip just keeps producing addresses; the ULA decides whether to push pixels.

## Pitfalls

- **R5 + R4×(R9+1) must sum to 312 across cycles** — easy to break when changing screen layout (e.g. moving from 24-row to 25-row playfield). Recompute the residue cycle's R4.
- **Timer compensator is tuned** for the exact VSync IRQ entry cost and ULA-enable position. Changing the IRQ handler's first instructions shifts the visible top edge by exactly that many cycles.
- **Variable updates (`line`, `addr`) should be done outside the visible CRTC cycle** — the IRQ handler latches `iline ← line` and reads `addr` only at VSync, so the main loop is free to update between frames.
- **The status panel is structural**. Reducing it to zero rows breaks the timing tolerance and starts to flicker.

## Applied case — Twisted Brain "Smiley Drop"

[[sources/twisted-brain]] Part 14 uses smooth vertical scroll as a **sprite reveal** rather than a screen scroll. The Smiley image is the only thing in the scrolling window; everything else around it is masked off by setting Vertical Displayed R6 *larger* than Vertical Total R4 so the VADJ scanlines themselves are visible (showing the top fragment of the Smiley sprite as it drops in). The bottom status window is a different prerendered image.

The blank/unblank lever in that implementation is **CRTC R8 (`&00` non-interlace + display delay = 0 vs `&30` display delay = 3 = blanked)** — see [[hardware/crtc-6845]]'s screen-blank-via-R8 note. Same `R8` trick as in this page's `&F0`/`&C0`, just expressed via different bits because Smiley Drop doesn't want the cursor-off behaviour.

## Builds on

- [[techniques/vertical-rupture]] — required reading first.
- [[video/hardware-scrolling]] — the 8-scanline-step base case this extends.
- [[hardware/crtc-6845-advanced]] — register-rewrite phase verdicts.
- [[hardware/video-ula]] — screen-enable bit used for the rock-steady top edge.
- [[timing/via-timers]] — T2 one-shot, ISR-entry cost.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
