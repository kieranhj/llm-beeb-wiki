---
title: Undefined Opcodes on 6502 / 65C12 / R65C02
type: hardware
tags: [6502, 65c12, opcodes, undocumented, illegal, nop]
sources: [6502org-65c02-opcodes, naug-ch05-6502-isa, master-arm]
machines: [BBC B, BBC B+, Master 128, Master Compact, Master Turbo, 6502 2P]
updated: 2026-06-17
---

# Undefined Opcodes

What every undocumented / unimplemented opcode does on each CPU variant that ships in BBC kit. The summary up front: **the BBC Master's 65C12 does NOT raise BRK on undefined opcodes** — that's a WDC W65C02S behaviour, and WDC parts were never used by Acorn. All Acorn CMOS parts (G65SC12, R65SC12, R65C02) treat unimplemented opcodes as deterministic multi-byte NOPs with fixed cycle counts. The "illegal" instructions of the NMOS 6502 (the LAX / SAX / SHA / ARR / etc. family) are *only* a Model B / Electron concern — every CMOS Beeb turns them into NOPs of varying width.

## TL;DR per CPU

| CPU | Machines | Undefined behaviour |
|---|---|---|
| **NMOS 6502** | Model B, B+ (main CPU), Electron | ~105 undocumented opcodes with varied real semantics: LAX, SAX, DCP, ISC, SLO, RLA, SRE, RRA, ANC, ARR, ALR, AXS, SHA, SHX, SHY, TAS, LAS, plus a `KIL`/`JAM` family that halts the CPU. Several are unstable (depend on noise on the data bus, temperature). **Avoid.** |
| **R65SC12** | Master 128, Master Compact, B+ 6502 co-pro | All non-decoded opcodes execute as deterministic NOPs. 78 holes total — see table below. **No BRK trap.** |
| **R65C02** | Master Turbo (internal 65C102), 6502 2nd Processor | Same family as R65SC12 but with BBR/BBS/RMB/SMB filling columns `$x7` and `$xF`. Only 46 holes remain (columns `$x3` and `$xB` plus the column-2 holes). **No BRK trap.** |
| **WDC W65C02S** | *Never shipped in any BBC machine* | Undefined opcodes are reserved for future expansion; recent WDC parts do BRK. Listed here only because the rumour gets repeated. |

## The Master's 65C12 hole map

The R65SC12 fits in 256 opcode slots like this. **Bold** cells are undefined NOPs; everything else is a documented instruction:

```
     x0   x1   x2   x3   x4   x5   x6   x7   x8   x9   xA   xB   xC   xD   xE   xF
0x  BRK  ORA  NOP  NOP  TSB  ORA  ASL  NOP  PHP  ORA  ASL  NOP  TSB  ORA  ASL  NOP
1x  BPL  ORA  ORA  NOP  TRB  ORA  ASL  NOP  CLC  ORA  INC  NOP  TRB  ORA  ASL  NOP
2x  JSR  AND  NOP  NOP  BIT  AND  ROL  NOP  PLP  AND  ROL  NOP  BIT  AND  ROL  NOP
3x  BMI  AND  AND  NOP  BIT  AND  ROL  NOP  SEC  AND  DEC  NOP  BIT  AND  ROL  NOP
4x  RTI  EOR  NOP  NOP  NOP  EOR  LSR  NOP  PHA  EOR  LSR  NOP  JMP  EOR  LSR  NOP
5x  BVC  EOR  EOR  NOP  NOP  EOR  LSR  NOP  CLI  EOR  PHY  NOP  NOP  EOR  LSR  NOP
6x  RTS  ADC  NOP  NOP  STZ  ADC  ROR  NOP  PLA  ADC  ROR  NOP  JMP  ADC  ROR  NOP
7x  BVS  ADC  ADC  NOP  STZ  ADC  ROR  NOP  SEI  ADC  PLY  NOP  JMP  ADC  ROR  NOP
8x  BRA  STA  NOP  NOP  STY  STA  STX  NOP  DEY  BIT  TXA  NOP  STY  STA  STX  NOP
9x  BCC  STA  STA  NOP  STY  STA  STX  NOP  TYA  STA  TXS  NOP  STZ  STA  STZ  NOP
Ax  LDY  LDA  LDX  NOP  LDY  LDA  LDX  NOP  TAY  LDA  TAX  NOP  LDY  LDA  LDX  NOP
Bx  BCS  LDA  LDA  NOP  LDY  LDA  LDX  NOP  CLV  LDA  TSX  NOP  LDY  LDA  LDX  NOP
Cx  CPY  CMP  NOP  NOP  CPY  CMP  DEC  NOP  INY  CMP  DEX  NOP  CPY  CMP  DEC  NOP
Dx  BNE  CMP  CMP  NOP  NOP  CMP  DEC  NOP  CLD  CMP  PHX  NOP  NOP  CMP  DEC  NOP
Ex  CPX  SBC  NOP  NOP  CPX  SBC  INC  NOP  INX  SBC  NOP  NOP  CPX  SBC  INC  NOP
Fx  BEQ  SBC  SBC  NOP  NOP  SBC  INC  NOP  SED  SBC  PLX  NOP  NOP  SBC  INC  NOP
```

