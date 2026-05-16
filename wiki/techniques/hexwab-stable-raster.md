---
title: Stable Raster (hexwab's cycle-exact sync)
type: technique
tags: [stable-raster, raster, timing, vsync, irq, t1, jitter, sync]
sources: [hexwab-stable-raster]
updated: 2026-05-16
---

# Stable Raster

Lock CPU execution to the TV raster with **2-cycle precision**, frame after frame, surviving variable-length-instruction IRQ entry. This is the foundation for any raster effect where 8-cycle horizontal phase drift would be visible — single-pixel-aligned palette changes in MODE 1/2, beam-race buffer mutation that lands on the same column every line, etc.

Documented by hexwab on the Retrosoftware forum (2016): [[sources/hexwab-stable-raster]].

The simpler [[techniques/fx-framework]] approach used by [[sources/twisted-brain]] accepts ~8 cycles of jitter — fine for most effects. Use this technique when you need tighter.

## The problem stable raster solves

When you set up a continuous-mode timer to fire every frame, the IRQ doesn't enter on the exact target cycle. It enters somewhere in the **next 0-7 cycles** depending on:

- Which 6502 instruction was executing when the timer hit its threshold (instructions are 2-7 cycles long; the IRQ waits for completion).
- Cycle stretching of any SHEILA access the interrupted code was performing.
- IRQ vector dispatch latency (depending on NMOS vs CMOS 6502 — Master is 1c longer).

If your effect just runs a per-raster palette write, that 0-7c jitter manifests as a 0-7-cycle horizontal-position shift of each raster line's colour change, which looks like flickering or noisy edges.

## The four stages

### Stage 0 — disable interlacing

Interlaced frames alternate field durations. Stable raster requires every frame to be identical length, so force non-interlaced: clear R8 bit 0 of the [[hardware/crtc-6845|CRTC]] before starting.

### Stage 1 — initial vsync narrowing-loop sync

```asm
; Wait for vsync flag
.wait
    BIT &FE4D
    BEQ wait                ; wait for bit 1 (CA1) = 1
; We're now within ~10 cycles of vsync edge.

; Narrowing loop: spend almost-one-frame, then check if vsync arrived again
LDA #2
.narrow
    STA &FE4D               ; ACK vsync
    ; ... spend (frame_cycles - 2) cycles ...
    BIT &FE4D
    BNE narrow              ; if vsync hit, narrow further
; Falls through when our wait-loop straddled the vsync edge
; — we now know vsync just hit within the last 2 cycles.
```

Credit for the narrowing-loop idea: tricky.

Why 2-cycle precision is the floor: VIA reads (`BIT &FE4D`) are cycle-stretched to 1 MHz boundaries. We can never resolve finer than 2 (2 MHz) cycles for any sync that involves reading a VIA. Frames are always an even number of 2 MHz cycles, so this is consistent and not a problem.

### Stage 2 — continuous T1 in free-run mode

Configure System VIA + User VIA T1 to fire at exactly the right phase:

```asm
; T1 latch = frame_cycles - 2 (the -2 is empirically required, likely the latch-load delay)
LDA #<&4DFE : STA UVIA_T1L_L          ; user VIA T1 low latch (= frame period - 2)
LDA #>&4DFE : STA UVIA_T1L_H          ; user VIA T1 high latch
; ACR: T1 continuous, PB7 disabled
LDA #&40    : STA UVIA_ACR
; Start T1 by writing T1C-H
LDA #>&4DFE : STA UVIA_T1C_H

; Hook IRQ1V to our handler
LDA #<handler : STA &204
LDA #>handler : STA &205
```

Key constraints:

- **Must use T1** (not T2) — T2 has no continuous-reload mode.
- **Must hook IRQ1V** (not IRQ2V) — for minimum dispatch latency.
- **Must use User VIA T1** (not System VIA T1) — so the handler can read T1's latch during the ISR without acknowledging the System T1 interrupt that MOS depends on. (If you use System T1, MOS's view of the 100 Hz tick is destroyed.)
- **Resync System VIA T1 to User VIA T1** — minimises the chance of a System T1 IRQ firing during the User T1 ISR's critical section.
- **MOS IRQ dispatch ROM is in the timing path** — identical cycle counts across MOS 1.20, 2.00, 3.20, 3.50, so portable. MOS 0.1 stores A at `&DE` instead of `&FC` but the timing is the same.

