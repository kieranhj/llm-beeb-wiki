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
| C | MOS commands | 24-44 | Created [[os/star-commands]] (full resident MOS command table + FS commands + sideways-ROM dispatch + per-command detail for GO/CONFIGURE/FX/KEY/HELP) |
| D | Using MOS routines | 45-164 | D.2 (OSBYTE) filed into [[os/osbyte]]. D.3 (OSWORD) cross-checked vs [[os/osword]] — Master-new calls (`&0E` Read CMOS clock, `&0F` Write CMOS clock) already documented; master-rm added to sources. D.4-D.10 (OSCLI/OSRDCH/OSRDSC/OSWRCH/OSNEWL/OSASCI/OSWRSC/OSEVEN/GSINIT/GSREAD) cross-checked vs [[os/calls]] — already comprehensive. |
| **E** | **The VDU driver (~60 pages)** | **165-224** | E.1-E.3 filed: extended [[os/vdu]] + [[video/plot-codes]]. E.4 filed: created [[os/vdu-internals]] (variable table, page-0 workspace, second-32K layout, 8 C000 primitive entry points). E.5 pending. |
| F | Hardware and memory usage | 225-264 | Cross-checked vs [[hardware/master-overview]] / [[memory/memory-map]] / [[memory/shadow-ram]] / [[memory/paged-rom]] / [[hardware/1mhz-bus]] / [[hardware/system-via]] / [[hardware/user-via]] — already comprehensive (Master ARM ingest covered the same ground at greater electrical detail). master-rm added to sources of all 7 pages. |
| G | Filing Systems (common) | 265-296 | Cross-checked vs [[os/filing-systems]] (already comprehensive). G.7 sideways-RAM pseudo-addressing detail filed into [[memory/paged-rom]]. master-rm added to filing-systems.md sources. |
| H | The Cassette Filing System | 297-308 | Cross-checked vs [[os/filing-systems]] — CFS API already covered via NAUG. |
| I | The ROM Filing System | 309-320 | Cross-checked vs [[os/filing-systems]] — RFS API already covered. |
| J | The Disc Filing Systems (DFS + ADFS) | 321-383 | Created [[os/disc-formats]] (DFS catalogue layout sector 0+1, ADFS Free Space Map + Root Directory sector layout, file/dir attribute encoding, DFS-vs-ADFS comparison table). Commands cross-checked vs existing [[os/star-commands]] + [[os/filing-systems]]. |

### Part 2

| Ch | Title | Pages | Filed into |
|---|---|---|---|
| K-N | BBC BASIC / keywords / errors / technical | 11-145 | *out of scope (BASIC programming primer); BASIC error list already in [[os/errors]]* |
| O | The BBC BASIC assembler | 146-169 | Cross-checked vs [[tools/basic-assembler]] — already comprehensive (via NAUG Ch2 ingest). master-rm added to sources. |
| P | Assembler keywords | 170-205 | Cross-checked vs [[hardware/6502-isa]] / [[hardware/6502-addressing-modes]] / [[hardware/6502]] — already comprehensive (via NAUG Ch5 + Master ARM App 8 ingest). master-rm added to sources of all 3 pages. |
| Q | Assembler errors | 206-215 | Cross-checked vs [[os/errors]] — assembler errors `Byte`/`Index`/`Out of range` already documented. |
| R-T | System editor / formatter | 216-282 | *out of scope (productivity apps)* |
| U | TERMINAL emulator | 283-313 | *out of scope* |

## Filed into (incremental audit trail)

Populated as chapters are ingested. Each entry: chapter → wiki pages created/extended.

