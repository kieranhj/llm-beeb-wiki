---
title: Serial I/O (RS232 / RS423)
type: os
tags: [serial, rs232, rs423, baud, 6850, serial-ula]
sources: [naug-ch15-serial]
updated: 2026-05-13
---

# Serial I/O — MOS Interface

Reference for MOS-level serial port use. For the chip-level details, see [[hardware/6850-acia]] and [[hardware/serial-ula]].

## The 5-pin DIN socket

| Pin | Signal | Direction |
|---|---|---|
| 1 | Signal ground | — |
| 2 | **CTS** — clear to send | input |
| 3 | **TD** — transmit data | output |
| 4 | **RD** — receive data | input |
| 5 | **RTS** — request to send | output |

Notch on metal shield → **left side** of computer (correct orientation). The plug inserts physically rotated 180° too — won't damage but won't work.

**BBC-to-BBC null modem**: cross-wire TD↔RD and RTS↔CTS on each end, plus ground.

## RTS/CTS semantics on the BBC

Not standard EIA RS232. The BBC's RTS is **asserted unless the receive buffer is full**, and the BBC stops transmitting when its CTS input is unasserted. This is closer to standard DTR/DSR than to RS232 RTS/CTS — useful caveat when connecting a BBC to a PC.

For PC interop, you typically need a hardware cable that:
- Cross-wires the data lines (TD↔RD).
- Cross-wires RTS↔CTS *and* asserts the PC's DTR/DSR/DCD permanently.

A "null modem with hardware handshake" cable is what works.

## OSBYTE summary

| OSBYTE | Function | Notes |
|---|---|---|
| `&02` (2) | Select input stream | X=0 kbd, X=1 RS423, X=2 both |
| `&03` (3) | Select output stream | Bit-packed (see below) |
| `&07` (7) | Set rx baud | X = code 0-8 |
| `&08` (8) | Set tx baud | X = code 0-8 |
| `&89` (137) | Cassette motor | X=0 off, X=1 on |
| `&9C` (156) | R/W 6850 control register + OS shadow | Tube-safe path |
| `&B0` (176) | R/W CFS timeout counter | Decremented per vsync (50 Hz) |
| `&B1` (177) | R/W input source flag | Used by `&02` |
| `&B5` (181) | R/W RS423 mode | See below |
| `&BF` (191) | R/W RS423 use flag (bit 7) | Bit 7 set = free |
| `&C0` (192) | Read shadow of 6850 control reg | Don't write — would desync |
| `&CB` (203) | R/W RS423 handshake threshold | Default 9 bytes |
| `&CC` (204) | R/W RS423 input suppression | Non-zero = ignore input |
| `&CD` (205) | R/W RS423/cassette select | `&00` serial, `&40` cassette |
| `&E8` (232) | R/W 6850 IRQ bit mask | See [[os/interrupts]] |
| `&EC` (236) | R/W output stream destination flag | Used by `&03` |
| `&F2` (242) | Read shadow of serial ULA register | Read-only access |

## Baud rates

`OSBYTE &07` (rx) and `OSBYTE &08` (tx) take X = code:

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

X=0 and X=7 both give 9600 baud (legacy code aliasing). Use X=7 for clarity.

## Input stream selection (`OSBYTE &02`)

```asm
LDA #&02 : LDX #x_value : JSR &FFF4
```

| X | Effect |
|---|---|
| 0 | keyboard only (default) |
| 1 | RS423 only (keyboard disabled) |
| 2 | both keyboard + RS423 |

Returns previous source in X.

## Output stream selection (`OSBYTE &03`)

X is a bit field:

| Bit | Set means |
|---|---|
| 0 | Enable RS232/423 output |
| 1 | Disable VDU |
| 2 | Disable printer driver |
| 3 | Enable printer independent of `VDU 2`/`VDU 3` |
| 4 | Disable spooled output |
| 6 | Disable printer unless preceded by `VDU 1` |

`*FX 3,0` = defaults: RS423 disabled, VDU enabled, printer follows `VDU 2`/`VDU 3`, spool follows `*SPOOL`.

