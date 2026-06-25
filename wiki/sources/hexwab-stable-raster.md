---
title: hexwab — Cycle-exact display diddling (stable raster)
type: source
url: http://www.retrosoftware.co.uk/forum/viewtopic.php?f=73&t=1007
author: hexwab
contributors: [RichTW (CMOS-6502 cycle correction), tricky (the narrowing-loop sync idea)]
date: 2016-06-30
local: raw/articles/hexwab-stable-raster.md
tags: [stable-raster, raster, timing, vsync, irq, t1, jitter, hardware]
updated: 2026-05-16
---

# hexwab — "Cycle-exact display diddling"

Retrosoftware-forum post from June 2016 in which hexwab documents the **stable-raster** technique on the BBC: getting a fixed, jitter-free trigger relative to the TV raster that's accurate to 2 cycles (cycle-stretched 1 MHz precision).

This is the technique that [[techniques/fx-framework]] (Twisted Brain) decided *not* to use ("8-cycle jitter, deemed not worth the extra effort for this demo"). Worth its own page because it's the next level up in precision — needed when even 8 cycles of horizontal phase drift would be visible (e.g. for pixel-precision raster effects).

## Key technical claims

### The four stages

1. **Stage 0 — disable interlacing.** Interlaced fields are not the same duration. Force `R8` bit 0 = 0.
2. **Stage 1 — narrowing-loop sync to VSync.**
   - Tight loop on `BIT &FE4D` for the vsync flag bit. Lands within ~10 cycles of the actual VSync edge.
   - Then ACK vsync and loop for **`frame_cycles − 2`** cycles, checking and ACKing vsync each iteration.
   - Stop as soon as vsync *hasn't* hit — exit aligns to the falling-side of the vsync window with cycle-stretched-2c precision.
   - Idea: tricky (credited in the post).
   - Why 2-cycle precision: VIA reads are cycle-stretched, aligning to 1 MHz boundaries. Frames are always an even number of 2 MHz cycles, so this is sufficient.
3. **Stage 2 — set up T1 to fire just before each frame.**
   - Wait until just before the first displayed raster.
   - Set T1 latches to `&4DFE` for a 312-line screen (= `312*64 − 2`). The `−2` inverts the standard VIA-timer `+2` offset: 1 µs startup-load tick + 1 µs through-zero underflow — see [[timing/via-timers#anatomy-of-the-2]].
   - Must use T1 (not T2) because T2 doesn't have continuous-reload mode.
   - Must hook **`IRQ1V`** (not `IRQ2V`) for minimum-latency dispatch.
   - Must use the **User VIA** T1 (not System VIA T1) so the IRQ handler can read T1's latch without acknowledging the *system* T1's interrupt — which would otherwise leave MOS with no way to detect that the system T1 had also fired.
   - Resync the System VIA T1 to the User VIA T1 to minimise the chance of System T1 firing during our handler's critical section.
   - Critically dependent on the cycle-precise timing of the **MOS IRQ ROM dispatch code** — fortunately identical across MOS 1.20, 2.00, 3.20, 3.50. (MOS 0.1 stores A at `&DE` instead of `&FC`, but the timing is the same.)
4. **Stage 3 — jitter compensation.**
   - Read the low byte of T1's latch (the count at the moment our handler started).
   - That tells us how late the IRQ was (jitter caused by the IRQ entry landing on different instructions of variable length in the interrupted code).
   - Use a lookup-driven delay loop to "spend the slack" so we always end at the same cycle relative to the raster.
   - Latch read is cycle-stretched, aligning us back to a 1 MHz boundary — that's why 1 MHz timer precision doesn't matter here.

### The jitter-compensation delay table

From the post — example for "low delay, low robustness":

| T1 latch on entry | Cycles to delay |
|---|---|
| `>&4DEA` | impossible (IRQ entered too early) |
| `&4DEA` | 6 |
| `&4DE9` | 4 |
| `&4DE8` | 2 |
| `&4DE7` | 0 |
| `<&4DE7` | we missed it (IRQ entered too late) |

Higher delay = more robustness (more slack window) at the cost of consuming more frame-time in the compensation step.

### Quirks captured in the thread

- **CMOS 6502 (e.g. Master)**: `JMP (&0204)` in the MOS IRQ handler is **1 cycle longer** than on NMOS 6502 (RichTW's correction). Stable-raster code that's tuned on a Model B will be 1 cycle off on a Master.
- **Random unexplained IRQs** persist even with ADC disabled, no keys pressed, and System VIA T1 sync'd to User VIA T1. hexwab notes "It would be good to know what they are" — no clear resolution in the thread.

## Filed into

- [[techniques/hexwab-stable-raster]] — new technique page (the canonical write-up).
- [[techniques/fx-framework]] — updated to point at this technique as the higher-precision alternative.
- [[sources/twisted-brain]] — open-followup pointing here resolved.

## Open follow-ups

- Identify the "random unexplained IRQs" that defeat naive stable-raster setups. Candidate sources: ACIA (RS423/cassette idle), light pen, network, sound-buffer-empty events. Worth a Stardot follow-up if anyone has scoped this.
- CMOS-6502 cycle-correct version of the timer-load constant. Currently the demo code is NMOS-tuned.
- Cross-platform comparison with Electron (DavidB in the thread asks about per-frame timing on Electron, which has different VIA-less timing fundamentals).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
