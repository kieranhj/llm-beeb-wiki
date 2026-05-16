---
title: Fixed-Point Arithmetic (base-127)
type: technique
tags: [arithmetic, fixed-point, multiplication, 3d, lookup-tables, signed]
sources: [retrosoftware-fast-mult]
updated: 2026-05-16
---

# Fixed-Point Arithmetic — the base-127 trick

The 6502 has no FPU. For 3D, signal processing, and anything involving sines, reciprocals, or interpolation, you need fractional arithmetic that runs in a handful of cycles per multiply. The conventional answer is fixed-point: store fractional values as integers multiplied by a constant. This page documents the **base-127** representation — the precision-optimal way to encode `[-1.0, +1.0]` in a signed byte, by Talbot-Watkins ([[sources/retrosoftware-fast-mult]]).

The "trick" headline: **you don't need to pick a power-of-two fixed-point base**. With a LUT-based multiply, any constant is free. So pick the one that maximises precision and fits the byte symmetrically — which turns out not to be 64, 128, or 256, but **127**.

## Why power-of-two fails for `[-1, +1]` in a signed byte

| Base | Range encoded | Fits 8-bit signed? | Precision | Verdict |
|---|---|---|---|---|
| ×256 | -1.0..+1.0 → -256..+256 | **No** — needs 10 bits | 1/256 | Wastes 2 bits per value |
| ×128 | -1.0..+1.0 → -128..+128 | **Asymmetric** — -128 OK, +128 overflows | 1/128 | Can't represent +1.0 |
| ×64  | -1.0..+1.0 → -64..+64 | Yes, with waste | 1/64 | -65..-128 and +65..+127 unused |
| **×127** | -1.0..+1.0 → -127..+127 | **Yes, symmetric** | **~1/127** | Maximum precision, no waste |

Base-128 fails because of the asymmetry of two's complement (signed 8-bit covers -128..+127, not -128..+128). Base-64 wastes nearly half the byte's range. Base-127 fills the byte cleanly.

The objection to base-127 is "but then every multiply needs `/127`!" — which sounds awful, except that **we bake the /127 into the lookup table**.

## The multiply

Recall the half-square identity (see [[techniques/multiplication]]):

```
ab = f(a+b) − f(|a−b|),   where f(x) = x² / 4
```

Now make the table do the /127 too:

```
ab / 127 = g(a+b) − g(|a−b|),   where g(x) = x² / (4·127)
```

That's it. A single 256-byte table (high bytes only for S8 output; low bytes additionally needed for fractional accuracy in S15 output) does both the multiply and the fixed-point scaling in two LDA/SBC pairs.

Table size: **512 bytes total** (`MultTableHigh` + `MultTableLow`). Plus a 320-byte sin/cos table if you want trig.

## Signed multiply — the 4-way case split

The half-square method needs unsigned indices. The naïve way to handle signed inputs:

```
remember_sign = sign(a) XOR sign(b)
if a < 0: a = -a
if b < 0: b = -b
result = unsigned_multiply(a, b)
if remember_sign: result = -result
```

This costs cycles, and worse, the negative-input cases are slower than the positive cases — branch-predictable timing matters for raster-locked code.

**Better**: split into 4 cases by sign combo, and for the cases where the result *would* need negating, **reverse the subtraction order** of the two table reads instead. Free negation.

| Case | Computation |
|---|---|
| `++` (both positive) | `f(a+b) − f(|a−b|)` |
| `+−` (a pos, b neg) | `f(|a+b|) − f(a−b)` |
| `−+` (a neg, b pos) | `f(|a+b|) − f(b−a)` |
| `−−` (both negative) | `f(−(a+b)) − f(|b−a|)` |

Same number of table reads, no final-result negation. Cycle cost is uniform across all 4 cases.

The trick relies on: `f(−x) = f(x)` (since `x² = (−x)²`), and that swapping the subtraction order negates the result.

## S8 × S8 → S8 routine (~58 c)

```asm
; X = val1 (signed, -127..+127)
; Y = val2 (signed, -127..+127, treated as fixed-point with 127 = 1.0)
; Result: A = (val1 * val2) / 127, signed -127..+127

.S8_x_Fixed
    STX mulval1
    STY mulval2
    CLC
    TYA : BMI val2neg
    TXA : BMI val1neg_val2pos

.val1pos_val2pos                ; A holds val1, C clear
    ADC mulval2
    TAX                         ; X = val1 + val2
    SEC
    LDA mulval1
    SBC mulval2
    BCS skipnegate
    EOR #255 : ADC #1
    SEC
.skipnegate
    TAY                         ; Y = |val1 - val2|
    LDA MultTableHigh,X
    SBC MultTableHigh,Y
    RTS

; ... three more case-paths (val1neg_val2pos, val1pos_val2neg, val1neg_val2neg)
; each ~10-12 cycles, all converge to a 2-LDA/SBC table lookup pair.
```

