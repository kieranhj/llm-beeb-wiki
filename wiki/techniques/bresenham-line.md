---
title: Bresenham Line Drawing on the BBC Micro
type: technique
tags: [graphics, bresenham, line, mode-4, mode-2, vector, wireframe]
sources: [line-drawing-implementations]
updated: 2026-05-17
---

# Bresenham Line Drawing

Comparative reference for five hand-tuned 6502 line implementations on the BBC Micro: **Elite**, **RTW**, **NJ**, **Tricky** (all MODE 4/4S), and **Raster** (MODE 2). All numbers from [[sources/line-drawing-implementations]] — the comparative-analysis PDF that ships alongside the source repo `kieranhj/line-test`.

The wiki's [[user_wiki_mission|envelope-pushing bias]] points at NJ and Raster: both pull tricks (cumulative-mask batching, carry-chain invariants, deferred counting) that the textbook 6502 Bresenham doesn't.

## TL;DR — pick one

| Use case | Pick | Why |
|---|---|---|
| Long lines, performance first, code size no object | **NJ** | ~26c/pixel steep; ~5c/pixel shallow pass-through; 8.75c/pixel horizontal |
| Memory-tight (single page) | **RTW** | 297 bytes; ~42c/pixel; clean source |
| Balanced speed/size, ROM-friendly (no SMC) | **Tricky** | 1270 B; ~34c/pixel; dispatch-table architecture |
| Polygon edges (chained segments) | **Raster** | Open endpoints, runtime colour, MODE 2 |
| Very short lines (3-8 pixels) | **RTW** or **Tricky** | Low setup cost — NJ's ~100c setup penalty doesn't amortise |

## Steep-line cycle breakdown (per pixel, common path)

| Component | Elite | RTW | NJ | Tricky | Raster Y-up | Raster Y-down |
|---|---:|---:|---:|---:|---:|---:|
| Plot pixel | 14 | 15 | 13 | 13 | 16 | 16 |
| Error update | 9 | 8 | **4** | 6 | 5 | 5 |
| Error store/load | — | 3 | **2** | 3 | 2 | 2 |
| Y-step | 5 | 5 | 5 | 5 | **4** | 8 |
| Count | 5 | 8 | **—** | 4 | 8 | 8 |
| Carry restore | — | 2 | — | — | — | 2 |
| **Total** | ~35 | ~42 | **~26** | ~34 | ~37 | ~41 |

(Assumes: no x-step, no row/column crossing, branch-not-taken common path.)

**Why NJ wins steep:** three independent savings compound — register-flow error (no LDA/STA zp), self-modified `SBC #imm` instead of `SBC zp`, and [[techniques/deferred-counting|deferred pixel counting]] (DEC only on x-step). Total advantage over Tricky: 8c/pixel.

**Why Raster Y-down costs 4c more than Y-up:** `DEY/BMI` is carry-neutral; `INY/CPY #8` clears C and forces an explicit `SEC` to restore the [[techniques/carry-chain-invariant|C=1 invariant]].

## Shallow-line per-pixel costs

Shallow lines differ fundamentally between implementations:

| Strategy | Impl | Pass-through cycles/pixel | Horizontal (amortised) |
|---|---|---:|---:|
| Per-pixel RMW | Elite, Tricky | ~34-38 | same |
| Screen-byte caching | RTW | ~41 (cached) | ~32 (8 pixels share read+write) |
| Cumulative mask batching | **NJ** | **~5** (pass-through) | **~8.75** (8-pixel batch) |
| Pixel-pair (MODE 2) | Raster | ~21.5 (fast-fast pair) | ~21.5 |

NJ's [[techniques/cumulative-mask-batching|cumulative mask batching]] is the standout. For 8 consecutive horizontal pixels: 7 pass-throughs × 5c + 1 batch write (32c) + 3c carry = 70c total = 8.75c/pixel. This is close to the theoretical minimum (the screen RMW alone is ~11c per 8 pixels).

## Setup cost — when long-loop wins flip

Setup runs once per line. For short lines it dominates.

| Impl | Setup cycles | Cycles/pixel | Break-even vs RTW (steep) |
|---|---:|---:|---:|
| RTW | 45-55 | ~42 | (baseline) |
| Tricky | 50-70 | ~34 | ~3 pixels |
| Elite | 80-100 | ~35 | ~7 pixels |
| **NJ** | **100-120** | **~26** | **~4 pixels** |
| Raster | 50-60 (first), ~30 chained | ~37 | (different metric) |

