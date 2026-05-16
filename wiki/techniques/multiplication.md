---
title: 8×8 Multiplication on 6502
type: technique
tags: [arithmetic, multiplication, lookup-tables, performance]
sources: [retrosoftware-fast-mult]
updated: 2026-05-16
---

# 8×8 Multiplication

The 6502 has no MUL instruction. Every multiply is software, and the choice of algorithm dominates the cost of anything geometric, arithmetic-heavy, or signal-processing. This page covers unsigned 8×8 → 16-bit. For signed fractional multiply (the actually-useful case for 3D / DSP work), see [[techniques/fixed-point]].

Three approaches in order of (cycles, table-bytes) tradeoff:

| Method | Cycles (avg) | Table size | Notes |
|---|---|---|---|
| Shift-and-add | ~113 | 0 | Baseline; no setup, no memory cost |
| Half-square LUT (4 tables) | **~55** | 1024 B | Classic `(a+b)²/4 − (a−b)²/4` trick |
| Half-square LUT (3 tables) | ~67 | 768 B | Same trick, 256 B saved via low-byte XOR identity |

Worth noting up front: the *real* speed wins on 6502 come from **knowing one of your operands at assembly time**. A `multiply by 17` is `ASL : ADC orig : ADC orig : ADC orig : ADC orig` (or self-modified shift-add) — costs ≤20 cycles and zero tables. Generic routines are only needed when both operands are runtime-variable.

## 1. Shift-and-add

Standard 8-bit Russian peasant. One iteration per source bit, shift result down and conditionally add multiplicand:

```asm
; A * X -> product (16-bit at zp)
.multiply
    CPX #0 : BEQ zero            ; X=0 special case
    DEX : STX product+1
    LSR A  : STA product         ; first iteration unrolled
    LDA #0
    BCC s1 : ADC product+1 : .s1 ROR A : ROR product
    BCC s2 : ADC product+1 : .s2 ROR A : ROR product
    BCC s3 : ADC product+1 : .s3 ROR A : ROR product
    BCC s4 : ADC product+1 : .s4 ROR A : ROR product
    BCC s5 : ADC product+1 : .s5 ROR A : ROR product
    BCC s6 : ADC product+1 : .s6 ROR A : ROR product
    BCC s7 : ADC product+1 : .s7 ROR A : ROR product
    BCC s8 : ADC product+1 : .s8 ROR A : ROR product
    STA product+1
    RTS
```

Average **~113 cycles**. The `BCC` skips a 4-cycle add when the corresponding bit is 0, so cost is data-dependent: ~85c when one operand is small, ~140c when both are dense. Full source in `raw/code/fastmult.6502`.

## 2. Half-square LUT — the trick

The identity:

```
(a + b)² − (a − b)² = 4ab
```

So if `f(x) = x² / 4`, then `ab = f(a+b) − f(a−b)`. Two LUT reads and a subtract.

The `/4` is **lossless** — `(a+b)² − (a−b)²` is always a multiple of 4, so discarding the low 2 bits from the squared values loses nothing.

For 8-bit `a, b`:
- `a + b` ranges 0..510 → needs two tables (one for n < 256, one for n ≥ 256).
- `a − b` ranges 0..255 (after taking absolute value) → uses the 0..255 table.
- Each table is 256 × 16-bit entries → split into low-byte and high-byte tables for indexed addressing.

That's **4 tables × 256 bytes = 1024 bytes** of LUT.

### 4-table version (~55 c)

```asm
; num1 * num2 -> result (16-bit)
.mult
    SEC : LDA num1 : SBC num2 : BCS positive   ; |num1 - num2|
    EOR #255 : ADC #1
    .positive
    TAY                                         ; Y = |a-b|
    CLC : LDA num1 : ADC num2 : TAX             ; X = a+b
    BCS morethan256
    SEC
    LDA sqrlo256,X : SBC sqrlo256,Y : STA result
    LDA sqrhi256,X : SBC sqrhi256,Y : STA result+1
    RTS
.morethan256
    LDA sqrlo512,X : SBC sqrlo256,Y : STA result
    LDA sqrhi512,X : SBC sqrhi256,Y : STA result+1
    RTS
```

Two 16-bit subtractions: 8 LDA/SBC/STA cycles each ≈ 32c, plus the sign-fix and add. Average **~55 cycles** — about **2× faster** than shift-and-add.

### 3-table version (~67 c) — 256 B saved

Observation: `sqrlo512(n) = sqrlo256(n)` when `n` is even, and `sqrlo512(n) = sqrlo256(n) XOR &80` when `n` is odd. So one low-byte table covers both ranges:

```asm
.morethan256
    LDA sqrhi512,X : STA result+1
    TXA : AND #1 : BEQ skip : LDA #&80
    .skip
    EOR sqrlo,X                              ; XOR &80 only if X is odd
    .lessthan256
    SBC sqrlo,Y : STA result
    LDA result+1 : SBC sqrhi256,Y : STA result+1
    RTS
```

The `TXA : AND #1 : BEQ : LDA : EOR` insertion costs ~10c in the morethan256 path, hence ~67c average. **Saves 256 bytes** at modest cycle cost.

## Why this works — and why it's still fast

Per-operation cost breakdown for the 4-table half-square method:
- 1× absolute-difference (SEC, LDA, SBC, BCS, EOR, ADC) ≈ 14c
- 1× sum (CLC, LDA, ADC, TAX) ≈ 8c
- 2× 16-bit indexed SBC (4 LDA + 2 SBC + 2 STA) ≈ 28c
- Branch and overhead ≈ 5c
- **Total ≈ 55c**, vs shift-and-add's **113c**

The win comes from collapsing 8 conditional adds into 2 table reads. The table itself encodes the multiplication structure.

## Variants and further reading

The half-square method is one of many. **Toby Lobster's [`multiply_test`](https://github.com/TobyLobster/multiply_test)** repo benchmarks dozens of 6502 multiplication routines — different table sizes, different unrolling strategies, signed/unsigned, 8×8/8×16/16×16. If you need to pick the right tradeoff for a specific use case, that's the place to start. Companion repo [`sqrt_test`](https://github.com/TobyLobster/sqrt_test) does the same for square root.

Other approaches worth knowing about (not covered here in detail):

- **Log/exp tables**: `ab = exp(log(a) + log(b))`. Wider table footprint, similar performance, gets you division for free.
- **Self-modifying multiply-by-constant**: assemble the constant in at runtime, then unroll into bit-set adds. Faster than any LUT when the constant is known to live for many iterations.
- **Booth's algorithm / radix-4**: 2 bits per iteration. Better for 16×16 than the half-square (which needs much bigger tables for 16-bit operands).

## Used by

- [[techniques/fixed-point]] — builds the base-127 fixed-point multiply on top of `MultTableHigh` (the half-square table further divided by 127).
- 3D engine inner loops, signal-processing, anywhere `a*b` shows up in a per-frame inner loop.
