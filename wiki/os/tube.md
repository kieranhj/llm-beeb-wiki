---
title: Tube — Software Protocol
type: os
tags: [tube, 2nd-processor, parasite, transfer, claim]
sources: [naug-ch18-tube, master-arm]
updated: 2026-05-16
---

# Tube — Software Protocol

How code on either side of the Tube uses it. For the chip-level hardware reference, see [[hardware/tube-ula]].

## Detect a Tube — OSBYTE `&EA`

```asm
LDA #&EA : LDX #0 : LDY #&FF : JSR &FFF4
; X = &FF if Tube present, 0 if not
```

**Always call this first** before using `&406` entries. The Tube code at `&400-&7FF` is only loaded when a Tube is present; otherwise that range is language workspace and JSR-ing there crashes.

## What changes when Tube is active

- Current language is **copied to the parasite** at language-select time.
- Service-call paged-ROM dispatch still runs on the host.
- Host **OSHWM bumps by `&600`** (fonts auto-exploded via `OSBYTE &14`).
- Tube transfer code occupies host `&400-&7FF` (overlays language workspace, which is unused because the language is on the parasite).
- Parasite has **no I/O hardware** — all OSWRCH/OSRDCH/OSFILE pass over the Tube to the host.
- **Direct screen pokes from the parasite don't work** — screen RAM is in host memory.
- **IRQ1V/IRQ2V on the parasite are not implemented** — interrupts are physical on the host. To get interrupt-driven behaviour, install handlers on the host (via OSWORD `&06` or via paged-ROM service ROM).

## OS calls on the parasite

OSWRCH, OSRDCH, OSBYTE, OSWORD, OSFILE, OSARGS, OSBGET, OSBPUT, OSGBPB, OSFIND, OSCLI all work at the same `&FFxx` entry addresses on the parasite — but they round-trip to the host via the Tube. The parasite OS implements them by writing reason codes to R2 (or R1 for OSWRCH).

Dispatch table (parasite → host, NAUG §18.6 p333):

| Call | R | Bytes to host | Bytes from host |
|---|---|---|---|
| OSWRCH | R1 | 1 (char) | 0 |
| OSRDCH | R2 reason `&00` | 0 | 2 (C, A) |
| OSCLI | R2 reason `&02` | var (cmd + CR) | 1 (`&7F`) |
| OSBYTE A<&80 | R2 reason `&04` | 2 (X, A) | 1 (X) |
| OSBYTE A≥&80 | R2 reason `&06` | 3 (X, Y, A) | 3 (C, Y, X) |
| OSWORD A≠0 | R2 reason `&08` | var | var |
| OSWORD A=0 | R2 reason `&0A` | 5 (max, min, len, addr) | var |
| OSARGS | R2 reason `&0C` | 6 | 5 |
| OSBGET | R2 reason `&0E` | 1 (Y) | 2 (C, A) |
| OSBPUT | R2 reason `&10` | 2 (Y, A) | 1 (`&7F`) |
| OSFIND | R2 reason `&12` | var | 1 |
| OSFILE | R2 reason `&14` | 17 | 17 |
| OSGBPB | R2 reason `&16` | 14 | 15 |

Host → parasite (events / errors / data transfer setup) uses R1 / R2 / R4 in defined formats.

## The `&406` Tube entry — for filing systems and bulk transfer

`JSR &0406` is the user-side entry for everything beyond simple OS calls. **Always call from the I/O processor** (host) — this code doesn't exist on the parasite.

### Claim

```asm
.try_claim
    LDA #&C0 + my_id      ; my_id ∈ 0..63
    JSR &0406
    BCC try_claim         ; C=0 = busy, spin
    ; success — Tube is yours
```

