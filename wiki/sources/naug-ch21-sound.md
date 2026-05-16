---
title: NAUG Ch21 — Sound / Speech
type: source
parent: [[sources/naug]]
pages: 379-386
section: §21
tags: [sound, sn76489, speech, oswords, slow-bus]
updated: 2026-05-13
---

# NAUG Ch21 — Sound and Speech

Holmes & Dickens, *The New Advanced User Guide*, pp.379-386. The BBC's **TI SN76489** sound generator (3 tone channels + 1 noise) sits on the slow peripheral bus, driven by the System VIA's Port A + addressable-latch line 0. Speech (Model B / B+) is a separate optional chip.

## Sound system overview

- **76489** sound chip: 3 tone generators + 1 white-noise generator, mixed on-chip. Volume per channel (0-15, **0 = max**, 15 = off).
- MOS provides a high-level `SOUND`/`ENVELOPE` interface via OSWORDs that enqueues sound events into the 4 channel buffers (IDs 4-7, see [[os/buffers]]).
- The **100 Hz IRQ** (System VIA T1, [[os/interrupts]]) services those buffers — pulls the next byte, applies envelope, writes to the chip.
- For maximum control / minimum overhead, write the chip directly via the slow peripheral bus. NAUG gives a worked example (§21.3 p378).

## MOS interface

### OSWORD `&07` — SOUND

Equivalent to BASIC's `SOUND chan, amp, pitch, dur`. 8-byte parameter block:

| Offset | Bytes | Field |
|---|---|---|
| 0-1 | 2 | Channel |
| 2-3 | 2 | Amplitude |
| 4-5 | 2 | Pitch |
| 6-7 | 2 | Duration |

All four parameters are 16-bit little-endian, even though the underlying chip only takes 4-bit amplitudes — the high bits select special behaviour (envelope, sync-channels, etc.).

### OSWORD `&08` — ENVELOPE

14-byte parameter block — the 14 envelope parameters in the same order as BASIC's `ENVELOPE` command.

### Suppression / status OSBYTEs

| OSBYTE | Function | Notes |
|---|---|---|
| `&D2` (210) | R/W sound suppression | non-zero = sound disabled |
| `&D1` (209) | R/W speech suppression | `&50` = SPEAK opcode (enabled, default), `&20` = NOP (disabled) |
| `&EB` (235) | R/W speech-present flag | 0 = absent, `&FF` = present |
| `&D3`-`&D6` | R/W BELL parameters | channel / amp / freq / duration (`CTRL-G` sound) |
| `&18` (24) | Select external sound (Electron only) | — |
| `&E8` (232) | R/W external sound semaphore (Electron only) | — |
| `&74` (116) | Reset Electron sound system | Electron only; no-op on B+/Master; error on Model B |
| `&9E`/`&9F` | Read/write speech processor (Model B only) | direct chip access |

## The SN76489 — chip-level reference

### Register addressing (3-bit field within each command byte)

| R2 R1 R0 | Register |
|---|---|
| 0 0 0 | Tone 3 frequency |
| 0 0 1 | Tone 3 volume |
| 0 1 0 | Tone 2 frequency |
| 0 1 1 | Tone 2 volume |
| 1 0 0 | Tone 1 frequency |
| 1 0 1 | Tone 1 volume |
| 1 1 0 | Noise control |
| 1 1 1 | Noise volume |

NAUG calls the tone generators "Tone 1/2/3" and these map to BBC channels 1, 2, 3. Channel 0 in BBC numbering = noise.

### Tone frequency

10-bit divider. **Frequency = 4,000,000 / (32 × N)** = `125000 / N` Hz where N is the 10-bit value.

Examples:
- N=1: 125 kHz (inaudible, max).
- N=239: 523 Hz (middle C, approx).
- N=1023: 122 Hz (low).
- N=0 treated as N=1024 by some 76489 variants; safer to never write 0.

### Volume (4 bits)

| A3 A2 A1 A0 | Attenuation |
|---|---|
| 0000 | 0 dB (max, "15") |
| 0001 | -2 dB |
| ... | (-2 dB per step) |
| 1110 | -28 dB |
| 1111 | OFF |

