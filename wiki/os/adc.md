---
title: ADC & Joystick
type: os
tags: [adc, joystick, osbyte, advad, upd7002]
sources: [naug-ch20-adc]
updated: 2026-05-13
---

# ADC & Joystick — MOS Interface

For chip-level details see [[hardware/upd7002-adc]]. This page covers MOS-level access (OSBYTEs + ADVAL semantics).

## OSBYTE summary

| OSBYTE | Function |
|---|---|
| `&10` (16) | Select number of channels to auto-cycle (X = 1-4, or 0 to disable) |
| `&11` (17) | Force conversion on channel X (1-4) |
| `&80` (128) | Read ADC channel (X = 1-4) or buffer status (X = `&FF`-`&F7`) — see below |
| `&BC` (188) | Read current channel (channel currently converting) |
| `&BD` (189) | Read max channel (set by `&10`) |
| `&BE` (190) | R/W conversion resolution (`&00` default / `&08` 8-bit / `&0C` 12-bit) |

## OSBYTE `&80` — the dual-purpose call

X selects mode:

| X | Function |
|---|---|
| 0 | Returns last-converted channel + fire button states |
| 1-4 | Read ADC channel X (= BASIC ADVAL(X)) |
| `&FF`-`&F7` | Read buffer status (see [[os/buffers]]) |

The X=0 path returns (in **X** on exit; A is preserved by OSBYTE):
- X = channel number of last completed conversion (0 if none yet — i.e. immediately after `&10` or `&11`).
- Low 2 bits of X = fire button states (bit 0 = J1 fire, bit 1 = J2 fire). **Active-low** — bit clear means button pressed.

This is BASIC's `ADVAL(0)`. The channel-number and fire-button bits share the same byte; mask appropriately to separate them (`X AND &03` for fire bits, `X AND &FC` for channel).

For X = 1-4: returns the 16-bit ADC value in (X, Y) — X = low byte, Y = high byte. Combined: `(Y << 8) | X` = 0..`&FFFF`.

## Reading a joystick — standard pattern

```asm
LDA #&80 : LDX #1 : JSR &FFF4    ; ADVAL(1) = joystick 1 X
; X = LSB, Y = MSB of joystick 1 X position
STX joy1_x_lo
STY joy1_x_hi

LDA #&80 : LDX #2 : JSR &FFF4    ; ADVAL(2) = joystick 1 Y
LDA #&80 : LDX #3 : JSR &FFF4    ; ADVAL(3) = joystick 2 X
LDA #&80 : LDX #4 : JSR &FFF4    ; ADVAL(4) = joystick 2 Y

LDA #&80 : LDX #0 : JSR &FFF4    ; fire buttons
STX fire_buttons                 ; bit 0 = J1, bit 1 = J2 (active low)
```

For per-frame game polling, run this once per vsync ([[os/events]] event 4 or [[os/interrupts]] CA1 hook).

## Faster sampling: 8-bit mode

```asm
LDA #&BE : LDX #&08 : LDY #0 : JSR &FFF4    ; 8-bit conversions
```

Halves the latency per channel from ~10 ms to ~4 ms. For game purposes, 8-bit is usually more than enough — joystick precision is limited by the pot quality anyway.

Per-channel ADVAL is still returned as 16-bit (the chip left-justifies into the high byte). High byte alone gives 8-bit precision.

## Single-channel high-rate sampling

To poll one channel as fast as possible (ignoring the others):

```asm
LDA #&10 : LDX #1 : JSR &FFF4         ; auto-cycle only channel 1
LDA #&BE : LDX #&08 : LDY #0 : JSR &FFF4   ; 8-bit
.sample_loop
    LDA #&11 : LDX #1 : JSR &FFF4     ; force a conversion
    ; wait ~4ms or hook CB1 IRQ
    LDA #&80 : LDX #1 : JSR &FFF4
    ; X = result low, Y = result high
    JMP sample_loop
```

Theoretical max: ~250 samples/sec on a single channel in 8-bit mode. Good enough for tracking analogue pots or single-axis controllers; not enough for audio.

## Fire buttons via System VIA — direct

`OSBYTE &80, X=0` is the canonical path. The fire buttons are physically connected to **System VIA PB4 (J1) and PB5 (J2)**, active-low.

The naive "read `&FE40` directly" doesn't necessarily work as expected — see [[hardware/via-6522]] "IRA vs IRB asymmetry". When PB4/PB5 are configured as inputs, the 6522's behaviour for reading IRB is hardware-revision-dependent: some sources say IRB always returns the last value written to ORB (no live pin read), others say input-mode pins do reflect live state. MOS's joystick read uses the slow-bus protocol (set DDRB appropriately, then read), which works regardless.

**Verify against real hardware before relying on direct LDA**. The safest fast path is to hook the OSBYTE-internal poll instead of replacing it — or use the keyboard-event mechanism if all you want is "did the user press fire".

Faster than OSBYTE if you can do it: typically a hand-rolled read of the System VIA via the proper input-mode sequence costs ~20 cycles vs OSBYTE's hundreds. Worth doing for per-frame polling in tight game loops.

## Master Compact joystick simulator

The Compact has no real ADC. MOS synthesises ADVAL values from **User VIA** ([[hardware/user-via]], base `&FE60`) port-B pins on the combined joystick/user-port connector:

```
User VIA PB0 = joystick FIRE
User VIA PB1 = joystick LEFT
User VIA PB2 = joystick DOWN
User VIA PB3 = joystick UP
User VIA PB4 = joystick RIGHT
```

(These are distinct from the System VIA's PB4/PB5 fire-button pins on non-Compact machines.)

`OSBYTE &BE` on Compact has a completely different bit-layout to configure how the switches map to ADVAL values:

| Bit | Effect |
|---|---|
| 7 | 0 = MOS updates ADVAL from switches; 1 = ROM-provided values |
| 6 | If set, joystick movement injects ASCII into keyboard buffer (cursor keys + COPY) |
| 5 | 0 = "varying" emulated values that change over time; 1 = fixed `&0000`/`&7FFF`/`&FFFF` extremes |
| 3-0 | Speed of varying emulation (7 = fastest, 0 = slowest) |

With bit 6 set, Compact joystick acts as cursor keys (no extra game code needed for keyboard-driven games):

| Joystick | Key |
|---|---|
| RIGHT | cursor right (`&89`) |
| UP | cursor up (`&8B`) |
| DOWN | cursor down (`&8A`) |
| LEFT | cursor left (`&88`) |
| FIRE | COPY (`&87`) |

## Conversion-complete event (event 3)

[[os/events]] event 3 fires when an ADC conversion completes. X on entry = channel that just finished.

Useful pattern: enable event 3 + ADC auto-cycle, then handle each result as it arrives. Lower latency than polling `OSBYTE &80`:

```asm
LDA #&0E : LDX #3 : JSR &FFF4    ; enable event 3
LDA #&10 : LDX #4 : JSR &FFF4    ; auto-cycle 4 channels
; ... install EVNTV handler that switches on A=3 ...
```

## See also

- [[hardware/upd7002-adc]] — Chip-level reference.
- [[hardware/system-via]] — CB1 = EOC IRQ; PB4/PB5 = fire buttons.
- [[os/events]] — Event 3 = ADC conversion complete.
- [[os/buffers]] — OSBYTE `&80` X-range collision with buffer status.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
