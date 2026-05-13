---
title: NAUG Ch20 — ADC System
type: source
parent: [[sources/naug]]
pages: 372-378
section: §20
tags: [adc, joystick, upd7002, master-compact]
updated: 2026-05-13
---

# NAUG Ch20 — ADC System

Holmes & Dickens, *The New Advanced User Guide*, pp.372-378. The µPD7002 analogue-to-digital converter: 4-channel 12-bit ADC, primarily used for analogue joysticks but available for any 0..~1.8 V measurement.

## Hardware variants

| Machine | ADC |
|---|---|
| Model B, B+, Master 128 | µPD7002 4-channel 12-bit |
| Electron | None standard; Plus 1 expansion adds µPD7002 (mapped at `&FE18-&FE1A`) |
| Master Compact | **No real ADC** — software simulator that translates digital joystick / cursor keys into ADVAL-style values |

## SHEILA addresses

| Range | Function |
|---|---|
| `&FEC0-&FEDF` | µPD7002 on Model B, B+ (mirrored) |
| `&FE18-&FE1A` | µPD7002 on Master 128 + Electron Plus 1 |

Each chip has 3 visible registers:

| Offset | Read | Write |
|---|---|---|
| 0 (`&FEC0` / `&FE18`) | Status | Channel select + start conversion |
| 1 (`&FEC1` / `&FE19`) | High byte of result | — |
| 2 (`&FEC2` / `&FE1A`) | Low byte (in bits 7-4) | — |

## ADC OSBYTEs

### `OSBYTE &80` (128) — Read channel / read buffer status

Dual-purpose call (collision with buffer-status, see `[[os/buffers]]`):

| X | Action |
|---|---|
| 0 | Return last-completed channel in X; bits 0-1 = fire button states (ADVAL(0)) |
| 1-4 | Return ADC value for channel X in (X, Y) — ADVAL(1)..(4) |
| 255-247 (`&FF`-`&F7`) | Buffer status (see `[[os/buffers]]`) |

### `OSBYTE &10` (16) — Select ADC channels

X = number of channels to sample (1-4, or 0 to disable). MOS auto-cycles through channels 1..n in the background.

### `OSBYTE &11` (17) — Force ADC conversion

X = channel (1-4) to force. Immediate conversion regardless of current cycle.

### `OSBYTE &BC` (188) — Read current channel

Returns the channel currently being converted in X.

### `OSBYTE &BD` (189) — Read maximum channel

Returns the max channel being sampled (set by `&10`).

### `OSBYTE &BE` (190) — R/W conversion type

| X | Resolution |
|---|---|
| `&00` | Default (12 bit) |
| `&08` | 8-bit conversion (~4 ms) |
| `&0C` | 12-bit conversion (~10 ms) |

8-bit is 2-3× faster — values still in 0-`&FFFF` range but with less precision. The low bits of the high byte will be noisy in 8-bit mode (chip-dependent).

## Programming the µPD7002 directly

### Start conversion — write to register 0

```
bit:  7 6 5 4   3   2   1 0
      - - - -  res flag  chan
```

| Bits | Field |
|---|---|
| 0-1 | Channel number 0-3 (= CH0-CH3) |
| 2 | Flag input — set to 0 |
| 3 | Resolution: 0 = 8-bit (~4 ms), 1 = 12-bit (~10 ms) |
| 4-7 | unused |

Writing this register starts the conversion immediately.

### Status register — read register 0

| Bit | Meaning |
|---|---|
| 0-1 | Currently selected channel |
| 3 | Current conversion resolution (8 / 12) |
| 4-5 | Two MSBs of result (for fast read) |
| 6 | 0 = busy, 1 = not busy |
| 7 | 0 = conversion complete, 1 = not complete |

The "End-of-conversion" IRQ on System VIA CB1 (`[[hardware/system-via]]`) fires when bit 7 transitions 1→0. MOS hooks this IRQ to advance the channel cycle.

### Reading the result

12-bit result split across two registers:

- High byte (bits 11-4) at register 1.
- Low nibble (bits 3-0) in bits 7-4 of register 2.

The value is **left-justified** into the 16-bit ADVAL range (0..`&FFFF`). In 8-bit mode the low 4 bits of register 2 are noisy and should be masked.

## Joystick wiring

Standard analogue joystick: each axis = a pot wired between Vref (~1.8V) and analogue ground, wiper to channel input. Fire buttons connect to System VIA PB4 (joystick 1) and PB5 (joystick 2).

NAUG §20.2 p370 shows the standard 15-pin D analogue port pinout used by Model B / B+ / Master 128.

## Master Compact joystick — switched, not analogue

The Compact's "joystick" connector is on the User VIA's user port (PB0-PB4 + CB1/CB2):

| User VIA pin | Function |
|---|---|
| PB0 | Joystick FIRE / mouse left |
| PB1 | Joystick LEFT / mouse middle |
| PB2 | Joystick DOWN / mouse right |
| PB3 | Joystick UP / mouse X-axis |
| PB4 | Joystick RIGHT / mouse Y-axis |

MOS reads these and **synthesises analogue-looking ADVAL values** via `OSBYTE &BE` mode bits:

| Bit | Effect |
|---|---|
| 7 | 0 = MOS updates ADVAL from joystick; 1 = ROM-provided values |
| 6 | If set, joystick presses inject ASCII into keyboard buffer (cursor keys + COPY) |
| 5 | 0 = varying emulated values, 1 = fixed extremes (`&0000`, `&7FFF`, `&FFFF`) |
| 3-0 | Emulation speed (7 = fastest changes, 0 = slowest) |

## Joystick-as-cursor-keys

Setting `OSBYTE &BE` X-bit 6 makes Compact joystick presses inject cursor keys:

| Joystick | Key |
|---|---|
| RIGHT | cursor right (&89) |
| UP | cursor up (&8B) |
| DOWN | cursor down (&8A) |
| LEFT | cursor left (&88) |
| FIRE | COPY (&87) |
| Mouse left | COPY (&87) |
| Mouse middle | RETURN (&0D) |
| Mouse right | DELETE (&7F) |

Useful for keyboard-driven games to support a joystick without bespoke handling.

## Performance notes

- 12-bit conversion: ~10 ms per channel. With 4 channels cycling, each channel updates at ~25 Hz. Too slow for some fast-action games.
- 8-bit conversion: ~4 ms. 4 channels at ~62 Hz — closer to per-frame.
- **Force-conversion `OSBYTE &11`** lets you sample one channel as fast as possible (~10 ms or ~4 ms) by skipping the auto-cycle.
- Direct chip programming is faster only if you stop using MOS conversions entirely — chip handshaking and IRQ ack still need the standard MOS protocol unless you take over IRQ1V.

## Filed into

- `[[hardware/upd7002-adc]]` — Chip reference (register map, conversion timing).
- `[[os/adc]]` — OSBYTE-level ADC interface + joystick reading patterns.
- Updates: `[[os/osbyte]]` — `&10`, `&11`, `&80`, `&BC`, `&BD`, `&BE` linked.
- Updates: `[[hardware/system-via]]` — ADC EOC on CB1 cross-link.

## Open follow-ups

- **Analogue port pinout** — captured at hint level (15-pin D, standard Acorn pinout). Full pin-by-pin reference if anyone builds custom hardware.
- **Tracker/light-pen modes** beyond joystick — ADC + LPSTB combinations for tracker balls. Niche; documented at headline level only.