BBC convention is **inverted**: in OSWORD `&07` amplitude `&FFxx` to `&FF00` = -15 to 0; amplitude 0 = silent. The MOS converts BBC amplitude to chip attenuation bits.

### Noise generator

| Bit | Field |
|---|---|
| FB | 0 = periodic noise, 1 = white noise |
| NF1, NF0 | Base frequency: 00=low, 01=med, 10=high, 11 = tone 1's frequency |

### Byte formats sent to chip

**Latch byte** (selects register + carries low data nibble):

```
bit:  7   6   5   4   3   2   1   0
      1   R2  R1  R0  d3  d2  d1  d0
```

bit 7 = 1 marks it as a latch byte (the chip uses this to distinguish from data bytes).

**Data byte** (extends previous frequency write with high bits):

```
bit:  7   6   5   4   3   2   1   0
      0   X   F9  F8  F7  F6  F5  F4
```

bit 7 = 0 marks it as a data byte. After writing a frequency latch byte, you may send any number of data bytes to update the high bits of the same channel's frequency without re-latching.

**Noise source byte**:

```
bit:  7   6   5   4   3   2   1   0
      1   R2  R1  R0  X   FB  NF1 NF0
```

**Volume update**:

```
bit:  7   6   5   4   3   2   1   0
      1   R2  R1  R0  A3  A2  A1  A0
```

## Direct chip write — the slow-bus dance (NAUG §21.3 p378)

The 76489 isn't on the 6502 bus — it hangs off the System VIA's **slow peripheral bus** (Port A) with `/WE` driven by System VIA addressable-latch line 0 ([[hardware/system-via]]).

Sequence to write one byte:

```asm
SEI                  ; MOS uses the slow bus constantly — own it
                     ; (also: keyboard scan, speech, CMOS on Master)
; 1. Set DDRA = &FF (Port A all output)
LDA #&FF : STA &FE43
; 2. Put data byte on Port A
LDA #data : STA &FE41
; 3. Pulse sound /WE low (latch line 0 = 0)
LDA #0   : STA &FE40    ; PB3 (data bit) = 0, PB0-2 (latch addr) = 000 → line 0 goes low
; 4. Hold low for ≥8 µs — the chip needs the pulse width
LDX #4
.delay  DEX : BNE delay  ; ~8 µs at 2 MHz (5c per iteration × 4 ≈ 20c = 10 µs — comfortable)
; 5. Pulse /WE high again
LDA #8   : STA &FE40    ; PB3 = 1, latch line 0 → 1 (chip /WE deasserted)
CLI
```

NAUG's example uses `OSBYTE &97` (write SHEILA) to do steps 1-5 — slower per write but Tube-safe.

The 8 µs hold time is a chip requirement, not a 6502 timing constraint. At 2 MHz CPU = 16 cycles. A tight `DEX:BNE` loop or even a few NOPs cover it.

## Filed into

- [[hardware/sn76489]] — Chip reference: registers, frequency math, byte formats.
- [[os/sound]] — MOS sound interface: OSWORDs, suppression OSBYTEs, BELL.
- Updates: [[hardware/system-via]] slow-bus section — already documents the dance; cross-link added.
- Updates: [[os/buffers]] — sound channel buffers 4-7 referenced.

## Open follow-ups

- **ENVELOPE format detail** — NAUG just says "14 bytes matching BASIC ENVELOPE". The 14-parameter breakdown is in the User Guide / BASIC manual; capture if it becomes relevant for fast envelope work.
- **OSWORD `&07` channel encoding** — high byte of the 2-byte channel field controls sync-channel and "queue or flush" behaviour. Acorn docs the encoding (`&00xx`-`&FFxx` semantics). Worth filing if writing music engines.
- **Speech chip** (TMS5220-family) — Ch21 §21.4 mentions OSBYTE `&9E`/`&9F` + the SOUND `&FFxx` channel encoding triggers speech. Detailed protocol is in the Speech System User Guide, not this book.
- **Master vs Model B sound timing** — Master's 65C12 BCD penalty ([[hardware/6502]]) may affect tight MOS sound-IRQ loops by a few cycles; investigate if envelope timing differs perceptibly.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
