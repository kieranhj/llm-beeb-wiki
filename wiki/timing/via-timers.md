---
title: VIA Timers (T1, T2)
type: timing
tags: [via, t1, t2, timer, raster, vsync]
sources: [naug-ch22-vias, via-timer-chip-level-refs]
updated: 2026-06-17
---

# VIA Timers (T1, T2)

Each 6522 VIA has two 16-bit timers that decrement at **1 MHz** — i.e. one tick = 1 µs = 2 CPU cycles (at 2 MHz CPU clock). Both VIAs ([[hardware/system-via]], [[hardware/user-via]]) have a T1 and a T2, so the BBC has **four** timers total — though System VIA T1 is often claimed by MOS sound, leaving T2 + both User VIA timers free for user code.

## T1 — full-featured

Four modes selected by ACR bits 6 (continuous), 7 (PB7 output):

| ACR6 | ACR7 | Behaviour |
|---|---|---|
| 0 | 0 | **One-shot.** IFR bit 6 set on timeout; no further IRQ until T1C-H rewritten. |
| 0 | 1 | One-shot + **PB7 pulse low** for the count duration. |
| 1 | 0 | **Free-run.** IFR bit 6 set at each timeout, counter reloads from latches automatically. |
| 1 | 1 | Free-run + **PB7 square wave**. No CPU cycles needed. |

### Loading T1

```asm
LDA #lo : STA T1C_L     ; load low latch (no count starts yet)
LDA #hi : STA T1C_H     ; loads high latch AND starts count
```

