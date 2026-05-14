---
title: NAUG Ch5 — 6502 Instruction Set
type: source
parent: [[sources/naug]]
pages: 35-106
section: §5
tags: [6502, 65c12, r65c02, instruction-set, cycles, opcodes]
updated: 2026-05-13
---

# NAUG Ch5 — The 6502 Instruction Set

Holmes & Dickens, *The New Advanced User Guide*, pp.35-106. The chapter's structure is one page per mnemonic, each listing addressing modes, byte counts, cycle counts, opcodes, flag effects, and a worked example. This source page captures the chapter-level facts; the per-mnemonic data is filed in [[hardware/6502-isa]].

## Notational conventions (§5.0, p37)

- One instruction cycle = **0.5 µs** on BBC Model B / Master (2 MHz)
- One instruction cycle = **0.33 µs** on 6502 second processor (3 MHz)
- One instruction cycle = **0.25 µs** on Master Turbo co-processor (4 MHz)
- `*` marks instructions/modes new on the **65C12** (Master series).
- `**` marks instructions only on the **Rockwell R65C02** (Master Turbo and 6502 second processor): BBR, BBS, RMB, SMB, plus WAI/STP. The BASIC assembler does not recognise these — must be assembled with EQUate.

## Processor registers and status flags (§5.1, p35-36)

- **A** (8-bit accumulator): arithmetic and logical operations.
- **X**, **Y** (8-bit index registers): offsets for indexed addressing; loop counters.
- **SP** (8-bit stack pointer): low byte of stack address; high byte is always `&01`. Stack lives in `&0100-&01FF`.
- **PC** (16-bit program counter).
- **P** (status register), bits:
  - bit 0 — **C** Carry: set on add overflow, cleared on subtract borrow; bit 9 in shifts/rotates.
  - bit 1 — **Z** Zero.
  - bit 2 — **I** Interrupt disable. Set by CPU on entry to IRQ.
  - bit 3 — **D** Decimal mode (BCD arithmetic).
  - bit 4 — **B** Break — set in the status copy pushed by BRK.
  - bit 5 — unused.
  - bit 6 — **V** Overflow.
  - bit 7 — **N** Negative.

## Key cross-CPU differences captured in this chapter

- **CLD on entry to BRK** is cleared on the 65C12 but **not** on the NMOS 6502 (§5.2 BRK, p52). Critical for interrupt handlers if D is being used.
- **Decimal-mode arithmetic** costs an extra cycle on the 65C12 for `ADC`/`SBC` (§5.2 ADC p39, SBC p91, CLD p56, SED p93).
- **JMP (indirect)** takes **6 cycles on 65C12** vs **5 cycles on the 6502A** — the 65C12 fix is one cycle slower (§5.2 JMP p71). The 65C12 also fixes the page-boundary bug present in the NMOS JMP (ind).
- RMW `absolute,X` (ASL/LSR/ROL/ROR) takes **6 cycles (+1 if page crossed) on 65C12** but **7 cycles on the 6502A** (§5.2 ASL p41, LSR p76, ROL p87, ROR p88).
- 65C12 adds `(zp indirect)` mode (no X/Y) for ADC, AND, CMP, EOR, LDA, ORA, SBC, STA — opcode pattern `&x2`. 5 cycles, 2 bytes.
- 65C12 adds: **BRA** (rel, 3c +1 page), **STZ/CLR**, **DEC A/INC A** (alias DEA/INA), **PHX/PHY/PLX/PLY**, **TRB/TSB**, **JMP (abs,X)**, immediate **BIT**, plus `zp,X` and `abs,X` modes for BIT.
- R65C02-only: **BBR0..7**, **BBS0..7** (5c +1 if branch +2 if new page), **RMB**, **SMB**, **WAI**, **STP**. Must be hand-assembled with EQUB.

## Branch timing (uniform across 6502 / 65C12)

All conditional branches: **2 cycles base, +1 if branch taken, +2 if branch destination is on a different page.** A taken branch within the same page is 3c; to a different page, 4c.

## Page-crossing penalty (load-side)

`absolute,X`, `absolute,Y`, and `(indirect),Y` incur +1 cycle on loads (ADC/AND/CMP/EOR/LDA/ORA/SBC) when the indexed address crosses a page boundary. Stores via these modes always pay the worst-case cycle count (no conditional penalty — they are listed at the higher count in this chapter).

## Filed into

- [[hardware/6502]] — CPU entity page (registers, flags, machine variants).
- [[hardware/6502-isa]] — Full instruction reference: cycle table, opcodes, addressing modes per mnemonic.

## Key extracts retained

- Summary mnemonic table — see [[hardware/6502-isa#summary]] (p38).
- Per-mnemonic cycle/opcode tables — see [[hardware/6502-isa]].
- BBR/BBS opcode lists — see [[hardware/6502-isa#r65c02-only]] (p42-43).

## Open follow-ups

- Page-crossing on stores: NAUG lists stores at the unconditional worst-case count (no `+1p` annotation). [[sources/naug-ch03-04-arithmetic-addressing]] and [[hardware/6502-addressing-modes]] document this consistently; closed.
- WDC W65C02S datasheet cross-check for 65C12 RMW abs,X exact timing remains a nice-to-have but not blocking.
