---
title: Vertical Rupture (CRTC split-screen)
type: technique
tags: [crtc, raster, split-screen, scrolling, mode-2]
sources: [retrosoftware-smooth-vscroll, hd6845sp-hitachi-datasheet, naug-ch13-video]
updated: 2026-05-16
---

# Vertical Rupture

**Vertical rupture** is the technique of running **more than one CRTC cycle inside a single TV frame** by reprogramming R4 (vertical total) mid-frame. Each cycle has its own R12/R13 screen-start, so a single physical screen can show two or more independent windows — typically a hardware-scrolling playfield and a stationary status panel. Term originates in the Amstrad CPC demo scene ([[sources/retrosoftware-smooth-vscroll]]).

This is the foundation for [[techniques/smooth-vertical-scroll]] and most raster-split tricks on the Beeb.

## Why it works

Three properties of the 6845 combine:

1. **R12/R13 are latched at the start of each CRTC cycle** (see [[hardware/crtc-6845]] and [[hardware/crtc-6845-advanced]]). Writing them mid-cycle changes the address used by the **next** cycle, not the current one.
2. **R4 (vertical total), R6 (vertical displayed), R7 (vertical sync position) are read fresh each cycle** — not pre-latched. Rewriting R4 cuts the current cycle short or extends it; rewriting R6/R7 changes what's displayed and where VSync fires for the cycle they govern.
3. The TV is locked to the CRTC's HSYNC/VSYNC; provided you keep `Σ(R4+1)(R9+1) + ΣR5 = 312` over the frame, the picture stays in lock.

So: at any time during a CRTC cycle, write the next cycle's R12/R13; cut the current cycle short with a new R4; the chip ends that cycle, latches the new R12/R13, and begins a fresh cycle with the new start address.

## The R7-rewrite caveat

The Hitachi datasheet classifies R7 mid-frame rewrites as **NG** (see [[hardware/crtc-6845-advanced]]). The technique still works because writes happen during the *preceding* cycle and have settled before the new cycle's VSync window is reached. The NG verdict applies to rewrites *during* the cycle whose VSync position is being changed. As long as R7 updates land before the new cycle's vertical-sync comparator fires, the chip behaves.

## Worked example — MODE 2, 16-row split

From `raw/code/vrupt.6502` (rupture demo accompanying [[sources/retrosoftware-smooth-vscroll]]). Top 16 rows hardware-scroll a `&5800-&7FFF` playfield (uses the `&8000` wraparound — requires the 10K-screen latch). Bottom 16 rows show a stationary panel at `&3000`.

```
PAL frame = 39 char rows = 312 scanlines
Cycle 1 (top, scrolled):  16 rows = 128 scanlines, R12/R13 = playfield_addr/8
Cycle 2 (bottom, static): 23 rows = 184 scanlines, R12/R13 = &3000/8, VSync inside this cycle
                          --
                          39 rows ✓
```

### Setup (run once)

```asm
SEI
LDA #&7F : STA &FE4E         ; disable all System VIA IRQ sources
LDA #&A2 : STA &FE4E         ; enable CA1 (vsync) + T2 only
LDA #255 : STA &FE48 : STA &FE49   ; quiesce T2

LDA #0 : STA &FE4B           ; ACR = T2 one-shot (timed interrupt mode)
LDA #4 : STA &FE4C           ; (no PB7 squarewave)
LDA #15 : STA &FE42          ; DDRB: low nibble = outputs (addressable latch driver)

; 10K-screen wraparound: set latch bits 4 then 5 (clear bit 4 + set bit 5)
LDA #12 : STA &FE40          ; latch: clear bit 4
LDA #13 : STA &FE40          ; latch: set bit 5

LDA #irq AND 255 : STA &204  ; IRQ1V → our handler
LDA #irq DIV 256 : STA &205

LDA #0      : STA addr       ; addr = &5800/8 (top playfield base)
LDA #&58/8  : STA addr+1
CLI
```

### IRQ handler (three entry paths via `whichtimer` state)

**On VSync**: latch R12/R13 to the new playfield address, then start a T2 timer for **2560 1MHz ticks** (5 char rows × 8 scanlines × 64 ticks/scanline) to wake us once the new CRTC cycle has begun.

