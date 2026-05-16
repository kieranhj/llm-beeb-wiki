---
title: "scarybeastsecurity — Sampled sound, 1980s style, from the SN76489"
type: source
tags: [source, blog, sn76489, sound, sample, pcm]
publisher: scarybeastsecurity.blogspot.com
author: Chris Evans (scarybeasty)
year: 2020
url: https://scarybeastsecurity.blogspot.com/2020/06/sampled-sound-1980s-style-from-sn76489.html
updated: 2026-05-16
---

# Sampled sound, 1980s style, from the SN76489

Chris Evans's June 2020 blog post analysing **how the SN76489 — a 1980 square-wave-only sound chip — was made to play digital audio samples on machines like the BBC Micro, Sega Master System, and the Coleco/TI 99**. The author developed `sampstream`, a BBC Micro tape/disc-streamed sample player that demonstrates the technique on real hardware.

This is a primary-source analytical write-up: oscilloscope traces, signal-path tracing, and direct hardware experimentation. Not a how-to tutorial — there's no code listing — but the technique explanation is rigorous and includes downstream analog-chain detail that's missing from most BBC sound documentation.

## Bibliographic

- **URL**: https://scarybeastsecurity.blogspot.com/2020/06/sampled-sound-1980s-style-from-sn76489.html
- **Author**: Chris Evans ("scarybeasty"), security researcher and Beeb demoscene experimenter (author of the *jsbeeb* and *beebjit* emulators referenced elsewhere in the wiki).
- **Date**: June 2020
- **Format**: Blog post with embedded oscilloscope photos and YouTube/SoundCloud audio clips.

## Filed into

- Created [[techniques/sampled-sound]] — wiki page documenting the carrier-modulation technique end-to-end with BBC-specific implementation notes.
- Refined [[hardware/sn76489]] — added the 4 MHz clock input fact (with reference to Master ARM Ch 1 as primary source); added the analog-chain downstream stages (LM324N, LM386N-1, normalising network); flagged the ~8 kHz LM324N low-pass as a possible explanation for high-frequency-tone distortion seen by the author.

## Key technical claims

### The technique itself

> "The usual basis of sampled sound playback is driving the SN76489 as a PCM device, i.e. a sequence of sample amplitude values."

> "The PCM stream is modulated simply by rapidly altering the volume of the 125kHz wave"

The mechanism: set one tone channel to **period = 1** (so the chip emits a 125 kHz square wave), then write a stream of 4-bit volume values to that channel's attenuator. Each different volume produces a different DC offset in the 125 kHz signal. The downstream analog chain (LM324N op-amp + LM386N-1 + speaker normalisation) low-pass-filters away the 125 kHz carrier and leaves the PCM envelope on the speaker.

> "The key for sample playback is likely that the mid-point voltage differs for each volume."

So **the volume DAC is the sample output**. There's no special sample register on the chip — you abuse the attenuator.

### Clock input (disputed in comments — Master ARM is authoritative)

The blog says:

> "In the BBC Micro, the clock input to the sound chip is 2MHz and it has an internal divide-by-8, making it a 250kHz device."

**This is wrong.** [[sources/master-arm]] Ch 1 (page 16): *"It receives a reference clock of 4MHz from central timing."* The SN76489 internal divider is **÷16**, not ÷8 — so 4 MHz ÷ 16 = 250 kHz reference. Both descriptions land at the same 250 kHz internal rate, but the input clock is 4 MHz. A commenter on the post raised this point against the Master schematic; the author did not amend the main text.

Either way: period = N gives `reference ÷ 2 ÷ N` Hz output. Period 1 = 125 kHz. Period 0 is *undefined* (some clones treat as 1024).

### Downstream analog chain (the bit usually missing from BBC docs)

> "There's some extra ciruitry between the LM386N-1 and the speaker, to keep the speaker happy. It normalizes the oscillation around the positive voltage point"

Per the author's signal tracing, the SN76489 output passes through:
1. **LM324N** op-amp (quad). Likely contains an ~8 kHz low-pass.
2. **LM386N-1** audio power amplifier.
3. Post-amp DC-normalising network for the speaker.

Evidence for the LM324N low-pass: an 8 kHz square wave from the chip emerges as nearly a sine wave, not a square — characteristic of a filter rolling off in that band.

### Signal levels

- 125 kHz square wave from the chip: 720 mV peak-to-peak, centred ~3.3 V (not symmetric around 0).
- The asymmetric centring is what enables PCM modulation via volume changes — each attenuator level shifts the centre.

### Why sample playback is comparatively quiet

> "This is likely one reason sampled sound playback is relatively quiet."

The PCM signal is the difference between different DC offsets — a fraction of the full square-wave amplitude. After low-pass filtering, only that smaller fraction reaches the speaker.

### What the author's `sampstream` demo achieves

- Custom disc loader that auto-detects 8271 (Model B) vs WD1770 ([[hardware/wd1770]]) controller.
- Real-time 50 Hz oscilloscope view on screen.
- "Near instant start and uninterrupted 400 KB of sample playback" (i.e. continuous streaming from disc).
- Acknowledged not using best-in-class pre-processing or compression.

### Prior art mentioned

- **Spy Hunter** (arcade) — early example of sampled speech on the SN76489.
- **Galaforce** and **Icarus** (BBC Micro) — creative tone-channel use.
- **pcmenc project** — state-of-the-art today; uses multi-channel balancing and mid-point correction to fight 4-bit resolution limits.
- **SMS Power** — community resource on SN76489 deep details.
- **MAME SN76489 driver source** — for chip variants.

### Compatibility commentary

Some references claim the SN76489 can't hold a steady square wave for long periods. The author refutes this with oscilloscope evidence:

> "Some references state that the SN76489 cannot hold a steady square wave output, particularly for longer periods. However, this is clearly not true — at least for this variant."

### Quality / quote on emulation accuracy

> "the sample playback quality on a 1980 chip is obviously not too badly mangled because YouTube content ID recognizes emulator recordings"

Real hardware: "less harsh and louder" than emulators (per the author).

## What's missing from the article

- **No code listing.** The author doesn't walk through the assembly of his player. The wiki's [[techniques/sampled-sound]] page reconstructs the implementation pattern from the [[hardware/sn76489]] write-protocol and [[hardware/system-via]] slow-bus dance.
- **No sample rate quoted.** The 400 KB / disc-stream figure implies multi-minute playback at modest rates, but neither the achievable sample rate nor the bus-bandwidth bottleneck is computed in the post.
- **No T1-timing recipe.** [[timing/via-timers]] T1 free-run is the natural way to drive sample-rate-locked writes; the author doesn't discuss it.
- **No comparison vs DAC-cartridge approaches** (Music 5000, Acornsoft speech). Those bypass the SN76489 entirely.

## See also

- [[hardware/sn76489]] — chip-level reference, including 4 MHz clock input + slow-bus write protocol.
- [[techniques/sampled-sound]] — implementation pattern derived from this source + the SN76489 page.
- [[sources/stardot-sn76489-sampled]] — 2025 follow-on Stardot threads: the persistent-`/WE` 62.5 kHz write trick + scarybeasts' multi-channel sampled-song demos building on this 2020 piece.
- [[hardware/system-via]] — slow data bus, the bottleneck for SN76489 writes.
- [[timing/via-timers]] — T1 free-run as the natural sample-rate clock.
- [[reference_emulator_accuracy]] (memory) — author Chris Evans is the *jsbeeb* / *beebjit* author.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
