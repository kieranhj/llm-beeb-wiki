---
title: NAUG Ch18 — Tube / Second Processor
type: source
parent: [[sources/naug]]
pages: 334-358
section: §18
tags: [tube, second-processor, parasite, copro, 6502-2p, z80, 32016]
updated: 2026-05-13
---

# NAUG Ch18 — Second Processors and the Tube

Holmes & Dickens, *The New Advanced User Guide*, pp.334-358. The **Tube** is the hardware + software interface between the BBC (host / "I/O processor") and an external CPU board ("second processor" / "parasite"). The host owns all I/O; the parasite has only CPU + RAM + OS ROM + Tube ULA.

## Architecture

```
+-----------------------------+      +-----------------------------+
|   BBC (I/O processor)       |      |   Second processor          |
|   - all I/O (screen, kbd,   |      |   - CPU (6502/Z80/32016/..) |
|     printer, disc, ADC..)   | +--+ |   - RAM (~64 KB to 4 MB)    |
|   - current language ROM    |<|T |>|   - OS ROM (small)          |
|   - paged ROMs              | |ub| |   - Tube ULA                |
|   - 16/32K user RAM         | |e | |   - **no I/O hardware**     |
|   - Tube ULA @ &FEE0-&FEFF  | +--+ |   - Tube ULA @ &FEF8-&FEFF  |
+-----------------------------+      +-----------------------------+
```

When a Tube is active:
- The **parasite** runs the current language (BASIC etc.) — copied across at language-select time.
- The **host** runs the Tube servicing code (in language workspace `&400-&7FF`).
- Every I/O call on the parasite generates a Tube transaction → host handles it (OSWRCH, OSRDCH, OSFILE, etc.) → result returned.

## 32-bit addressing across the Tube

Logical 4 GB address space (filing systems and OSWORD `&05`/`&06`):

- `&FFFF0000-&FFFFFFFF` (top 64 KB of 4 GB) = **I/O processor memory**.
- Everything below = **second processor memory** (typically only the low 64 KB on a 6502 2P; more on Z80 / 32016).

When a filing system can't detect a Tube, only the low 2 bytes are used (= 64 KB host space).

## Tube ULA registers

The ULA implements **four register pairs** (status + data), each 8 bits wide. Addresses differ on each side:

| Reg | Host addr | Parasite addr | Purpose |
|---|---|---|---|
| R1 status | `&FEE0` | `&FEF8` | bit 7 = data present, bit 6 = not filled, bits 5-0 = control |
| R1 data | `&FEE1` | `&FEF9` | OSWRCH, events, ESCAPE. Writing IRQs parasite. |
| R2 status | `&FEE2` | `&FEFA` | bit 7 = data, bit 6 = not filled |
| R2 data | `&FEE3` | `&FEFB` | Other OS calls |
| R3 status | `&FEE4` | `&FEFC` | as above |
| R3 data | `&FEE5` | `&FEFD` | **Data transfer & I/O errors. Writing NMIs parasite.** |
| R4 status | `&FEE6` | `&FEFE` | as above |
| R4 data | `&FEE7` | `&FEFF` | Control of data transfer. Writing IRQs parasite. |

Register 1 status has additional control bits:
- bit 5 P: parasite reset (active low)
- bit 4 V: enable 2-byte FIFO on R3
- bit 3 M: enable parasite NMI from R3
- bit 2 J: enable parasite IRQ from R4
- bit 1 I: enable parasite IRQ from R1
- bit 0 Q: enable host IRQ from R4

R3 (and optionally R4) is **FIFO-buffered** — for queued data transfers. R1, R2, R4 are simple latches.

**Don't poke Tube registers directly** except when implementing custom filing systems. Indiscriminate writes cause unserviceable interrupts → host crash.

## OS call dispatch over the Tube (parasite → host)

NAUG §18.6 table (p333):

| Call | Reason code (R2) | → host bytes | ← host bytes |
|---|---|---|---|
| OSRDCH | `&00` | 0 | 2 (C flag bit 7, then char) |
| OSCLI | `&02` | var (cmd + `&0D`) | 1 (`&7F`) |
| OSBYTE A<&80 | `&04` | 2 (X, A) | 1 (X) |
| OSBYTE A≥&80 | `&06` | 3 (X, Y, A) | 3 (C bit 7, Y, X) |
| OSWORD A≠0 | `&08` | var | var |
| OSWORD A=0 | `&0A` | 5 (max, min, len, addr) | var (`&FF` ESC or `&7F` ack + line) |
| OSARGS | `&0C` | 6 (Y, 4 bytes, A) | 5 (A, 4 bytes) |
| OSBGET | `&0E` | 1 (Y) | 2 (C bit 7, A) |
| OSBPUT | `&10` | 2 (Y, A) | 1 (`&7F`) |
| OSFIND | `&12` | var | 1 (handle or `&7F`) |
| OSFILE | `&14` | 17 (bytes 3-18 + A) | 17 |
| OSGBPB | `&16` | 14 | 15 |
| OSWRCH | (R1) | 1 char | 0 |

Calls go via the data register noted (R1 for OSWRCH; R2 for everything else).

Host → parasite events use R1 (BRK = R4 reason `&FF` then R2 message; events = 1 byte block; ESCAPE flag change = 1 byte; data transfer begin = R4 reason then params).

## Tube software entry points on the I/O processor

Loaded at `&400-&7FF` (overlays language workspace when Tube active):