**Timeout** = `(N+2) × 1 µs` where N is the loaded 16-bit value (NAUG §22.4.10 p397). At N=0, the first timeout is 2 µs (4 CPU cycles). See [[#anatomy-of-the-2|Anatomy of the +2]] below for what the two extra µs actually are.

For continuous (free-run) operation, write both latches via `T1L_L`/`T1L_H` (regs 6/7) to update the *period* of the next cycle without restarting the current one.

### Clearing T1 IFR

Any of: read T1C-L, read T1C-H, write T1C-H, or write `&40` to IFR. Most efficient: `LDA T1C_L` (4c).

## T2 — simpler

Two modes selected by ACR bit 5:

| ACR5 | Mode |
|---|---|
| 0 | **Interval timer (one-shot only).** No free-run mode for T2. |
| 1 | **Pulse counter** — T2 decrements once per negative-going pulse on PB6 |

T2 has no PB7 output, no continuous mode. It's a one-shot from the moment T2C-H is written. To repeat, the IRQ handler must rewrite T2C-H.

### Clearing T2 IFR

Read T2C-L or write T2C-H. `LDA T2C_L` (4c).

## Anatomy of the +2

The `(N+2) µs` formula applies to **both** T1 and T2 in interval mode. It is **not** a magic constant — it decomposes into one µs of startup delay plus one µs of through-zero underflow. Understanding the breakdown matters when you're synchronising to T2/T1 at single-cycle precision (e.g. [[techniques/hexwab-stable-raster]]) or polling T2C-L for a specific tick.

Sequence from the CPU's `STA TxC_H` to the IRQ firing:

| Stage | What happens on the chip | Cost |
|---|---|---|
| 1. The write | `STA TxC_H` is a SHEILA access → cycle-stretched to align with the 1 MHz Φ2 bus. Register update completes at the *end* of the stretched bus cycle. | 4-6 CPU cycles (2-3 µs) — see [[timing/cycle-stretching]] |
| 2. **Load tick** | On the *next* Φ2 edge after the write, the counter loads N from the latch pair. **No decrement on this tick** — this is the startup delay. | +1 µs |
| 3. Countdown | Counter decrements once per Φ2 edge: N, N-1, …, 2, 1, 0. | N µs |
| 4. **Underflow tick** | The `0 → &FFFF` transition fires the IFR bit (5 for T2, 6 for T1). | +1 µs |
| 5. CPU sees IRQ | Standard 6502 IRQ entry — finish current instruction, push PC/P, fetch vector. | 7+ CPU cycles |

So the **+2** is exactly: +1 dead load tick + 1 underflow tick. Stages 1 and 5 are outside the formula — they're the cost of getting to and from the timer, not the timer's own delay.

The WDC W65C22 datasheet (Fig 18) actually shows `!IRQ` falling at **N+1.5** Φ2 cycles. The half-cycle is because the IRQ-out pin is updated on the opposite Φ2 phase from the count itself. For polled or IRQ-driven code on the BBC this rounds to the +2 µs that NAUG quotes; for chip-level emulation (jsbeeb / b2 / beebjit) it matters.

### Real-hardware verification

hoglet ran a real-hardware test on Model B and Master 128 ([Stardot 16138](https://stardot.org.uk/forums/viewtopic.php?t=16138)): write T2C-H = 1, then read T2C-L back in a tight loop. Sequence observed: `1, 0, &FF, &FE, &FD, &FC, ...`. This confirms:

- The counter passes **through zero** (not skipping to `&FFFF`).
- The IFR bit fires on the `0 → &FFFF` transition (stage 4 above), not when the counter first becomes zero.
- So you have a **1 µs window at T2C-L = 0** to catch the count via polling before the IRQ trigger.

### When you can't use the formula

The +2 model breaks down in two cases:

- **Re-trigger before timeout.** Writing TxC-H again re-runs stage 2 (load tick) — you get one *extra* µs you wouldn't get from waiting for the first count to expire and re-arming in the IRQ handler. Useful for extending a wait without losing precision.
- **Reading T1C-L mid-count to clear IFR while continuing.** The read doesn't perturb the count, but the bus-side cycle stretch on the read itself is variable depending on Φ2 phase — see [[timing/cycle-stretching]] for the 2c/3c distribution. T2 has the same property.

## Practical patterns

### Periodic IRQ at < 50 Hz

Use T1 free-run on **User VIA** (System VIA T1 may be in use by MOS sound). Hook IRQ2V. Loaded value `N` gives a period of `(N+2) µs`.

For exactly 50 Hz: `N = 19998` (period = 20000 µs). For 100 Hz: `N = 9998`.

### Raster split at a specific scan line

Each scan line on a UK BBC is 64 µs (1/(50 × 312)) — but in **non-interlace** mode used by all modes except 7, that's 64 µs per line. Programming T1 with `N = 64 × lines_to_wait - 2` from the start of vsync gives an IRQ at that line.

Pattern:

1. In your vsync handler (System VIA CA1, IFR bit 1), program **User VIA** T1 in one-shot mode with the desired offset.
2. T1 fires after `(N+2) µs` from the program write.
3. In the T1 IRQ handler, write your raster effect (palette change, mode bit toggle, R12/R13 reposition).
4. To chain another split, immediately reprogram T1 with the next delta.

Cycle-accurate splits require fast IRQ entry — the 7-cycle IRQ overhead plus your handler's preamble (PHA/PHX/PHY/LDA IFR/CMP/etc.) easily costs 20+ cycles, so plan accordingly. For exactly-cycle-aligned splits, disable IRQs and busy-wait on `LDA T1C_L` until the count is near zero.

### Audio via PB7

ACR bits 6=1, 7=1 → T1 free-run with PB7 square wave. The frequency on PB7 is `500 kHz / (N+2)`. For a 1 kHz tone, `N = 498`.

This gives you an audio channel without going through the SN76489 — useful for sample playback (1-bit pulse-width modulation), or as an extra voice. Output is on the user port pin PB7; connect to amp.

### Pulse counting (mouse / tachometer)

Set ACR bit 5 = 1. Load T2 with the number of pulses you want to count. Each negative-going edge on PB6 decrements T2. When it hits zero, T2 IFR fires.

Useful for measuring rotation rate of a quadrature encoder (1 channel into PB6, count edges over a known time window).

## Sound and the System VIA T1

MOS uses System VIA T1 to time sound-envelope updates (every 20 ms). If you steal T1, sound queues stop processing — channels keep playing their current note but envelopes don't update, the next note in a queue won't trigger.

The standard advice: **prefer User VIA timers** for general-purpose timing. Touch System VIA timers only if you've turned off MOS sound (`*FX 210,1` or `OSBYTE 210` with X=1).

## Caveats

- The latches survive timeouts; the *counter* reloads from them in free-run mode. If you change the latches via regs 6/7 while free-running, the change takes effect at the *next* timeout, not immediately.
- Writing T1C-H or T2C-H clears the relevant IFR bit — useful in handlers.
- A timer write while IRQs are enabled, with the timer already at a small count, may produce an IRQ between the C-L write and C-H write. Disable IRQs around the load to be safe.

See [[hardware/via-6522]] for register layout. See [[sources/naug-ch08-interrupts]] (pending) for the IRQ dispatch chain.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
