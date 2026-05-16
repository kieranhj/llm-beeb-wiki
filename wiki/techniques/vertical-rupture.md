---
title: Vertical Rupture (CRTC split-screen)
type: technique
tags: [crtc, raster, split-screen, scrolling, mode-2]
sources: [retrosoftware-smooth-vscroll, hd6845sp-hitachi-datasheet, naug-ch13-video, accc-compendium]
updated: 2026-05-16
---

# Vertical Rupture

**Vertical rupture** is the technique of running **more than one CRTC cycle inside a single TV frame** by reprogramming R4 (vertical total) mid-frame. Each cycle has its own R12/R13 screen-start, so a single physical screen can show two or more independent windows — typically a hardware-scrolling playfield and a stationary status panel. Term originates in the Amstrad CPC demo scene ([[sources/retrosoftware-smooth-vscroll]]).

This is the foundation for [[techniques/smooth-vertical-scroll]] and most raster-split tricks on the Beeb.

## Why it works

Three properties of the 6845 combine:

1. **R12/R13 are loaded into VMA when `C4=C9=C0=0`** (see [[hardware/crtc-internal-counters]] for the counter model). Each new CRTC cycle re-loads VMA from the current R12/R13 — so writing R12/R13 during a cycle changes the address used by the *next* cycle, not the current one.
2. **R4, R6, R7 are read at specific cycle phases** — not pre-latched. Per the per-register write-window summary in [[hardware/crtc-6845-advanced]]: R4 affects the Last-Line verdict only when written at C0<2 of the candidate scanline; R6 affects display-off any time; R7 has a C0vs<2 (block) vs C0vs≥2 (trigger mid-line) dichotomy (see [[techniques/triggered-vsync]]).
3. The TV is locked to the CRTC's HSYNC/VSYNC; provided you keep `Σ(R4+1)(R9+1) + ΣR5 = 312` over the frame, the picture stays in lock.

So: at any time during a CRTC cycle, write the next cycle's R12/R13; cut the current cycle short with a new R4 (timed to land at C0<2 of the would-be Last-Line scanline); the chip ends that cycle, loads VMA from the new R12/R13, and begins a fresh cycle with the new start address.

## Register-write windows for safe rupture

For each register you'll touch during a rupture, where the write must land on the **scanline that should end the cycle** (per [[sources/accc-compendium]] §11-§16, summarised on [[hardware/crtc-6845-advanced]]):

| Register | Required write phase | If you miss the window |
|---|---|---|
| R4 (cut cycle short) | C0<2 of the candidate Last-Line scanline | Chip uses old R4, cycle extends by one scanline. Causes the [[techniques/kefrens-bars|"+1-raster drift"]] bug. |
| R6 (cut visible rows) | Any phase before C4 reaches R6 | Cycle still displays old number of rows this scanline |
| R7 (move VSync) | Anywhere safe, but avoid C0vs<2 of the line where C4=R7 | C0vs<2 + R7=C4 blocks VSync for the field (see [[techniques/triggered-vsync]]) |
| R12/R13 | Anywhere before the C4=C9=C0=0 boundary that starts the next cycle | VMA loads from old R12/R13 for next cycle |
| R5 (adjust scanlines) | Before C0=2 of the last frame line | Adjust isn't applied this frame |

The "land at C0<2 of the candidate scanline" requirement for R4 is the chief footgun. With 8-cycle-stretched STA accesses to `&FE00`/`&FE01` and ~5c instruction setup, you have a 16c-ish window — manageable but not generous.

## The "Last Line" state — what actually arms the cycle boundary

Per [[hardware/crtc-internal-counters]]: the chip evaluates `C9=R9 AND C4=R4` at C0=0,1 of every scanline. If true, "Last Line" is armed and that scanline ends the current cycle (C9/C4 reset to 0, VMA loads from R12/R13). If false, the scanline is treated as a continuing row.

To cut a cycle short via R4:
1. Decide which scanline of the cycle should be the last.
2. Compute the R4 value that satisfies `C4=R4` on that scanline.
3. Write the new R4 **before C0=2 of that scanline** (typically: during the *previous* scanline, near C0=R0).

For 8-scanline cycles (R9=7) you have 7 scanlines of slack before the Last-Line evaluation. For 1-scanline cycles (R9=0, single-scanline rupture) there's no slack at all — see [[techniques/single-rasterline-rupture]] for the specialised timing discipline.

## The R7-rewrite caveat

The Hitachi datasheet classifies R7 mid-frame rewrites as **NG**, but the precise mechanism per [[sources/accc-compendium]] §16.4.1.1 is:

- R7 written at **C0vs<2** with value=C4 *blocks* VSync for that field (no firing).
- R7 written at **C0vs≥2** with value=C4 *triggers* VSync immediately mid-line.
- R7 written with value≠C4 simply moves the VSync trigger point for the field.

For vertical rupture, the safe pattern is to write R7 well before the cycle whose VSync position is being changed reaches `C4=R7−1`. The retrosoftware demo writes R7 during the preceding cycle which sidesteps both pathologies. See [[techniques/triggered-vsync]] for the full breakdown.

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
- **R12/R13 is the easiest mid-frame rewrite to time** because VMA only loads at C4=C9=C0=0 boundaries. R4/R6/R7 rewrites have stricter per-register timing windows — see "Register-write windows" above and [[hardware/crtc-6845-advanced]] for the full breakdown. Don't move them earlier or later without thinking through which cycle samples them.

## The extreme version: single-rasterline rupture

The technique above splits a frame into 2-3 CRTC cycles for status panels and similar. The same mechanism scales to **64, 128, or 256 cycles per frame**, each cycle just 1-4 scanlines tall, used to display tiny pre-rendered buffers or beam-raced 80-byte scanline buffers over the whole screen. That's the basis of essentially every Twisted-Brain-style demo effect — see [[techniques/single-rasterline-rupture]] for the chassis and [[sources/twisted-brain]] for an inventory of effects built on it.

## Builds on / used by

- [[techniques/smooth-vertical-scroll]] — two-cycle rupture + R5 manipulation for sub-row vertical motion.
- [[techniques/single-rasterline-rupture]] — the extreme version of this technique used by modern Beeb demos.
- [[techniques/rvi]] — per-line C9 selection on top of single-scanline rupture, exploits the same Last-Line semantics.
- [[techniques/triggered-vsync]] — R7 mid-line trigger / blocked-VSync gotcha; relevant when the rupture timing intersects the C4=R7 boundary.
- [[techniques/crtc-counter-freeze]] — sibling experimental technique (R0=0 to suspend the chip entirely).
- [[hardware/crtc-internal-counters]] — the C0/C4/C9 counter model and Last-Line semantics that underpin the technique.
- [[hardware/crtc-6845]], [[hardware/crtc-6845-advanced]] — chip-level latching behaviour.
- [[video/hardware-scrolling]] — the address arithmetic this technique splits across cycles.
- [[hardware/system-via]] — addressable latch bits for 10K/16K/20K screen wraparound select.
- [[timing/via-timers]] — System VIA T2 one-shot used for the inter-cycle waits.
