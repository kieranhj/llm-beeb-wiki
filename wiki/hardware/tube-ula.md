---
title: Tube ULA
type: hardware
tags: [tube, parasite, 2nd-processor, fifo]
sources: [naug-ch18-tube]
sheila: ["&FEE0", "&FEFF"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-05-13
---

# Tube ULA

Custom Acorn chip implementing the **Tube** — a fast (2 MHz clocked) communication channel between the BBC ("I/O processor") and a second processor ("parasite"). The ULA sits on **both sides** of the Tube; each side sees its own copy at different SHEILA offsets.

| Machine slot | Address range |
|---|---|
| Host (I/O processor) | `&FEE0-&FEE7` |
| Parasite | `&FEF8-&FEFF` |

## Register layout

Four 8-bit register pairs (status + data). Status and data of each register are at adjacent addresses:

| Register | Host status | Host data | Parasite status | Parasite data | Purpose |
|---|---|---|---|---|---|
| R1 | `&FEE0` | `&FEE1` | `&FEF8` | `&FEF9` | OSWRCH / events / ESCAPE |
| R2 | `&FEE2` | `&FEE3` | `&FEFA` | `&FEFB` | Other OS calls |
| R3 | `&FEE4` | `&FEE5` | `&FEFC` | `&FEFD` | Data transfer / I/O errors |
| R4 | `&FEE6` | `&FEE7` | `&FEFE` | `&FEFF` | System control |

## Status register bits

R2, R3, R4 status:

| Bit | Meaning |
|---|---|
| 7 | DA — Data present (a byte is waiting to be read on this side) |
| 6 | NF — Not Filled (transmit buffer has space) |
| 5-0 | unused |

**R1 status** carries the same DA/NF plus 6 control bits:

| Bit | Name | Function |
|---|---|---|
| 7 | DA1 | Data present in R1 |
| 6 | NF1 | R1 transmit not filled |
| 5 | P | Parasite reset (active low) |
| 4 | V | Enable 2-byte FIFO on R3 |
| 3 | M | Enable parasite NMI from R3 write |
| 2 | J | Enable parasite IRQ from R4 write |
| 1 | I | Enable parasite IRQ from R1 write |
| 0 | Q | Enable host IRQ from R4 write |

## FIFO vs latch

- **R1, R2, R4** = single-byte latches. Write blocks until receiver reads.
- **R3** = FIFO. With V=1 (2-byte buffer), the host can queue multiple bytes for the parasite. R3 is the channel for bulk data transfers.

## Interrupt sources

The Tube generates **3 IRQ types on each side**, plus an NMI on the parasite:

| Source | Triggers |
|---|---|
| R1 write to parasite | Parasite IRQ (if I=1) — used for OSWRCH char, events, ESCAPE flag change |
| R3 write | Parasite **NMI** (if M=1) — high-priority data transfer |
| R4 write to parasite | Parasite IRQ (if J=1) — system control |
| R4 write to host | Host IRQ (if Q=1) — parasite initiated transaction |

NMI on data transfer is what makes 2 MHz throughput possible: the parasite can be doing other work, and an NMI immediately yanks it to service the byte.

## Hands off (mostly)

**Direct Tube register pokes are dangerous.** Writing arbitrary bytes triggers unserviceable interrupts on the other side → crash. Direct access is only appropriate when implementing a custom filing system or transfer protocol — see `[[os/tube]]` for the safe `&406` entry point.

The one exception: during a bulk transfer initiated via `&406`, you **do** read/write `&FEE5` directly (the R3 data register) to move bytes — but only after the transfer has been set up through `&406` and with the prescribed inter-byte delays.

## Hardware availability

| Machine | Tube |
|---|---|
| Model B | External (via Tube connector at rear) |
| B+ | External |
| Master 128 | External + internal co-processor socket (ITU bit in ACCCON selects) |
| Master Compact | External (via cartridge port) |
| Electron | **No Tube** (uses ULA pins differently) |

The **ACCCON `ITU` bit** (`[[memory/shadow-ram]]`) on Master selects internal vs external Tube.

## See also

- `[[os/tube]]` — Software protocol: claim/release, data transfer, OS dispatch.
- `[[memory/memory-map]]` — Tube range `&FEE0-&FEFF` in the SHEILA map.
- `[[memory/shadow-ram]]` — ACCCON ITU bit.
- `[[os/calls]]` — OSWRCH / OSRDCH non-vectored variants (`NVWRCH` / `NVRDCH`) that don't pass over Tube.
