---
title: "BeebWiki: CRTC"
type: source
tags: [video, crtc, 6845]
url: https://beebwiki.mdfs.net/CRTC
updated: 2026-05-14
---

# BeebWiki — CRTC

**URL:** https://beebwiki.mdfs.net/CRTC

## Summary

BBC-specific reference for the 6845-family CRTC: register table, BBC MODE defaults, Acorn-specific quirks. Complements the NAUG chapter; useful for cross-checking R10 cursor encoding (which our wiki had wrong) and the MODE 7 R12/R13 XOR `&54` quirk (not previously documented).

## Key technical claims

### Hardware access

- `&FE00` write = register select; read = status register.
- `&FE01` = register data.
- **Status register (`&FE00` read):** bit 7 = update-in-progress (cleared by writing R31); bit 6 = light-pen strobe (cleared on R16/R17 read); bit 5 = vertical blanking (set when `VerticalCount ≥ R6`).

### Register summary

| Reg | Width | Function |
|---|---|---|
| R0 | 8 | HTC — horizontal total |
| R1 | 8 | HDC — horizontal displayed |
| R2 | 8 | HSP — horizontal sync position |
| R3 | 8 | Sync widths: bits 3-0 HSW (0=16); bits 7-4 VSW (0=16) |
| R4 | 7 | VTC — vertical total |
| R5 | 5 | VTA — vertical total adjust (scanlines) |
| R6 | 7 | VDC — vertical displayed |
| R7 | 7 | VSP — vertical sync position |
| R8 | — | bits 7-6 cursor delay (3=disabled); bits 5-4 display delay (3=disabled); bit 1 sync mode; bit 0 interlace |
| R9 | 5 | NSL — scanlines per character − 1 (− 2 in interlace) |
| R10 | — | bits 6-5 BLK; bits 4-0 cursor start scanline |
| R11 | 5 | Cursor end scanline |
| R12,R13 | 14 | Screen start address |
| R14,R15 | 14 | Cursor position |
| R16,R17 | 14 | Light pen position (R/O) |
| R18-R30 | — | Reserved (writes undefined; reads `&00`) |
| R31 | — | Status control (some 6845 variants) |

### R10 cursor BLK encoding (bits 6-5)

| BLK | Effect |
|---|---|
| `00` | Cursor off |
| `01` | Cursor on, **no blink** (steady) |
| `10` | Blink slow — 1/16 field rate |
| `11` | Blink fast — 1/32 field rate (used during screen editing) |

### BBC MODE defaults

(R0 row reproduced **as printed by BeebWiki**; appears to be an error — see contradictions below.)

```
Reg | M0 | M1 | M2 | M3 | M4 | M5 | M6 | M7 |
R0  | 127| 127| 127| 127| 127| 127| 127| 127|  ← BeebWiki value (suspect)
R1  | 80 | 80 | 80 | 80 | 40 | 40 | 40 | 40 |
R2  | 98 | 98 | 98 | 98 | 49 | 49 | 49 | 51 |
R3 HSW |  8|  8|  8|  8|  4|  4|  4|  4 |
R3 VSW |  2|  2|  2|  2|  2|  2|  2|  2 |
R4  | 38 | 38 | 38 | 30 | 38 | 38 | 30 | 30 |
R5  |  0 |  0 |  0 |  2 |  0 |  0 |  2 |  2 |  (+*TV)
R6  | 32 | 32 | 32 | 25 | 32 | 32 | 25 | 25 |
R7  | 34 | 34 | 34 | 27 | 34 | 34 | 27 | 27 |
R8 INT |  1|  1|  1|  1|  1|  1|  1|  1 |  (+*TV)
R8 DIS |  0|  0|  0|  0|  0|  0|  0|  1 |
R8 CUR |  0|  0|  0|  0|  0|  0|  0|  2 |
R9  |  7 |  7 |  7 |  9 |  7 |  7 |  9 | 18 |
R10 CSL|  7|  7|  7|  7|  7|  7|  7| 18 |
R10 BLK|  1|  1|  1|  1|  1|  1|  1|  1 |
R11 CEL|  8|  8|  8|  9|  8|  9|  9| 19 |
```

### Acorn-specific quirks

- **MODE 7 R12/R13 XOR `&54`:** Address written to R12/R13 in MODE 7 is XORed with `&54` so the resulting "6845 address" lands in the `&2000-&2FFF` range that flags Teletext addressing for the address translator. Cross-reference: see [[hardware/address-translation]] MODE 7 formula.

- **Cursor end-line bug in MOS:** Acorn's VDU drivers set CEL one beyond the correct value: CEL=8 in graphics modes (correct: 7), CEL=9 in stripey modes (with CSL=8 → 2-scanline cursor), CEL=19 in MODE 7 (cell is 20 scanlines). Works because the CRTC clips, but technically incorrect.

- **MODE 7 R2 (HSP):** Standard MOS uses 51; setting 52 gives a more centred picture.

- **6845 variant required:** BBC needs a 6845S. Three S-specific features used: R3 vertical-sync width support, R6 odd values (25 for MODES 3/6/7), R8 character/cursor delay (MODE 7 uses display delay = 1, cursor delay = 2).

- **Character-based cursor fallback** (for hardware without true 6845): if CSL < NSL/2, render block; else render underscore.

- **Default blink rates:** Slow = 1/16 field freq (~3 Hz at 50 Hz); fast = 1/32 field freq (~1.5 Hz) during screen editing.

- **R8 interlace:** All standard MODEs set bit 0 = 1 (interlace sync, but with R9 making each character row span an even number of scanlines so the field-pairs effectively render the same content). True interlace-sync-and-video uses both bits = 1 — MODE 7 only.

- **R12/R13 hardware scrolling (soft modes):** address is `physical_addr / 8`, range `&0000-&0FFF`. Wrap at `&1000-&1FFF` triggers the wraparound mechanism (see [[hardware/address-translation]]).

### Programming method

Standard: `VDU 23,0,R,V,0,0,0,0,0,0` (Tube-safe, with `*TV`/VDU 23,1 cursor-control caveats). Direct `&FE00`/`&FE01` STA available on I/O processor.

## Cross-check against existing wiki

| Claim | Wiki state | BeebWiki | Resolution |
|---|---|---|---|
| R0 default for MODES 4-7 | 63 | 127 (whole row) | **Wiki correct** — BeebWiki appears wrong (1 MHz × 64 char = 64µs PAL scanline; 128 char would be 128µs out-of-spec). Flag in source page; do not "fix" entity page. |
| R10 BLK bits 6-5 encoding | "bit 6 enable, bit 5 rate" with `bit6=0,bit5=1` claimed to disable | 4-state field: off / steady / slow / fast | **Fix entity page** — BeebWiki's encoding matches the 6845 datasheet. |
| MODE 7 R12/R13 XOR `&54` | not documented | documented | **Add to entity page**. |
| 6845S variant needed | not noted | noted | **Add to entity page**. |
| MODE 7 alt HSP=52 | not noted | noted | **Add as a tip in custom-modes**. |

## Filed into

- Updated: [[hardware/crtc-6845]] (R10 fix, MODE 7 XOR, 6845S note, second-source citation).

## Notes

The R0=127-across-the-board appears to be a transcription error in BeebWiki — the rest of the row data is sensible and matches MOS. NAUG §13.3.3 p196 has the correct `R0=63` for LF modes. We keep our entity-page values from NAUG; the source page logs the discrepancy.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