### Stage 3 — jitter compensation via latch read

On entering the IRQ handler:

```asm
.handler
    ; Read T1 low latch — this is the *current* counter value.
    ; If the IRQ entered late, the counter is lower (further past zero).
    LDA UVIA_T1C_L          ; 4c (cycle-stretched, aligns us to 1 MHz boundary)
    ; Index into a small lookup table of delay values
    TAX
    LDA delay_table, X      ; 4c
    JMP (delay_dispatch)    ; or unrolled NOP slide
```

The latch read is cycle-stretched — aligning to a 1 MHz boundary. So even though we have 1 MHz timer precision, the read itself aligns us to the same phase as the timer was. After this, a variable-length NOP slide brings us out at the exact same cycle every frame.

The trade-off: more slack in the delay table = more robustness (handles a wider range of entry jitter) = more cycles consumed before useful work starts.

## Example delay table (from hexwab's post)

For "low delay, low robustness":

| T1 latch on entry | Cycles to delay |
|---|---|
| > `&4DEA` | impossible (IRQ entered too early — should never happen if timer is right) |
| `&4DEA` | 6 |
| `&4DE9` | 4 |
| `&4DE8` | 2 |
| `&4DE7` | 0 |
| < `&4DE7` | missed — fatal, handler should bail / resync |

The narrow window (only 4 valid latch values = 8 cycles of acceptable entry jitter) means this configuration *will* break if there are unexpected interrupt sources. For robustness, widen the table to accept more values — at the cost of consuming more useful-work cycles in the compensator.

## Quirks and caveats

- **CMOS 6502 (Master) is 1c slower** on the `JMP (&0204)` indirect inside MOS — the whole timing table needs +1c adjustment. RichTW's correction in the thread.
- **Random unexplained IRQs** — even with ADC off, no keypresses, System T1 sync'd to User T1, hexwab observes occasional jitter from sources he couldn't identify. Candidates: ACIA, light pen, network, sound-buffer events. If you're targeting <2c jitter you'll need to mask these at the IER level.
- **Music players don't compose with this technique** without care — variable-length music player calls steal IRQ-handler budget. Twisted Brain's solution was to abandon stable raster and accept jitter; an alternative is to time the music player into its own cycle-counted slot.
- **The frame-period constant** (`312*64 - 2 = &4DFE`) is for a 312-line PAL signal. Customised CRTC configurations producing different total raster counts need the constant recomputed.

## When to reach for this

- Per-raster palette/colour changes where the change point must hit the same horizontal pixel column on every line — e.g. high-precision raster bars, pixel-aligned colour gradients.
- Demos with vertical-rupture cycle splits where the cycle boundary must land within a known horizontal slot of the displayed line (cycle-stretched ACCCON writes in [[techniques/parallax-bars]] need this kind of precision to avoid single-pixel "glitch" rows).
- Any effect where the FX-framework jitter manifests visibly. If you can't see it: don't bother, [[techniques/fx-framework]] is simpler and cheaper.

## Builds on / used by

- [[hardware/system-via]] / [[hardware/user-via]] — T1 continuous mode, latch register addresses, IER masks.
- [[hardware/crtc-6845]] — non-interlace setup (R8 bit 0).
- [[timing/cycle-stretching]] — why VIA reads align to 1 MHz boundaries (the bedrock of the latch-read jitter-compensation trick).
- [[os/interrupts]] — IRQ1V hook pattern, MOS IRQ dispatch timing.
- Referenced by [[techniques/fx-framework]] as the next-precision-level alternative.
- Referenced by [[techniques/kefrens-bars]], [[techniques/parallax-bars]] as the path to eliminating the residual jitter in those effects.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
