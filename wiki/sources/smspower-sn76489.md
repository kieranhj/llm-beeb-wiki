---
title: SMSPower — SN76489 reference (Maxim et al.)
type: source
tags: [source, sn76489, sound, smspower, lfsr, noise]
publisher: smspower.org
author: Maxim, with contributions from John Kortink, Charles MacDonald, Daniel Bienvenu, finaldave, blargg
year: 2002-2005
url: https://www.smspower.org/Development/SN76489
updated: 2026-08-15
---

# SMSPower — SN76489 reference

The community-canonical chip-level reference for the SN76489 PSG, primarily authored by **Maxim** between 2002 and 2005 on the SMS Power site. The BBC Micro is one of many systems explicitly covered — including the specific LFSR feedback taps that distinguish the BBC's chip variant from the Sega-integrated versions.

This is the **best public reference for the noise generator's exact bit-level behaviour**. Sega-specific PCM tricks documented here transfer almost directly to the BBC.

## Bibliographic

- **URL**: https://www.smspower.org/Development/SN76489
- **Primary author**: Maxim
- **Contributors**: John Kortink (initial results + BBC Micro noise data), Charles MacDonald (SMS1/GG/Genesis/SC-3000H noise sampling), Daniel Bienvenu (ColecoVision noise data, same as BBC), finaldave (LFSR implementation + SIMD parity), blargg (preprocessing techniques).
- **First wikified**: 1 May 2005
- **Latest changes shown**: 12 November 2005
- **Format**: Long single-page reference with diagrams, code snippets, dB tables, history log.

## Key technical claims (focus: noise generation, since this is what the wiki most needed)

### BBC Micro is the SN76489AN discrete chip, with 15-bit LFSR

> "It is used on many of Acorn's BBC and 'Business Computer' computers such as the BBC Micro."

The BBC uses the standard discrete **SN76489AN** — the same chip family as the Sega SG-1000, SC-3000, ColecoVision and Tandy 1000. The Sega Mark III / Master System / Game Gear / Mega Drive instead integrate a *modified* SN76489 into the VDP, which differs in the noise LFSR (16-bit) and may differ in DC behaviour for period ≤ 1 (see "Sample playback" caveat below).

### Internal clock divider

> "It divides this clock by 16 to get its internal clock. The datasheets specify a maximum of 4MHz."

Confirms 4 MHz / 16 = 250 kHz reference. The wiki's `hardware/sn76489.md` and the Master ARM are consistent with this.

### Register write protocol (precise bit layout)

> "If bit 7 is 1 then the byte is a LATCH/DATA byte.
> `%1cctdddd`
> Bits 6 and 5 (cc) give the channel to be latched, ALWAYS.
> Bit 4 (t) determines whether to latch volume (1) or tone/noise (0) data
> The remaining 4 bits (dddd) are placed into the low 4 bits of the relevant register.
> 
> If bit 7 is 0 then the byte is a DATA byte.
> `%0-DDDDDD`
> If the currently latched register is a tone register then the low 6 bits of the byte (DDDDDD) are placed into the high 6 bits of the latched register."

> "**The latched register is NEVER cleared by a data byte.**"

So after a tone-latch + data-byte sequence, the channel is still latched and additional data bytes will keep updating that channel's high 6 bits without re-latching. Useful for smooth frequency sweeps.

### Critical: tone registers update immediately

> "Also of note is that the tone registers update immediately when a byte is written; they do not wait until all 10 bits are written."

So during a two-byte tone update, between the latch byte and the data byte, the tone register holds a transient mixed value (low 4 bits = new, high 6 bits = old). For sample playback this matters — it means the chip is briefly outputting at a glitched frequency for ~16 µs.

### Noise register layout

3 bits, written via either:
- Latch byte `%1110dddd` (top bit of dddd discarded — only low 3 bits matter)
- Or data byte (only low 3 bits matter)

Bit 2 = mode (1 = white, 0 = "periodic"). Bits 1, 0 = shift rate.

### Noise channel counter reset values

