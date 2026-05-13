---
title: NAUG Ch19 — Clocks, Timers, CMOS
type: source
parent: [[sources/naug]]
pages: 359-371
section: §19
tags: [clock, timer, cmos, rtc, 146818, master-specific]
updated: 2026-05-13
---

# NAUG Ch19 — Clocks, Timers, CMOS RAM

Holmes & Dickens, *The New Advanced User Guide*, pp.359-371. Three things bundled together:

1. **System clock + interval timer** — two 5-byte software clocks updated 100×/sec by the System VIA T1 IRQ (`[[os/interrupts]]`).
2. **Master 146818 real-time clock** — battery-backed, keeps time across power-off. Compact has no RTC.
3. **CMOS RAM** (Master) / **EEPROM** (Compact) — non-volatile config storage accessed via slow-bus.

## System clock + interval timer

Both are **5-byte values, LSB first**, in OS workspace around `&292-&29F` (`[[memory/os-workspace]]`). Incremented every centisecond by the 100 Hz T1 handler.

| OSWORD | Function | Block size |
|---|---|---|
| `&01` | Read system clock | 5 bytes returned |
| `&02` | Write system clock | 5 bytes input |
| `&03` | Read interval timer | 5 bytes returned |
| `&04` | Write interval timer | 5 bytes input |

X+Y point to the parameter block in memory.

**System clock** is what BASIC's `TIME` function reads. **Interval timer** is decremented per tick; when it reaches zero, **event 5** fires (`[[os/events]]`) — useful as a one-shot timer callback.

### Dual-clock atomicity

MOS keeps **two copies** of the system clock (likewise interval timer). They're incremented alternately so a reader can never catch one mid-increment. `OSBYTE &F3` reads which copy is current — returns 5 or 10, an offset from `&28D` to the current 5-byte clock. Direct readers should:

1. Read `OSBYTE &F3` → offset.
2. Read 5 bytes from `&28D + offset`.

Or just use OSWORD `&01`/`&03` which handles this atomically.

## Master RTC (146818 CMOS clock)

Master 128 has a Motorola/Hitachi 146818-class RTC chip. Master Compact has no RTC (returns `Fri,31 Dec 1999.23:59:59` for `*TIME`).

### OSWORD `&0E` — Read RTC

XY+0 selects mode:

| XY=0 | Read clock → 24-byte string `ddd,nn mmm yyyy.hh:mm:ss\r` at XY+0 |
| XY=1 | Read clock → 7-byte BCD at XY: year/month/day/dow/hh/mm/ss |
| XY=2 | Convert BCD at XY+1..+7 → 24-byte text string back into XY+0..+23 |

### OSWORD `&0F` — Write RTC

XY (first byte) selects mode:

| XY=8 | Time only: `hh:mm:ss` text at XY+1..+8 |
| XY=15 | Date only: `ddd,nn mmm yyyy` at XY+1..+15 |
| XY=24 | Time + date together: full 24-byte text at XY+1..+24 |

## CMOS RAM / EEPROM (Master / Compact)

- **Master 128**: 50 bytes of battery-backed CMOS RAM in the 146818 chip. Locations 0-13 are the RTC's time/control regs; locations 14-63 are RAM.
- **Master Compact**: 128 or 256 byte EEPROM (write-cycle limited — ~10,000 per location).

Accessed via slow-bus through System VIA. Two OSBYTEs:

| OSBYTE | Function |
|---|---|
| `&A1` (161) | **Read** CMOS RAM/EEPROM (X = location, returns byte in Y) |
| `&A2` (162) | **Write** CMOS RAM/EEPROM (X = location, Y = byte) |

On Compact, `OSBYTE &A1, X=&FF` returns Y=0 (no EEPROM), Y=`&7F` (128B), Y=`&FF` (256B).

### Master CMOS layout (§19.5.1 p357)

| Addr | Function |
|---|---|
| 0 | Econet station number |
| 1 | File server station number |
| 2 | File server network number |
| 3 | Printer server station number |
| 4 | Printer server network number |
| 5 | d0-3 default FS ROM, d4-7 default language ROM |
| 6 | ROMs 0-7 inserted bits |
| 7 | ROMs 8-15 inserted bits |
| 8 | EDIT ROM data |
| 9 | Telecomms reserved |
| 10 | d0-2 default MODE, d3 shadow, d4 interlace, d5-7 *TV setting |
| 11 | FDRIVE / CAPS / dir-load / default-drive bits |
| 12 | Keyboard auto-repeat delay |
| 13 | Keyboard auto-repeat rate |
| 14 | Printer ignore character |
| 15 | Tube selection + baud rate + *FX5 |
| 16 | BEEP loudness + Tube int/ext + scrolling + boot + serial format |
| 17 | ANFS settings |
| 18 | Compact joystick settings |
| 19 | Reserved |
| 20-29 | Reserved Acorn firmware |
| 30-45 | Allocated to ROMs 0-15 |
| 46-49 | User applications |

`*CONFIGURE` and `*STATUS` commands manipulate these — typically the right approach for user-visible config.

## 146818 hardware registers (Master only, §19.6)

When direct chip access is needed (e.g. for alarm interrupts not exposed by MOS):

| Addr | Function |
|---|---|
| 0-9 | Time/date registers (BCD or binary per DM bit) |
| 10 | Register A — UIP, divider, periodic interrupt rate |
| 11 | Register B — SET, PIE, AIE, UIE, SQWE, DM, 24/12, DSE |
| 12 | Register C — IRQF, PF, AF, UF (read-only, clear on read) |
| 13 | Register D — VRT (valid RAM and time) |
| 14-63 | 50 bytes user RAM |

### Three interrupt sources

- **Alarm IRQ** (AIE bit) — fires when current time matches alarm time. Alarm bytes can be set to `&FF` for "don't care" (e.g. every minute).
- **Periodic IRQ** (PIE bit) — rates from 122 µs to 500 ms, selectable via RS3..RS0.
- **Update-ended IRQ** (UIE bit) — fires after each 1.984 ms update cycle.

### Master link LK4

Alarm IRQs are **physically disconnected by default** — must close link LK4 on the Master mainboard to enable. Otherwise no IRQ reaches the 65C12 regardless of how you program the chip.

### Direct chip access via slow-bus

Like the sound chip and keyboard, the CMOS/RTC sits on the System VIA's slow peripheral bus. PB6 = chip enable, PB7 = address strobe. Worked example in §19.6 (§p362-364) shows a complete IRQ-driven alarm-clock pattern.

## OSBYTE summary

| OSBYTE | Function |
|---|---|
| `&A1` (161) | Read CMOS RAM/EEPROM |
| `&A2` (162) | Write CMOS RAM/EEPROM |
| `&F3` (243) | Read which clock-copy is current (offset 5 or 10) |

## Filed into

- `[[os/clocks]]` — System clock + interval timer reference.
- `[[hardware/cmos-rtc]]` — 146818 chip + register layout + IRQ sources (Master only).
- Updates: `[[os/osword]]` — `&01-&04`, `&0E`, `&0F` linked.
- Updates: `[[os/osbyte]]` — `&A1`, `&A2`, `&F3` linked.

## Open follow-ups

- Master `*CONFIGURE` / `*STATUS` command syntax — only listed at headline level. Would need the Master User Guide for the full per-option enumeration.
- Compact EEPROM write-cycle wear levelling — none provided by MOS; if heavy-writing apps care, they should implement their own.
