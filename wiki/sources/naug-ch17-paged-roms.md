---
title: NAUG Ch17 — Paged ROMs
type: source
parent: [[sources/naug]]
pages: 290-333
section: §17
tags: [paged-rom, service-call, language-rom, rfs, osrdrm, sideways-ram]
updated: 2026-05-13
---

# NAUG Ch17 — Paged ROMs

Holmes & Dickens, *The New Advanced User Guide*, pp.290-333. Largest single chapter in the book — covers the **paged ROM as a software system**: header format, language vs service ROMs, the full service-call protocol, RFS (the *ROM filing system), OSRDRM, extended vectors, 100 Hz polling.

This complements [[memory/paged-rom]] (which covers the hardware paging — `&FE30`, ANDY, sideways RAM testing). Ch17 is about what lives in the 16 KB ROM window and how it talks to MOS.

## Key facts captured

### ROM types

- **Language ROM**: provides a language entry point at offset 0. Receives control after reset / `*` command. Owns user RAM `OSHWM..HIMEM` and 4 pages of workspace at `&400-&7FF` plus zp `&00-&8F`. Examples: BASIC, FORTH, BCPL, VIEW.
- **Service ROM**: provides a service entry point at offset 3. Called by MOS on every service-call event (unknown `*` command, BRK, OSBYTE/OSWORD passthrough, etc.). Examples: DFS, ADFS, printer drivers.

Most ROMs are *both* — a language ROM with a service entry. BASIC is the historical exception (language-only).

### ROM header (16 + t + v + c bytes)

```
offset  size  field
   0     3    JMP <language_entry>   ; or three zeros if not a language
   3     3    JMP <service_entry>
   6     1    ROM type byte
   7     1    copyright offset (= 10 + len(title) + len(version))
   8     1    binary version number
   9    [t]   title string (terminated by zero)
  9+t    1    zero byte
 10+t   [v]   version string (e.g. "1.00")
 10+t+v 1    zero byte
 11+t+v [c]   copyright string — MUST start with "(C)" (`&28,&43,&29`)
 11+t+v+c 1   zero byte
 12+t+v+c 4   Tube relocation address (for 2nd-processor copy)
 16+t+v+c+ ...  code and data
```

### ROM type byte (offset 6)

| Bits | Meaning |
|---|---|
| 0-3 | Processor type: `0`=6502 BASIC, `1`=6502 Turbo, `2`=6502 code (non-BASIC), `3`=6800, `8`=Z80, `9`=32016, `&B`=80186, `&C`=80286, `&D`=ARM |
| 4 | (Electron only) Firm-key expansion present |
| 5 | Language has Tube relocation address |
| 6 | Is a language (initialise on reset) — Master is strict about this |
| 7 | Has a service entry — set on virtually all ROMs |

Typical service-only ROM: `&82` (service + 6502 code).

### Service-call dispatch

When MOS needs to do a service-call event:

1. MOS pages in each ROM **from highest priority (15) downward**.
2. JSRs the ROM's service entry (offset 3) with:
   - `A` = reason code (the "why")
   - `X` = current ROM number (so the ROM can read its slot)
   - `Y` = call-specific parameter
3. If the ROM **claims** the call: clear A (return `A=0`) and RTS. MOS stops scanning.
4. If the ROM doesn't claim: return A unchanged. MOS continues to the next-lower-priority ROM.

ROM number 15 = highest priority, 0 = lowest. So the priority gradient runs **opposite** to ROM ID — bigger number = first to see service calls.

### Service call reason codes (NAUG §17.4.1 p295-304)

Full table in [[os/service-calls]]. Highlights:

