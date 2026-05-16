---
title: OSWORD Calls
type: os
tags: [osword, mos, reference]
sources: [naug-appendix-ab, master-rm]
updated: 2026-05-16
---

# OSWORD Calls

OSWORD provides extended OS services that need more than the two byte parameters of OSBYTE. Each OSWORD takes a **parameter block** in memory.

**Call: `JSR &FFF1`** (indirected through `&20C`) with:
- `A` = OSWORD number
- `X` = parameter block address LSB
- `Y` = parameter block address MSB

The parameter block layout is per-call. NAUG Appendix B (p448) gives the directory; each chapter gives full details.

## Standard OS OSWORDs

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&00` |  0 | Read line from currently selected input stream | 106 | (Ch6, pending) |
| `&01` |  1 | Read system clock | 352 | (Ch19, pending) |
| `&02` |  2 | Write system clock | 352 | (Ch19, pending) |
| `&03` |  3 | Read interval timer | 352 | (Ch19, pending) |
| `&04` |  4 | Write interval timer | 352 | (Ch19, pending) |
| `&05` |  5 | Read byte of I/O processor memory (Tube) | 347 | (Ch18, pending) |
| `&06` |  6 | Write byte of I/O processor memory (Tube) | 347 | (Ch18, pending) |
| `&07` |  7 | Perform a SOUND command | 372 | (Ch21, pending) |
| `&08` |  8 | Define an ENVELOPE | 372 | (Ch21, pending) |
| `&09` |  9 | Read pixel value | 175 | [[sources/naug-ch13-video]] |
| `&0A` | 10 | Read character definition | 171 | [[sources/naug-ch13-video]] |
| `&0B` | 11 | Read palette value for a given logical colour | 178 | [[sources/naug-ch13-video]] |
| `&0C` | 12 | **Write palette value for a given logical colour** (interrupt-safe) | 177 | [[sources/naug-ch13-video]] |
| `&0D` | 13 | Read previous + current graphics cursor positions | 175 | [[sources/naug-ch13-video]] |
| `&0E` | 14 | Read real-time clock (Master CMOS) | 353 | (Ch19, pending) |
| `&0F` | 15 | Write real-time clock (Master CMOS) | 355 | (Ch19, pending) |

## Filing-system OSWORDs

| Hex | # | Function | Notes |
|---|---|---|---|
| `&7A` | 122 | Issue Telesoftware command | Telesoft FS |
| `&7D` | 125 | Read disc cycle number | DFS/ADFS |
| `&7E` | 126 | Read disc/directory size | DFS/ADFS |
| `&7F` | 127 | **Issue FDC command** | Direct floppy controller; param block format per FDC chip (1770 or 8271) — see Ch16 §16.4 (pending) |
| `&80` | 128 | Issue IEEE command | IEEE-488 |

## Tube OSWORDs

| Hex | # | Function | Notes |
|---|---|---|---|
| `&FF` | 255 | R/W I/O processor memory (Z80 second processor) | Ch18 (pending) |

## Performance note

OSWORD round-trip overhead is significant (parameter block fetch + dispatch + work + RTS). For high-rate operations the alternatives are:

- **Palette writes**: `OSWORD &0C` is interrupt-safe and tube-compatible. For raw speed in IRQ-disabled code, `STA &FE21` is 4 cycles vs hundreds for OSWORD — but you lose Tube compatibility and must restore OS palette state.
- **Pixel reads** (`OSWORD &09`): there's no faster way without computing the address yourself. For dense reads, walk screen memory directly using the layout from [[video/modes]].
- **SOUND/ENVELOPE**: there's no escape — the SN76489 protocol via System VIA addressable latch + slow peripheral bus is involved enough that OSWORD is usually the right answer unless you're writing your own player.

## Cross-reference

For directory-level navigation, see [[sources/naug-appendix-ab]]. Per-call detail accrues as relevant chapters are ingested — cross-references appear inline against each call entry above.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