Holes (the NOPs): **78 opcodes total**.

### Holes by category — bytes, cycles, side effects

| Slot pattern | Slots | Bytes | Cycles | What it actually does on the bus |
|---|---|---|---|---|
| `$x3` (all 16) | $03 $13 $23 $33 $43 $53 $63 $73 **$83** $93 $A3 $B3 $C3 $D3 $E3 $F3 | 1 | 1 | True 1-cycle no-op. No memory access. No flag change. |
| `$xB` (all 16) | $0B $1B $2B $3B $4B $5B $6B $7B $8B $9B $AB $BB $CB $DB $EB $FB | 1 | 1 | True 1-cycle no-op. No memory access. No flag change. |
| `$x7` (all 16) | $07 $17 $27 $37 $47 $57 $67 $77 $87 $97 $A7 $B7 $C7 $D7 $E7 $F7 | 1 | 1 | True 1-cycle no-op. (R65C02: these are `RMB0..7` / `SMB0..7` — see R65C02 differences below.) |
| `$xF` (all 16) | $0F $1F $2F $3F $4F $5F $6F $7F $8F $9F $AF $BF $CF $DF $EF $FF | 1 | 1 | True 1-cycle no-op. (R65C02: `BBR0..7` / `BBS0..7`.) |
| immediate holes | $02 $22 $42 $62 $82 $C2 $E2 | 2 | 2 | Reads + discards operand byte. No write. |
| zp NOP | $44 | 2 | 3 | Reads zp address `(PC+1)`. **I/O hazard** (see below). |
| zp,X NOP | $54 $D4 $F4 | 2 | 4 | Reads `(zp+X) & $FF`. **I/O hazard.** |
| absolute NOP (long) | $5C | 3 | 8 | Reads from `(addr & $FF00) \| $FF` and then `$FFFF`. **I/O hazard.** |
| absolute NOP | $DC $FC | 3 | 4 | Reads absolute address. **I/O hazard.** |

So **`$93` on the Master is a 1-byte, 1-cycle NOP** — same as every other `$x3`. It's the slot where the NMOS unstable `SHA (zp),Y` lives, and the CMOS designers reclaimed it as a guaranteed no-op.

### Why "1 byte 1 cycle" matters

These are the cheapest pad instructions on a CMOS Beeb — half the cost of `NOP` (`$EA`, 1c-fetch + 1c-internal = 2c) on any 6502. Useful when you need a single bus cycle of delay and don't want to spend two:

```asm
EQUB &03    ; 1c — half the cost of NOP &EA (2c)
```

The 1-byte 1-cycle holes are however **not officially documented** by any of Acorn, Rockwell, or CMD — they're behaviour you've measured and decided to trust. Code that relies on them won't port to a W65C02S retrofit (if anyone ever does that to a Master), and the BBC BASIC assembler does not recognise any mnemonic for them — emit via `EQUB`. Comment what you're doing.

### I/O hazard on the multi-byte holes

The 2-, 3-, and 4-cycle holes (`$44 $54 $D4 $F4 $5C $DC $FC`) all perform a real memory read at an operand-derived address. If the operand happens to point into SHEILA (`$FE00-$FEFF`), you'll trigger a side-effect read on a peripheral — typically clearing a VIA IFR flag, latching a 6845 register read, or stepping a buffer. This is the same hazard as legitimate-but-unused `LDA $FExx` does, but it's silent: nothing in your disassembler will flag a "stray read of `$FE4D`" if it's wearing the `$DC` costume.

