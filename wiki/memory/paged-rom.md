---
title: Paged ROM / Sideways RAM
type: memory
tags: [paged-rom, sideways-rom, sideways-ram, andy]
sources: [naug-ch12-memory, beebwiki-andy, master-arm, master-rm]
updated: 2026-05-14
---

# Paged ROM / Sideways RAM

The 16 KB window at `&8000-&BFFF` is **paged** — at any moment it holds one of 16 possible banks ("sideways ROMs" or "sideways RAMs"). The active bank is chosen by the **ROM paging register** at SHEILA `&FE30`.

## The paging register (`&FE30`)

```
bit:   7    6    5    4    3    2    1    0
       RAM  -    -    -    PR3  PR2  PR1  PR0
```

- **Bits 0-3 (PR0-PR3)**: ROM/RAM bank number (0-15).
- **Bit 7 (RAM select)**:
  - **Master**: when set, swaps in 4 KB of private RAM ("**ANDY**") at `&8000-&8FFF` — MOS uses this during graphics ops.
  - **B+**: when set, swaps in 12 KB of paged RAM at `&8000-&AFFF`. Can hold ROM images (loadable as the current language with `*FX 142,128`, but not retained across BREAK).
  - **Model B / Electron**: bit 7 is unused.

The Master ARM ([[sources/master-arm]] Ch 3) explicitly notes bits 4-6 of ROMSEL are reserved (always 0) — don't write them.

## Master ROM organisation (matrix-decoded)

Per [[sources/master-arm]] Ch 3 page 32, the Master's 16 ROM slots are *not* sixteen independent sockets. They are matrix-decoded:

- **Slots 4-7** are paired into two 32 KB ROM positions on the board. The least significant bit of ROMSEL picks the upper vs lower 16 KB of each 32 KB ROM. (So slots 4+5 share a 32 KB chip; slots 6+7 share a 32 KB chip.)
- **Slots 0-3** are similarly paired into two 32 KB positions on a "cartridge ROM" data path.
- **Slots 8-15** live in a single 128 KB ROM on a separate data bus (this is where MOS, BASIC, the editor, and the on-board utilities live).
- **Sideways RAM**: the Master 128 ships with **none**, but the four slots 4-7 can be link-selected to host 4 × 16 KB SWR instead of ROM (deselecting the corresponding ROM pair in 32 KB chunks). The Master Compact ships with 4 KB SWR (ANDY only).

You don't usually need to care about this from software — ROMSEL is uniform 0-15 — but the matrix matters if you're populating ROM sockets: certain ROM-slot combinations require physical link changes.

## **DO NOT** write `&FE30` directly

The MOS owns this register. It pages ROMs in and out *often* — for example, every time a `*` command is processed, every paged-ROM service call, every language-ROM call. If you write to `&FE30` without coordinating, the **current language ROM may be swapped out**, and the next instruction fetched from `&8000-&BFFF` will be from the wrong bank. The machine crashes immediately.

Use OSBYTE / service-call APIs instead. See [[os/paged-roms]] for the ROM header format, language vs service distinction, and the three safe ways to call into another ROM:

- `OSRDRM` (`&FFB9`) — single-byte read from any slot.
- `OSBYTE &8F` — issue a paged-ROM service call.
- **Extended vectors** — permanent intercept; MOS handles paging on every dispatch.

See [[os/service-calls]] for the complete service-call reason-code table.

## Standard ROM allocations (Model B with DFS + BASIC)

| Slot | Typical content |
|---|---|
| 15 | BASIC (highest priority) |
| 14 | (free) |
| ... | (free) |
| 0-13 | Filing systems, utilities — DFS usually 0 |

Slot numbers reflect **priority order** — higher number = higher priority for handling service calls. The currently active "language" ROM is selected at boot from whichever ROM has type bit indicating it's a language (Ch17).

## Sideways RAM (SWR)

B+ and Master can have some sideways slots populated with RAM instead of ROM. **`OSBYTE &44`** tests which banks contain writable memory:

```asm
LDA #&44 : JSR &FFF4
; on exit: X bits 0-3 set for banks 4-7 that are RAM
```

The OS test method (per §12.2 p159-160): switch in the candidate bank via `&FE30`, write a byte at `&80xx` (within the bank), read it back. If the read matches, the bank is RAM.

