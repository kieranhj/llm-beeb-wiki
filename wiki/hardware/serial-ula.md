---
title: Serial ULA
type: hardware
tags: [serial, ula, baud-rate, cassette]
sources: [naug-ch15-serial]
sheila: ["&FE10", "&FE17"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact (with expansion)]
updated: 2026-05-13
---

# Acorn Serial ULA

Custom Acorn chip — partner to the 6850 ACIA ([[hardware/6850-acia]]). Provides:

- Baud-rate clock generation for both transmit and receive (split, can be different).
- RS423-vs-cassette routing.
- Cassette motor + relay control.

Sits at SHEILA `&FE10-&FE17`. **Write-only single register at `&FE10`**.

## Register layout

```
bit:  7   6   5   4   3   2   1   0
      M   S   rxC rxB rxA txC txB txA
```

| Bit | Field |
|---|---|
| 7 | M — cassette motor + relay (1 = on) |
| 6 | S — system: 1 = RS423 active, 0 = cassette active |
| 5-3 | Receive baud rate select (3-bit code) |
| 2-0 | Transmit baud rate select (3-bit code) |

## Baud rate codes

The 3-bit code is "inverted-plus-1" relative to the OSBYTE `&07`/`&08` value:

| OSBYTE X | ULA bits 2-0 (or 5-3) | Baud |
|---|---|---|
| 0 | `000` | 9600 (alias) |
| 1 | `111` | 75 |
| 2 | `110` | 150 |
| 3 | `101` | 300 |
| 4 | `100` | 1200 |
| 5 | `011` | 2400 |
| 6 | `010` | 4800 |
| 7 | `001` | 9600 |
| 8 | `000` | 19200 |

The OS does the inversion. If you write `&FE10` directly, compute `ULA_bits = (OSBYTE_X + 1) AND 7` (with X=0 and X=8 both mapping to ULA `000`, but for different baud rates — context-dependent on whether RS423 or cassette is selected).

These rates rely on the **6850's clock divider being set to ÷64** ([[hardware/6850-acia]]). The default RS423 control word includes this divider.

## Reading the current ULA state

`&FE10` is write-only. The OS maintains a shadow copy that **OSBYTE `&F2`** reads:

```asm
LDA #&F2 : LDX #0 : LDY #&FF : JSR &FFF4
; X = current ULA register value
```

Don't *write* via `&F2` — that just updates the shadow, leaving the chip stale.

## RS423 vs cassette switch

Bit 6 selects which subsystem owns the 6850's TD/RD lines:

- **Bit 6 = 1 (RS423)**: 6850 connects to the serial DIN socket. Baud rates from the rx/tx fields.
- **Bit 6 = 0 (cassette)**: 6850 connects to the cassette interface. Baud rate fixed to CFS-appropriate value (driven by the 6850's clock-divide setting via `OSBYTE &8C`).

Switching via OSBYTE `&CD` (R/W RS423/cassette flag):
- Flag = `&00`: RS423 mode (next baud-rate select will pick this up).
- Flag = `&40`: cassette mode.

**Change only takes effect on the next baud-rate-select OSBYTE call** (§15.3.10). Just writing `&CD` flag isn't enough — follow with `OSBYTE &07` or `&08` to commit.

## Cassette motor

Bit 7 controls the cassette motor relay. Use `OSBYTE &89` (`*MOTOR`):

```asm
LDA #&89 : LDX #1 : JSR &FFF4         ; motor on
LDA #&89 : LDX #0 : JSR &FFF4         ; motor off
```

CFS load/save commands handle motor automatically. Manual control useful for searching tape or debugging.

## All-control summary via OSBYTEs

The recommended path — touch the chip only through these:

| OSBYTE | Function |
|---|---|
| `&07` (7) | Set RS423 rx baud rate |
| `&08` (8) | Set RS423 tx baud rate |
| `&89` (137) | Cassette motor |
| `&CD` (205) | RS423 / cassette select |
| `&F2` (242) | Read shadow copy |

Going direct (`STA &FE10`) is faster (~5 cycles vs OSBYTE's hundreds) but you must update the shadow byte yourself or future OS calls will desync.

## See also

- [[hardware/6850-acia]] — 6850 chip (data path).
- [[os/serial]] — Higher-level serial OS reference.
- [[memory/memory-map]] — `&FE10-&FE17` in SHEILA.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
