---
title: NAUG Ch15 — Serial I/O (RS232/423)
type: source
parent: [[sources/naug]]
pages: 240-256
section: §15
tags: [rs232, rs423, 6850, serial-ula, acia, cassette]
updated: 2026-05-13
---

# NAUG Ch15 — Serial I/O (RS232 / RS423)

Holmes & Dickens, *The New Advanced User Guide*, pp.240-256. The BBC's serial port: hardware (6850 ACIA + Serial ULA), Acorn's 5-pin DIN connector, OS calls for baud rate / input/output stream selection / RS423-vs-cassette switching.

## Key facts captured

- **Hardware**: 6850 ACIA at SHEILA `&FE08-&FE0F` + Serial ULA at SHEILA `&FE10-&FE17`.
- **Connector**: 5-pin DIN on the back of the BBC. Signals: ground, CTS, TD, RD, RTS.
- The Acorn philosophy was deliberately minimalist — full RS232 has 25 pins; Acorn uses 5.
- The BBC uses **RS423** electrical levels (compatible with RS232 over short cables, more robust over long ones). Master series reverted to calling it RS232 in marketing, but the hardware is essentially identical.
- RTS/CTS handling on BBC is **not standard RS232 semantics**: BBC asserts RTS until its receive buffer fills, deasserts when full. Compatible with another BBC; for IBM-PC interop, RTS/CTS lines must usually be cross-wired specifically.

## Acorn 5-pin DIN socket

```
 1  signal ground
 2  CTS  (clear to send, input)
 3  TD   (transmitted data, output)
 4  RD   (received data, input)
 5  RTS  (request to send, output)
```

**Plug insertion warning**: the DIN can physically insert in two 180°-rotated orientations. Wrong orientation usually doesn't damage but doesn't work either. The notch in the metal shield should face **left of the computer** (when looking at the rear).

## 6850 ACIA

Asynchronous Communications Interface Adapter — Motorola's classic UART chip. Drives the actual byte-level serial framing.

### Registers

| SHEILA | Function |
|---|---|
| `&FE08` | Status (read) / Control (write) |
| `&FE09` | Receive data (read) / Transmit data (write) |

Mirrored across `&FE08-&FE0F` (any address in range hits the same regs).

### Control register bits

Set via `OSBYTE &9C` (Tube-safe; also updates OS shadow copy):

| Bits | Field | Effect |
|---|---|---|
| 1-0 | Clock divider | `00` ÷1, `01` ÷16, `10` ÷64 (default RS423), `11` master reset |
| 4-2 | Data format | 8 combinations: word length (7/8), parity (even/odd/none), stop bits (1/2) |
| 6-5 | RTS + TX IRQ | `00` RTS low, TX IRQ off; `01` RTS low, TX IRQ on; `10` RTS high, TX IRQ off; `11` RTS low + break-level + TX IRQ off |
| 7 | RX IRQ enable | Receive data full / over-run / DCD transition IRQ |

Data format table (NAUG §15.3.7 p245):

| 4-2 | Word | Parity | Stop bits |
|---|---|---|---|
| 000 | 7 | even | 2 |
| 001 | 7 | odd | 2 |
| 010 | 7 | even | 1 |
| 011 | 7 | odd | 1 |
| 100 | 8 | — | 2 |
| 101 | 8 | — | 1 |
| 110 | 8 | even | 1 |
| 111 | 8 | odd | 1 |

The clock divider (bits 1-0 = `10`, ÷64) is what baud-rate selection relies on. **Don't change it unless you're also driving CFS.**

## Serial ULA

8-bit **write-only** register at SHEILA `&FE10`. Controls baud rate selects, RS423/cassette switch, cassette motor.

```
bit:  7   6   5   4   3   2   1   0
      M   S   r1  r2  r3  t1  t2  t3
```

| Bits | Field |
|---|---|
| 7 | M — cassette motor + relay (1 = on) |
| 6 | S — system select: 1 = RS423, 0 = cassette |
| 5-3 | Receive baud rate select (inverted, +1) |
| 2-0 | Transmit baud rate select (inverted, +1) |

