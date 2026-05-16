---
title: NAUG Ch6 — OS Introduction
type: source
parent: [[sources/naug]]
pages: 107-125
section: §6
tags: [mos, os-calls, vectors, zero-page, workspace]
updated: 2026-05-13
---

# NAUG Ch6 — Introduction to the OS

Holmes & Dickens, *The New Advanced User Guide*, pp.107-125. Defines the **MOS API surface**: vectored entry points, indirection vectors, OSBYTE / OSWORD generic protocol, zero-page and page-two workspace allocation.

This is the contract the MOS exposes to user code. The wiki's [[memory/zero-page]] and [[memory/os-workspace]] close the `memory/vdu-workspace` stub that was left over from the earlier Ch13 ingest.

## Key facts captured

- All OS calls take their **primary parameter in A**. Secondary in X, Y. If more is needed, X+Y form a 16-bit pointer to a **parameter block**.
- **Vectored** calls JMP-indirect through a 2-byte vector in page 2 (e.g. `OSWRCH JMP (&20E)`). Vector contents differ per machine. Intercepting a vector lets you wedge into the OS path.
- **Non-vectored** calls (NVWRCH `&FFCB`, NVRDCH `&FFC8`, etc.) are faster (no indirection) but **not available across the Tube**.
- All OS calls **preserve the interrupt status** (though interrupts may be enabled during the call — relevant for IRQ handlers that mustn't call OS).
- Decimal flag must be CLEAR before any OS call (per Ch3 §3.2 — see [[hardware/6502]]).

## Vector & entry-point table (NAUG §6.1 p102)

| Routine | Address | Vector | Function |
|---|---|---|---|
| (User) | — | USERV `&200` | User vector (catches unknown OSWORD `&E0-&FF`) |
| (BRK) | — | BRKV `&202` | BRK handler |
| (IRQ) | — | IRQ1V `&204` | Primary IRQ vector |
| (IRQ) | — | IRQ2V `&206` | Unrecognised IRQ vector |
| OSCLI | `&FFF7` | CLIV `&208` | Command line interpreter |
| OSBYTE | `&FFF4` | BYTEV `&20A` | OSBYTE dispatcher |
| OSWORD | `&FFF1` | WORDV `&20C` | OSWORD dispatcher |
| OSWRCH | `&FFEE` | WRCHV `&20E` | Write char to output |
| OSNEWL | `&FFE7` | — | Write LF+CR |
| OSASCI | `&FFE3` | — | Write char (`&D` → LF+CR) |
| OSRDCH | `&FFE0` | RDCHV `&210` | Read char from input |
| OSFILE | `&FFDD` | FILEV `&212` | Load/save file |
| OSARGS | `&FFDA` | ARGSV `&214` | File arguments |
| OSBGET | `&FFD7` | BGETV `&216` | Get byte from file |
| OSBPUT | `&FFD4` | BPUTV `&218` | Put byte to file |
| OSGBPB | `&FFD1` | GBPBV `&21A` | Multi-byte file I/O |
| OSFIND | `&FFCE` | FINDV `&21C` | Open/close file |
| (FSC) | — | FSCV `&21E` | Filing system control |
| (Event) | — | EVNTV `&220` | Event dispatch |
| (Print) | — | UPTV `&222` | User print |
| (Econet) | — | NETV `&224` | Econet |
| (VDU) | — | VDUV `&226` | Unrecognised VDU command |
| (Key) | — | KEYV `&228` | Keyboard |
| (Buf) | — | INSV `&22A` | Insert into buffer |
| (Buf) | — | REMV `&22C` | Remove from buffer |
| (Buf) | — | CNPV `&22E` | Count/purge buffer |
| (Spare) | — | IND1V `&230` | Spare |
| (Spare) | — | IND2V `&232` | Spare |
| (Spare) | — | IND3V `&234` | Spare |
| NVWRCH | `&FFCB` | — | Non-vectored OSWRCH |
| NVRDCH | `&FFC8` | — | Non-vectored OSRDCH |
| GSREAD | `&FFC5` | — | Read char from string |
| GSINIT | `&FFC2` | — | String input init |
| OSEVEN | `&FFBF` | — | Generate event |
| OSRDSC | `&FFB9` | — | Read byte from screen / paged ROM (formerly "OSRDRM") |
| OSWRSC | `&FFB3` | — | Write byte to screen |

## OSBYTE convention (§6.3.1)

- `A` = call number.
- `X`, `Y` = parameters per call.
- On exit: A preserved, X/Y may return values.
- For OSBYTEs `&A6-&FF`: `<NEW>=(<OLD> AND Y) EOR X`; old value returned in X. Read: X=0, Y=&FF. Write: X=value, Y=0.
- Unknown OSBYTE → paged ROM service call `&07` with A/X/Y in zp `&EF`/`&F0`/`&F1`.

## OSWORD convention (§6.3.2)

- `A` = call number.
- `X`+`Y` = parameter block address (LSB+MSB).
- Block layout per call; results written back to the same block.
- Unknown OSWORD with A=`&E0-&FF` → USERV (`&200`).
- Other unknown OSWORD → paged ROM service call `&08`, A/X/Y in `&EF`/`&F0`/`&F1`.
- **DFS 0.90 bug**: that DFS version intercepts any unknown OSWORD ≥ `&80` and treats it as OSBYTE `&7F`. Avoid that range unless you know DFS 0.90 isn't present.

## Zero page allocation (§6.6.1)

The most performance-critical resource on the BBC: page 0. NAUG splits it as:

| Range | Owner |
|---|---|
| `&00-&6F` | Language workspace (BASIC has most of it) |
| **`&70-&8F`** | **User zero page** (32 bytes — safe to use) |
| `&90-&9F` | Econet workspace |
| `&A0-&A7` | NMI workspace |
| `&A8-&AF` | OS temporary workspace |
| `&B0-&BF` | FS temporary workspace |
| `&C0-&CF` | Filing system workspace |
| `&D0-&E1` | VDU workspace (see [[memory/zero-page]]) |
| `&E2-`onwards | OS / CFS / FS / OSBYTE/OSWORD parameter storage |
| `&EF` | OSBYTE/OSWORD A value (during call) |
| `&F0` | OSBYTE/OSWORD X value |
| `&F1` | OSBYTE/OSWORD Y value |
| `&FC` | Accumulator save during IRQ |
| `&FF` | Escape flag (bit 7 only) |

Detail in [[memory/zero-page]].

## Page 2 — OS variables and vectors (§6.6.2)

- `&200-&235` — Operating-system vectors (table above).
- `&236-&28F` — OS variables addressable via OSBYTE `&A6-&FF`.
- `&290`-`&29F` — `*TV` settings, TIME values (dual-clock for atomicity), interval timer.
- `&2A0-`onwards — Paged ROM table, INKEY countdown, ADC results, event enable flags, key rollover, buffer pointers, CFS state, OSFILE control blocks.

Detail in [[memory/os-workspace]].

## OSHWM — where user RAM starts

- `OSBYTE &83` — Read OSHWM (low byte in X, high byte in Y).
- `OSBYTE &B3` — R/W *primary* OSHWM (top of OS RAM ignoring font state). On Master this OSBYTE doubles as paged-ROM 100Hz polling semaphore.
- `OSBYTE &B4` — R/W *current* OSHWM (may differ from primary if font is exploded).

OSHWM is the MSB of a 16-bit address always on a page boundary. On Model B with DFS, typically `&19` (= `&1900`). After exploding fonts up to OSHWM+`&600`.

## Filed into

- [[memory/zero-page]] — Full zp allocation with user/MOS regions and MOS-bypass notes.
- [[memory/os-workspace]] — Page 1, page 2, page 3 workspace consolidated (closes the earlier `memory/vdu-workspace` stub).
- [[os/calls]] — Master OS entry-point reference (replaces stubs in `os/osbyte.md` / `os/osword.md`).
- Updates: [[memory/memory-map]] now links to zero-page and os-workspace pages.

## Open follow-ups

- DFS 0.90 OSWORD interception bug detail — only Model B with that specific DFS revision. Sidelined.
- Master-specific OSHWM 100Hz semaphore use → covered when Ch17 ingested.
- Filing-system OS calls (OSFILE..OSFIND) — details in Ch16 (pending).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
