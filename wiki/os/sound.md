---
title: MOS Sound Interface
type: os
tags: [sound, osword, envelope, bell]
sources: [naug-ch21-sound]
updated: 2026-05-13
---

# MOS Sound Interface

The MOS-level sound API: `OSWORD &07` (SOUND), `OSWORD &08` (ENVELOPE), suppression OSBYTEs, BELL. For direct chip writes, see [[hardware/sn76489]].

## OSWORD `&07` — SOUND

```asm
LDX #params MOD 256
LDY #params DIV 256
LDA #&07
JSR &FFF1
```

Parameter block (8 bytes, all 16-bit little-endian):

| Offset | Field |
|---|---|
| 0-1 | Channel |
| 2-3 | Amplitude |
| 4-5 | Pitch |
| 6-7 | Duration |

### Channel encoding

The 16-bit channel value carries more than just "which channel":

- Low nibble (bits 0-3): channel number 0-3 (0 = noise, 1-3 = tones).
- High bits: flush / sync / queue control:
  - `&00xx` — queue normally.
  - `&FFxx`, `&FExx`, `&FDxx`, `&FCxx` — speech-channel codes (when speech hardware present, channel goes to the speech chip via OSBYTE `&9F`).
  - Bits in the top byte select "flush before queueing", channel sync, and (on speech) phrase selection.

NAUG §21.1.1 p372 documents the parameter shape but defers to the BASIC User Guide for the full encoding semantics. Capture more if needed.

### Amplitude

`&FF00`-`&FF0F` = BASIC amplitudes -15..-0 = chip volumes 15..0. Or pass an **envelope number** (1-16) in the amplitude field to attach an ENVELOPE to this sound.

### Pitch

Frequency, 0-255. BBC pitch unit ≈ 1/4 semitone. Pitch 0 = ~7 Hz, pitch 255 ≈ Hz to come. The MOS converts pitch to the 10-bit divider N for the chip ([[hardware/sn76489]]).

### Duration

Length in 20 ms units (1/50th sec). -1 = play indefinitely.

## OSWORD `&08` — ENVELOPE

```asm
LDX #params MOD 256
LDY #params DIV 256
LDA #&08
JSR &FFF1
```

14-byte parameter block — same 14 parameters as BASIC's `ENVELOPE` command (envelope number, step length, pitch slopes, amplitude slopes, etc.). NAUG defers the full breakdown to the User Guide.

After definition, the envelope is referenced by number in the amplitude field of `OSWORD &07`.

## Sound suppression

| OSBYTE | Function | Encoding |
|---|---|---|
| `&D2` (210) | Sound on/off | 0 = enabled (default); ≠0 = disabled. Standard `<NEW>=(<OLD> AND Y) EOR X`. |
| `&D1` (209) | Speech on/off | `&50` (SPEAK) = enabled, `&20` (NOP) = disabled. |
| `&EB` (235) | Speech presence | Read-only effectively; 0 = absent, `&FF` = present. |

## CTRL-G BELL parameters

The `&07` ASCII bell. Configured via:

| OSBYTE | Field | Default |
|---|---|---|
| `&D3` (211) | Channel | 3 |
| `&D4` (212) | Amplitude / envelope | 144 (`(-13 - 1) * 8 + 256 = 144`, envelope 0 = amplitude -13) |
| `&D5` (213) | Frequency / pitch | 100 |
| `&D6` (214) | Duration | 6 |

NAUG §21.1.7 p374 documents the amplitude encoding: `((amp_or_env - 1) * 8) mod 256`, with low 3 bits = H/S parameters of the channel.

## Sound buffer ↔ chip pipeline

1. `OSWORD &07` parses parameters, enqueues into the appropriate **channel buffer** (4-7, [[os/buffers]]).
2. **100 Hz IRQ** (System VIA T1, [[os/interrupts]]) services buffers:
   - Pulls next note.
   - Applies envelope (pitch + amplitude steps).
   - Writes to the SN76489 via the slow-bus dance ([[hardware/sn76489]]).
3. Note plays for its duration; envelope continues stepping per 100 Hz tick.

Latency from `OSWORD &07` to first audible output: **up to 10 ms** (next 100 Hz tick). For lower latency, write the chip directly ([[hardware/sn76489]]).

## When to bypass MOS

| Use case | Path |
|---|---|
| BASIC-style music, simple SFX | `OSWORD &07` + `OSWORD &08` |
| Game sound with envelopes | Mostly `OSWORD &07`; reserve channel 0 for direct hits |
| Sample playback (PCM-ish) | Direct [[hardware/sn76489]], timer-driven |
| Custom music engine (tracker / SID-style) | Mostly direct |
| Sub-frame-timed FX | Direct |

The 100 Hz envelope step is the speed ceiling for MOS-driven sound. Anything faster needs direct chip writes paced by a VIA timer.

## See also

- [[hardware/sn76489]] — Chip-level reference.
- [[hardware/system-via]] — Slow-bus protocol (sound /WE on latch line 0).
- [[os/buffers]] — Channel buffers 4-7.
- [[os/interrupts]] — 100 Hz T1 IRQ that services the buffers.
- [[timing/via-timers]] — Timer-driven direct sound writes.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
