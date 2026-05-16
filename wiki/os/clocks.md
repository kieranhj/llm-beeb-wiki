---
title: System Clock & Interval Timer
type: os
tags: [clock, timer, interval-timer, time, event-5]
sources: [naug-ch19-clocks-cmos]
updated: 2026-05-13
---

# System Clock & Interval Timer

Two **5-byte counters** in OS workspace, incremented every centisecond (100 Hz) by the System VIA T1 IRQ handler ([[os/interrupts]]).

- **System clock**: ever-increasing tick count since reset. Read by BASIC's `TIME` function.
- **Interval timer**: decrements every tick; when it crosses zero, **event 5** fires ([[os/events]]).

## OSWORD calls

All take a 5-byte parameter block at X+Y:

| OSWORD | A | Function |
|---|---|---|
| `&01` (1) | 1 | Read system clock |
| `&02` (2) | 2 | Write system clock |
| `&03` (3) | 3 | Read interval timer |
| `&04` (4) | 4 | Write interval timer |

Block layout:

```
+0 LSB
+1
+2
+3
+4 MSB
```

```asm
.read_clock
    LDX #clock_block MOD 256
    LDY #clock_block DIV 256
    LDA #1                   ; OSWORD &01
    JSR &FFF1
    ; clock_block now holds the 5-byte clock value, LSB first
```

## Dual-clock atomicity

MOS keeps **two copies** of the system clock and two of the interval timer. Each tick alternates which copy is being incremented; the other is "stable" and available for reading. Otherwise a 5-byte read could catch a clock mid-increment (low bytes wrapped, high bytes not yet incremented).

`OSBYTE &F3` returns which copy is the "current readable" one — as an offset (5 or 10) from base address `&28D`. Direct readers do:

```asm
LDA #&F3 : LDX #0 : LDY #&FF : JSR &FFF4    ; X = offset (5 or 10)
; X+&28D = current 5-byte clock base
```

For most uses just call `OSWORD &01` — it handles the dual-copy logic internally.

## Tick rate

100 Hz on all standard machines. Source: System VIA T1 timer running free-run with PB7 output disabled, period programmed to fire every 10 ms. See [[timing/via-timers]] and [[os/interrupts]].

This is the **same timer** the OS uses for sound envelope updates, key-buffer servicing, RS423 6850 takeover timeout, etc. **Don't steal T1** unless you've turned off MOS sound (`OSBYTE &D2 X=1`).

## Interval timer as a one-shot

For "fire event 5 in N centiseconds":

```asm
; Set interval timer to N (positive)
.set_interval
    LDA #-N MOD 256          ; (the timer is "set then decrement to zero"
    STA timer_block + 0      ;  so write a positive starting value)
    LDA #-N DIV 256
    STA timer_block + 1
    LDA #0
    STA timer_block + 2
    STA timer_block + 3
    STA timer_block + 4
    LDX #timer_block MOD 256
    LDY #timer_block DIV 256
    LDA #4                   ; OSWORD &04 — write interval timer
    JSR &FFF1
    ; Then enable event 5
    LDA #&0E : LDX #5 : JSR &FFF4
```

Hook EVNTV; in your handler test A=5; on hit, you've reached zero. Disable event 5 after handling if it was a one-shot.

## Performance reads

OSWORD round-trip is ~hundreds of cycles. For a tight read loop (e.g. game timing inside a frame):

1. `OSBYTE &F3` once per read → cached offset.
2. `LDA &28D+offset+i` for each byte of the 5-byte value.

Or just sample one byte (lowest = 1/100 sec) if precision is sufficient. Beware: the byte is being written by the IRQ handler ~every 10 ms; if you read while interrupts are enabled, two consecutive reads can differ by an unexpected amount.

For per-frame tick counting, prefer hooking the 100 Hz handler directly (or using event 5 / event 4 vsync).

## See also

- [[os/events]] — Event 5 = interval timer crossed zero.
- [[os/interrupts]] — 100 Hz T1 source; full background-task list per tick.
- [[timing/via-timers]] — System VIA T1 details + "don't steal T1" warning.
- [[memory/os-workspace]] — Clock storage around `&292-&29F`.
- [[hardware/cmos-rtc]] — Master's real-time clock (separate; battery-backed).

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