Treat these as worse-than-NOP and don't rely on them. The 1-byte 1-cycle slots have no bus access and are safe.

## R65C02 differences (Master Turbo, 6502 2nd Processor)

The Rockwell R65C02 (used in the Master Turbo's internal 65C102 and in the external 6502 2nd Processor) fills columns `$x7` and `$xF` with the bit-manipulation extensions:

- `$x7` → `RMB0..7 zp` / `SMB0..7 zp` (16 opcodes, 2-byte, 5-cycle each)
- `$xF` → `BBR0..7 zp,rel` / `BBS0..7 zp,rel` (16 opcodes, 3-byte, 5/6-cycle)

So on Turbo / 2P, only **46 holes** remain — columns `$x3` and `$xB` (still 1-byte 1-cycle NOPs) plus the 7 immediate holes plus the 7 multi-byte holes.

Concrete consequence: code that *intentionally* executes `$07` as a 1c pad on a Master 128 will execute `RMB0 zp` on a Master Turbo or via a 6502 2P — reading-modifying-writing whatever zp page byte the next byte names. That's a real corruption bug. **Don't pad with column-7 or column-F holes.** Use `$x3` or `$xB` only.

Detecting R65C02-vs-R65SC12 from software has no clean MOS API. The standard trick is to install a `BRKV` handler, execute e.g. `SMB0 &70` via `EQUB &87 : EQUB &70`, and:

- On R65C02 it executes silently — your handler doesn't fire.
- On R65SC12 it's a 1-byte 1-cycle NOP — the *next* byte (`$70` here) is then decoded as an opcode (`BVS rel`), which is harmless if you laid down a safe follow-up but otherwise unpredictable. So the test is "did `$70` get executed?" — easier to detect via a zp before/after value.

Note: this is the inverse of the test in [[hardware/6502#detecting-nmos-vs-cmos-at-runtime]] — that one distinguishes NMOS from any CMOS using `PHX`/`PLX`; this one distinguishes R65SC12 from R65C02 within the CMOS family.

## NMOS 6502 (Model B, B+, Electron)

For completeness — the wiki doesn't have an NMOS undocumented-opcode page yet because it isn't useful on BBC kit (Acorn's MOS and BBC BASIC never used them, and no demo code reaches for them since the same machines can be running a Master CPU under emulation). One-line summary: avoid. If you want detail, the canonical reference is [[sources/6502org-65c02-opcodes]] for CMOS and the [No More Secrets / 6502 Undocumented Opcodes](http://www.oxyron.de/html/opcodes02.html) writeup for NMOS — not yet ingested.

The handful of NMOS illegals that are *stable* and were used by Commodore / Apple II demo coders (LAX, SAX, DCP, ISC, ANC) are pure NOPs on every BBC CMOS CPU. Cross-platform code that uses them silently breaks on a Master.

## Why this page contradicts the old claim in `hardware/6502.md`

This page was created on 2026-06-17 after a user query. The old version of [[hardware/6502]] (section "Detecting NMOS vs CMOS at runtime", line 76) claimed:

> the BRK that the 65C12 raises on encountering an undocumented opcode

That was wrong. The BRK-on-undefined behaviour is specific to **WDC W65C02S** (with the `RDY` / `BBR` reservation strategy from ~1990 onward). The R65SC12 in every shipping Master is a **Rockwell** part and follows the original 65C02 convention of treating undefined opcodes as deterministic NOPs. The `hardware/6502.md` claim has been corrected to point at this page.

How the BRK-trap rumour spreads: emulators sometimes default to "trap undefined" as a debug aid (jsbeeb has a config flag), and writers conflate that with the chip's real behaviour. On real Master 128 hardware running an R65SC12, `$93` does nothing for 1 cycle and execution continues.

## See also

- [[hardware/6502]] — CPU variants, registers, flags, NMOS-vs-CMOS detection idiom.
- [[hardware/6502-isa]] — Per-mnemonic byte/cycle reference for the *documented* instructions.
- [[hardware/6502-addressing-modes]] — Mode mechanics for the documented opcodes.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
