---
title: BBC Micro Line Drawing Implementations — Comparative Analysis
type: source
tags: [bresenham, line, technique, graphics, mode-4, mode-2]
source_files:
  - raw/notes/BBC Line drawing implementations.pdf
  - raw/notes/line-test/Linedraw Elite.txt
  - raw/notes/line-test/rtw-linedraw.asm
  - raw/notes/line-test/nj-linedraw4.asm
  - raw/notes/line-test/tricky-linedraw.asm
updated: 2026-05-17
---

# Source: BBC Micro Line Drawing Implementations

## Bibliographic

- **PDF:** `raw/notes/BBC Line drawing implementations.pdf` — analysis-only synthesis document (no named author in the PDF metadata). 9 pages, no date. Compares five 6502 Bresenham implementations.
- **Source repo:** [kieranhj/line-test](https://github.com/kieranhj/line-test) — supplies four of the five analysed routines: `Linedraw Elite.txt`, `rtw-linedraw.asm`, `nj-linedraw4.asm`, `tricky-linedraw.asm` plus a test harness `line-test.asm`. Mirrored into `raw/notes/line-test/`.
- **Missing:** `raster.s` (MODE 2 implementation analysed in §3.2, §7.5) is not in the repo. Cycle claims for Raster cannot be cross-checked against source within this wiki.

## Summary

A side-by-side cycle/byte analysis of five hand-tuned Bresenham line implementations on the BBC Micro:

| Impl. | Mode | Code size | Steep cycles/pixel | Origin |
|---|---|---|---|---|
| Elite | MODE 4/5 | ~350 B (est.) | ~35 | Disassembly of *Elite* (Bell/Braben, 1984) |
| RTW | MODE 4S | 297 B | ~42 | Rich Talbot-Watkins |
| NJ | MODE 4S | 2365 B | ~26 | "NJ" (unidentified) |
| Tricky | MODE 4S | 1270 B | ~34 | "Tricky" (unidentified) |
| Raster | MODE 2 | 1425 B | ~37 (up) / ~41 (down) | external (`raster.s`, not in repo) |

The document is itself a synthesis — every cycle count is the author's analysis of the source, not a benchmark measurement. Treat as authoritative for *relative* ranking and as a guide-rail for *absolute* numbers.

## Key technical claims

### Architectural taxonomy (§2)

- **Direction dispatch** falls into three families:
  - *Self-modified branches* (RTW): `PLP`/`BCC`/`BCS` patch 4 branch offsets at setup.
  - *Self-modified operands* (NJ): `dx`/`dy` patched into 16 `SBC #imm`/`ADC #imm` instructions; dispatch via indirect `JMP` through per-pixel-position address tables.
  - *Pure dispatch tables* (Tricky, Raster): 128-byte tables of code addresses; no inner-loop self-modification.
- **Error accumulator location** is the single biggest per-pixel cost lever: register-flow (NJ, Raster) saves 2c/pixel vs zero-page (Elite, RTW, Tricky).
- **NJ's cumulative pixel-mask batching** (§3.2): for shallow lines, X carries a bitmask accumulating across all columns traversed since the last y-step. A single `EOR (scr),Y / STA (scr),Y` then writes 1-8 pixels in one read-modify-write. Yields ~5c/pixel on the no-y-step pass-through path; ~8.75c/pixel amortised on horizontal lines.

### Per-pixel cycle tables (§3.1, §10)

| Component | Elite | RTW | NJ | Tricky | Raster (Yup) | Raster (Ydown) |
|---|---|---|---|---|---|---|
| Plot pixel | 14 | 15 | 13 | 13 | 16 | 16 |
| Error update | 9 | 8 | 4 | 6 | 5 | 5 |
| Error store/load | — | 3 | 2 | 3 | 2 | 2 |
| Y-step | 5 | 5 | 5 | 5 | 4 | 8 |
| Count | 5 | 8 | — | 4 | 8 | 8 |
| Carry restore | — | 2 | — | — | — | 2 |
| **Steep total** | ~35 | ~42 | ~26 | ~34 | ~37 | ~41 |

Notes:
- NJ's 0-cycle counting is from *deferred counting* — `DEC cnt` fires only on minor-axis steps, not per pixel. For dx=10, dy=100 steep line: saves ~360c total.
- Raster's Y-up vs Y-down gap (4c) is because `DEY/BMI` preserves carry but `INY/CPY #8` clears it, forcing an explicit `SEC`.
- NJ's `SBC #imm` (2c) vs ZP `SBC zp` (3c) saves 1c/pixel; the cost is ~64c of setup (8 STA-abs per axis × 2 = 16 patches).

### Setup costs (§4)

| Impl. | Setup cycles | Break-even vs RTW (steep) |
|---|---|---|
| Elite | 80-100 | — |
| RTW | 45-55 | (baseline) |
| NJ | 100-120 | ~4 pixels |
| Tricky | 50-70 | ~4-5 pixels |
| Raster | 50-60 (first), ~30 amortised in chains | — |

For lines shorter than ~5 pixels, NJ's setup penalty can exceed its inner-loop savings.

### Raster's distinctive features (§2.7, §7.5)

- Only colour-capable implementation (runtime-configurable colour parameter).
- Only one with **open-endpoint chaining** — last pixel not drawn; `raster_base` and Y left positioned for the next segment. Designed for wireframe polygon rendering with shared vertices (avoids double-XOR artifacts).
- **Carry-chain invariant**: C=1 maintained across all loop iterations, eliminating `SEC` from hot paths. Y-up DEY/BMI exploits carry-neutrality.
- **Pixel-pair processing**: MODE 2's 2-pixels-per-byte enables a single `STA` for 2 pixels (fast-fast pair) at ~21.5c/pair.
- Internal `init_base` overhead protection (~8c every call) regardless of whether overflow is possible.

### The three "innovations worth stealing" (§9.2)

1. **NJ's cumulative pixel-mask batching** — multiple pixels per `EOR`. Portable to any MODE 4 implementation.
2. **Raster's carry-chain invariant** — systematic C=1 maintenance eliminates `SEC`. Portable to anything using SBC-based error.
3. **Raster's open-endpoint chaining** — drawing up-to-but-not-including endpoint. Benefits any polygon renderer.

### Internal inconsistencies / cautions

- **Elite setup cost**: §3 ranking ("Pre-divided error, compact") describes ~50c division loop, but §10 setup-cost table lists 80-100c. Filed as the higher number with a flag.
- All cycle figures use `~` qualifiers in the source — treat as ±2c estimates, not exact counts.
- The "Raster" implementation is not in the line-test repo. Its analysis cannot be source-checked here. The named features (open endpoints, carry-chain, pixel-pair) and cycle estimates are all from the doc alone.

## Filed into

- [[techniques/bresenham-line]] — main comparison page, cycle tables, recommendations
- [[techniques/cumulative-mask-batching]] — NJ's batched shallow-line write
- [[techniques/carry-chain-invariant]] — Raster's C=1 discipline
- [[techniques/open-endpoint-chaining]] — Raster's polygon-friendly endpoint convention
- [[index]]
- [[log]]

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