The OS shadow copy lives in zero-page workspace; access via OSBYTE `&F2` (read only — direct writes would desync). Direct hardware writes via `STA &FE10` are valid but bypass the shadow.

### Baud rate codes

Both `OSBYTE &07` (set rx baud) and `OSBYTE &08` (set tx baud) take X = code:

| X | Baud |
|---|---|
| 0 | 9600 |
| 1 | 75 |
| 2 | 150 |
| 3 | 300 |
| 4 | 1200 |
| 5 | 2400 |
| 6 | 4800 |
| 7 | 9600 |
| 8 | 19200 |

The OS converts X to the ULA's inverted-plus-1 encoding internally.

## OS calls — RS423 / RS232

| OSBYTE | Function |
|---|---|
| `&02` (2) | Select input stream (X=0 kbd, 1 RS232, 2 both) |
| `&03` (3) | Select output stream (X bits select RS232 / VDU / printer / spool) |
| `&07` (7) | Set RS423 receive baud rate |
| `&08` (8) | Set RS423 transmit baud rate |
| `&89` (137) | Cassette motor (X=0 off, X=1 on) |
| `&9C` (156) | R/W 6850 control register + OS shadow |
| `&B0` (176) | R/W CFS timeout counter (decremented per vsync = 50 Hz) |
| `&B5` (181) | R/W RS423 mode |
| `&BF` (191) | R/W RS423 use flag (bit 7) |
| `&C0` (192) | Read OS copy of 6850 control reg (don't write — would desync) |
| `&CB` (203) | R/W RS423 handshake level (free-space threshold; default 9) |
| `&CC` (204) | R/W RS423 input suppression flag |
| `&CD` (205) | R/W RS423/cassette selection (`&00` = serial, `&40` = cassette). Change takes effect on next baud-rate select. |
| `&E8` (232) | R/W 6850 IRQ bit mask |
| `&F2` (242) | Read OS copy of serial ULA register |

### RS423 mode (OSBYTE `&B5`)

| Flag | Behaviour |
|---|---|
| 0 | ESCAPEs recognised from RS423; soft keys expanded; input-buffer event fires; cursor editing works |
| 1 (default) | All bytes go straight into buffer; no event; no ESCAPE recognition |

For terminal emulators / file transfer, mode 1 is correct (don't want incoming `&1B` to abort). For interactive use (remote console), mode 0.

### Handshake threshold (OSBYTE `&CB`)

When the input buffer has fewer than X bytes free, the OS deasserts RTS to stop the sender. Default 9 — leaves room for ~9 in-flight bytes after RTS goes high before overrun.

## CFS — Cassette Filing System

The cassette tape system shares hardware (6850 + Serial ULA) with RS423; they're switched via ULA bit 6.

CFS baud rates: **300** and **1200**. Selected via the 6850 clock divider — `OSBYTE &8C` (`*TAPE`) configures this. Once switched to cassette mode, the same OSBYTEs `&07`/`&08` won't work (they assume RS423 ÷64 clocking).

CFS timeout (`OSBYTE &B0`) decremented every vsync (50 Hz) — times inter-block gaps + leader tones on tape reads.

## Filed into

- `[[hardware/6850-acia]]` — Chip register reference + control word format.
- `[[hardware/serial-ula]]` — ULA register + baud-rate encoding.
- `[[os/serial]]` — OS call reference + Acorn 5-pin pinout + RS423 mode discussion.

## Open follow-ups

- **CFS programming details** — tape format covered briefly in Ch16 (`[[sources/naug-ch16-filing]]` §16.3.1). Not file-system-level interesting.
- **Software UART** — there's no NAUG coverage of bit-banging your own serial via User VIA, but it's a reasonable performance project (would give finer baud-rate control and arbitrary protocols).
- **6850 IRQ handling** — captured in `[[os/interrupts]]` already; cross-link confirmed.
