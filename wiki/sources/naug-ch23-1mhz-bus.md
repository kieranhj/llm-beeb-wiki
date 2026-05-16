---
title: NAUG Ch23 — 1MHz Bus & Cartridges
type: source
parent: [[sources/naug]]
pages: 409-425
section: §23
tags: [1mhz-bus, fred, jim, cartridge, hardware-expansion]
updated: 2026-05-13
---

# NAUG Ch23 — One Megahertz Bus & Cartridge Interfaces

Holmes & Dickens, *The New Advanced User Guide*, pp.409-425. The 1MHz bus is the BBC's hardware expansion path beyond the 8-line user port. Defines what you can plug into the underside connector, how the address-decoding works, the clean-up circuits the BBC needs (clock-stretching produces address glitches), and the Master/Compact/Electron cartridge variants.

## Key facts captured

- **Two expansion routes**: User port (8 GPIO from User VIA, [[hardware/user-via]]) or **1MHz bus** (full address bus + buffered data bus + control signals). For anything beyond simple I/O, you need 1MHz bus.
- **1MHz bus connector**: 34-pin IDC, under-keyboard front edge of mainboard. All machines except Master Compact and Electron (which use the cartridge slot instead).
- **FRED** = page `&FC` (`&FC00-&FCFF`) for memory-mapped peripherals (up to 255 registers + paging register at `&FCFF`).
- **JIM** = page `&FD` (`&FD00-&FDFF`) for paged memory — 256 bytes × paging register = **up to 64 KB of paged expansion memory**. Page selector is in FRED at `&FCFF` (the "JIM paging register").
- **SHEILA** = page `&FE`, internal I/O, also exposed read/write via OSBYTEs.
- Memory-mapped I/O OSBYTEs (Tube-safe wrappers):

| OSBYTE | Function | Page |
|---|---|---|
| `&92` (146) | Read FRED | `&FC` |
| `&93` (147) | Write FRED | `&FC` |
| `&94` (148) | Read JIM | `&FD` |
| `&95` (149) | Write JIM | `&FD` |
| `&96` (150) | Read SHEILA | `&FE` |
| `&97` (151) | Write SHEILA | `&FE` |

X = offset within page, Y = byte (write) / byte returned (read).

## FRED allocations (NAUG §23.2 p404)

Acorn-reserved per-device sub-pages within `&FC00-&FCFF`:

| Range | Device | Notes |
|---|---|---|
| `&FC00-&FC0F` | Test hardware | (cartridge: undefined) |
| `&FC10-&FC13` | Teletext adapter | |
| `&FC14-&FC1F` | Prestel adapter | |
| `&FC20-&FC27` | IEEE-488 interface | |
| `&FC28-&FC2F` | Econet (Electron) | |
| `&FC30-&FC3F` | Cambridge Ring | |
| `&FC40-&FC47` | Winchester disc | |
| `&FC60-&FC6F` | Serial expansion | |
| `&FC80-&FC8F` | Test hardware | |
| `&FCB0-&FCBF` | 6522 VIA (Electron only) | |
| `&FCC0-&FCCF` | 1770 FDC (Electron only) | |
| `&FCE0-&FCEF` | Tube (Electron only) | |
| `&FCFF` | **JIM paging register** | sets which 256-byte JIM page is visible |

Unreserved ranges (`&FC50-&FC5F`, `&FC70-&FC7F`, `&FC90-&FCAF`, `&FCD0-&FCDF`, `&FCF0-&FCFE`) are available for user hardware.

## JIM paging

