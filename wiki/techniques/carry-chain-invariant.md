---
title: Carry-Chain Invariant (Raster's SEC-elimination discipline)
type: technique
tags: [optimisation, 6502, carry, line-drawing, bresenham]
sources: [line-drawing-implementations, raster-source]
updated: 2026-05-17
---

# Carry-Chain Invariant

A hot-loop discipline used by `raster.s` (from `ebenupton/virus`) to maintain `C=1` across every iteration of the Bresenham loop, eliminating the per-pixel `SEC` (2c) that other implementations pay. The header comment in raster.s formalises this as the **carry chain**.

See [[techniques/bresenham-line]] for the comparison.

## The problem

Bresenham's standard form uses `SBC` for the error update:

```asm
SEC                   ; 2c
LDA err
SBC delta_minor       ; sets C=1 on no-borrow, C=0 on borrow
STA err
```

The `SEC` is needed because no other instruction in the inner loop reliably leaves `C=1` on entry. RTW, Tricky, and Elite all pay this 2-cycle cost on every steep iteration.

## The idea

Instead of restoring C with `SEC`, *prove* that every reachable path through the loop leaves `C=1` on exit. Then the next iteration's `SBC` starts pre-carried — no `SEC` needed.

raster.s's commentary documents the proof, instruction by instruction:

| Instruction | Carry after | Notes |
|---|---|---|
| `SBC delta_minor` (no borrow) | `C=1` | preserved → next iter OK |
| `SBC delta_minor` (borrow) | `C=0` | followed by `ADC delta_major` |
| `ADC delta_major` (post-borrow) | **`C=1` always** | wrapped error + delta_major > 255, guaranteed by Bresenham invariant |
| `SBC #$F8` (column +8) | `C=1` | $F8 ≤ low-byte, no borrow |
| `ADC #$08` (column +8) | `C=0` or `C=1` | needs `SEC` to restore |
| `DEY` | unchanged | carry-neutral — this is the key |
| `BMI`, `BPL`, `BCC`, `BCS` | unchanged | branches don't touch C |
| `INY` / `CPY #8` | C=0 (common) | row cross only when Y=8 |

The carry-neutrality of `DEY` is what makes Y-up loops faster than Y-down: on Y-up, the row-step doesn't disturb C, so the chain holds. On Y-down, `INY/CPY #8` clears C and forces an explicit `SEC`.

## The saving

**Y-up steep loop:** 2c/pixel saved (no `SEC`).

**Y-down steep loop:** still needs `SEC` after `CPY #8`. raster.s pays 4c more per pixel on Y-down vs Y-up (the `INY` + `CPY` + `SEC` chain vs the carry-neutral `DEY/BMI`).

The analysis doc (§8.5 rec. 4) suggests always drawing steep lines Y-up (swapping endpoints if needed, as Tricky does), which would universalise the Y-up saving. Break-even point: 3 pixels.

## Where else it applies

Any hot loop using SBC for arithmetic: multiplication routines, scrolling, fixed-point math, anywhere `SEC + SBC` appears repeatedly. The technique is:

1. Trace every reachable path through the loop.
2. Identify which instructions touch C.
3. Prove that *every* exit point leaves C in the state the next iteration needs.
4. Where the proof fails, restructure (use `DEC` instead of `DEY`+`CPY`, use `SBC #$F8` instead of `ADC #$08`, etc.) until it holds.

The technique compounds with branch outlining (rare-case handlers placed off the hot path) — see raster.s lines 102-110 for the full statement.

## Costs

- **Programmer discipline.** Every change to the loop must re-validate the proof. A casual `LDA #imm` or `CMP zp` in the wrong place silently breaks it.
- **Documentation burden.** The chain is invisible to anyone not reading the carry-state column. raster.s spends ~15 lines of its header comment laying it out — this is necessary, not optional.
- **Y-down asymmetry.** As noted: 4c penalty on Y-down. Either accept it or implement endpoint-swap (extra setup cost, ~10c).

## When to use it

- **Performance-critical inner loops** where 2c/pixel matters (line drawing, scrolling, multiplication).
- **Hand-written assembly** where you control every instruction. Compiler output won't preserve this kind of invariant.

## When *not* to use it

- **Maintenance-heavy code.** If the loop will be modified often by different hands, the invariant will break and produce silent corruption.
- **Code where 2c/pixel is in the noise** — high-level glue, setup paths, one-shot routines.

## Cross-references

- [[techniques/bresenham-line]] — the comparison page (steep cycle table)
- [[techniques/cumulative-mask-batching]] — NJ's analogous trick (different mechanism)
- [[techniques/open-endpoint-chaining]] — Raster's other named innovation
- [[hardware/6502-isa]] — per-instruction carry effects
- [[sources/raster-source]] — annotated source for raster.s

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