`*FX 3,1` adds RS423 output (so OSWRCH bytes go to both screen and serial).

## RS423 mode (`OSBYTE &B5`)

Controls how received RS423 bytes are processed:

| Flag | Behaviour |
|---|---|
| 0 | ESCAPE bytes generate ESCAPE events; soft-key expansion applies; input-buffer event fires per byte; cursor editing keys work |
| 1 (**default**) | Bytes go straight into buffer; no events; no escape recognition |

Mode 1 is correct for terminal emulators and file transfer (don't want stray `&1B` to abort). Mode 0 makes RS423 input behave exactly like keyboard input — useful for remote console.

## Handshake threshold (`OSBYTE &CB`)

When the RS423 input buffer has fewer than X bytes free, the OS deasserts RTS to halt the sender. Default 9. Increase for slow-responding senders, decrease if you really need every byte of buffer (and trust the sender to stop on time).

## 6850 control word — basic configuration

For standard RS423 8-N-1 at the selected baud:

```asm
; 6850 control: clk÷64, 8 bits no parity 1 stop, RTS low, TX IRQ disabled, RX IRQ enabled
LDA #&95         ; 1001 0101 — bit 7=1 (RX IRQ), bits 6-5=00 (RTS low TX off), bits 4-2=101 (8-N-1), bits 1-0=10 (÷64)
LDX #&95
LDA #&9C : JSR &FFF4
```

For raw 7-E-1 (common for ASCII terminals):

```asm
LDA #&91         ; bits 4-2=010 (7 bits, even, 1 stop)
LDX #&91
LDA #&9C : JSR &FFF4
```

## Bulk transfer pattern

For sending a buffer of bytes:

```asm
.send_loop
    LDA &FE08       ; status
    AND #&02        ; TDRE
    BEQ send_loop   ; wait until TX register empty
    LDA (src),Y
    STA &FE09       ; transmit
    INY
    BNE send_loop
    ; ... next page handling ...
```

For 9600 baud this is fine; ~960 bytes/sec means the CPU spends most of its time waiting. At 19200 it's ~1.9 KB/sec — still loosely bounded by the serial line, not the CPU.

For higher throughput consider:
- **IRQ-driven transmit** — let the TDRE IRQ wake up your buffer-drain code; foreground does other work.
- **Direct ULA write** for baud-rate switches (skips the OSBYTE overhead).

## CFS (cassette) tangent

The same 6850 + Serial ULA drive the cassette interface. Switching:

```asm
LDA #&CD : LDX #&40 : LDY #0 : JSR &FFF4   ; cassette mode flag
LDA #&8C : LDX #12 : JSR &FFF4             ; *TAPE 12 (1200 baud)
```

Back to RS423:

```asm
LDA #&CD : LDX #0 : LDY #0 : JSR &FFF4     ; serial mode flag
LDA #&07 : LDX #7 : JSR &FFF4              ; rx 9600
LDA #&08 : LDX #7 : JSR &FFF4              ; tx 9600
```

CFS timeout via `OSBYTE &B0` is a vsync-counted (50 Hz) timer for tape block gaps.

## Bypass-MOS strategies

- **Direct `STA &FE09`** for transmit — saves the OSWRCH dispatch but you must check status yourself.
- **Direct `LDA &FE09`** for receive — pulls the byte and clears RX flag in one read.
- **Custom IRQ2V handler** — claim 6850 IRQs via `OSBYTE &E8` mask, handle yourself for custom protocols (e.g. packet framing).
- **Bit-bang via User VIA** — for arbitrary baud rates or non-standard framing (SPI etc.). Costs CPU cycles but unconstrained by the 6850's framing rules.

## See also

- [[hardware/6850-acia]] — Chip details.
- [[hardware/serial-ula]] — Baud rate + cassette switch.
- [[os/interrupts]] — 6850 IRQ in MOS dispatch chain.
- [[os/buffers]] — RS423 in/out buffers (IDs 1, 2).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