**`OSBYTE &45`** returns which SWR banks are allocated as "extended addressing" (used as workspace by ROMs).

SWR is commonly used to:
- Load a ROM image from disk into RAM and use it like a real ROM (no need to physically program an EPROM during development).
- Provide extra workspace to filing systems / utilities via pseudo-addresses.

### Master sideways-RAM addressing modes (`*SRDATA` / `*SRROM`)

Per [[sources/master-rm]] Ch G.7, the Master's 4 × 16 KB SWR banks can be addressed in two ways, **set per-bank** via `*SRDATA <bank>` (data-style) or `*SRROM <bank>` (ROM-style, default):

- **Absolute addressing** (ROM-style): bank n appears at `&8000-&BFFF` when ROMSEL = n. Read/write via direct CPU access. Used when the bank holds an executable ROM image.
- **Pseudo addressing** (data-style): the 4 banks are aliased as one **contiguous 64 KB block** addressed by special pseudo-addresses, accessible only via `*SRREAD` / `*SRWRITE` (and their OSWORD `&05`/`&06` equivalents). Bank ID = W/X/Y/Z corresponds to ROMs 4/5/6/7:

| Pseudo address range | bank ID | ROM slot |
|---|---|---|
| `&00000` - `&03FEF` | W | 4 |
| `&03FF0` - `&07FDF` | X | 5 |
| `&07FE0` - `&0BFCF` | Y | 6 |
| `&0BFD0` - `&0FFBF` | Z | 7 |

(The 16-byte gaps reserve ROM-header space; you can't pseudo-address bytes that would land on a ROM type/copyright/entry-point header.)

This lets you treat a contiguous 64 KB of SWR as a flat data store from BASIC or assembly without managing ROMSEL by hand — useful for large lookup tables, sprite banks, sample data, etc. The trade-off is that pseudo-addressed banks can't simultaneously be executed as ROM images.

## Why this matters for performance

- The 16 KB at `&8000-&BFFF` is **prime real estate** — fast (no Tube indirection), addressable directly, and you have 16 banks of it. Performance-critical code that doesn't fit in main RAM can live in a sideways ROM/RAM.
- **Cross-bank calls are expensive**: invoking code in a different ROM requires a paging-register write (a few cycles), which means you must temporarily own `&FE30`. The MOS provides `OSRDRM` for read access and a paged-ROM service-call dispatcher; *direct* JSRs into another ROM require disabling IRQs and carefully managing `&FE30`.
- ANDY (Master, 4 KB at `&8000-&8FFF`) is **always-available private RAM** invisible to most software — useful for fast-access lookup tables in performance code on Master.

## ANDY — accessing the paged RAM area

| Machine | Size | Range | Notes |
|---|---|---|---|
| B+ | 12 KB | `&8000-&AFFF` | Top of shadow RAM (above the 20 KB shadow screen). Bit 7 of `&FE30` selects. |
| Master 128 / Compact | 4 KB | `&8000-&8FFF` | Reserved for MOS use (see AllMem `&8000-&8FFF` workspace breakdown). User writes are dangerous. |

**Access methods** (from [[sources/beebwiki-andy]]):

1. **Direct paging**: write `&FE30` with the top bit set, then access `&8000+`. Same caveats as any direct `&FE30` write — prefer OSBYTE `&8F` or use only inside SEI.
2. **OSWORD `&05`** — read byte at extended address `&FFFExxxx` (xxxx = ANDY offset).
3. **OSWORD `&06`** — write byte at the same address form.

The `&FFFE`-prefix form is a Tube-safe convention.

**MOS scan rule:** MOS does not search ANDY for languages or service-ROM images. Code placed at `&8000` in ANDY cannot be entered via `*command` dispatch — JSR directly with the right ROMSEL value already set.

**B+ shadow trick:** on the B+ specifically, the paged-in ANDY window at `&A000-&AFFF` exposes a 4 KB chunk of the shadow display memory. Writing here directly modifies what the shadow screen displays — useful for fast back-buffer fills. Behaviour with shadow display disabled is undocumented.

See [[memory/memory-map]] for the wider layout. See [[memory/shadow-ram]] for screen-area RAM bank-switching (`&FE34` ACCCON), which is a separate mechanism.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
