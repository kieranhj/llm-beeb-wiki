---
title: raster.s — Annotated MODE 2 Line Rasterizer
type: source
tags: [bresenham, line, technique, graphics, mode-2, 65c12]
source_files:
  - raw/notes/line-test/raster.s
updated: 2026-05-17
---

# Source: raster.s (ebenupton/virus)

## Bibliographic

- **Origin:** [ebenupton/virus / raster.s](https://github.com/ebenupton/virus/blob/master/raster.s) — Eben Upton's "virus" repo. Mirrored into `raw/notes/line-test/raster.s` (1421 lines, ~1425 bytes assembled per the comparative analysis).
- **Counterpart analysis:** [[sources/line-drawing-implementations]] — describes Raster's architecture and cycle costs as part of a 5-way comparison. The source confirms (and elaborates on) every claim there.
- **Build target:** MODE 2 (128×160, 4bpp, 2 pixels per byte). **65C12 required** — uses `BRA` (line 106 of header). Won't run on a vanilla NMOS 6502, despite the comparative-analysis doc's feature table listing all five implementations as "Works on 65C02: Yes".

## Summary

A heavily-optimised Bresenham line rasterizer for MODE 2, designed for chained polygon-edge rendering. The 200-line header comment in the source is itself a pedagogical document — it lays out the architectural decisions, the carry-chain proof, the branch-outlining strategy, and the API contract.

The file is the canonical reference for three of the techniques in this wiki:

- [[techniques/carry-chain-invariant]] — systematic C=1 maintenance
- [[techniques/open-endpoint-chaining]] — polygon-friendly endpoint convention
- (Pixel-pair processing — documented in [[techniques/bresenham-line]])

## Key technical claims (from the source header itself)

### API contract (header §35-42)

```
draw_line draws pixels from (raster_x0,raster_y0) up to but NOT
including (raster_x1,raster_y1). On return, raster_base/Y are
positioned at (raster_x1,raster_y1).
```

Caller protocol:
1. `JSR init_base` once per polyline
2. `JSR draw_line` per segment, copying `x1→x0`, `y1→y0` between calls
3. Plot the final pixel manually using `(raster_base),Y`

### MODE 2 byte layout (header §17-30)

- 128×160 pixels, 4bpp, 64 byte-columns
- Character rows of 512 bytes (64 cols × 8 rows)
- `addr = screen_base + char_row*512 + byte_col*8 + sub_row`
- Per byte: **left pixel = bits 5,3,1**; **right pixel = bits 4,2,0**
- Colour 7 left = `$2A`, colour 7 right = `$15`, both = `$3F`
- AND-clear masks: clear left = `$D5`, clear right = `$EA`

### Steep vs shallow dispatch (header §73-78)

- **Steep** (|dy| > |dx|): 8 variants indexed by `{x0_parity, x_dir, y_dir}`. One pixel per iteration.
- **Shallow** (|dx| ≥ |dy|): 16 variants indexed by `{x0_parity, ~count_parity, x_dir, y_dir}`. Pixel pairs.

Total: 24 loop entries.

### Two-pixel pairing (header §80-100)

Three sub-cases per shallow pair:
- **fast-fast (ff):** neither pixel Y-steps. Single `STA raster_color_both` writes both. No RMW.
- **slow:** first pixel Y-steps. Both pixels need RMW.
- **fast-slow:** first pixel fast, second Y-steps.

Loop architecture also picks "mid" vs "end" for the `DEC+BNE` test based on `x0_parity XOR ~count_parity`, eliminating one branch entirely. Dispatch encodes this in entry point (`_l` vs `_r`).

### Carry chain (header §56-71)

Documented invariant: `C=1` on entry to each iteration. Proof per instruction:
- `SBC delta_minor` no-borrow → C=1 preserved
- `SBC delta_minor` borrow → `ADC delta_major` always produces C=1 (Bresenham invariant: wrapped error + delta_major > 255)
- `SBC #$F8` (col +8) preserves C=1
- `ADC #$08` (col +8) needs SEC
- `DEY` carry-neutral — preserves chain on Y-up
- `INY/CPY #8` clears C — Y-down needs SEC

Y-up gains 2c/pixel from eliminating SEC. Y-down doesn't — 4c gap between variants.

### Branch outlining (header §102-110)

65C02 (65C12) branch cost: taken = 3c, not-taken = 2c. Every conditional branch is arranged so common case falls through. Rare handlers outlined after the fall-through, returning via `BRA` (+2 bytes per outline, saves 1c on every common iteration).

Applied to: Y-up row cross (1/8), Y-down row cross (1/8), column page cross (1/32), Bresenham Y-step (workload-dependent).

### Page/row cross deduplication (header §112-121)

Row cross every 8 Y-steps; column page cross every 32 column steps. Right-moving page handlers share the `DEC pixel_count + BNE + RTS` tail — page handler `BRA`s to a `_dec` label after the `SEC`, saving 4 bytes per instance at +3c on the rare page-cross path.

### Steep X-step / pixel toggle (header §123-136)

Steep lines alternate left/right pixel phases:
- **Y-down (tdr/tdl):** X-step uses `BRA` to paired ystep label — remote branch.
- **Y-up (tur/tul):** X-step *inlines* the paired phase's Y-step + loop-back. Costs ~20 bytes per pair, saves 3c per X-step.

### Register conventions (header §138-145)

- **Inner loop:** X = Bresenham error, Y = sub-row 0..7, A = scratch
- **ZP:** `raster_base` (2B pointer), `delta_minor`/`delta_major`, `pixel_count` (pixels for steep, pairs for shallow), `raster_color_{left,right,both}`

## Contradictions surfaced

- **65C02-only:** The comparative analysis doc says (Feature Comparison, §6) "Works on 65C02: Yes" for all five implementations. raster.s uses `BRA` (65C12-only) extensively for branch outlining — it will not assemble or run on NMOS 6502. The doc's feature table is wrong on this point. The other four (Elite, RTW, NJ, Tricky) are all NMOS-compatible per their sources.

## Filed into

- [[techniques/bresenham-line]] — main comparison page
- [[techniques/carry-chain-invariant]] — Raster's carry discipline
- [[techniques/open-endpoint-chaining]] — Raster's API contract
- [[video/modes]] — MODE 2 byte layout cross-check
- [[index]]
- [[log]]

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