| Entry | Function |
|---|---|
| `&400` | Copy current language to second processor |
| `&403` | Copy ESCAPE flag to second processor |
| `&406` | **Transfer data / claim / release / execute** — the entry point user software can call |

## `&406` — the user-facing entry

`A` = reason code. Two classes:

### Claim / release

| A | Function |
|---|---|
| `&C0 + caller_id` | Claim the Tube. Returns C=1 on success, C=0 if busy (caller should retry). |
| `&80 + caller_id` | Release. Only the original claimer (matching `caller_id`) can release. |

Caller IDs reserved:
- `&0` = CFS
- `&1` = DFS
- `&2` = NFS low-level
- `&3` = NFS high-level
- `&4`-`&3F` = user-assignable

```asm
.claim
    PHA
.retry
    LDA #&C0 + my_id
    JSR &0406
    BCC retry          ; C=0 means busy, spin
    PLA
    RTS

.release
    PHA
    LDA #&80 + my_id
    JSR &0406
    PLA
    RTS
```

### Data transfer / execute (after claiming)

X+Y point to a parameter block containing a **32-bit second-processor address** (4 bytes, LSB first).

| A | Function | Init delay | Per-byte delay |
|---|---|---|---|
| 0 | Multi-byte read (2P → I/O) | 24 µs | 24 µs |
| 1 | Multi-byte write (I/O → 2P) | 0 | 24 µs |
| 2 | Multi-byte-pair read (2P → I/O) | 26 µs | 26 µs/pair |
| 3 | Multi-byte-pair write (I/O → 2P) | 0 | 26 µs/pair |
| 4 | **Execute at given address** (no return) | — | — |
| 5 | Reserved | — | — |
| 6 | 256-byte read (2P → I/O) | 19 µs | 10 µs/byte |
| 7 | 256-byte write (I/O → 2P) | 0 | 10 µs/byte |

Once initiated, the host reads/writes bytes by accessing the **R3 data register** at `&FEE5` directly (with the per-byte delay between accesses). The delay is mandatory — the chip needs time to refill the FIFO from the parasite side.

Reason 4 (execute) has implicit Tube release — no need to call release after.

For other reasons, the caller must explicitly release once done.

## Tube OSBYTE / OSWORD

| Call | Function |
|---|---|
| OSBYTE `&EA` (234) | R/W Tube-present flag (0 = absent, `&FF` = present). Read first before any `&406` call. |
| OSWORD `&05` (5) | Read byte of I/O processor memory (from parasite). 5-byte block: 4-byte address + byte. |
| OSWORD `&06` (6) | Write byte of I/O processor memory. Same block. |
| OSWORD `&FF` (Z80) | Z80-specific bulk transfer. 13-byte block (i/o addr, z80 addr, length, R/W). |

For *single byte* host-memory access from the parasite, OSWORD `&05`/`&06` is the way. For *bulk* transfers, use the `&406` data-transfer protocol.

## Parasite memory map

```
&FFFF +--------------------------+
      | Tube hardware            |
      | + parasite OS ROM        | &F800-&FFFF (2 KB)
&F800 +--------------------------+
      | user memory              |
&C000 +--------------------------+
      | current language         | &8000-&BFFF (16 KB, not relocated)
&8000 +--------------------------+
      | main user memory         |
 OSHWM+--------------------------+
      | language workspace       | &0400-&07FF
&0400 +--------------------------+
      | OS workspace             |
&0000 +--------------------------+
```

OSHWM on a 6502 2P typically = `&0800`. Up to 44 KB user RAM available with BASIC relocated to `&B800`.

Zero page is usable up to `&EE` (the OS uses `&EE-&FF`). Page 2 indirection vectors not used by the parasite OS are also free.

## Things that change when Tube is active

- **Host OSHWM bumps by `&600`** — fonts are auto-exploded on Tube (`OSBYTE &14`). E.g. Model B with DFS goes from `&1900` to `&1F00`.
- **Tube code occupies `&400-&7FF`** on the host (overlays language workspace).
- **Direct screen pokes don't work** from the parasite — screen RAM is in the host, not the parasite's address space. Either use OSWRCH (slow) or use the `&406` transfer protocol from the parasite to push pixel data to host screen RAM.
- **IRQ1V/IRQ2V on parasite are not implemented** — IRQs are physically in the host. Interrupt-driven user code must live in the host (in a service ROM or installed via host-side initialisation). The "event handling" workaround: install event handlers on the host from the parasite via OSWORD `&06` writes.
- **Tube events get 10 ms not 2 ms** — event handlers across the Tube have a longer budget because of the round-trip cost.

## Filed into

- [[hardware/tube-ula]] — Tube ULA register reference (host + parasite addresses).
- [[os/tube]] — Tube software protocol: claim/release/transfer, OSBYTE `&EA`, OSWORDs `&05`/`&06`, parasite OS dispatch table, what changes when Tube is active.
- Updates: cross-links to [[hardware/6502]] (6502 2P at 3 MHz), [[memory/memory-map]] (Tube at `&FEE0`), [[os/calls]] (Tube-safe vs non-vectored variants).

## Open follow-ups

- **Custom filing system implementation** over the Tube — chapter has worked example (§18.8 p346) for a 20 KB transfer ROM. Captured as pattern; full code lives in `raw/manuals/`.
- **Z80 2P OS jump table** at `&FFCE-&FFFE` — captured in source page; if Z80 work matters, file as [[os/z80-2p]].
- **32016 2P PANOS** — UNIX-like OS, separate documentation; out of scope.
- **80186 2P (Master 512)** — IBM PC emulation; out of scope.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
