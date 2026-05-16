---
title: 1MHz Bus & Cartridge Interface
type: hardware
tags: [1mhz-bus, fred, jim, cartridge, expansion]
sources: [naug-ch23-1mhz-bus, beebwiki-cycle-stretching, master-arm, master-rm]
machines: [BBC Model B, BBC B+, Master 128, Master Compact, Electron]
updated: 2026-05-16
---

# 1MHz Bus & Cartridge Interface

The BBC's primary hardware expansion path. Where the user port ([[hardware/user-via]]) gives you 8 GPIO + 2 control lines, the 1MHz bus gives you the **full 6502 address+data bus + interrupt lines + system clock**, enough to attach memory-mapped peripherals, paged memory, FDCs, sound chips, sample players, anything that wants real bus access.

## Architecture

Three special pages of the 6502 address space are routed through the 1MHz bus (or cartridge connector):

| Page | Name | Purpose | Size |
|---|---|---|---|
| `&FC` | **FRED** | Memory-mapped I/O — 255 registers + paging register | 256 bytes |
| `&FD` | **JIM** | Paged memory — 256 bytes × selectable page | up to **64 KB** |
| `&FE` | **SHEILA** | Internal I/O (CRTC, ULA, VIAs, etc.) — see [[memory/memory-map]] | 256 bytes |

The CPU runs at 2 MHz; the 1MHz bus runs at 1 MHz. When the CPU accesses `&FC` or `&FD`, **the clock is stretched** by 1-2 extra cycles to align with the 1 MHz peripheral clock. See [[timing/cycle-stretching]] for full per-instruction cost and the (sometimes-surprising) list of other SHEILA addresses that pay the same penalty.

## The connector

34-pin IDC underneath the keyboard front edge on Model B, B+, Master 128. Pin map (§23.4 p406):

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | 0V | 2 | R/W |
| 3 | 0V | 4 | 1MHzE (clock) |
| 5 | 0V | 6 | NNMI |
| 7 | 0V | 8 | NIRQ |
| 9 | 0V | 10 | **NPGFC** |
| 11 | 0V | 12 | **NPGFD** |
| 13 | 0V | 14 | NRST |
| 15 | 0V | 16 | Audio In |
| 17 | 0V | 18 | D0 |
| 19 | 0V | 20 | D1 |
| 21 | 0V | 22 | D2 |
| 23 | 0V | 24 | D3 |
| 25 | n/c | 26 | n/c |
| 27 | A0 | 28 | A1 |
| 29 | A2 | 30 | A3 |
| 31 | A4 | 32 | A5 |
| 33 | A6 | 34 | A7 |

D4-D7 are also present — full pinout in NAUG §23.4.

- **NPGFC**: active low when CPU addresses page `&FC`.
- **NPGFD**: active low when CPU addresses page `&FD`.
- **Audio In**: 9 KΩ input to the BBC's audio amp; 3 V RMS = max volume. Useful for sample players, expansion sound boards.

## FRED — memory-mapped I/O (`&FC00-&FCFF`)

Acorn has assigned ranges of FRED to standard peripherals. **Don't trample these** if you want your hardware to coexist with other Acorn expansions:

| Range | Reserved for |
|---|---|
| `&FC00-&FC0F` | Test hardware |
| `&FC10-&FC13` | Teletext adapter |
| `&FC14-&FC1F` | Prestel |
| `&FC20-&FC27` | IEEE-488 |
| `&FC28-&FC2F` | Econet (Electron) |
| `&FC30-&FC3F` | Cambridge Ring |
| `&FC40-&FC47` | Winchester disc |
| `&FC60-&FC6F` | Serial expansion |
| `&FC80-&FC8F` | Test hardware |
| `&FCB0-&FCBF` | 6522 VIA (Electron) |
| `&FCC0-&FCCF` | 1770 FDC (Electron) |
| `&FCE0-&FCEF` | Tube (Electron) |
| **`&FCFF`** | **JIM paging register** |

User-available ranges: `&FC50-&FC5F`, `&FC70-&FC7F`, `&FC90-&FCAF`, `&FCD0-&FCDF`, `&FCF0-&FCFE`. Plenty of room for custom devices.

## JIM — paged expansion memory (`&FD00-&FDFF`)

Writing a byte `p` to `&FCFF` selects which 256-byte page `p` appears at `&FD00-&FDFF`. With 8-bit page select, total paged memory = 256 × 256 = **64 KB**.

