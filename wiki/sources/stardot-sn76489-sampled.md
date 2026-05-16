---
title: Stardot — scarybeasts' SN76489 PCM playback threads (2025)
type: source
tags: [source, stardot, sn76489, sound, sample, pcm]
publisher: stardot.org.uk
author: Chris Evans (scarybeasts) + various
year: 2025
url: https://stardot.org.uk/forums/viewtopic.php?t=30838, https://stardot.org.uk/forums/viewtopic.php?t=31654
updated: 2026-05-16
---

# Stardot — scarybeasts' SN76489 PCM playback threads (2025)

Two Stardot threads by Chris Evans / "scarybeasts" that build on his [[sources/scarybeast-sn76489-sampled|2020 blog post]]:

1. **t=30838** (April 2025) — bus-side behaviour analysis: discovers that **holding `/WE` continuously low across consecutive writes works reliably**, halving the per-sample bus dance and enabling **62.5 kHz sustained write rate** (one byte every 16 µs).
2. **t=31654** (September 2025) — applies the 62.5 kHz write technique to produce the first BBC PCM playback demos with comparable quality to MOD-style 4-channel mixed-sample audio: **12.5 kHz × 4-channel and 15 kHz × 3-channel** mixed playback of Amiga-era tunes (Lotus Esprit Turbo Challenge, Chaos Engine, Escape from Planet of Robot Monsters).

These two threads together are the **current canonical reference for high-quality PCM playback on BBC SN76489**, superseding all earlier techniques (which were typically single-channel ≤ ~8 kHz).

## Bibliographic

- **t=30838 — "SN76489 sound chip bus-side behaviour"**: started 2025-04-04 by scarybeasts. Documents the 62.5 kHz sustained-write discovery with `sn_test.ssd` / `SNLEVEL` test program. hoglet contributed FPGA verification.
- **t=31654 — "BBC SN76489 sampled song playback demos"**: started 2025-09-09 by scarybeasts. Posts demo `.ssd` files + YouTube links. Contributions from hoglet (BeebFPGA verification, "very hard to tell any difference" vs real Master), Matt Godbolt (jsbeeb fixes triggered by the demos), dominicbeesley (C20K FPGA implementation with user-controllable HPF).
- **Source code**: https://github.com/scarybeasts/misc/tree/master/beebmod/

## Key technical claims

### 62.5 kHz sustained write rate via persistent /WE-low (t=30838)

> "It is writing one new byte to the chip every 16us which is a rate of 62.5kHz."

> "There are a few references across the internet that discuss leaving WE active on a SN76489. Some say it's reliable and some say it's not. I think it is reliable if you are careful."

hoglet's verification:

> "allow multiple successive writes to occur if the WR_N signal was held continuously low"

Mechanism: instead of the textbook latch-pulse cycle (drive bus, pulse `/WE` low, hold ≥8 µs, pulse `/WE` high, repeat), you set `/WE` low **once** and then just drop new bytes onto Port A at 16 µs intervals. The chip latches each on the rising edge of its internal sampling — provided the bus value is stable when the chip samples (the "9 µs alignment" mentioned in t=30838). Saves the latch-line addressable-latch dance per write, which is the bulk of the slow-bus cost.

### Resulting playback rates (t=31654)

| Demo | Rate | Channels |
|---|---|---|
| Lotus Esprit Turbo Challenge title song | **12.5 kHz** | 4-channel mixed |
| Chaos Engine subsongs 4, 11 | **15 kHz** | 3-channel mixed |
| Escape from Planet of Robot Monsters | **15 kHz** | 3-channel mixed |

These are MOD-tracker-style mixed multi-channel samples — the SN76489 still only has one PCM channel (the volume DAC of one tone channel), so **all multi-channel mixing happens in software** on the 6502 before each sample byte is written. Inner loop runs at 62.5 kHz (= the bus rate) with a 4× or 5× decimation per output sample.

### Sample pre-processing (t=31654, Lotus song write-up)

> "The squishing of 8-bit into 4-bit values is done at runtime, again with lookup tables."

Per-instrument adjustments:
- Slap bass: 2× gain for SNR
- Bass/snare drums: zero-level drift to match SN76489 output curve
- Guitar: magnitude-axis flip to preserve detail

### Storage trade-offs (t=31654)

- **Lotus** consumes all available RAM — impractical from tape without strategic loading pauses.
- Alternative approaches noted: compress samples (suspected highly compressible), use generated waveforms (square/saw), short 1-2 KB looped samples (bass / organ / sax), play same sample at different offsets (TFMX-style reuse).

### Hardware limits

- **Built-in BBC speaker is the bottleneck.** Low frequencies (Chaos Engine bassline) "mostly stripped by the speaker and the circuitry that immediately precedes it" — the LM324N 8 kHz low-pass + speaker normaliser ([[hardware/sn76489]]) butcher the bass.
- External amplifier (Monitor Audio Airstream A100 in hoglet's case) needed to hear the full quality.
- BeebFPGA "very hard to tell any difference" vs real Master — establishes that the technique is hardware-honest, not an emulator artefact.

### Emulator support (t=31654)

Recommended emulator order (as of 2025-09):
1. **b-em** — works out of the box
2. **beebjit** — needs HEAD from master
3. **b2** — needs HEAD from `wip/master`

Other emulators produce poor audio. Matt Godbolt explicitly committed to fixing jsbeeb after seeing the demos.

### Cross-references made in-thread

- Cinter (Amiga 4K demo scene synth) — https://github.com/askeksa/Cinter
- Sarah's NES Castlevania player thread — viewtopic.php?t=18290
- pcmenc — already referenced in [[sources/scarybeast-sn76489-sampled]]

## What's still missing from primary sources

- **No cycle-by-cycle inner-loop kernel** posted in either thread; the GitHub repo holds it.
- **No formal SNR / THD measurements** — quality is reported subjectively.
- **No explicit "how to silence the other channels" recipe** — implicit in the multi-channel mixer (other tone channels' volumes are set to off; the noise channel is similarly off).

## Filed into

- Created [[techniques/sampled-sound]] — synthesises the 2020 blog (carrier-modulation physics) + the two 2025 threads (62.5 kHz persistent-`/WE` trick + 4-channel software mixing achieving Amiga-MOD-equivalent quality) into one wiki technique page.
- Extended [[hardware/sn76489]] — added the persistent-`/WE` write pattern as a high-performance alternative to the textbook latch-pulse dance.

## See also

- [[sources/scarybeast-sn76489-sampled]] — the 2020 blog laying out the physics.
- [[techniques/sampled-sound]] — the implementation pattern derived from these three sources.
- [[hardware/sn76489]] — chip-level reference (clock, registers, write protocols).
- [[hardware/system-via]] — slow-bus dance (the persistent-`/WE` trick is a slow-bus optimisation).
- [[reference_emulator_accuracy]] — relevant emulator status as of 2025-09 per hoglet/Godbolt.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