- JIM pages `&00-&7F` reserved for Acorn-defined extensions.
- JIM pages `&80-&FF` available for user applications.
- Write the page number to `&FCFF` (FRED's paging register) to bring that page of expansion RAM into `&FD00-&FDFF`.

## 1MHz bus signals (34-pin connector, §23.4 p406)

Active signals (others = `0V` for shielding):

| Pin | Name | Direction | Function |
|---|---|---|---|
| 2 | R/W | output | 6502 read-not-write, buffered by 2× 74LS04 |
| 4 | 1MHzE | output | 1 MHz system clock (50% duty square) |
| 6 | NNMI | input | NMI to 6502 (3K3 pull-up). Active low edge. **Disc and Econet rely heavily** — share carefully. |
| 8 | NIRQ | input | IRQ to 6502 (3K3 pull-up). Open-collector. |
| 10 | NPGFC | output | Active low when `&FC` accessed |
| 12 | NPGFD | output | Active low when `&FD` accessed |
| 14 | NRST | output | System reset (active low) |
| 16 | Audio In | input | 9 KΩ input to audio amp; 3V RMS = max volume |
| 18-24 | D0-D7 | bidir | Data bus via 74LS245 buffer, direction = R/W |
| 27-34 | A0-A7 | output | Low 8 address lines via 74LS244 buffer |

## The clock-stretching gotcha (§23.5 p408-410)

CPU runs at **2 MHz**; 1MHz bus peripherals run at **1 MHz**. When the 6502 accesses page `&FC`/`&FD`, the CPU clock is stretched to align with the 1MHz peripheral clock. This produces two problems:

### Problem 1 — address-decoding glitches

Addresses change on the 2 MHz clock cycle. The 1MHz clock alternately high and low while the addresses change. Spurious `NPGFC`/`NPGFD` pulses can occur during the "P" glitch period (1MHzE high, addresses unsettled).

### Problem 2 — double accesses

A 1MHz access initiated while 1MHzE is high accesses the device immediately, then again on the next 1MHzE high edge. For most devices fine; for **read-clears-flag** devices (like a VIA IFR), the second access trashes state.

### Clean-up circuit 1 (§23.5.3)

R-S latch built from 3 NOR gates with 1MHzE gating the input. Removes "P" glitches; "Q" glitches (1MHzE low) remain but are harmless for most uses.

### Clean-up circuit 2 (§23.5.4)

D-flip-flop latching NPGFC/D on the 1MHzE rising edge. Produces a 100% clean page-select but with tighter timing — some peripherals can't tolerate the brief CS pulse.

## 1MHz bus timing requirements (§23.6.5 p412)

| Symbol | Description | Min | Max |
|---|---|---|---|
| t_as | Address + R/W set-up time | 300 ns | 1000 ns |
| t_ah | Address + R/W hold time | 30 ns | — |
| t_pgs | NPGFC/D set-up | 250 ns | 1000 ns |
| t_pgh | NPGFC/D hold | 30 ns | — |
| t_dsw | Write data set-up | — | 150 ns |
| t_dhw | Write data hold | 50 ns | — |
| t_dsr | Read data set-up | 200 ns | — |
| t_dhr | Read data hold | 30 ns | — |

These are minimums — assume **one peripheral on the bus**. Heavier load extends rise/fall times.

## Cartridge interface (§23.7 p413-418)

Cartridge slot on Master 128 / Master Compact / Electron Plus 1. Carries 1MHz bus signals **plus extra signals** (ROM selection, 16 MHz clock, audio routing, ROMQA paging bit, OE2/LPSTB).

**Critical Master detail**: cartridge slot can run at **1 MHz or 2 MHz**, selectable via the `IFJ` bit of ACCCON ([[memory/shadow-ram]]) or `OSBYTE &6B`:

- X=0 (`*FX 107,0`): external 1MHz bus active.
- X=1 (`*FX 107,1`): internal cartridge bus active at 2 MHz.

Only one is active at a time — switching the cartridge to 2 MHz **disconnects 1MHz bus accesses**. Don't switch while a 1MHz bus device might NMI.

## 128 KB EPROM cartridges (§23.7.1 p414)

Each Master cartridge slot can hold one 32 KB EPROM (27256) appearing as 2 paged ROMs, **or two 27513 chips** providing 4 × 16 KB blocks each = up to 128 KB per slot.

The 27513 has an internal "block select register": writing the desired block number (0-3) to any address inside the EPROM selects which 16 KB block appears. Block 0 is selected at power-up. Code that bank-switches must:

1. Live in block 0 (or copy itself to each block).
2. Have interrupt-handling code in **all 4 blocks**, or switch back to block 0 on every IRQ entry.
3. Track currently-selected block in RAM.

Example block-switch:
```asm
LDA #newblk
STA &8000        ; any address inside the EPROM works
```

## Filed into

- [[hardware/1mhz-bus]] — Bus reference, FRED/JIM allocations, clean-up circuits, design rules.
- Updates: [[memory/memory-map]] — FRED/JIM cross-link refreshed.

## Open follow-ups

- **Master Compact's joystick/mouse + cartridge slot variant** — different connector, partial signal set. Captured in source; rarely relevant unless targeting Compact specifically.
- **CRTC reset signal via cartridge** (`ROMSTB/CRTCRST` pin) — Master uses this for genlock; potentially useful for synchronisation tricks but out of scope here.
- **27513 EPROM availability** — these are obsolete; for new 128 KB cartridges, use a 27512 (64 KB) per slot with external glue logic, or modern flash.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
