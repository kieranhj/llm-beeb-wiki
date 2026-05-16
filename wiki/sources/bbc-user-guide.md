---
title: BBC Microcomputer User Guide (Coll, 1982)
type: source
tags: [user-guide, source, manual, acorn, model-b]
publisher: Acorn Computers
year: 1982
format: PDF
location: raw/manuals/BBC_User_Guide.pdf
pages: 522
updated: 2026-05-16
---

# BBC Microcomputer User Guide

Acorn's official end-user manual for the BBC Model A/B. Published 1982, shipped with every machine. Predates the Master Series.

Most of the manual is a BASIC tutorial (introducing variables, loops, procedures, etc.) — out of scope for a performance wiki. Several chapters are however **the canonical primary source** for things now buried in derived references:

- **VDU control codes** (Ch 34) — the bible for what each VDU n does. The wiki's `os/vdu.md` is sourced primarily from here.
- **Advanced graphics + PLOT codes** (Ch 29) — original list of PLOT codes 0-95 (later extended on Master).
- **FX/OSBYTE calls** (Ch 42) — first published OSBYTE reference (incomplete; superseded by NAUG App A/B).
- **Error messages** (Ch 46) — canonical Model B error number ↔ message map.
- **Appendix** (Ch 48) — ASCII codes, INKEY numbers, character codes table, machine ID table.

For Master-era content, prefer [[sources/master-arm]]. For Master-era OSBYTE/OSWORD, prefer [[sources/naug-appendix-ab]]. The User Guide is **the** authority for the original VDU driver spec — the Model B's behaviour defined what every later machine had to remain compatible with.

## Bibliographic

- **Title**: BBC Microcomputer System User Guide
- **Author**: John Coll (with Acorn editorial input)
- **Publisher**: Acorn Computers Ltd. / British Broadcasting Corporation
- **Year**: 1982 (first ed.); reprinted with minor updates through 1984.
- **PDF source**: [bitshifters/bbc-documents](https://github.com/bitshifters/bbc-documents) archive
- **Format**: 522-page PDF.

## Chapter index (performance/hardware-relevant only)

| Ch | Title | Pages | Filed into |
|---|---|---|---|
| 1-27 | BASIC tutorial chapters | 9-126 | *out of scope (BASIC programming primer)* |
| 28 | Teletext and MODE 7 | 152-161 | Cross-checked against [[hardware/saa5050]] — UG is beginner-level intro; technical detail already in saa5050.md (Mullard datasheet + BeebWiki sources). bbc-user-guide added to saa5050 sources. |
| 29 | Advanced Graphics | 162-181 | Created [[video/plot-codes]] (PLOT k=0-95 from this chapter + k=96-255 from Master ARM Ch 6) |
| 30 | Sound | 182-189 | *cross-checked vs [[hardware/sn76489]] / [[os/sound]] — no new content* |
| 31-33 | File handling, BASIC keywords | 190-378 | *out of scope* |
| 34 | VDU drivers | 379-391 | Created [[os/vdu]] (full VDU 0-31 + 127 control code reference) |
| 35-41 | Cassette / printers / misc | 392-417 | *out of scope or already in NAUG* |
| 42 | FX Calls and OSBYTE calls | 420-443 | Cross-checked against [[os/osbyte]] — User Guide's original OSBYTE list is a strict subset of NAUG App A/B and Master ARM additions. bbc-user-guide added to osbyte sources. |
| 43 | Assembly language | 444-468 | *out of scope — already covered by NAUG Ch2 ingest* |
| 44 | Analogue input | 469-472 | *cross-checked vs [[hardware/upd7002-adc]] — no new content* |
| 45 | Expanding the system | 473-475 | *pending — original 1MHz / Tube / disc expansion overview* |
| 46 | Error messages | 476-484 | Created [[os/errors]] (BASIC 0-44 + CFS 216-223 + MOS 250+ + filing-system error tables) |
| 48 | Appendix | 487-514 | Cross-checked: ASCII / INKEY tables already covered in [[os/keyboard]] (via NAUG Ch14 + Master ARM Ch 5 ingest); BASIC keyword token table covered in [[tools/basic-assembler]]. bbc-user-guide added to keyboard.md sources. |

## Filed into

- **Ch 34 (VDU drivers)** → created [[os/vdu]] (full VDU control code reference table, per-code semantics, byte-count for each).
- **Ch 29 (Advanced Graphics) + Ch 33 (PLOT BASIC keyword)** → created [[video/plot-codes]] covering PLOT k=0-95 (line variants, fills, triangles, single points) from User Guide and k=96-255 (rectangle, parallelogram, circle, ellipse, flood fill) from Master ARM Ch 6.
- **Ch 46 (Error messages)** → created [[os/errors]] (BASIC 0-44 alphabetical, CFS 216-223, MOS 250+, DFS/ADFS/NFS conventions, BRK-raising-from-user-code pattern).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
