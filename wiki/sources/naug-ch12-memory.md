---
title: NAUG Ch12 — Memory
type: source
parent: [[sources/naug]]
pages: 162-171
section: §12
tags: [memory, paged-rom, sideways-ram, shadow-ram, acccon]
updated: 2026-05-13
---

# NAUG Ch12 — Memory

Holmes & Dickens, *The New Advanced User Guide*, pp.162-171. Compact (10pp) but high-leverage — defines the memory map all other chapters reference.

## Key facts captured

- 6502 address space is 64 KB. Common to all BBC machines:
  - `&0000-&2FFF` (12 KB) — user RAM, MOS variables.
  - `&3000-&7FFF` (20 KB) — screen RAM (max). The portion not used by current MODE is available to the user.
  - `&8000-&BFFF` (16 KB) — paged ROM/RAM (sideways).
  - `&C000-&FBFF` — MOS ROM.
  - `&FC00-&FCFF` — **FRED** (1 MHz bus expansion / cartridges on Master).
  - `&FD00-&FDFF` — **JIM** (1 MHz bus expansion / cartridges on Master).
  - `&FE00-&FEFF` — **SHEILA** (memory-mapped I/O for all hardware: 6845, ULA, VIAs, paging registers).
  - `&FF00-&FFFF` — MOS ROM (vectors etc.).
- **ROM paging register** at SHEILA `&FE30`. Low 4 bits (PR0-PR3) select one of 16 paged ROM banks at `&8000-&BFFF`. Bit 7 is machine-specific:
  - **Master**: bit 7 set → 4 KB of RAM ("ANDY") swapped in at `&8000-&8FFF` (used by MOS during graphics).
  - **B+**: bit 7 set → 12 KB of RAM at `&8000-&AFFF`.
- **Test sideways RAM**: `OSBYTE &44` returns X with bits 0-3 set for SWR banks 4-7. Available on B+/Master only.
- **ACCCON register** at SHEILA `&FE34` controls shadow RAM, HAZEL filing-system RAM, Tube selection, cartridge vs 1 MHz bus. Layout differs between B+ and Master:
  - **B+**: only `S` bit (single shadow select; combined VDU-write + display).
  - **Master**: bits 0=D, 1=E, 2=X, 3=Y, 4=ITU, 5=IFJ, 6=TST, 7=IRR. See [[memory/shadow-ram]].
- **Shadow RAM**: B+ and Master have an extra 20 KB bank at `&3000-&7FFF` independent of main memory. When selected (`*shadow`, OSBYTE `&72`, or MODE 128-135), screen lives in shadow and `&3000-&7FFF` in main memory is free for user code/data.
- **HAZEL** (Master only): 8 KB filing-system RAM at `&C000-&DFFF` overlaying MOS VDU driver. Switched by ACCCON `Y` bit. Must be switched back before next OSWRCH or the VDU driver vanishes mid-call.
- `OSBYTE &84` returns the bottom of display RAM (i.e. HIMEM for non-shadow) — or `&8000` if shadow mode is in use. `OSBYTE &85` same but for a given mode (X = mode).
- **Master direct-access OSBYTEs** for double-buffered animation:
  - `&6C` — select which `&3000-&7FFF` bank the CPU sees (X=0 main / 1 shadow).
  - `&70` — which bank the VDU driver writes to (X=0 default / 1 main / 2 shadow).
  - `&71` — which bank the 6845 reads from for display (X=0 default / 1 main / 2 shadow).
  - Combined: write next frame into the bank that isn't currently displayed, then flip `&71`.
- `OSBYTE &FE`: machine ID (X = 0 Electron / 1 B+ / `&40` Model A / `&80` Model B). Master uses this byte differently.

## Critical do-not warning (§12.3 p168)

**Never write `&FE30` directly from user code.** The MOS keeps track of the active paged ROM; an unsynchronised write can swap the current language ROM out and crash the machine instantly. Use the relevant OSBYTEs / service calls (Ch17 ingest, pending). The MOS itself changes `&FE30` *often* — assume the value is volatile across any OS call.

## Filed into

- [[memory/memory-map]] — 64KB layout with machine-specific extras.
- [[memory/paged-rom]] — sideways ROM/RAM mechanics, paging register, ANDY.
- [[memory/shadow-ram]] — shadow RAM + ACCCON, including Master vs B+ differences and double-buffering technique.
- Plus the page-3 / zero-page VDU workspace mentioned in §13.2 — folded into [[memory/memory-map]] references.

## Open follow-ups

- HAZEL precise use cases — chapter says "filing systems"; full picture needs Ch16 ingest.
- ROM service call protocol (`&FE30` write side-effects) — Ch17 ingest.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
