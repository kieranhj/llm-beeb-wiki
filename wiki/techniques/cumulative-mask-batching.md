---
title: Cumulative Pixel-Mask Batching (NJ's shallow-line trick)
type: technique
tags: [graphics, bresenham, line, mode-4, optimisation, smc]
sources: [line-drawing-implementations]
updated: 2026-05-17
---

# Cumulative Pixel-Mask Batching

The single most clever idea in BBC line drawing. Invented (so far as the line-test analysis records) by "NJ" in `nj-linedraw4.asm`. Drops shallow-line cost from ~34c/pixel to ~5c/pixel on the no-y-step common path, and to ~8.75c/pixel amortised on horizontal lines.

See [[techniques/bresenham-line]] for the broader implementation comparison.

## The problem it solves

In MODE 4 (8 pixels/byte), a near-horizontal Bresenham line will plot several pixels into the same screen byte before y-steps onto the next row. The naive approach reads the byte, EORs in one pixel, writes the byte — *for every pixel*. That's `LDA (scr),Y / EOR #imm / STA (scr),Y` = 13c per pixel, *plus* error update and counting. The screen byte gets read 8 times and written 8 times to draw 8 pixels.

RTW improves on this with **screen-byte caching**: hold the byte in A across pixels in the same byte, write it out only on y-step or column change. Saves ~5c/pixel for horizontal runs.

NJ goes further.

## The idea

Each pixel column within a byte has its own loop entry point (`a00`, `a10`, ..., `a70`). At the entry, X is loaded with a *cumulative mask* covering this column and all columns to its right:

```
a00: LDX #$FF   ; columns 0-7 traversed since last y-step
a10: LDX #$7F   ; columns 1-7
a20: LDX #$3F   ; columns 2-7
a30: LDX #$1F   ; columns 3-7
a40: LDX #$0F   ; columns 4-7
a50: LDX #$07   ; columns 5-7
a60: LDX #$03   ; columns 6-7
a70: LDX #$01   ; column 7 only
```

**Key insight:** when no y-step occurs, control falls through to the next column's `SBC` directly, *skipping* its `LDX #imm`. X retains the wider mask from the original entry point — accumulating coverage column by column. The actual screen write happens only on y-step, when one `EOR (scr),Y / STA (scr),Y` commits *all* accumulated columns in a single RMW.

## The hot path

For each pixel column, no-y-step case:

```asm
; (X already holds cumulative mask from earlier entry)
b50: SBC #dy    ; 2c — dy is self-modified immediate
     BCS b60    ; 3c — fall through to next column on no-y-step
```

**5 cycles per pixel** on the pass-through path. No screen access. No counter decrement. No carry restoration.

## The y-step batch write

When the `BCS` falls through (y-step needed), the accumulated mask gets committed:

```asm
     ADC #dx        ; 2c   restore error
     STA err        ; 3c
     TXA            ; 2c   recover cumulative mask from X
     AND #&XX       ; 2c   trim to columns actually traversed
     EOR (scr),Y    ; 5c   batch-write all pixels at once
     STA (scr),Y    ; 6c
     DEC cnt        ; 5c   counter fires only on y-step
     BEQ done       ; 2c
     DEY            ; 2c
     BPL nextrow    ; 3c
                    ; = 32 cycles for the batch
```

For 8 pixels in a byte: 7 × 5c + 32c + 3c = **70 cycles / 8 pixels = 8.75c/pixel**. The screen is read once, written once. Approaching the theoretical floor.

For a 45° diagonal (y-step every pixel): no batching gain — degenerates to ~37c/pixel.

## Why it works

Three properties combine:

1. **Falling through column entry points** — code is unrolled per pixel column, but consecutive columns are physically adjacent in memory. The `BCS` to the next column lands on its `SBC`, *past* its `LDX #imm`.
2. **X carries state across loop iterations** — Bresenham's other implementations clobber X for indexing or counting. NJ reserves X for the cumulative mask.
3. **The mask values are monotonic** — `$FF, $7F, $3F, ...` — successive masks are strict subsets of earlier ones, so trimming at write time (`TXA / AND #trim`) yields exactly the pixels traversed since entry.

## Costs

- **Code size:** 32 unrolled column bodies (8 columns × 4 octants) plus the steep loops. NJ totals 2365 bytes.
- **Setup:** ~100-120c. 16 SBC immediate operands need patching with dx/dy on every line.
- **SMC:** Cannot run from ROM. Self-modifying both setup operands and (implicitly) operates through `JMP (x1)` indirect-through-table dispatch.
- **Complexity:** the `ls` (loop-segment) and `errs` variables handle the final partial column. Easy to get off-by-one wrong. The source is dense and minimally commented.

## When to use it

- **Long, near-horizontal lines** (e.g. wireframe horizons, vector-mode terrain). Massive win.
- **Game logic where line drawing is a clear hot path** and 2 KB of code is acceptable.

## When *not* to use it

- **Short lines** (<5 pixels). Setup cost dominates — see [[techniques/bresenham-line]] for break-even table.
- **45°-ish lines.** Y-step every pixel → no batching, no win over Tricky.
- **ROM code.** Can't SMC.
- **Memory-tight projects.** RTW at 297 B is 1/8 the size with comparable horizontal-line performance via byte-caching.

## Adapting to other modes

- **MODE 5/2 (colour):** harder. The batched RMW needs both AND-mask (clear) and ORA-value (set) per pixel. Could be done with two accumulator registers, or by pre-composing the colour into the cumulative mask. Adds ~3c/pixel and complicates the trim mask.
- **MODE 2:** only 2 pixels per byte → batching gain is at most 1 extra pixel per write. Probably not worth the architecture change vs Raster's pixel-pair approach.
- **MODE 0/3:** 8 pixels/byte like MODE 4 — directly applicable.

## Adapting to other implementations

Tricky's dispatch-table architecture is close enough to NJ's that the cumulative-mask trick could be retrofitted. The doc (§8.4) explicitly flags this as the highest-impact improvement to Tricky: could reduce shallow per-pixel cost from ~34c to ~10c.

## Cross-references

- [[techniques/bresenham-line]] — the comparison page
- [[techniques/deferred-counting]] — NJ's other key innovation
- [[techniques/carry-chain-invariant]] — Raster's analogous-but-different shallow trick
- [[hardware/6502-isa]] — SBC #imm vs SBC zp cycle cost
- [[sources/line-drawing-implementations]] — full citation

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