Reserved caller IDs (6-bit, OR'd with `&C0` to claim or `&80` to release). Full list per [[sources/master-arm]] Ch 12:

| ID | Filing system |
|---|---|
| `&0` | CFS (cassette) |
| `&1` | DFS |
| `&2` | NFS — low-level network |
| `&3` | NFS — filing system layer |
| `&4` | ADFS |
| `&5` | TFS (Telesoft) |
| `&6` | Reserved for Acorn |
| `&7` | VFS (video filing system) |
| `&8` | SRM (SRAM utilities) |
| `&9` | Z80 (for CP/M) |
| `&F` | (Used by an independent manufacturer per ARM Ch 12) |
| `&A-&E`, `&10-&3F` | User-assignable |

Claim with `LDA #&C0|id`, release with `LDA #&80|id`.

### Release

```asm
LDA #&80 + my_id
JSR &0406
```

Must use the same ID you claimed with. Tube transactions sandwich between claim and release.

### Data transfer

After claiming, call `&406` with `A` = reason code (0-7) and X+Y = parameter-block address. The block contains a **32-bit parasite-side address** (4 bytes LSB-first).

| A | Direction | Granularity | Init delay | Per-byte delay |
|---|---|---|---|---|
| 0 | 2P → host | byte | 24 µs | 24 µs |
| 1 | host → 2P | byte | 0 | 24 µs |
| 2 | 2P → host | byte pair | 26 µs | 26 µs |
| 3 | host → 2P | byte pair | 0 | 26 µs |
| 4 | execute at parasite addr | — (implicit release, no return) | — | — |
| 5 | reserved | — | — | — |
| 6 | 2P → host | 256-byte block | 19 µs | 10 µs |
| 7 | host → 2P | 256-byte block | 0 | 10 µs |

After the `&406` call, the actual byte-by-byte data moves through **R3 at `&FEE5`** — direct host-side reads/writes to that address. The mandatory delays between accesses give the Tube ULA time to refill/drain the FIFO from the parasite.

### Worked transfer pattern (host side)

```asm
; Set up parameter block at &2F00 with parasite source address
LDA #addr_lo  : STA &2F00
LDA #addr_mid : STA &2F01
LDA #addr_hi  : STA &2F02
LDA #addr_top : STA &2F03   ; usually 0 for low 64K of parasite

; Claim
.claim_loop
    LDA #&C0+id : JSR &406 : BCC claim_loop

; Initiate 256-byte read from 2P
LDX #&00 : LDY #&2F : LDA #6 : JSR &406

; Initial delay ≥ 19 µs (38 cycles at 2 MHz)
LDX #6 : .id   DEX : BNE id

; Read 256 bytes via R3, with 10 µs per byte
LDY #0
.loop
    LDA &FEE5
    STA (dest),Y
    NOP : NOP : NOP        ; ~5 cycles padding for 10 µs (4 + 4 + 4 = need ~12 = 6 µs more)
    INY
    BNE loop

; Release
LDA #&80+id : JSR &406
```

The exact NOP padding depends on the rest of the loop body — measure on real hardware or in emulator.

## File-address encoding for Tube-aware filing systems

When a parasite program calls OSFILE/OSGBPB, the LOAD/EXEC addresses in the control block are **32-bit** and the upper 16 bits select where in the host/parasite address space the file lands. Per [[sources/master-arm]] Ch 12:

| Upper 16 bits | Lower 16 bits | Interpretation |
|---|---|---|
| `&FFFF` | `&0000-&FFFE` | **Host main memory** at the lower-16-bit address. **`&FFFF0400-&FFFF07FF` is reserved for Tube comms code when the Tube is active — do not overwrite.** |
| `&FFFE` | `&3000-&7FFF` | **Host shadow memory** (LYNNE) — same address window as the main screen. Not supported by CFS / TFS / RFS. |
| `&FFFFFFFF` | (full word) | Indicates the named program is to be `*EXEC`ed (script-style ingestion). |
| `&JKLM` (anything else) | `&0000-&FFFF` | **Parasite memory** — up to a 4 GB parasite address space (`&00000000-&BFFFFFFF`). |

Filing systems must inspect these bits and dispatch the actual data transfer either locally (host case) or via the `&406` claim/transfer/release dance (parasite case). The Master ADFS and ANFS handle all four cases correctly; older filing systems may not — CFS in particular only knows host addresses.

When writing a Tube-aware utility ROM, set the LOAD/EXEC addresses with the appropriate prefix to control where the file lands. A common pattern for "load a helper into host memory but execute it on the parasite" is:

```asm
; LOAD addr = &FFFF1F00  (host memory, page 1F)
; EXEC addr = &00001F00  (parasite call address)
```

The filing system loads the bytes into host page 1F, then the parasite jumps to its own 1F00 — which only works if you've also stashed a parasite-side copy. The usual approach is two separate `*LOAD` calls, one per side.

## OSWORD `&05`/`&06` — single-byte host memory access from parasite

For one-off reads/writes of host memory from the parasite:

```asm
; Parameter block:
;   +0..3 = 32-bit host address (use &FFFFxxxx for low 64K)
;   +4    = byte (output for read, input for write)

LDX #pb MOD 256
LDY #pb DIV 256
LDA #5            ; or 6 for write
JSR &FFF1
; for OSWORD &05: byte returned at pb+4
```

Slow (full OSWORD round-trip per byte) but simple. For bulk data, use the `&406` protocol from the host side — write a "fetch from parasite" routine and put it in a service ROM.

## Performance notes

- A **single OSWRCH from the parasite** is ~10× slower than on a non-Tube machine. For text-heavy parasite code, that adds up fast.
- **Bulk transfers via reason 6/7** approach 100 KB/s — limited by the 10 µs/byte (16 cycles between reads at 2 MHz host). The actual throughput depends on the parasite's CPU speed and the inter-byte instruction overhead.
- A **6502 second processor at 3 MHz** runs user code ~50% faster than the host ([[hardware/6502]]), but every I/O call pays Tube round-trip. Compute-heavy code wins; I/O-heavy code loses.
- **Direct hardware pokes on the parasite** are pointless — the parasite has no I/O. Any "use direct STA &FE21 for fast palette change" trick must run **on the host**, installed there by the parasite (via `&406` reason 1 + reason 4 to write then execute the code in host memory).

## NVWRCH / NVRDCH and the Tube

`NVWRCH` (`&FFCB`) and `NVRDCH` (`&FFC8`) — the non-vectored OSWRCH / OSRDCH variants — **bypass the Tube indirection**. They write/read directly on whichever processor they're called from. Useful as a 3-cycle saving when:

- On the host: you know there's no Tube, or you specifically want to keep the call local.
- On the parasite: you're outputting to the parasite's own OS (rare, but valid for some debug paths).

For Tube-transparent code, **don't** use NVWRCH/NVRDCH.

## See also

- [[hardware/tube-ula]] — Tube ULA registers + IRQ sources.
- [[memory/memory-map]] — Tube at `&FEE0-&FEFF` (host) / `&FEF8-&FEFF` (parasite).
- [[memory/shadow-ram]] — ACCCON `ITU` bit (Master internal/external Tube select).
- [[hardware/6502]] — 6502 2P at 3 MHz, Master Turbo at 4 MHz.
- [[os/calls]] — OS entry points (all Tube-aware except NVWRCH/NVRDCH).
- [[os/paged-roms]] — service ROMs as the right place for Tube transfer code.