Average **58 cycles** including JSR/RTS. Full 4-case listing in `raw/code/fixedpoint.6502`.

**Accuracy** (measured by the author): 75% of results within ±0.5, 99% within ±1.0. Errors come from the `(x²/(4·127) + 0.5)` rounding in the table — adequate for graphics, perspective, sound envelopes, anywhere the result will be quantised back to integers anyway.

## S15 × S8 → S15 routine (~170 c)

For "scale a 15-bit signed coordinate by a fixed-point factor" — i.e. perspective divides, scaling world coordinates. Splits val1 into high 8 bits and low 7 bits, multiplies each by val2, adds the partials.

```
val1 (15-bit signed) = (high_8_bits << 7) + low_7_bits
val1 * val2 = ((high << 7) * val2) + (low * val2)
            = (high * val2 << 7) + (low * val2)
```

The high-byte multiply uses both `MultTableHigh` and `MultTableLow` (need the fractional bit to round correctly after the right-shift). The low-byte multiply is inlined from `S8_x_Fixed` (only the val1-positive cases — low 7 bits are always unsigned).

Average **~170 cycles**. Used per-vertex in a 3D pipeline, so the inlining matters.

## Sine and cosine — for free

The bundled sin/cos table is built to dovetail with the multiply routines:

```basic
.SineTable
CosineTable = SineTable + 64     ; cos(θ) = sin(θ + 90°), offset 64 entries
FOR n, 0, 255 + 64
    EQUB INT(SIN(n/128*PI) * 127 + 0.5)   ; values scaled to ±127
NEXT
```

**Angle convention**: 256 = 360°. Pick this and angle arithmetic becomes free — angle addition is `ADC`, no modulo needed (8-bit wraps automatically). One byte per angle. The trig values come out already in base-127, so they feed directly into `S8_x_Fixed` or `S15_x_Fixed`.

Table size: **320 bytes** (256 sin + 64 cos extension, shared backing store).

Entry points provided:
```asm
.S8_x_Cosine     ; A = X * cos(Y)
.S8_x_Sine       ; A = X * sin(Y)
.S15_x_Cosine    ; XA = XA * cos(Y)
.S15_x_Sine      ; XA = XA * sin(Y)
```

So `r * cos(θ)` becomes `LDY angle : LDX radius : JSR S8_x_Cosine`. About **65 cycles** including the sin/cos lookup. That's the per-channel cost of a 2D rotation.

## What this enables

- **2D rotation** per vertex: 2 × `S8_x_Fixed` = ~120c.
- **3×3 matrix × 3-vector** (3D rotate): 9 × `S15_x_Fixed` = ~1530c, ≈ 0.77 ms at 2 MHz. Fits comfortably in a 20 ms frame even with hundreds of vertices.
- **Bilinear interpolation**: `start * t + end * (1−t)` is two `S8_x_Fixed` + an add.
- **Perspective divide via reciprocal table**: pre-tabulate `1/z` as a base-127 fixed-point value, then multiply.

## Open follow-ups

- The author left "Extending the algorithm to multiply bigger values by a fixed-point number" as TODO. The S15×S8 path is fine for most game work but S15×S15 or S15×S31 (e.g. for accurate perspective divides on large worlds) needs a worked extension.
- **Division** is the other 6502 arithmetic gap. Reciprocal-multiply (LUT of `127/n` for n=1..127, then `S8_x_Fixed`) gives `a/b` in ~70c if a one-byte-precise quotient is acceptable. Worth a [[techniques/division]] page if the use case comes up.
- For an exhaustive comparison of 6502 multiplication routines (and square roots) across many algorithms and table sizes, see Toby Lobster's benchmark suites: [`multiply_test`](https://github.com/TobyLobster/multiply_test) and [`sqrt_test`](https://github.com/TobyLobster/sqrt_test).

## Builds on

- [[techniques/multiplication]] — the half-square identity that makes base-127 affordable.
- Unused but available: any code that needs `[-1, +1]` math without the precision loss of base-64.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