Page allocation:
- `&00-&7F`: Acorn-reserved.
- `&80-&FF`: user.

For larger expansions you'd cascade JIM with a second paging register inside FRED (e.g. a 16-bit page latch driving an external RAM chip).

### `&00EE` — RAM shadow of the JIM paging register (IRQ-safe pattern)

The paging register at `&FCFF` is **write-only** — you cannot read back the current page. Per [[sources/master-arm]] Ch 10, Acorn allocated zero-page `&00EE` as the canonical RAM image. The MOS reset/BREAK clears both to `&00`.

**The IRQ-safe write sequence is:**

```asm
LDA #new_page
STA &EE              ; update RAM image FIRST
STA &FCFF            ; then write the register
```

The ordering matters: if an IRQ fires between the two stores and your IRQ handler also touches the paging register, the handler will read `&EE` (still the old value), do its work, and restore by writing `&EE` back to `&FCFF` — which would clobber your in-flight new value. Updating `&EE` first means the handler sees the new value if it interrupts you mid-sequence, and restores correctly.

Any code (interrupt or otherwise) that *transiently* changes the JIM page must save and restore both `&EE` and `&FCFF`:

```asm
; entry — save state
LDA &EE : PHA
LDA #my_page : STA &EE : STA &FCFF

; ... do paged-FD work ...

; exit — restore
PLA : STA &EE : STA &FCFF
```

This `&EE` convention stays in the **I/O processor's zero page even if a Tube second processor is fitted** — the paging register physically lives on the host side. Parasite code reaches it via OSBYTEs `&94`/`&95` (which the Tube ROM marshals through to the host's `&FCFF`).

## Access from CPU

Three ways:

### 1. Tube-safe via OSBYTEs

| Operation | OSBYTE | Notes |
|---|---|---|
| Read FRED  | `&92` | X = offset, Y = byte returned |
| Write FRED | `&93` | X = offset, Y = byte to write |
| Read JIM   | `&94` | (same shape) |
| Write JIM  | `&95` | |
| Read SHEILA | `&96` | also works for `&FE` |
| Write SHEILA | `&97` | |

Slow (full OSBYTE dispatch — ~hundreds of cycles), but works across the Tube. Use when your code might run on a second processor.

### 2. Direct LDA/STA from the host

```asm
LDA &FCxx        ; read FRED
STA &FCxx        ; write FRED
LDA #page : STA &FCFF   ; select JIM page
LDA &FDxx        ; access JIM
```

Fastest — clock-stretching is automatic. `LDA abs` to a `&FC`/`&FD` address costs **5-6c** vs 4c at a non-stretched address (the extra is variable by 1 MHz phase — see [[timing/cycle-stretching]]).

**Doesn't work from a Tube parasite** — the parasite has no `&FCxx` mapping. Parasite code that needs FRED access must trampoline via the Tube using OSBYTE `&92`-`&97` or via OSWORD `&05`/`&06`.

### 3. Master cartridge slot at 2 MHz

`OSBYTE &6B` selects between the external 1MHz bus and the internal cartridge slot. With X=1, cartridge accesses run at 2 MHz (twice as fast). With X=0, the 1MHz bus is active. **Only one at a time** — switching mid-flight will lose any pending 1MHz IRQ/NMI.

## Clock-stretching gotchas

The 2 MHz CPU clock is stretched to align with the 1 MHz peripheral clock on every `&FC`/`&FD` access. Stretch is **2 or 3 normal cycles** depending on the phase of the access — not a flat 2c. The same mechanism applies to most SHEILA peripherals (CRTC, ACIA, Serial ULA, both VIAs, ADC) — see [[timing/cycle-stretching]] for the full address-by-address breakdown.

Two problems result for the hardware designer attaching new devices to FRED/JIM:

### Problem 1 — address-decoding glitches

While the CPU is mid-cycle changing addresses, 1MHzE may be high. Decoders that produce a CS pulse from the address bus may briefly assert it during a transition. Generally harmless except for level-triggered devices.

### Problem 2 — double accessing

A read started when 1MHzE is high accesses the device immediately, then is repeated on the next 1MHzE high edge. **Most peripherals don't care**, but **read-clears-flag** registers (like a 6522 IFR via ORA) lose state on the spurious second read.

### Clean-up circuits

NAUG §23.5 gives two reference circuits to gate the page-select against 1MHzE:

