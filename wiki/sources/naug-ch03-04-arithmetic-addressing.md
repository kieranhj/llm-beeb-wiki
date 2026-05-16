---
title: NAUG Ch3 + Ch4 — Arithmetic & Addressing Modes
type: source
parent: [[sources/naug]]
pages: 22-34
section: §3, §4
tags: [6502, 65c12, addressing-modes, bcd, twos-complement]
updated: 2026-05-13
---

# NAUG Ch3 + Ch4 — Arithmetic & Addressing Modes

Holmes & Dickens, *The New Advanced User Guide*, pp.22-34. Foundational chapters for the ISA reference ([[hardware/6502-isa]]). Captured here because cycle costs and flag effects only make sense once you know *which* addressing mode produced them.

## Key facts captured

### Arithmetic (§3)

- 2's complement: -128..+127 with 8 bits. Sign = bit 7. To negate: invert all bits and add 1.
- Carry flag is the 9th bit on add, borrow indicator on subtract (carry **clear** = borrow occurred).
- Overflow flag set when signed-result-bit-7 is wrong. Specifically: when a carry from bit 6→7 happens without an external carry, or vice versa.
- BCD via `SED`. Each nibble holds 0-9; 6 of the 16 nibble values are skipped. Carry stores the inter-byte carry as expected. Use `CLD` to leave BCD mode.
- **The decimal flag must always be cleared (`CLD`) before any OS call** (§3.2 p18). NMOS does *not* auto-clear D on IRQ/BRK; 65C12 does. If you SED at the start of a routine, CLD before returning or before any JSR into MOS.
- BCD has no standard signed representation — roll your own for negative numbers.
- **65C12 BCD** (§3.3 p18): `ADC` and `SBC` in decimal mode cost **+1 cycle** because the 65C12 correctly updates N, V, Z (NMOS leaves them indeterminate after BCD). Use BCD only when the cycle hit is acceptable.

### Addressing modes (§4)

12 modes (NMOS) + 2 added on 65C12:

| Mode | Syntax | Operand width | Notes |
|---|---|---|---|
| Implicit | `RTS`, `NOP` | 0 | No operand |
| Accumulator | `ASL A` | 0 | A *is* the operand |
| Immediate | `LDA #&FF` | 1 | Constant embedded in instruction |
| Absolute | `LDA &3000` | 2 | 16-bit address |
| Zero page | `LDA &80` | 1 | Address `&00xx`; 1c faster than abs |
| Indirect | `JMP (&1900)` | 2 | JMP only on NMOS; **buggy** (see below) |
| Absolute,X / Absolute,Y | `LDA &3000,X` | 2 | +X or +Y; +1c if page crossed (loads only) |
| Zero page,X | `LDA &80,X` | 1 | Wraps within zp |
| Zero page,Y | `LDX &80,Y` | 1 | LDX/STX only |
| (Indirect,X) | `LDA (&80,X)` | 1 | Pre-indexed; pointer at `(&80+X)` in zp |
| (Indirect),Y | `LDA (&80),Y` | 1 | Post-indexed; pointer at zp, then +Y; +1c if page crossed |
| Relative | `BNE label` | 1 | Branches only; signed -128..+127 from PC-after-branch |

**65C12 additions** (§4.12):
- `(absolute,X)` — only for `JMP`. PC ← (`addr + X`).
- `(zero page)` — no index. For ADC, AND, CMP, EOR, LDA, ORA, SBC, STA. Opcode pattern `&x2`. 5c, 2 bytes — same cost as `(ind),Y` minus the page-crossing penalty (no penalty since no index).
- Extended `BIT`: now supports immediate, `abs,X`, `zp,X` (NMOS only had `zp` and `abs`).
- `DEC A` / `INC A` (synonyms `DEA` / `INA`).

### The JMP (indirect) bug (§4.6 p21)

NMOS 6502A (Model B, B+, Electron, 6502 second processor): when the indirect address has low byte `&FF`, the high byte of the jump target is fetched from the **same page**, not the next one.

```
; NMOS behaviour:
JMP (&19FF)   ; LSB from &19FF, MSB from &1900 (NOT &1A00)
```

**Fixed on 65C12** (Master series, Master Compact). The fix costs +1c (6c vs 5c on NMOS) but is the safer instruction. To avoid the bug on NMOS without paying the cycle hit: never place a jump-table pointer with `(&xxFF)`.

### Relative branches

8 conditional branches (BCC, BCS, BEQ, BMI, BNE, BPL, BVC, BVS) plus 65C12 BRA. Range is **-128..+127 bytes from the byte after the branch instruction**. An offset of `-2` (`&FE`) branches to the branch itself (infinite loop).

The assembler computes the offset; `Out of range` error means the label is outside ±126ish. Workarounds:

```asm
; Long-distance "not equal" branch
    CMP something
    BEQ skip          ; invert the condition
    JMP far_label     ; unconditional, 3 bytes vs 2
.skip
```

## Filed into

- [[hardware/6502-addressing-modes]] — Full addressing-mode reference with worked examples.
- [[hardware/6502]] — Added JMP (ind) bug detail and CLD-before-OS rule.
- [[hardware/6502-isa]] — Already had cycle data; cross-linked to addressing modes for the *why*.

## Open follow-ups

- BCD multi-byte arithmetic worked examples — programmer rolls own; could file a technique page if BCD turns out to be in scope for performance work.
- Cross-reference the NMOS-vs-65C12 BCD flag indeterminacy with WDC 65C02 datasheet at some point.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