- `&01` Absolute workspace claim (reset only)
- `&02` Relative private workspace claim (reset only)
- `&03` Auto-boot (reset)
- `&04` Unrecognised `*` command — the **main extension point** for service ROMs
- `&05` Unknown interrupt — IRQ chain fallback
- `&06` BRK occurred
- `&07` Unknown OSBYTE
- `&08` Unknown OSWORD
- `&09` `*HELP` query
- `&0A`-`&0C` Workspace/NMI claim/release (issued by ROMs via OSBYTE `&8F`)
- `&0D`/`&0E` RFS init / get-byte (the *ROM filing system)
- `&0F` Vectors claimed (notify other ROMs)
- `&10` Close *SPOOL/*EXEC files
- `&11` Font implosion/explosion warning (Electron/Model B)
- `&12` Initialise filing system
- `&15` **100 Hz poll** (Electron + Master only)
- `&27` Reset call (Master)
- `&FE`/`&FF` Tube system init

### Workspace allocation protocol

On every reset, MOS issues:

1. Service call `&01` to each ROM in priority order, with Y = current "top of fixed area" (starts at `&E`, growing by Y returned).
2. Service call `&02` with Y = top of absolute area, each ROM may claim **private** pages (stored in `&DF0+ROM_ID`, one byte per ROM).
3. Service call `&03` (auto-boot) — the highest-priority filing-system ROM that responds becomes the default FS.

So a service ROM can quietly grab a page or two of RAM at reset time without the user noticing — until it pushes OSHWM up.

### Why you can't JSR into another ROM

The paging register `&FE30` is constantly mutated by MOS. If you JSR into code at `&8000-&BFFF` from outside the paged ROM, you can't guarantee which ROM is currently in. The mechanisms to safely call into another ROM:

- **`OSRDRM` (`&FFB9`)** — Read one byte from a specified ROM. Set `Y` = ROM number, `&F6/&F7` = address. Returns byte in A. The OS handles the paging for you. Slow per-byte (each call costs OSRDRM dispatch overhead). On older MOS without OSRDRM, you must do the paging yourself with interrupts disabled.
- **Service call `&8F`** — Issue a paged-ROM service call from user code (`OSBYTE &8F` with X=reason, Y=parameter). MOS scans the ROMs as usual; appropriate ROM claims and runs its service entry.
- **Extended vector** — Point an OS vector (e.g. WRCHV `&20E`) at a 3-byte entry in the **extended vector table** (origin via `OSBYTE &A8`/`&A9`). Each entry is `addr_lo, addr_hi, rom_num`. MOS will page in the named ROM before transferring control. This is how filing systems install themselves: the FS vector points to a stub in `&FF00+` that jumps via extended-vector to ROM code.

### OSRDRM — read byte from any ROM

`JSR &FFB9` (no indirection). Set:
- `Y` = ROM number
- `&F6/&F7` = address within `&8000-&BFFF`

Returns byte in A. Not available across Tube (second processor can't reach the paging register).

### Extended-vector layout

OS vectors at `&200-&234` (e.g. WRCHV `&20E`) by default point into MOS ROM. To intercept:

1. OS vector → stub address in `&FF00+vector_num*3` (in MOS ROM).
2. That stub reads the 3-byte entry at `extvec_origin + vector_num*3`:
   - 2 bytes target address
   - 1 byte ROM number (MOS pages it in first)
3. JMPs to the target address.

`OSBYTE &A8`/`&A9` returns the LSB/MSB of `extvec_origin`. Procedure to hook (NAUG §17.4.3 p312-313):

```asm
; Want to intercept vector number n (e.g. n = &E/2 = 7 for WRCHV)
; 1. SEI
; 2. Read OSBYTE &A8/&A9 → V (extended vector origin)
; 3. Store my_entry_addr_lo at V + 3n
;    Store my_entry_addr_hi at V + 3n + 1
;    Store my_rom_num       at V + 3n + 2
; 4. Save (vector &200+2n) for chain-through
; 5. Write &FF00+3n into (&200+2n)
; 6. CLI
```

### 100 Hz paged-ROM polling (Master/Electron only)

If your ROM wants to do background work every 10 ms without owning an IRQ:
- `OSBYTE &16` — increment polling semaphore.
- `OSBYTE &17` — decrement polling semaphore.
- `OSBYTE &B9` — read/write semaphore.

When the semaphore is non-zero, MOS issues service call `&15` at 100 Hz. Your ROM should decrement Y by the number of work-units it consumed.

### `OSBYTE &A4` — check for 6502 code

Given an address in X+Y, this OSBYTE verifies the data is a valid paged-ROM image (copyright string at offset 7, etc.) and that the processor type byte at offset 6 indicates 6502. If not a language ROM, BRKs with "This is not a language". If not 6502, BRKs with "I cannot run this code". Use before `OSBYTE &8E` to enter a sideways-RAM-loaded ROM.

## Filed into

- [[os/paged-roms]] — ROM header format, language vs service distinction, language entry protocol, ROM-installation workflow.
- [[os/service-calls]] — Complete service-call reference table with reason codes and entry/exit conventions.
- Updates: [[memory/paged-rom]] cross-links to these; previous "don't write `&FE30` directly" rule now has the OSRDRM / extended-vector alternatives spelled out.

## Open follow-ups

- `*ROM` data block format (CRC, file headers) — captured in source page but not filed into a dedicated wiki page; only useful if writing a ROM-resident filing system.
- Service call `&21-&26` (Master HAZEL workspace claims) — only relevant to filing-system development.
- Worked printer-buffer ROM example (§17.4.2) and RFS example (§17.5.7) — pattern is captured; full code in `raw/manuals/...` PDF for reference.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
