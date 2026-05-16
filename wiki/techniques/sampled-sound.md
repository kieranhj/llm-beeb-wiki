---
title: Sampled (PCM) sound playback on the SN76489
type: technique
tags: [sound, sn76489, sample, pcm, slow-bus, scarybeasts, t1]
sources: [scarybeast-sn76489-sampled, stardot-sn76489-sampled, master-arm]
updated: 2026-05-16
---

# Sampled (PCM) sound playback on the SN76489

The SN76489 is a 1980 square-wave-and-noise chip — it has **no DAC, no sample register, and no PCM mode**. Yet BBC, Sega Master System, and TI 99/4A coders have been getting recognisable digital audio out of it since the early '80s (Spy Hunter's speech samples being the canonical first example).

This page covers two generations of the technique:

1. **The 1980s technique** — single-channel PWM-via-volume, period-1 carrier, manual loop, ≤8 kHz.
2. **scarybeasts (2025)** — persistent-`/WE` 62.5 kHz write rate, software-mixed 3-4 channel playback, Amiga-MOD-comparable quality. Documented in [[sources/scarybeast-sn76489-sampled]] (2020 physics analysis) + [[sources/stardot-sn76489-sampled]] (2025 demos).

For the chip-level reference (registers, write protocol, clock) see [[hardware/sn76489]]. For the slow-bus mechanics see [[hardware/system-via]].

## How it works — the carrier-modulation trick

The technique exploits a specific physical accident of the SN76489 + downstream-analog combination on BBC:

1. Set one tone channel to **period = 1** → chip emits a 125 kHz square wave (`reference ÷ 2 ÷ N = 250 kHz ÷ 2 ÷ 1`).
2. 125 kHz is ultrasonic — way above any audible range and above the LM324N's ~8 kHz low-pass.
3. The square wave has an **asymmetric DC centring** that depends on the channel's volume attenuator (720 mV pp, centred ~3.3 V at max volume per scarybeasts' oscilloscope traces).
4. **Changing the volume changes the DC midpoint** of the carrier.
5. The downstream low-pass (LM324N stage) strips out the 125 kHz carrier entirely, leaving only the DC-offset envelope on the speaker.
6. Write a stream of 4-bit volume values to the channel → the chain reproduces the envelope as audio.

So **the volume DAC is the sample output**. There is no special PCM register; you're abusing a side effect of the attenuator.

## The 1980s technique (single-channel ≤ ~8 kHz)

### Setup

```asm
; Silence noise + tones 2,3 so only tone 1's carrier is active
SEI                        ; own the slow bus

LDA #&9F : JSR snwrite     ; tone 1 volume = OFF  (silence)
LDA #&BF : JSR snwrite     ; tone 2 volume = OFF
LDA #&DF : JSR snwrite     ; tone 3 volume = OFF
LDA #&FF : JSR snwrite     ; noise volume = OFF

; Set tone 1 to period 1 (125 kHz carrier)
LDA #&81 : JSR snwrite     ; latch byte: tone 1 freq low nibble = 1
LDA #&00 : JSR snwrite     ; data byte: high 6 bits = 0
                           ; → 10-bit divider = 0b0000000001 = 1

; Now we're ready: write &90..&9F to set tone 1 volume = 0..15
; (note: SN76489 volume is inverted — &90 = max, &9F = silent)
CLI
```

`snwrite` is the standard latch-pulse-on-line-0 dance — see [[hardware/sn76489]] "Direct-write sequence". Each call costs ~30 cycles + the ~8 µs latch hold.

### Inner loop (polled)

```asm
; X = sample index; sample data is byte stream of pre-shifted volume bytes (&90-&9F)
.play_loop
    LDA samples,X
    STA &FE41              ; bus = volume byte
    LDA #&00 : STA &FE40   ; /WE low
    JSR delay_8us
    LDA #&08 : STA &FE40   ; /WE high
    INX
    BNE play_loop
```

Per sample: ~30+ cycles for the latch dance + 8 µs `/WE` hold = ~16 µs absolute minimum per sample → **62.5 kHz hard ceiling** (and lower in practice once you add sample-fetch + loop overhead). Realistic 1980s rates: 4-8 kHz with a fully unrolled inner loop, more like 2-4 kHz with sample-source decoding (e.g. CFS streaming).

