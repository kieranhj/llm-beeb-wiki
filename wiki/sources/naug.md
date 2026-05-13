---
title: The New Advanced User Guide (NAUG)
type: source
tags: [reference, book, master, master-compact, model-b, b-plus, electron]
authors: [Mark Holmes, Adrian Dickens]
publisher: Adder Publishing Limited, Cambridge
pages: 458
machines: [BBC Model B, BBC B+, Master 128, Master Compact, Electron]
file: raw/manuals/New_Advanced_User_Guide.pdf
ingest-mode: chapter-by-chapter
updated: 2026-05-13
---

# The New Advanced User Guide

Comprehensive technical reference for the BBC Master, Master Compact, Model B, B+, and Electron. Successor / expansion of the original Acorn *Advanced User Guide*. Covers the full hardware stack (6502/65C12, memory map, video, VIAs, 1MHz bus, Tube, ADC, sound) and the Machine Operating System (MOS) — including the complete OSBYTE and OSWORD call tables.

This is the foundational reference for the wiki. Most hardware-detail and MOS-call claims elsewhere should cite a specific chapter and page here.

## Citation convention

Cite as `[[sources/naug]] §<chapter>.<section> p<page>` — e.g. `[[sources/naug]] §13.3.5 p199` for "Vertical Timing".

When a chapter is fully ingested, this page links to the per-chapter source stub (e.g. `[[sources/naug-ch13-video]]`), and detailed claims should cite the chapter stub directly.

## Chapter index

Status legend: `[ ]` not yet ingested · `[~]` partial · `[x]` ingested

- `[ ]` **Ch1** New to machine code — p10
- `[x]` **Ch2** BASIC Assembler — p13 (OPT, P%, labels, EQU, BRK, CALL/USR, macros, user zero page) → `[[sources/naug-ch02-basic-assembler]]`
- `[x]` **Ch3** Machine Code Arithmetic — p22 (2's complement, BCD, 65C12 BCD) → `[[sources/naug-ch03-04-arithmetic-addressing]]`
- `[x]` **Ch4** Addressing Modes — p26 (all NMOS modes + 65C12 additions) → `[[sources/naug-ch03-04-arithmetic-addressing]]`
- `[x]` **Ch5** 6502 Instruction Set — p35 (full mnemonic reference, ~70 pages) → `[[sources/naug-ch05-6502-isa]]`
- `[x]` **Ch6** OS Introduction — p107 (OSWRCH, OSRDCH, OSBYTE, OSWORD, OSCLI, OS memory page 0, page 2) → `[[sources/naug-ch06-os-introduction]]`
- `[x]` **Ch7** Events — p126 (EVNTV, enable/disable, OSEVEN) → `[[sources/naug-ch07-events]]`
- `[x]` **Ch8** Interrupts — p131 (NMI, IRQ, OS handler, System/User VIA, Electron ULA, BRK) → `[[sources/naug-ch08-interrupts]]`
- `[x]` **Ch9** Buffers — p143 (INSV, REMV, CNPV, buffer operations) → `[[sources/naug-ch09-buffers]]`
- `[x]` **Ch10** Escape — p154 → `[[sources/naug-ch10-escape]]`
- `[x]` **Ch11** Hardware — p157 → `[[sources/naug-ch11-hardware]]`
- `[x]` **Ch12** Memory — p162 (overview, paged ROM/RAM, shadow RAM, Master access control) → `[[sources/naug-ch12-memory]]`
- `[x]` **Ch13** Video/Graphics — p172 (VDU, 6845 CRTC, horizontal/vertical timing, scrolling, fast animation, Video ULA, palette, screen memory maps) → `[[sources/naug-ch13-video]]`
- `[x]` **Ch14** Keyboard — p225 → `[[sources/naug-ch14-keyboard]]`
- `[x]` **Ch15** Serial I/O — p240 (RS232C, Acorn RS423, 6850, Serial ULA, CFS) → `[[sources/naug-ch15-serial]]`
- `[x]` **Ch16** Filing Systems — p257 (OSFILE/OSARGS/OSBGET/OSBPUT/OSGBPB/OSFIND, FSCV, CFS, RFS, DFS, ADFS, NFS, 1770 FDC) → `[[sources/naug-ch16-filing]]`
- `[x]` **Ch17** Paged ROMs — p290 (ROM header, service calls, installation per machine, language ROMs, *ROM, OS routines, 100Hz polling) → `[[sources/naug-ch17-paged-roms]]`
- `[x]` **Ch18** 2nd Processor / Tube — p334 (32-bit addressing, Tube ULA, 6502/Z80/32016 second processors) → `[[sources/naug-ch18-tube]]`
- `[x]` **Ch19** Clocks, Timers, CMOS — p359 (system clock, timers, CMOS RTC, CMOS RAM) → `[[sources/naug-ch19-clocks-cmos]]`
- `[x]` **Ch20** ADC system — p372 → `[[sources/naug-ch20-adc]]`
- `[x]` **Ch21** Sound / Speech — p379 (76489 sound chip, speech chip) → `[[sources/naug-ch21-sound]]`
- `[x]` **Ch22** VIAs — p387 (User/Printer VIA, System VIA, ports, handshaking, timers T1/T2, shift register, interrupts) → `[[sources/naug-ch22-vias]]`
- `[x]` **Ch23** 1MHz Bus & Cartridges — p409 (FRED &FC, JIM &FD, bus signals, timing, 128K EPROM cartridges) → `[[sources/naug-ch23-1mhz-bus]]`
- `[x]` **Ch24** Miscellaneous — p426 (BREAK/reset, printer, *CODE/*LINE, NETV, KEYV) → `[[sources/naug-ch24-misc]]`
- `[ ]` **Glossary** — p439
- `[ ]` **Bibliography** — p442
- `[x]` **Appendix A — OSBYTE Calls** — p443 → `[[os/osbyte]]` (directory; detail backfilled per-chapter)
- `[x]` **Appendix B — OSWORD Calls** — p448 → `[[os/osword]]` (directory; detail backfilled per-chapter)
- `[ ]` **Index** — p449

## Ingest plan

Chapter-by-chapter, on demand. When you say "ingest naug ch13", the workflow is:

1. Read the chapter in full.
2. Create `wiki/sources/naug-ch<N>-<slug>.md` with section-level summary and key extracts.
3. Create/update the affected entity, concept, and technique pages across the wiki, with `[[sources/naug-ch<N>-<slug>]]` citations.
4. Update the checkbox above, update `wiki/index.md`, append to `wiki/log.md`.

Appendices A and B will be done as full-table extractions into `wiki/os/osbyte.md` and `wiki/os/osword.md`.

## Notes on machine coverage

NAUG covers five machines that differ in important ways. When extracting claims, always note which machine(s) a claim applies to. Common variants:

- **NMOS 6502** (Model B, B+, Electron) vs **65C12 / 65SC12** (Master, Master Compact) — additional addressing modes and instructions (see Ch3.3, Ch4.12).
- **Memory map** differs across B / B+ / Master (shadow RAM, sideways RAM, ANDY/HAZEL regions on Master) — see Ch12.
- **Video ULA** (Model B / B+ / Master) vs **Electron ULA** (combined video + sound + cassette + keyboard).
- **Sound**: 76489 on BBC models; Electron uses its own ULA.
- **Tube**: not present on Electron.

When a wiki page describes a feature, prefer to state machine applicability up front.
