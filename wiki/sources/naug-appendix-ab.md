---
title: NAUG Appendix A + B — OSBYTE / OSWORD index
type: source
parent: [[sources/naug]]
pages: 443-448
section: Appendix A, Appendix B
tags: [osbyte, osword, mos, reference]
updated: 2026-05-13
---

# NAUG Appendix A + B — OSBYTE / OSWORD Index

Holmes & Dickens, *The New Advanced User Guide*, pp.443-448. These appendices are **directory tables** — they list every OSBYTE (`&00`-`&FF`) and OSWORD (`&00`-`&FF`) with a one-line function description and a page reference to where the full semantics live in the body of the book.

For each call, the **detailed protocol** (entry params, exit state, side effects, machine-specific behaviour) is in the chapter listed in the `page` column. The wiki files [[os/osbyte]] and [[os/osword]] hold the directory; full semantics for individual calls are filled in as the referenced chapter is ingested.

## OSBYTE — `JSR &FFF4` (indirected through `&20A`)

Standard call:
```asm
LDA #call_number    ; OSBYTE number in A
LDX #x_value
LDY #y_value
JSR &FFF4
```

Two common patterns:
- **Read/write state byte**: `NEW = (OLD AND Y) EOR X`. To **read**: X=0, Y=&FF → OLD returned in X. To **write**: X=value, Y=0 → OLD returned in X, byte set to value.
- **Do-an-action**: X and Y are entry parameters; exit state varies.

## OSWORD — `JSR &FFF1` (indirected through `&20C`)

Standard call:
```asm
LDA #call_number
LDX #param_block AND 255
LDY #param_block DIV 256
JSR &FFF1
```

OSWORD always uses a **parameter block** in memory at the address in `X+Y`. The block layout depends on the call.

## Filed into

- [[os/osbyte]] — Full directory of OSBYTE calls. Each row links to the wiki chapter source page (e.g. [[sources/naug-ch13-video]]) when ingested; otherwise lists the NAUG page number.
- [[os/osword]] — Full directory of OSWORD calls, same format.

## Open follow-ups

The chapter-page references in this index mean that **every chapter** of NAUG is potentially the canonical source for some OSBYTE/OSWORD. Backfill semantics as chapters are ingested. Notable chapters with concentrations of OSBYTE/OSWORD detail:

- Ch6 OS Introduction — generic OS calls (next ingest)
- Ch13 Video — `&13`, `&86`, `&87`, `&9A`, `&9B`, `&A0`, `&A5`, `&AE`, `&AF`, `&B8`, `&B9`, `&C1`-`&C3`, `&D9`, `&DA`, plus OSWORDs `&09`, `&0A`, `&0B`, `&0C`, `&0D` (ingested ✓)
- Ch12 Memory — `&44`, `&45`, `&6C`, `&70`-`&72`, `&84`, `&85`, `&FA`, `&FB`, `&EF`, `&FE` (ingested ✓)
- Ch8 Interrupts — `&BA`, `&CB`, `&E7`, `&E8`, `&E9` (ingested ✓)
- Ch7 Events — `&0D`, `&0E`
- Ch9 Buffers — `&15`, `&80` (also ADC), `&88`-`&8A`, `&98`, `&99`, `&91`
- Ch14 Keyboard — `&0B`, `&0C`, `&76`-`&7A`, `&C4`-`&CA`, `&DB`-`&E4`
- Ch15 Serial — `&07`, `&08`, `&02`, `&03`, `&9C`, `&B0`, `&B1`, `&B5`, `&BF`, `&C0`, `&CB`-`&CD`, `&F2`
- Ch16 Filing — `&77`, `&7F`, `&87`-`&8D`, `&C6`, `&C7`, `&6D`
- Ch17 Paged ROMs — `&8D`-`&8F`, `&A4`, `&A8`-`&AB`, `&BA`-`&BB`, `&FC` (next-next ingest)
- Ch18 Tube — `&9D`, `&82`, `&EA`
- Ch19 Clocks/CMOS — `&A1`, `&A2`, `&F3`, OSWORDs `&01`-`&04`, `&0E`, `&0F`
- Ch20 ADC — `&10`, `&11`, `&80`, `&BC`-`&BE`
- Ch21 Sound — `&D1`-`&D6`, `&74`, `&E8`, OSWORDs `&07`, `&08`
- Ch24 Misc — `&00`, `&01`, `&05`, `&06`, `&88`, `&7B`, `&F1`, `&F0`, `&F5`-`&F9`, `&FD`, `&FF`

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
