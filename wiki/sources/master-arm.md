---
title: Advanced Reference Manual for the BBC Master Series
type: source
tags: [master, m128, source, manual, acorn]
publisher: Acorn Computers
year: 1986
format: PDF
location: raw/manuals/Advanced_Master_Reference_Manual.pdf
pages: 292
updated: 2026-05-16
---

# Advanced Reference Manual for the BBC Master Series

Acorn's official technical manual for the Master 128 (and by extension the Master Compact / Master ET / Master Turbo). The canonical reference for everything Master-specific that diverges from the Model B/B+ documented in the [[sources/naug|NAUG]].

This is a substantial document (292 pages). Key chapters are filed individually below; each ingest pass extends this page's "filed into" list and the chapter's own coverage.

## Bibliographic

- **Title**: Advanced Reference Manual for the BBC Master Series
- **Publisher**: Acorn Computers Ltd.
- **Year**: ~1986 (first published with the Master 128 release)
- **PDF source**: [bitshifters/bbc-documents](https://github.com/bitshifters/bbc-documents) archive
- **Format**: 292-page PDF, mixed text + circuit diagrams + tables

## Why this matters

The Master Series is a superset of the Model B/B+ but with significant differences:

- **65C12 CPU** (CMOS) with extra opcodes — *not* the NMOS 6502 of the Model B.
- **128 KB DRAM** total (vs 32 KB on Model B, 64 KB on B+).
- **ACCCON shadow-RAM control** for separate display/CPU views of the 32 KB display area.
- **Lynne/Hazel internal ROM filling slots** (sideways ROM/RAM is now bank-managed differently).
- **146818 RTC + CMOS** for battery-backed clock and configuration storage.
- **65C102 Turbo co-processor** option (internal Tube), plus 80186 PC and Z80 CP/M options.
- **8-bit addressable latch** on System VIA Port B is reused for CMOS chip-enable/RW (PB6/PB7), not speech.
- **MOS 3.20** (later 3.50 on Compact) with extended vector table and second-32K-of-RAM management.

For performance and demo work, the Master matters because:

- The 65C12 has cheaper stack operations (PHX/PHY/PLX/PLY, ~3c each) and **STZ** (single-instruction zero) — measurable in tight loops.
- Shadow RAM via ACCCON lets you double-buffer display memory without an `OS.MODE` switch.
- The full 32 KB display area is CRTC-addressable identically to the Model B (so [[techniques/rvi]] and rupture techniques port unchanged), but you now have shadow RAM for the back buffer.
- "Lower 64 KB" via ACCCON shadow is an effective doubling of CRTC-reachable memory.

## Chapter index (CRTC 0 / BBC-perspective filter)

| Ch | Title | Pages | Filed into |
|---|---|---|---|
| 1 | The Master Series Architecture | 14-20 | [[hardware/master-overview]] |
| 2 | Circuit Description | 21-28 | *(not ingested — schematic-level detail)* |
| 3 | Memory Organisation | 29-33 | Refined [[memory/shadow-ram]] (E-bit precise mechanism, region (a)/(b) vocabulary); refined [[memory/paged-rom]] (Master matrix ROM organisation, ROMSEL reserved bits) |
| 4 | Slow Data Bus | 34-38 | Refined [[hardware/cmos-rtc]] (sideways-ROM alarm pattern via service calls &04/&05); cross-checked SDB control port table in [[hardware/system-via]] |
| 5 | Keyboard Controller | 39-43 | Refined [[os/keyboard]] with KBDENC three-mode scan (free-run / column / row) hardware section |
| 6 | Screen Display | 44-53 | Cross-checked [[hardware/crtc-6845]] + [[hardware/video-ula]] register tables; refined [[video/modes]] with shadow modes 128-135 allocations; created [[techniques/interlaced-640x512]] (Master-specific 640×512 interlaced 2-colour recipe) |
| 7 | The User Port | 54-62 | Cross-checked [[hardware/user-via]] / [[hardware/via-6522]] / [[timing/via-timers]] — already comprehensive. master-arm added to user-via.md sources. ARM Ch 7 has a nice multi-axis stepper-motor worked example using CB1 (alarm) + PB7 (T1 freq gen) + PB6 (T2 pulse count) — outside performance/demo scope, just noting it exists. |
| 8 | The Serial Processor | 63-64 | *pending — low priority* |
| 9 | Peripheral Bus Controller | 65-71 | *pending — low priority* |
| 10 | The 1MHz Bus | 72-78 | Refined [[hardware/1mhz-bus]] with the `&00EE` zero-page RAM shadow convention and IRQ-safe paging-register write sequence |
| 11 | The Machine Operating System | 79-99 | Refined [[memory/os-workspace]] (Master "second 32 KB" workspace map, soft-char + soft-key relocation, extended-vector triple-table install procedure); refined [[hardware/master-overview]] (soft-char + soft-key relocation notes) |
| 12 | Dual Processor Systems / Tube | 100-121 | Refined [[os/tube]] with the full claimer-ID table (0-9 + &F) and the 32-bit LOAD/EXEC address encoding for Tube-aware filing systems (`&FFFF` = host, `&FFFE` = shadow, `&FFFFFFFF` = *EXEC, `&JKLM` = parasite) |
| 13 | Z80 Second Processor | 122-132 | *pending — low priority* |
| 14 | 80186 Second Processor | 133-146 | *pending — low priority* |
| 15 | Disc Filing Systems | 147-149 | *pending — low priority* |
| 16 | Advanced Network Filing System | 150-161 | *low priority* |
| 17-19 | Terminal, Editor, View | 162-166 | *out of scope (productivity apps)* |
| App 1 | B and B+ differences | 167-172 | Filed into [[synthesis/model-differences]] |
| App 2 | B/B+ and M128 differences | 173-191 | Filed into [[synthesis/model-differences]] |
| App 3 | M128 and Compact differences | 192-201 | Filed into [[synthesis/model-differences]] |
| App 4 | NFS / ANFS differences | 202-204 | *low priority* |
| App 5 | Changes in BASIC 4 | 205-206 | *out of scope* |
| App 6 | PCB Links and Test Points | 207-211 | *out of scope* |
| App 7 | Cartridge Interface | 212-216 | *pending — Master-specific* |
| App 8 | 65C12 Instruction Set | 217-284 | Cross-checked [[hardware/6502-isa]] / [[hardware/6502]] — already accurate including the 65C12-vs-R65C02 split (BBR/BBS/RMB/SMB are R65C02-only, *not* in the Master's main 65C12 — only in the 6502 2P and Master Turbo 65C102). master-arm added to sources. |

## Filed into (per-page audit trail)

Updated incrementally as chapters are ingested. Each entry: chapter → wiki pages created/extended.

- **Ch 1 (architecture overview)** → created [[hardware/master-overview]]; cross-refs added from [[hardware/system-via]] and [[hardware/6502]].
- **Ch 3 (memory organisation)** → refined [[memory/shadow-ram]] with the precise E-bit mechanism (flowchart-level: "previous opcode fetch from `&C000-&DFFF` AND current cycle not an opcode fetch") and Acorn region/LYNNE/HAZEL vocabulary; refined [[memory/paged-rom]] with Master ROM matrix-decoding details and the ROMSEL bits 4-6 reserved note.
- **Ch 4 (slow data bus)** → added master-arm to [[hardware/system-via]] sources; refined [[hardware/cmos-rtc]] with the sideways-ROM alarm-driver pattern (service calls `&04` + `&05`) and a strobe-ordering reminder for the slow-bus dance.
- **Ch 5 (keyboard controller)** → refined [[os/keyboard]] with KBDENC three-mode scan section (free-run / column detection / row detection) and the 10 ms rescan loop.
- **Ch 6 (screen display)** → cross-checked [[hardware/crtc-6845]] per-mode register table (no contradictions); added master-arm to [[hardware/video-ula]] sources; refined [[video/modes]] with shadow modes 128-135 allocation table; created [[techniques/interlaced-640x512]] (Master-specific 640×512 interlaced 2-colour recipe using main+LYNNE half-frame alternation).
- **Ch 7 (user port)** → cross-checked [[hardware/user-via]] / [[hardware/via-6522]] / [[timing/via-timers]] — already comprehensive. master-arm added to user-via.md sources.
- **Ch 10 (1MHz bus)** → refined [[hardware/1mhz-bus]] with the `&00EE` zero-page RAM shadow of the JIM `&FCFF` paging register and the IRQ-safe write sequence (update `&EE` *before* `&FCFF` to prevent IRQ handlers from restoring stale values).
- **Ch 11 (MOS)** → refined [[memory/os-workspace]] with the Master "second 32 KB" workspace map (soft-key buffer at `&8000-&83FF`, soft chars moved to `&8900-&8FFF`, MOS CLI buffer at `&DC00-&DCFF`, transient-utility at `&DD00-&DEFF`) and the extended-vector triple-table install procedure (`OSBYTE &A8`, `&FF00+(vector-&200)*3/2` dispatch). Refined [[hardware/master-overview]] with the relocation notes.
- **Ch 12 (Tube / dual processor)** → refined [[os/tube]] with the full filing-system claimer-ID table (0-9 + `&F` independent) and the 32-bit LOAD/EXEC file-address encoding (`&FFFF` = host main, `&FFFE` = host shadow, `&FFFFFFFF` = *EXEC, `&JKLM` = parasite). Worked pattern for Tube-aware utility ROM addressing.
- **App 8 (65C12 instruction set)** → cross-checked [[hardware/6502-isa]] / [[hardware/6502]] against ARM App 8 — already comprehensive (new opcodes, addressing modes, 65C12 vs R65C02 split correctly attributed). master-arm added to sources. No new pages required.
- **App 1 + 2 + 3 (model differences)** → synthesised into [[synthesis/model-differences]] — single cross-model comparison page (B / B+ / Master 128 / Master Compact). Covers memory map, CPU, FDC, video, IO, ACCCON/ROMSEL bit-by-bit, OSBYTE additions, detection patterns, what's portable vs what's not. The page is the canonical lookup for "does X work on Y?"

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