- **Ch E.1-E.3 (VDU driver: intro, summary, descriptions)** → significantly extended [[os/vdu]] with: parsing model (byte-range table), `OSBYTE &DA` queue-length call, full VDU 18 GCOL mode 5 + ECF mode-byte encoding, VDU 23,n complete sub-function reference (cursor on/off levels, ECF row-byte pixel mapping per bpp, VDU 23,7 direct scroll, VDU 23,8 clear-block base-position table, VDU 23,16 cursor-movement-control flag bits). Significantly extended [[video/plot-codes]] with: precise "k mod 8" coord+colour semantics (relative/absolute + plot-mode selection), precise GXR primitive specifications (circles with radius limit, arc/chord/sector 3-point geometry, ellipse parameter convention with worked rotated-ellipse PROC, flood-fill workspace usage), move/copy rectangle special k handling.
- **Ch E.4 (VDU variables + plot vector internals)** → created [[os/vdu-internals]] — comprehensive VDU variable table (`&300-&37F`), Page-0 VDU workspace map, Master second-32K layout (ECF patterns + 7 character-definition pages + ROM defaults at `&B900-&BFFF`), and the 8 `&C000-&C015` primitive entry points (load/store shadow-aware byte, PLBYTE, HPLOT, EIGABS, WIND with 9-position window-clipping table, GADDR, IEG) with worked example re-implementing PLOT 64-71 from the unknown-PLOT-codes vector. Sideways-ROM intercept caveat documented.
- **Ch E.5 (Teletext modes 7 + 135)** → refined [[hardware/saa5050]] with the VDU driver's 3-character substitution table (`#` ↔ `£` ↔ `_` swap to reconcile BBC ASCII with raw SAA5050 glyphs) and the canonical "which VDU commands work in MODE 7" reference table. master-rm added to sources.
- **Ch C (MOS commands)** → created [[os/star-commands]] with the full resident MOS command list (~45 commands), the dispatch chain (MOS resident → FS → sideways ROMs via service call &04 → `*RUN <name>` → error 254), filing-system command index per FS, and per-command detail for GO/GOIO/CONFIGURE/FX/KEY/HELP with internals.
- **Ch D.2 (OSBYTE)** → extended [[os/osbyte]] with MRM functional-grouping index (ADC/BREAK/CMOS/Econet/ESCAPE/FS/IO/keyboard/mode/printer/RS423/shadow/sound/system/time/Tube) and detailed list of all OSBYTEs marked £ "new on Master" or repurposed from Model B (108-114, 161-162, 164, 179, 182, 238, 250-251, 254 etc). master-rm added to sources.
- **Ch D.3-D.10 (OSWORD + OSCLI/OSRDCH/OSWRCH/OSNEWL/OSASCI/OSWRSC/OSEVEN/GSINIT/GSREAD)** → cross-checked vs [[os/osword]] / [[os/calls]] — Master-new OSWORD calls (`&0E` Read CMOS clock, `&0F` Write CMOS clock) already covered via NAUG Ch19. master-rm added to osword.md sources.
- **Ch F (Hardware and memory usage)** → cross-checked vs [[hardware/master-overview]] / [[memory/memory-map]] / [[memory/shadow-ram]] / [[memory/paged-rom]] / [[hardware/1mhz-bus]] / [[hardware/system-via]] / [[hardware/user-via]]. Master ARM ingest already covered the same ground at greater electrical-level detail. master-rm added to sources of 7 hardware/memory pages.
- **Ch G + H + I (Filing systems common, CFS, RFS)** → cross-checked vs [[os/filing-systems]] — already comprehensive. G.7 (sideways-RAM addressing modes — absolute vs pseudo with W/X/Y/Z bank IDs at `&00000-&0FFBF`) filed into [[memory/paged-rom]] as a new "Master sideways-RAM addressing modes" section. master-rm added to filing-systems.md sources.
- **Ch J (DFS + ADFS)** → created [[os/disc-formats]] — DFS catalogue layout (sector 0 = title + names; sector 1 = title-tail + MSN + free-pointer + 31 file headers with 18-bit addresses split across nibbles). ADFS Free Space Map (sectors 0+1, lock-stepped 82-entry start/length arrays + checksum); ADFS Root Directory (sectors 2-6, 47-entry format with Hugo identifier, 32-bit addresses, 5-byte name+access-attribute encoding); attribute encoding in top bits of name bytes (R/W/L/E); DFS-vs-ADFS comparison table.
- **Part 2 Ch O + P + Q (BASIC assembler + 65C12 ISA + errors)** → cross-checked vs [[tools/basic-assembler]] / [[hardware/6502-isa]] / [[hardware/6502-addressing-modes]] / [[hardware/6502]] / [[os/errors]] — already comprehensive (via NAUG Ch2 + Ch5 + Master ARM App 8 ingest). master-rm added to sources of all 4 hardware/tool pages.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
