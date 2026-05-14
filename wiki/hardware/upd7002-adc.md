---
title: µPD7002 ADC
type: hardware
tags: [adc, upd7002, joystick, analogue]
sources: [naug-ch20-adc]
sheila: ["&FEC0", "&FEDF"]
machines: [BBC Model B, BBC B+, Master 128, Electron (with Plus 1)]
updated: 2026-05-13
---

# NEC µPD7002 ADC

4-channel 12-bit analogue-to-digital converter. Used primarily for analogue joysticks (X, Y of two joysticks → 4 channels). Input range 0 to ~1.8 V (Vref).

## Hardware variants

| Machine | Address | Notes |
|---|---|---|
| Model B, B+ | `&FEC0-&FEDF` | Standard |
| Master 128 | `&FE18-&FE1A` | Moved to make room for Econet at `&FECx` |
| Electron + Plus 1 | `&FE18-&FE1A` | Optional |
| Master Compact | — | **No ADC**; analogue simulator for digital joystick / cursor keys |

## Register map

3 registers, 8-bit wide:

| Offset | Read | Write |
|---|---|---|
| 0 | Status | Start conversion |
| 1 | Result high byte | — |
| 2 | Result low nibble (in bits 7-4) | — |

## Start a conversion — write reg 0

| Bits | Field |
|---|---|
| 0-1 | Channel select 0-3 (CH0-CH3) |
| 2 | Flag input (set to 0) |
| 3 | 0 = 8-bit conversion (~4 ms), 1 = 12-bit conversion (~10 ms) |
| 4-7 | unused |

Writing this register **starts the conversion immediately**. Don't write again until conversion is complete (or the in-progress conversion is aborted).

## Status register — read reg 0

| Bits | Field |
|---|---|
| 0-1 | Currently selected channel (0-3) |
| 2 | (unused) |
| 3 | Current resolution (0 = 8-bit, 1 = 12-bit) |
| 4-5 | Two MSBs of latest result (fast peek) |
| 6 | 0 = busy, 1 = not busy |
| 7 | 0 = conversion complete, 1 = not complete |

When bit 7 transitions 1→0, **System VIA CB1 IRQ fires** ([[hardware/system-via]]). MOS hooks this for its 4-channel auto-cycle.

## Reading the result

12-bit value, split across two registers, **left-justified** to 16 bits:

```
high byte (reg 1):  R11 R10 R9  R8  R7  R6  R5  R4
low nibble (reg 2): R3  R2  R1  R0  -   -   -   -
```

The ADVAL value (BASIC) is the full 16-bit number, range `&0000`-`&FFFF`. In 8-bit mode the low nibble (R3-R0) is noisy and should be masked.

Reading the high byte alone gives an 8-bit result (`&00`-`&FF` is the meaningful range; the value is already shifted into the high byte).

## Conversion timing

- **12-bit**: ~10 ms per conversion.
- **8-bit**: ~4 ms (2-3× faster).

With 4 channels in auto-cycle (default MOS): each channel updates at ~25 Hz (12-bit) or ~62 Hz (8-bit).

For force-converting a single channel via `OSBYTE &11`, the rate is the per-channel rate (no waiting for the cycle to come round).

## Conversion abort

Writing a new conversion-start before the previous one has completed aborts the previous. The 12-bit / 8-bit mode bit from the *current* write applies. Useful for "screen vsync triggered ADC sample" patterns where you don't want stale data.

## Joystick wiring (Model B / B+ / Master 128)

15-pin D socket on the rear. Pinout per NAUG §20.2 p370:

| Channel | Function |
|---|---|
| CH0 | Joystick 1 X |
| CH1 | Joystick 1 Y |
| CH2 | Joystick 2 X |
| CH3 | Joystick 2 Y |

Plus:
- Vref output (~1.8 V) to power the pots.
- Analogue ground (separate from digital ground for noise immunity).
- Fire buttons → System VIA **PB4** (J1) and **PB5** (J2), accessible via slow-bus or directly.

Each axis is a 100 KΩ pot between Vref and Aground, wiper to channel input.

## Master Compact joystick — switched, not analogue

The Compact omits the µPD7002. Joystick switches feed the User VIA's user port (PB0-PB4 + CB1/CB2). MOS reads these and synthesises analogue-looking ADVAL values for compatibility.

See [[os/adc]] for the OSBYTE-level simulator config (`&BE` bits).

## Performance use cases

- **Game joystick reads**: use `OSBYTE &80, X=1..4` once per frame. Total cost ~hundreds of cycles per channel.
- **Lower latency**: hook IRQ2V on CB1, read the conversion result in the handler. Direct cycle-accurate timing.
- **Custom sampling rate**: write the chip directly with 8-bit mode + immediate read — gives ~4 ms per sample.
- **Audio sampling (low-rate)**: 8-bit conversions at ~4 ms = 250 Hz max. Too slow for serious audio capture; an external DAC + 1MHz-bus sampler would do better.

## See also

- [[os/adc]] — MOS-level ADC interface + joystick reading.
- [[hardware/system-via]] — CB1 = ADC end-of-conversion IRQ source.
- [[memory/memory-map]] — `&FEC0-&FEDF` (B/B+) and `&FE18-&FE1A` (Master/Electron) in SHEILA.