> | Low 2 bits of register | Value counter is reset to |
> | 00 | 0x10 |
> | 01 | 0x20 |
> | 10 | 0x40 |
> | 11 | Tone2 |

So setting noise register low bits to `11` drives the noise rate from a tone generator's current frequency — the "modulated noise" mode that lets you sweep noise pitch dynamically.

⚠ **Numbering caution**: SMSPower's "Tone2" is **zero-indexed** (`cc`=`10`, register field `100`). In the NAUG/BBC labelling used by [[hardware/sn76489]] that same generator is called **Tone 1**. Translate via the register field, not the label.

### LFSR width and taps — varies per system

> "The LFSR is an array of either 15 or 16 bits, depending on the chip version"

> "For white noise (Noise register bit 2 = 1):
> 
> For the SMS (1 and 2), Genesis and Game Gear, the tapped bits are bits 0 and 3 ($0009), fed back into bit 15.
> For the SG-1000, OMV, SC-3000H, **BBC Micro** and Colecovision, the tapped bits are bits 0 and 1 ($0003), fed back into bit 14.
> For the Tandy 1000, the tapped bits are bits 0 and 4 ($0011), fed back into bit 14."

So the **BBC's SN76489AN uses a 15-bit LFSR with taps at bits 0 + 1 (mask `$0003`), feedback into bit 14**. Period of the white-noise sequence: 2^15 - 1 = 32767 bits.

BBC Micro noise data credited to **John Kortink** in the page history.

### "Periodic noise" is a duty-cycle modifier, not actual noise

> "For 'periodic noise' (Noise register bit 2 = 0):
> 
> For all variants, only bit 0 is tapped, ie. the output bit is also the input bit. The effect of this is to output the contents of the shift register in loop of the same length (16 bits for the SMS (1 and 2), Genesis and Game Gear, **15 bits for SG-1000, OMV, BBC Micro, SC-3000H, ColecoVision and Tandy 1000**; other systems need investigation)."

> "When the noise register is written to, the shift register is reset, such that all bits are zero except for the highest bit. This will make the 'periodic noise' output a 1/16th (or 1/15th) duty cycle, and is important as it also affects the sound of white noise."

So on BBC: writing the noise register resets the shift register to `100_0000_0000_0000`. In "periodic" mode (bit-0 self-feedback), this 1-in-15 bit pattern then circulates, producing a **square wave with 1/15 duty cycle**. That's not noise at all — it's a very thin pulse train. Frequency = base_noise_rate / 15.

Maxim explicitly flags the misnomer:

> "Note that this 'periodic noise', as it is called in the original chip's documentation, is in fact not periodic noise as it is defined elsewhere (white noise with a configurable periodicity); it is a duty cycle modifier."

### "Periodic noise" frequency range on BBC

Maxim's range calculation for 3.58 MHz NTSC clock gives 6.8 Hz to 6991 Hz. Scaling to BBC's 4 MHz: roughly 7.6 Hz to 7812 Hz (with tone 2 driving), shifted 4 octaves below the tone range.

### Volume / attenuation — 2 dB per step

> "The SN76489 attenuates the volume by 2dB for each step in the volume register."

> ```c
> int volume_table[16] = {
>   32767, 26028, 20675, 16422, 13045, 10362, 8231, 6568,
>   5193, 4125, 3277, 2603, 2067, 1642, 1304, 0
> };
> ```

Index = attenuation register value 0..15. Index 15 is hard-clamped to 0 (silence) regardless of the 2 dB rule. SMS1 and Mega Drive measure these values accurately; **SMS2 has a hardware design mistake that clips the top 3 volume levels**.

### Imperfect-output behaviour — explains how sample playback actually works

> "Wherever a voltage (output) is artificially held away from zero, there will be leakage and the actual output will decay towards zero at a rate proportional to the offset from zero"

> "If the tone register value is zero, the constant offset output will just decay to zero. However, whenever the volume of the output is changed, the constant offset is restored. **This allows speech effects.**"

