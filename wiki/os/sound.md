---
title: MOS Sound Interface
type: os
tags: [sound, osword, envelope, bell]
sources: [naug-ch21-sound, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
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

**Measured (Paradroid, 2026-08-26, jsbeeb — [[sources/beeb-port-kit-hardware-facts]] §6):** `OSBYTE &D2` gates *new* `SOUND` commands; it does **not** stop a queue that is already draining. See "Measured in practice" below.

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

## Measured in practice — handing the sound system back (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Neither port uses the MOS sound system at all — Paradroid has its own SN76489 driver on its own IRQ, Edge Grinder replays a converted Arkos tune — so the facts here are about what the MOS does when it gets the machine back.

- **The MOS plays your data as notes.** Hand IRQ1V back with a character set over `&0800-&08FF` and the 100 Hz sound driver finds its queue pointers and channel buffers full of bitmaps: a quiet, rising sequence that a game's own mute cannot touch (chip read CH0 attenuation 14, CH1 13, periods falling 401 → 146 → 95). Zeroing `&0800-&087F` stopped it instantly. **`OSBYTE &D2` does NOT stop it** — it gates new `SOUND` commands, not a draining queue. **`OSBYTE &0F, X=0` (flush every buffer) BEFORE uninstalling the IRQ is the fix** (Paradroid, 2026-08-26, jsbeeb; [layer-11e-sound.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-11e-sound.md)). Layout of that page on [[memory/os-workspace]].
- **The 100 Hz sound driver writes `&0800-&08FF` while the MOS owns the machine**, which corrupted a compressed stream staged there at boot (Paradroid, 2026-08-30). See [[techniques/zx0-loading]].
- **The BREAK beep under a `*RUN` boot never ends on a Model B.** A `*RUN` boot (disc option 2) is entered with interrupts off (P = `&35` at the `!BOOT` stub, `B-DFS1.2` and `Master` alike); on the B, channel 0 still sounded after 400 frames, 523 Hz at attenuation 2. The debug build's `*EXEC` boot, which starts BASIC with interrupts on, left every channel at 15; the Master was silent either way. **Write attenuation 15 to all four channels yourself** (the kit's `install_irq`; Edge's `sn_write` sequence). **OSBYTE 126 does not stop it**: at the stub no ESCAPE is pending (`&FF` = `&00`, `&0276` = `&00`), and in OS 1.20 OSBYTE 126 at `&E65C` does nothing without one (`BIT &FF : BPL` returns X=0); only with an ESCAPE pending and `&0276` = 0 does it purge the buffers, and purging a sound buffer (`&E1AD` → `&ECA2` → `JSR &EB03`) is what silences a channel — so it silences sound only as an ESCAPE side effect (cf. [[os/escape]]). hexwab recommended OSBYTE 126 for the beep (paradroid-beeb #18); on this evidence it does nothing at that point in the boot (kit template, 2026-09-11, jsbeeb; code read from OS 1.20's `os.txt`; MOS 3.20 not disassembled — [[sources/beeb-port-kit-hardware-facts-2026-11]] §4). A real machine's beep under a `*RUN` boot is not measured.
- **MOS 1.20 and MOS 3.20 write the same SN76489 bytes in the same ticks** for the same SOUND and ENVELOPE blocks (Stryker's Run's 8 effects, jsbeeb 2.10.2 `B-DFS1.2` and Master, 2026-10-25), so a capture made on one fits the other.
- **What the MOS sound driver costs a game that keeps it** (MOS 3.20, Stryker's Run's original): sound queues and envelopes were 6.8% of all CPU cycles, inside a 100 Hz tick that takes ~16% in play; the tick re-enables interrupts (`CLI` at `&E720`) around its sound processing, so interrupts nest. Replacing it with the game's own 50 Hz driver took the whole interrupt budget from 10.6% to 2.2% (2026-10-16, jsbeeb 2.5.0; decision 25). See [[os/interrupts]].
- **Filing-system calls and the MOS sound driver**: on a Master, an IRQ1V handler that chains to the MOS across a `*LOAD` hands the 100 Hz tick back, and the MOS wrote 35 bytes of `&0800-&08FF` during one 26-sector load — anything of yours parked there must be saved across the call (1942, 2026-09-13, jsbeeb). See [[os/interrupts]].
- **A direct chip write from an IRQ coexists with a foreground keyboard poll** if it saves and restores DDRA and ORA around its strobe and touches only latch line 0 (Paradroid, 2026-08-21, 8,192 polls each way). See [[hardware/sn76489]], [[hardware/system-via]].

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