- **Circuit 1**: NOR-gate R-S latch. Removes "P" glitches (1MHzE high), leaves "Q" glitches (1MHzE low) which are harmless for most uses. Good default.
- **Circuit 2**: D-flip-flop on rising 1MHzE edge. Produces a 100% clean page-select but with brief output pulse — tight-timing devices may not see it.

If you're attaching an off-the-shelf 6522 / 6850 / 6840 to FRED, **use clean-up circuit 1 at minimum** — the chips don't tolerate spurious chip selects.

## Bus timing minimums

| Parameter | Min | Max |
|---|---|---|
| Address set-up before 1MHzE rising | 300 ns | 1000 ns |
| Address hold after 1MHzE falling | 30 ns | — |
| NPGFC/D set-up | 250 ns | 1000 ns |
| NPGFC/D hold | 30 ns | — |
| Write data set-up before 1MHzE falling | — | 150 ns |
| Write data hold | 50 ns | — |
| Read data must be valid before 1MHzE falling | 200 ns | — |
| Read data hold after 1MHzE falling | 30 ns | — |

Assumes one peripheral on the bus. Multiple peripherals extend rise/fall times — budget accordingly.

## Hardware design rules

Per §23.6:

1. **Don't draw power** from the BBC — peripherals need their own supply.
2. **Buffer all logic lines** — one LS-TTL load max per signal at the connector.
3. **Pass-through** the bus connector so daisy-chained devices work.
4. **Terminate** all lines except NRST/NNMI/NIRQ with 2K2 pull-up + 2K2 pull-down at the end of the chain.

## Cartridge slot variant (Master / Compact / Electron Plus 1)

The cartridge connector carries the 1MHz bus signals **plus**:

- **ROMOE**: active-low chip enable for cartridge ROMs during PHI2.
- **ROMQA**: low bit of `&FE30` paging register — selects between two 16 KB ROMs in a 32 KB chip.
- **A8-A13**: extra address lines (cartridge ROMs need full 14-bit address).
- **8 MHz clock** (Master / Compact) or **16 MHz** (Electron) — for synchronous peripherals.
- **CSYNC / MADET** (Master link-12 dependent): composite sync output, or machine-detect ground (cart can detect Master vs Electron).
- **OE2 / LPSTB**: cartridge-to-cartridge or light-pen-strobe input.
- **Audio in/out** with separate analogue ground.

**Master cartridge runs at 2 MHz** when selected via `OSBYTE &6B` X=1 (or ACCCON `IFJ` bit). At 2 MHz the addressing through cartridge is not clock-stretched — fast access to whatever's plugged in.

### 27513 EPROM blocks (128 KB / cart)

Master cartridge slot can hold a 27513 EPROM: 4 × 16 KB blocks, with the **current block selected by writing the block number to any address inside the EPROM**. Code switches blocks via:

```asm
LDA #newblk
STA &8000           ; writing to ROM address triggers the EPROM's internal block latch
```

Interrupts must be handled carefully — IRQ entry in block 1, 2, or 3 means the language ROM and OS service-call dispatch may try to call back into your ROM at the wrong block. Either:
- Put interrupt-handling code at the same offset in **all 4 blocks**, or
- Switch back to block 0 on every IRQ entry, restoring the previous block on exit.

## Performance use cases

- **Custom sound chip** (extra SN76489, SID, second YM2149): wire CS to a decoded FRED address. Write rates limited by 2 MHz / clock-stretching = ~1 MByte/s peak.
- **Sample DAC** (R-2R ladder or commercial 8-bit DAC): write to a FRED address every N µs via a timer-driven IRQ. Audible up to ~8 kHz comfortably, ~22 kHz pushing.
- **Bulk RAM expansion** (32K-256K): use JIM with external page register. Useful for compiled code overlays, large lookup tables.
- **External UART / USB / Ethernet**: 6850 ACIA / 16550 / dedicated chip on FRED.
- **Custom video chip** for sprite acceleration / overlay: more involved, needs careful sync to PAL timing.

## See also

- [[memory/memory-map]] — Where FRED/JIM/SHEILA sit in the 64 KB map.
- [[hardware/user-via]] — Simpler 8-line GPIO alternative.
- [[memory/shadow-ram]] — Master ACCCON `IFJ` bit (cartridge select).
- [[os/osbyte]] — `&6B` (cart/bus select), `&92-&97` (Tube-safe FRED/JIM/SHEILA access).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
