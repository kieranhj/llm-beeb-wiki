---
title: Master Series Reference Manual (Parts 1 + 2)
type: source
tags: [master, m128, source, manual, acorn, vdu, basic, mos]
publisher: Acorn Computers
year: 1986
format: PDF
location: raw/manuals/Master_Reference_Manual_Part_1.pdf, raw/manuals/Master_Reference_Manual_Part_2.pdf
pages: 400 + 324
updated: 2026-05-16
---

# Master Series Reference Manual (Parts 1 + 2)

Acorn's primary user/programmer documentation for the BBC Master 128. Two volumes totalling ~720 pages. Distinct from the **Advanced Reference Manual** ([[sources/master-arm]]) which is the deeper technical/electrical-level reference for service personnel and hardware developers.

This pair (often referred to as "MRM" in BBC scene) is the canonical user-and-programmer-level documentation:

- **Part 1** (400 pages): hardware, MOS, MOS commands, OSBYTE/OSWORD/OSCLI/OSRDCH/OSWRCH/etc., **VDU driver (60 pages of detail!)**, filing systems (CFS/RFS/DFS/ADFS).
- **Part 2** (324 pages): BBC BASIC IV, BASIC keywords, BASIC errors, BBC BASIC assembler, 65C12 ISA, system editor (EDIT), text formatter, TERMINAL emulator.

For Master-internal electrical and chip-level detail, prefer [[sources/master-arm]]. For programmer-level "how do I use VDU 23,8?" and "what does OSBYTE &14 do exactly?" prefer this manual — its VDU and OSBYTE sections are noticeably more detailed than NAUG's.

## Bibliographic

- **Title**: Master Series Reference Manual, Part 1 + Part 2
- **Publisher**: Acorn Computers Ltd.
- **Year**: ~1986
- **PDF source**: [bitshifters/bbc-documents](https://github.com/bitshifters/bbc-documents) archive
- **Format**: 400 + 324 = 724 pages across two PDFs.

## Chapter index (performance/hardware-relevant only)

### Part 1

| Ch | Title | Pages | Filed into |
|---|---|---|---|
| A | System Overview | 11-17 | *cross-checked vs [[hardware/master-overview]]* |
| B | The Machine Operating System (MOS) | 18-23 | *overview — cross-checked vs [[os/calls]]* |
| C | MOS commands | 24-44 | *pending — *command reference* |
| D | Using MOS routines | 45-164 | *cross-check vs [[os/osbyte]] / [[os/osword]] / [[os/calls]]* |
| **E** | **The VDU driver (~60 pages)** | **165-224** | E.1-E.3 filed: extensively extended [[os/vdu]] (parsing model, OSBYTE &DA, VDU 18 ECF modes, VDU 23,n complete sub-function reference) + [[video/plot-codes]] (precise k mod 8 semantics, GXR primitive geometry, move/copy rect). E.4-E.5 pending. |
| F | Hardware and memory usage | 225-264 | *cross-check vs Master ARM* |
| G | Filing Systems (common) | 265-296 | *pending — filing-system API* |
| H | The Cassette Filing System | 297-308 | *pending* |
| I | The ROM Filing System | 309-320 | *pending* |
| J | The Disc Filing Systems (DFS + ADFS) | 321-383 | *pending — catalogue formats, commands, technical info* |

### Part 2

| Ch | Title | Pages | Filed into |
|---|---|---|---|
| K-N | BBC BASIC / keywords / errors / technical | 11-145 | *out of scope (BASIC programming primer); BASIC error list already in [[os/errors]]* |
| O | The BBC BASIC assembler | 146-169 | *cross-check vs [[tools/basic-assembler]]* |
| P | Assembler keywords | 170-205 | *cross-check vs [[hardware/6502-isa]] / [[hardware/6502-addressing-modes]]* |
| Q | Assembler errors | 206-215 | *cross-check vs [[os/errors]]* |
| R-T | System editor / formatter | 216-282 | *out of scope (productivity apps)* |
| U | TERMINAL emulator | 283-313 | *out of scope* |

## Filed into (incremental audit trail)

Populated as chapters are ingested. Each entry: chapter → wiki pages created/extended.

- **Ch E.1-E.3 (VDU driver: intro, summary, descriptions)** → significantly extended [[os/vdu]] with: parsing model (byte-range table), `OSBYTE &DA` queue-length call, full VDU 18 GCOL mode 5 + ECF mode-byte encoding, VDU 23,n complete sub-function reference (cursor on/off levels, ECF row-byte pixel mapping per bpp, VDU 23,7 direct scroll, VDU 23,8 clear-block base-position table, VDU 23,16 cursor-movement-control flag bits). Significantly extended [[video/plot-codes]] with: precise "k mod 8" coord+colour semantics (relative/absolute + plot-mode selection), precise GXR primitive specifications (circles with radius limit, arc/chord/sector 3-point geometry, ellipse parameter convention with worked rotated-ellipse PROC, flood-fill workspace usage), move/copy rectangle special k handling.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
