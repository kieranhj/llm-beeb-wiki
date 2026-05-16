---
title: NAUG Ch11 — Hardware Introduction
type: source
parent: [[sources/naug]]
pages: 157-161
section: §11
tags: [hardware, sheila, overview, system-block]
updated: 2026-05-13
---

# NAUG Ch11 — Introduction to Hardware

Holmes & Dickens, *The New Advanced User Guide*, pp.157-161. Five-page chapter that frames the BBC system block diagram and tabulates the SHEILA memory map across all machines in the range.

**Mostly recapped elsewhere.** The chapter's primary contribution to the wiki is the consolidated **SHEILA table** showing which chips live at which offsets across Model B, B+, Master, Compact, and Electron.

## Key facts captured (vs what's already in the wiki)

- System block diagram (§p151) — the CPU plus three buses (data, address, control), with peripherals memory-mapped into the address space.
- 6502 / 65C12 generic family — both chips referred to as just "6502" throughout the rest of the book.
- 16-bit address bus → 64 KB max. Data bus bidirectional, address bus unidirectional (with video circuit exceptions allowing 6845 / 5050 to provide addresses for RAM fetches).
- Page `&FE` (SHEILA) holds the system hardware registers; `&FC` (FRED) and `&FD` (JIM) are for the 1 MHz expansion bus / cartridges ([[memory/memory-map]]).
- Co-processors connect via the Tube — Ch18 (separately ingested).

## Extra SHEILA assignments not previously captured

Per the consolidated table on §p154:

| Offset | Chip | Machine availability |
|---|---|---|
| `&00-&0F` | Electron ULA (various hardware functions) | **Electron only** |
| `&18` | Econet station number | Master, Compact |
| `&18-&1A` | µPD7002 ADC | **Electron only** |
| `&24` | Floppy disc control register | Master, Compact |
| `&28` | WD1770 FDC | Master, Compact |
| `&38` | INTOFF — Network NMI disable | B+, Master |
| `&3C` | INTON — Network NMI enable | B+, Master |

Note: on **Master / Compact**, the ADC moves from `&FEC0-&FEDF` (B/B+) to `&FEC0-` (with the Econet interface sharing that range on those machines).

## Filed into

- [[memory/memory-map]] — SHEILA table updated with the above entries.

## Open follow-ups

None — this chapter is summary material whose detail lives in the dedicated per-chip chapters (Ch12 memory, Ch13 video, Ch15 serial, Ch20 ADC, Ch22 VIAs, Ch23 1 MHz bus, etc.).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