### T1-based sample-rate clock (recommended for steady rate)

For a fixed sample rate independent of the host code, use User VIA T1 in free-run mode ([[timing/via-timers]]):

```asm
; Set up User VIA T1 for 8 kHz sample interrupt
LDA #&C0 : STA &FE6E       ; enable T1 IRQ
LDA #<(125-2) : STA &FE66  ; T1 low (125 cycles at 1 MHz = 125 µs = 8 kHz)
LDA #>(125-2) : STA &FE67  ; T1 high
LDA #&40 : STA &FE6B       ; ACR bit 6 = 1: T1 free-run continuous interrupts
```

Hook IRQ1V to a sample-fetch + chip-write routine. T1 underflows reload automatically. See [[techniques/fx-framework]] for the SEI + T1 free-run pattern used in demos.

## The 2025 technique (scarybeasts — persistent-/WE, 62.5 kHz, multi-channel)

Per [[sources/stardot-sn76489-sampled]] t=30838, hoglet:

> "allow multiple successive writes to occur if the WR_N signal was held continuously low"

### The persistent-/WE trick

Instead of pulsing `/WE` per write, hold it low **once** at start of playback and never release it. The chip latches each new byte on Port A as the bus stabilises — provided you maintain ~9 µs alignment per write (the SN76489 has an internal sampling cadence).

```asm
; Setup: silence other channels, set tone 1 period = 1 as before
; ...

; Hold /WE low PERMANENTLY for the duration of playback
LDA #&00 : STA &FE40       ; PB0-2 = 0 (line 0), PB3 = 0 (low)
                           ; latch-line value driving /WE is now 0 indefinitely

; Inner loop is just: STA &FE41 + cycle-pad to 16 µs per write
; (NO more &FE40 toggling per write — that's the win)
.play_loop
    LDA samples,X
    STA &FE41              ; bus = volume byte → chip latches at ~9 µs into the 16 µs window
    ; cycle-pad to 16 µs total per iteration (32 cycles at 2 MHz)
    INX
    BNE play_loop
```

Per write at 2 MHz CPU: ~16 µs = 32 cycles. Out of those 32 cycles you need:
- 4c `LDA samples,X` (or 4c `LDA (zp),Y` if streaming from a bigger buffer)
- 4c `STA &FE41` (+stretching → 5-6c in practice — `&FE41` is a stretched address)
- ~3-4c for whatever decimation / mixing computation
- ~18-20c headroom for software mixing

So the 32-cycle budget per chip write is **just enough** to run a software mixer at decimation-4 (= one mixed output sample every 4 chip writes = 15.625 kHz mixed rate) or decimation-5 (= 12.5 kHz mixed).

### Multi-channel software mixing (12.5 kHz × 4-ch / 15 kHz × 3-ch)

The SN76489 still has only one PCM output channel (one tone's volume DAC). All multi-voice mixing happens **on the 6502** before each chip write:

```text
For each chip write at 62.5 kHz:
  output = clamp((voice0[i0] + voice1[i1] + voice2[i2] + voice3[i3]) / 4)
  output_nibble = volume_lookup[output]   ; 8-bit → 4-bit via LUT
  write output_nibble to chip
```

scarybeasts' actual implementation uses runtime lookup tables for the 8-bit → 4-bit squish (handling per-instrument gain, midpoint adjustment, and the SN76489's non-linear attenuator curve in one step).

Per [[sources/stardot-sn76489-sampled]] t=31654:

> "The squishing of 8-bit into 4-bit values is done at runtime, again with lookup tables."

Per-voice pointer advance happens every 4 or 5 chip writes (depending on output sample rate). Pre-decimating samples to 12.5 / 15 kHz beforehand reduces the per-write work.

### Storage trade-offs

- **Lotus title song**: ~all RAM consumed by samples. From tape impractical without explicit load pauses.
- **Compression**: noted as a future improvement — sample streams suspected highly compressible.
- **Generated waveforms**: square / saw / sine generated on-the-fly are free.
- **Looped short samples** (1-2 KB each): bass, organ, sax samples cycled for melodic instruments — TFMX-style sample reuse.
- **Same sample at different offsets**: also TFMX-style; gives multiple "voices" from one sample buffer.

