---
title: Retrosoftware — Fast multiplication + fixed-point library
type: source
urls:
  - http://www.retrosoftware.co.uk/wiki/index.php/Fast_multiplication_routines
  - http://www.retrosoftware.co.uk/wiki/index.php/Fast_fixed-point_multiplication_library
author: Richard Talbot-Watkins (Richtw)
dates: [2008, 2009]
local:
  - raw/articles/retrosoftware-fast-multiplication.md
  - raw/articles/retrosoftware-fast-fixed-point.md
code:
  - raw/code/fastmult.6502
  - raw/code/fixedpoint.6502
tags: [arithmetic, multiplication, fixed-point, lookup-tables, signed]
updated: 2026-05-16
---

# Retrosoftware — Fast multiplication + fixed-point library

Two related articles by Talbot-Watkins on overcoming the 6502's lack of a hardware multiplier:

1. **Fast multiplication routines** (2008) — unsigned 8×8 → 16-bit. Three implementations: shift-and-add, half-square LUT, half-square LUT with space optimisation.
2. **Fast fixed-point multiplication library** (2009) — signed fractional multiply, building on (1). Introduces the **base-127** fixed-point representation as the precision-optimal way to encode `[-1.0, +1.0]` in a signed byte.

## Key technical claims

### Article 1 — generic 8×8 multiplication

- **Shift-and-add baseline**: 8 iterations of ADC + ROR, average **~113 cycles**. No tables.
- **Half-square identity**: `(a+b)² − (a−b)² = 4ab`, so `ab = f(a+b) − f(a−b)` where `f(x) = x²/4`. The `/4` is lossless because `(a+b)² − (a−b)²` is always a multiple of 4.
- **4-table LUT version**: tables of `f(x)` low/high for x = 0..255 and x = 256..510. Average **~55 cycles**, **1024 bytes** of tables.
- **3-table optimised version**: unify the two low-byte tables — `sqrlo512(n) = sqrlo256(n) XOR &80` when n is odd, otherwise identical. Average **~67 cycles**, **768 bytes** of tables.

### Article 2 — fixed-point representations

- **8 fractional bits** (`×256`): range `[-1, +1]` needs 10 bits to encode, wastes 2 bits per value, doesn't fit byte ops cleanly.
- **7 fractional bits** (`×128`): can encode -1.0 but not +1.0 (asymmetry of signed 8-bit).
- **6 fractional bits** (`×64`): symmetric, fits, but only 1/64 precision and wastes range `±65..127`.
- **Base 127** (`×127`): symmetric, fits, maximum precision (~0.78% per step). The `/127` divide is baked into the LUT: `f(x) = x²/(4·127)`.

### Article 2 — signed multiplication

- Naïve approach (remember sign, negate, multiply, negate) costs cycles and makes negative-input cases slower.
- **4-way case split** on sign combos (++ / -+ / +- / --) reverses the table-lookup subtraction order in cases where the result would need to be negated. Uniform cycle cost across all sign combos.
- For ++: `a*b = f(a+b) − f(|a-b|)`.
- For +-: `a*b = f(|a+b|) − f(a-b)` (note swapped operand order).
- For -+: `a*b = f(|a+b|) − f(b-a)`.
- For --: `a*b = f(-(a+b)) − f(|b-a|)`.

### Article 2 — performance

- **`S8_x_Fixed`** (S8×S8 → S8): **~58 cycles avg** including JSR/RTS. Accuracy: 75% within ±0.5, 99% within ±1.0.
- **`S15_x_Fixed`** (S15×S8 → S15): **~170 cycles avg**. Two-half multiply: high 8 bits via half-square, low 7 bits inlined.
- Tables: 512 bytes (`MultTableHigh` + `MultTableLow`). The S8 routine uses only `MultTableHigh`; the S15 routine needs both for fractional accuracy in the high-half result.
- Sine/cosine table: **320 bytes**, 256-step angle (so 360° = 256), cos = sin offset by 64.

### Use case mentioned

- 3D games: `x = r * SIN(angle)` style transforms.
- Perspective divides via reciprocal multiply (per-vertex, so cycle budget matters).
- Bilinear interpolation: `start*t + end*(1−t)`.

## Filed into

- [[techniques/multiplication]] — new entity page covering both generic-multiplication articles' content.
- [[techniques/fixed-point]] — new entity page covering the base-127 representation, signed multiply case-splits, S8/S15 routines, sin/cos table.
- [[index]] / [[log]] — standard updates.

## Open follow-ups

- Article 2 has an "Extending the algorithm to multiply bigger values by a fixed-point number" section the author left as TODO ("Will write this up sometime"). Worth deriving / sourcing the S15×S8 → S31 path if anyone needs higher dynamic range.
- Division routines (`a/b`, reciprocal LUT for `1/b`) aren't covered in these articles but are essential for perspective. Open page request: [[techniques/division]].
- See also Toby Lobster's comprehensive 6502-multiplication benchmark suite at https://github.com/TobyLobster/multiply_test for a much wider comparison (dozens of routines, full timing matrices), and the companion sqrt benchmarks at https://github.com/TobyLobster/sqrt_test.
