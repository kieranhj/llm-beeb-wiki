---
title: VIA Timer Chip-Level References (W65C22 + Kontros + Stardot)
type: source
tags: [via, 6522, timer, t1, t2, chip-level, timing]
urls:
  - https://eater.net/datasheets/w65c22.pdf
  - https://members.tripod.com/frank_kontros/6522/counters.htm
  - https://stardot.org.uk/forums/viewtopic.php?t=16138
  - https://stardot.org.uk/forums/viewtopic.php?t=16252
  - https://stardot.org.uk/forums/viewtopic.php?t=16262
ingested: 2026-06-17
---

# VIA Timer Chip-Level References

Combined source page for three references that together pin down the chip-internal behaviour of 6522 VIA timers (T1 and T2). Used to decompose the wiki's `(N+2) µs` formula into its constituent ticks and verify against real BBC hardware.

## 1. WDC W65C22 Datasheet (Sept 2010)

**URL:** https://eater.net/datasheets/w65c22.pdf  
**Publisher:** Western Design Center  
**Note:** The WDC W65C22S is the modern descendant of the original Rockwell R6522. Acorn shipped the Rockwell or Synertek part, not WDC's, but the timer-counter logic is identical across all CMOS-compatible variants. WDC's datasheet is more thorough than Rockwell's original.

### Key claims used

- **Figure 18 — Timer 2 one-shot mode timing**: `!IRQ` output transitions active (low) at **N+1.5** Φ2 cycles after the write to T2C-H. The half-cycle is because the IRQ-out pin updates on the opposite Φ2 phase from the counter itself.
- T2 timer comprises a write-only low-order latch (T2L-L), a read-only low-order counter (T2C-L), and a read/write high-order counter (T2C-H).
- Writing T2C-H: clears IFR bit 5, loads N from latches into the counter, starts the timer.

## 2. Frank Kontros — 6522 VIA Counters/Timers

**URL:** https://members.tripod.com/frank_kontros/6522/counters.htm  
**Author:** Frank Kontros  
**Date:** undated; based on Rockwell-era datasheet behaviour.

### Key claims used

- The 6522 timer's **period is N+2 cycles**; IRQ asserts at N+1.5 (consistent with WDC datasheet Fig 18).
- Both T1 and T2 follow this rule in interval/one-shot mode.
- The mechanism of the "+2" is one Φ2 cycle for latch-to-counter load + one Φ2 cycle for the through-zero (0 → `&FFFF`) underflow that fires the IFR bit.

## 3. Stardot Forum Discussions on VIA Emulation

### Stardot 16138 — "More interesting 6522 VIA emulation discrepancies"

**URL:** https://stardot.org.uk/forums/viewtopic.php?t=16138  
**Authors:** hoglet, scarybeasts (Chris Evans), others.

- **Real-hardware test (hoglet, Model B + Master 128):** writing T2C-H = 1 and then reading T2C-L back in a tight loop produces the sequence `1, 0, &FF, &FE, &FD, &FC, ...`. Verifies that the counter passes through zero and IFR fires on the `0 → &FFFF` underflow tick — not when the counter first reaches zero.
- Cross-emulator note: b-em, jsbeeb, b2 all add 1 to the counter on write (matching the `+1` startup-load tick). MAME adds 3 and skips zero (wrong).
- scarybeasts: "the correct implementation may in fact be to delay the counter update taking effect by 1 VIA 1Mhz timer tick" — confirms the load-tick model.

### Stardot 16252 — "6522 VIA emulation: ACR writes"

**URL:** https://stardot.org.uk/forums/viewtopic.php?t=16252

- ACR-write timing details, secondary to the count behaviour above. Confirms that changes to ACR (e.g. flipping T1 between one-shot and free-run) take effect at the next 1 MHz Φ2 edge.

### Stardot 16262 — "6522 VIA emulation: IFR write vs. timer interrupt"

**URL:** https://stardot.org.uk/forums/viewtopic.php?t=16262

- Race conditions when writing IFR (to clear a flag) on the same cycle as a timer underflow asserts the flag. Relevant for hand-rolled IRQ handlers.

## Synthesis: anatomy of (N+2) µs

The three sources triangulate the same picture:

| Stage | Source | Cost |
|---|---|---|
| Write to TxC-H | bus protocol | (CPU-side, not counted in N+2) |
| Counter loads N from latch on next Φ2 edge | Kontros + scarybeasts | +1 µs |
| Counter decrements N times | Kontros + WDC | N µs |
| Through-zero underflow fires IFR | hoglet hardware test + WDC Fig 18 | +1 µs |
| **Total** | | **N+2 µs** |

The WDC's "N+1.5" is the same picture from the IRQ-pin's perspective, half a Φ2 cycle earlier than the count-side underflow.

## Filed into

- [[timing/via-timers]] — added "Anatomy of the +2" section with stage-by-stage breakdown.
- [[hardware/via-6522]] — expanded T1/T2 timeout description with the +2 decomposition.
- [[techniques/fx-framework]] — cross-linked the "2 µs latch trim" remark to the explanation.
- [[techniques/hexwab-stable-raster]] — same cross-link.
- [[sources/hexwab-stable-raster]] — same cross-link.
- [[sources/twisted-brain]] — same cross-link.

## Cross-refs

- [[hardware/via-6522]] — generic 6522 register layout.
- [[hardware/system-via]] — System VIA at `&FE40`; ACR at `&FE4B`.
- [[timing/cycle-stretching]] — explains the SHEILA-access stretch that wraps the `STA TxC_H` write.

## Open follow-ups

- The "+2" formula in *free-run* mode is the same `(N+2) µs` per cycle as one-shot, but the breakdown is different (the underflow tick *is* the reload tick — no separate load cycle after the first cycle). Worth confirming on hardware whether free-run cycle 2 onward is exactly N+1 µs (no reload tick) or still N+2 µs (chip re-runs the load tick on every reload). hoglet's test rig could verify.
- No worked example yet of a re-trigger mid-count: does writing TxC-H while the counter is at value M reload N immediately, or does it interleave one µs of M before the reload?

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