## Sample pre-processing (per scarybeasts)

For best fidelity with 4-bit output:

| Adjustment | Why |
|---|---|
| **Per-instrument gain** | 2× gain on quiet samples (slap bass) lifts them above the SN76489's noise floor before quantisation |
| **Zero-level drift** | Centring each sample's DC to match the SN76489's non-linear attenuator midpoint reduces audible distortion |
| **Magnitude-axis flip** | For samples whose magnitude detail lives in the positive half, flipping preserves it after 4-bit quantisation |
| **No dithering mentioned** | But would be worth trying — could mask quantisation noise at low signal levels |

scarybeasts does the 8-bit → 4-bit quantisation **at runtime** via lookup tables, not in pre-processing. This lets the same sample source play through different per-voice mixing settings.

## Quality

Per [[sources/stardot-sn76489-sampled]] t=31654:
- On **external amplifier** (good speakers): "very hard to tell any difference" between BeebFPGA and real Master. Quality comparable to Amiga MOD-style 4-channel sample playback.
- On **internal BBC speaker**: low frequencies "mostly stripped" by the LM324N 8 kHz low-pass + speaker normalisation network. Lotus slap bass loses impact; high-frequency hiss becomes audible.
- **Effective audio bandwidth** through the BBC analog chain: ~16 kHz max (per hoglet's polyphase analysis in BeebFPGA).

For comparison: the technique is **strictly better than ZX Spectrum beeper music** (1-bit) and **comparable to Commodore 64 SID sample mode** (4-bit volume DAC tricks). It is **not as good as an Amiga**'s native 8-bit Paula channels but it is the same family of effect at a coarser resolution.

## Limitations

- **Bus bandwidth is the hard ceiling**: 62.5 kHz writes consume essentially all 6502 cycle budget. You can't render game graphics + run music engine + play samples in parallel; sample playback either pauses or dominates.
- **Built-in speaker mangles low frequencies**: a hardware limit. External amp / line out required for the full quality.
- **Sample data is hungry**: ~12.5 kB/s × 4 channels mixed → 50 kB/s of source data if uncompressed. Streaming from CFS (cassette) ~1.2 kbit/s = 150 B/s = totally impractical; from DFS at ~125 kB/s = workable with double-buffering.
- **MOS interference**: SEI + own the slow bus for the entire duration. MOS sound, keyboard scan, ADC, RTC, vsync IRQ — all suppressed while playing. Most demos disable VDU output too ([[techniques/custom-modes]] blanking pattern).

## When to reach for this

- **Demos** wanting genuine PCM speech / drums / instruments rather than synthesised chip sounds. Modern bar: scarybeasts-style 3-channel mixed playback.
- **Speech samples** (Spy Hunter pattern) — short, low-rate, fire-and-forget.
- **Sound effects** that can't be synthesised (explosions, voice clips). One-shot at lower rates is much cheaper.
- **Music engines** that want to layer real sample drums over chip-channel melody — keep one chip channel for samples, leave 2 for chip melodic, accept the 100% CPU cost during sample playback.

## When *not* to use it

- **In-game background music** unless your game can spare 100% CPU. Most BBC games use the chip's native 4-channel SOUND for music to keep cycles for gameplay.
- **High-fidelity audio** (>16 kHz bandwidth, full dynamic range) — wrong machine. Use a sampling cartridge (Music 5000, Sound Sampler) for actual hi-fi.
- **Long ambient tracks** — the storage cost dominates. Tracker-style (chip music + short sample stabs) is more economical.

## See also

- [[hardware/sn76489]] — chip-level reference (registers, clock, downstream analog chain).
- [[hardware/system-via]] — slow-bus protocol; the latch-pulse dance the persistent-`/WE` trick optimises away.
- [[timing/via-timers]] — User VIA T1 for sample-rate clocking.
- [[techniques/fx-framework]] — SEI + own-the-machine pattern from demo work.
- [[os/sound]] — MOS sound API (the path you bypass entirely for sample playback).
- [[sources/scarybeast-sn76489-sampled]] — 2020 blog laying out the physics.
- [[sources/stardot-sn76489-sampled]] — 2025 Stardot threads with the 62.5 kHz trick + multi-channel demos. **Source code at github.com/scarybeasts/misc/tree/master/beebmod/**.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