For a 5-pixel line, RTW (210c + 50c setup = 260c) beats NJ (130c + 110c setup = 240c) only marginally. Below 4 pixels, RTW wins outright. This matters for particle systems and short-segment fonts.

## Code size

| Impl | Bytes | Ratio | Fits in… |
|---|---:|---:|---|
| RTW | 297 | 1.0× | One page with room to spare |
| Elite | ~350 | 1.2× | Two pages |
| Tricky | 1270 | 4.3× | 5 pages |
| Raster | 1425 | 4.8× | 6 pages (24 loop variants + utilities) |
| NJ | **2365** | **8.0×** | 10 pages (32 fully-unrolled variants) |

On a MODE 4S setup with code at `&3000` and screen at `&6000`, NJ consumes 28% of available code space. RTW leaves ~11.5 KB free.

## Architectural taxonomy

### Direction handling

| Impl | Mechanism | Setup work |
|---|---|---|
| Elite | Conditional jumps select inline blocks | small |
| RTW | Self-modified branch offsets (4 patches) | small |
| NJ | Self-modified `SBC`/`ADC` operands (16 patches) + dispatch table | large |
| Tricky | Pure 128-byte dispatch table + indirect JMP | medium |
| Raster | 24 dispatch entries + RTS-trampoline (PHA/PHA/RTS) | medium |

### Error accumulator

| Impl | Where | Per-pixel overhead |
|---|---|---:|
| Elite, RTW, Tricky | ZP (LDA + STA) | 6c |
| **NJ, Raster** | **register flow (A↔X)** | **4c** |

### Pixel counting

| Impl | Mechanism | Per-pixel cost |
|---|---|---:|
| Elite | DEX/BNE | 5c |
| Tricky | DEX/BNE | 4c |
| RTW, Raster | DEC zp/BNE | 8c |
| **NJ** | **count axis-crossings only** | **0c (common path)** |

NJ's deferred counting — decrement only on x-step (steep) or y-step (shallow) — is the highest single-issue ROI of any of the techniques. For dx=10, dy=100 steep line: saves ~360 cycles.

## Three innovations worth stealing

The PDF (§9.2) calls these out as the portable ideas. Each gets a dedicated page:

1. [[techniques/cumulative-mask-batching]] — NJ's threading of X across pixel columns so 8 EORs become 1 RMW. Adaptable to any MODE 4 implementation.
2. [[techniques/carry-chain-invariant]] — Raster's systematic C=1 maintenance. Exploits DEY/BMI carry-neutrality on Y-up. Removes `SEC` from the hot loop.
3. [[techniques/open-endpoint-chaining]] — Raster's "don't draw last pixel; leave state pointing at endpoint." Polygon vertices write exactly once → no double-XOR artifacts.

## The hybrid ideal (§9.3)

A theoretical best-of-breed MODE 4 implementation would combine: NJ's cumulative batching + deferred counting + self-mod SBC, Raster's carry-chain + open endpoints + branch outlining, Tricky's endpoint-reversal (always draw Y-up). Estimated ~22-24c/pixel steep, ~5c/pixel shallow, ~1500-2000 bytes. Nobody has shipped this; the line-test repo benchmarks the existing four.

## Implementation notes worth knowing

- **Endpoint conventions:** Elite/RTW/NJ/Tricky draw both endpoints (closed). Raster draws first but *not* last — designed for shared-vertex polylines. Don't mix conventions in one renderer.
- **Vertical wrap:** only Tricky has it (optional `VWRAP` flag). Useful for wrap-around playfields.
- **65C12 / Master:** Elite, RTW, NJ, Tricky are NMOS-compatible. **Raster requires 65C12** — uses `BRA` extensively for branch outlining (the analysis doc's "Works on 65C02: Yes" claim for all five is wrong on Raster; see [[sources/raster-source]]).
- **Colour:** only Raster supports it. The others are pure-EOR monochrome. Adding colour costs ~5c/pixel (`LDA/AND/ORA/STA` vs `EOR`).
- **MODE 2 porting:** the MODE-4 implementations need ~3c/pixel extra (AND/ORA pixel writing) plus 64-column screen arithmetic. Raster's pixel-pair model is likely near-optimal for MODE 2 already.

## Cross-references

- [[hardware/6502]] — instruction timing
- [[hardware/6502-isa]] — SBC/ADC variant cycle costs
- [[video/modes]] — MODE 4 vs MODE 2 byte layouts
- [[memory/memory-map]] — screen base addresses
- [[techniques/fast-animation]] — sibling technique (sprites rather than lines)
- [[techniques/multiplication]] — analogous "compare implementations" technique page

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