This is the **physical mechanism** for sample playback that scarybeasts only partially explains. It's not just about the 125 kHz carrier being filtered out — it's that:
1. With tone register = 0 (or 1?), the chip output is a *constant DC* corresponding to the volume.
2. This DC decays toward 0 over time due to leakage (RC time constant in the analog chain).
3. **Volume writes refresh the DC** to the new level.
4. Rapid volume writes therefore reproduce the PCM envelope as a refreshed-DC sequence.

### Disputed claim: period 0/1 = DC vs square wave

> "If the register value is zero or one then the output is a constant value of +1. This is often used for sample playback on the SN76489."

> "(Note that this may be a feature of Sega's implementation of the SN76489. It does not appear in any Sega 8-bit code designed for older systems with the standard chip so it may need to be confirmed by experiment.)"

**Important contradiction with [[sources/scarybeast-sn76489-sampled]]**: scarybeasts measured a clean 125 kHz square wave at period = 1 on his real BBC, **not** a constant DC. The two views can reconcile:

- The Sega-integrated chips may genuinely emit DC at period ≤ 1 (different silicon).
- The discrete TI SN76489AN (BBC) emits a 125 kHz square wave at period = 1; the downstream low-pass strips the carrier and what reaches the speaker *is* effectively the volume-derived DC. So functionally the same end result via different chip-level paths.

For BBC implementation purposes either explanation works — the wiki documents both and notes the discrepancy.

### Sample playback methods documented (from Sega games — transferable to BBC)

1. **Simple 4-bit PCM**: nibble-packed data → emit as attenuation commands to one or more tone channels. Suffers from the non-linear (logarithmic 2 dB) volume response unless preprocessed.
2. **1-bit PCM**: max or silent volume only. Faithful but tiny dynamic range. Heavily clipped & amplified samples sound loud but distorted.
3. **8-bit PCM via lookup**: 8-bit input → table → triplet of attenuations for 3 channels emitted in close succession. Lookup table designed so the combined attenuations approximate the desired 8-bit value (despite non-linear per-channel response).

scarybeasts' multi-channel mixer (see [[techniques/sampled-sound]]) is a runtime-mixed extension of method 3 with a per-mix-sample 8→4-bit LUT.

### Preprocessing recommendations (blargg)

> "Preprocessing of the data to have a low-frequency DC offset can allow moving the range of the high-frequency waveform into the area of the non-linear response where the precision is greater. This can particularly help with samples with a large dynamic range."

scarybeasts' "zero-level drift" pre-processing in his Lotus song write-up implements something like this.

### Sampling rates seen in Sega games

> "The lowest quality audio seen in games is around 4kHz at 1 bit, which can fit 32.8s of audio in 16KB.
> The highest is around 21kHz at 4 bits, which can fit 1.6s of audio in 16KB."

For comparison: scarybeasts' BBC demos do **62.5 kHz raw chip writes** with internal mixing producing **12.5-15 kHz effective output sample rate × 3-4 channels**. The 21 kHz Sega rate is single-channel; scarybeasts' technique is strictly more advanced.

## Filed into

- Extended [[hardware/sn76489.md]] significantly — added the full noise-generator section (15-bit LFSR, BBC's $0003 white-noise tap mask, periodic-noise duty-cycle clarification, counter reset values per noise-rate setting); added the SMSPower volume reference table; clarified the period-0/1 DC-output behaviour (with the Sega-vs-discrete-chip ambiguity flagged); added the "voltage decay + volume writes refresh DC" mechanism that makes sample playback work physically.
- Cross-referenced from [[techniques/sampled-sound]] in the "How it works" section.

## See also

- [[hardware/sn76489]] — chip-level reference (significantly extended from this source).
- [[techniques/sampled-sound]] — sample-playback technique reference (1980s + scarybeasts' modern 62.5 kHz multi-channel).
- [[sources/scarybeast-sn76489-sampled]] — 2020 BBC-specific PCM analysis (period-1 carrier vs SMSPower's period-1 DC claim — both views reconcile to same audible result).
- [[sources/stardot-sn76489-sampled]] — 2025 scarybeasts demos applying the multi-channel-attenuation technique on BBC.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