```asm
.irq
    LDA &FE4D : AND #2 : BEQ timer   ; bit 1 = CA1 vsync
    STA &FE4D                        ; clear vsync flag
    STA vsync                        ; signal main loop
    STA whichtimer                   ; mark: next timer = "first"

    ; latch top playfield start
    LDA #12 : STA &FE00 : LDA addr+1 : STA &FE01
    LDA #13 : STA &FE00 : LDA addr   : STA &FE01

    ; T2 = 2560 ticks → IRQ once cycle 1 has begun
    LDA #<2560 : STA &FE48
    LDA #>2560 : STA &FE49
    LDA &FC : RTI
```

**First timer fire**: we're now inside cycle 1. Cut it to 16 rows, suppress VSync, set R6=16 displayed, and queue the bottom address into R12/R13 for cycle 2. Then T2 for **8192 ticks** (16 rows × 8 × 64) to wake at the cycle-1 → cycle-2 boundary.

```asm
.timer
    LDA whichtimer : BEQ secondtimer

    LDA #4  : STA &FE00 : LDA #15  : STA &FE01   ; R4 = 15 → 16-row cycle
    LDA #7  : STA &FE00 : LDA #255 : STA &FE01   ; R7 huge → no VSync this cycle
    LDA #6  : STA &FE00 : LDA #16  : STA &FE01   ; R6 = 16 → display all 16 rows

    LDA #12 : STA &FE00 : LDA #&30/8 : STA &FE01 ; queue bottom address
    LDA #13 : STA &FE00 : LDA #0     : STA &FE01

    STA whichtimer                                ; A=0 → flag "second timer next"
    LDA #<8192 : STA &FE48
    LDA #>8192 : STA &FE49
    LDA &FC : RTI
```

**Second timer fire**: we're now in cycle 2 (bottom panel). Restore normal CRTC values for the remaining 23 rows: VSync position back where MODE 2 expects it (so the TV stays locked frame-to-frame).

```asm
.secondtimer
    LDA #&20 : STA &FE4D                  ; clear T2 flag
    LDA #4 : STA &FE00 : LDA #22 : STA &FE01   ; R4 = 22 → 23 rows
    LDA #6 : STA &FE00 : LDA #16 : STA &FE01   ; R6 = 16 displayed
    LDA #7 : STA &FE00 : LDA #18 : STA &FE01   ; R7 = 23 - 5 = 18 (VSync 5 rows before cycle end)
    LDA &FC : RTI
```

The `23 - 5 = 18` is the key timing identity: default MODE 2 has 5 char rows after VSync, so placing VSync 5 rows before the end of cycle 2 keeps the TV in identical phase to a normal MODE 2 frame.

## Row budget table (this example)

| Cycle | R4 | Rows | R6 displayed | R7 (VSync) | Notes |
|---|---|---|---|---|---|
| 1 (top, scrolled)  | 15 | 16 | 16 | 255 (suppressed) | playfield in `&5800-&7FFF`, wraps at `&8000` |
| 2 (bottom, static) | 22 | 23 | 16 | 18 | panel at `&3000`, VSync near end |
| Total |  | **39 ✓** | | | matches PAL frame |

## Pitfalls

- **Cycle-row totals MUST sum to 39** (or `38 + R5` in residue-mode setups). Even one extra row drifts the picture — slow roll on the TV.
- **R5 must sum to 0 (or 8, or multiples)** if you're using rupture without smooth-scroll. Mismatched R5 across cycles desynchronises the field.
- **Timing tolerance**: the 2560/8192-tick waits are bounded above by "before the *current* cycle ends" and below by "after the new cycle has actually started". Talbot-Watkins notes the tolerance is generous, but tight timing is needed if you reduce status-panel height — a status panel acts as slack.
- **R12/R13 update is the only mid-frame rewrite that's universally safe**. The R4/R6/R7 rewrites here work because they happen during the *previous* cycle. Don't move them earlier or later without thinking through which cycle samples them.

## Builds on / used by

- [[techniques/smooth-vertical-scroll]] — two-cycle rupture + R5 manipulation for sub-row vertical motion.
- [[hardware/crtc-6845]], [[hardware/crtc-6845-advanced]] — chip-level latching behaviour.
- [[video/hardware-scrolling]] — the address arithmetic this technique splits across cycles.
- [[hardware/system-via]] — addressable latch bits for 10K/16K/20K screen wraparound select.
- [[timing/via-timers]] — System VIA T2 one-shot used for the inter-cycle waits.
