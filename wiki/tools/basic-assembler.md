---
title: BBC BASIC Inline Assembler
type: tool
tags: [basic-assembler, beebasm, opt, equ]
sources: [naug-ch02-basic-assembler]
updated: 2026-05-13
---

# BBC BASIC Inline Assembler

The BBC BASIC `[` / `]` block-level assembler. Almost all NAUG-style code examples in this wiki target this syntax (or its near-superset, BeebAsm). This page is the cheatsheet.

## Skeleton

```basic
   10 DIM code% &200          : REM allocate space
   20 OSWRCH = &FFEE
   30 FOR pass% = 0 TO 3 STEP 3
   40   P% = code%            : REM where the code will run
   50   [
   60   OPT pass%
   70   .entry  LDA #ASC"!"
   80           JSR OSWRCH
   90           RTS
  100   ]
  110   NEXT pass%
  120 CALL entry              : REM run it from BASIC
```

## OPT bits

| Bit | Set means |
|---|---|
| 0 | Listing enabled |
| 1 | Errors enabled (suppress on pass 1 to allow forward refs) |
| 2 | Remote assembly: bytes land at `O%`, labels resolve to `P%` (Level 2 BASIC only) |

Typical: `OPT 0` pass 1 (silent, no errors); `OPT 3` pass 2 (listing + errors). For remote assembly use `OPT 7`.

## Location counters

- `P%`: program counter — incremented as the assembler emits bytes. Sets label values and relative-branch offsets.
- `O%`: output address — where bytes actually land when OPT bit 2 is set. Lets you build a ROM image at one address while it'll run at another.

After the closing `]`, `P%` points to the first free byte. Useful for chaining data after code:

```basic
   80 .strend
   90 ]
  100 $P% = "Hello, BBC!"
  110 P% = P% + LEN($P%) + 1
  120 [ OPT pass%
  130 ...
```

## Labels

Prefix with `.`:

```basic
.entry   LDX #0          \ defines BASIC variable entry = current P%
.loop    LDA data,X
         BNE loop        \ refers to label
```

After assembly, labels are normal BASIC variables — print them, pass them to `CALL`, use in expressions.

## EQU directives (Level 2)

```basic
.msg     EQUS "Hello"    \ 5 bytes
         EQUB 13         \ 1 byte (CR)
         EQUB 0          \ null terminator
.table   EQUW &1234      \ 2 bytes (little-endian)
         EQUD &89ABCDEF  \ 4 bytes (little-endian)
```

| Directive | Bytes | Operand |
|---|---|---|
| `EQUB v` | 1 | 8-bit value |
| `EQUW v` | 2 | 16-bit, LSB first |
| `EQUD v` | 4 | 32-bit, LSB first |
| `EQUS s` | `LEN(s)` | String (no auto-null) |

Level 1 (1981 BASIC) has no EQU — exit `]`, poke via `?P%`/`!P%`/`$P%`, re-enter `[`.

## BRK + error convention

```basic
.error   BRK
         EQUB &FF              \ error number
         EQUS "Bad thing"      \ message
         EQUB 0                \ null terminator
```

When BRK fires the OS reads the byte after BRK as error number, then bytes until null as message. See [[os/brk]].

## CALL / USR register passing

Before `CALL`:
- `A% AND &FF` → A on entry
- `X% AND &FF` → X
- `Y% AND &FF` → Y
- `C% AND 1` → C flag

`USR(addr)` returns `(C<<24) | (Y<<16) | (X<<8) | A`.

```basic
A% = 65 : X% = 0 : Y% = 0 : CALL print_char
result% = USR(my_routine)
PRINT "A=";result% AND &FF
PRINT "X=";(result% >> 8) AND &FF
```

## Two-pass dance — why FOR pass%

Forward references (`BNE somewhere_later`) aren't resolvable until the assembler has seen `.somewhere_later`. Pass 1 (`OPT 0`) emits placeholders silently; pass 2 (`OPT 3`) emits the right offsets and reports any genuinely-broken labels or out-of-range branches.

**Always reset `P%`** at the start of each pass — same starting address both passes, otherwise labels resolve to pass-1 values but bytes land at pass-2 addresses.

## Macros via FN / PROC

```basic
DEF FNsave_regs(opt%)
[ OPT opt% : STA save_a : STX save_x : STY save_y : ]
= opt%

; In main:
.entry  OPT FNsave_regs(opt%)
        JSR work
        OPT FNrestore_regs(opt%)
        RTS
```

The `= opt%` at the function end returns the OPT value through — so `OPT FNfoo(opt%)` works as both an OPT directive **and** a macro expansion.

## User zero page

`&70-&8F` (32 bytes) — always safe to use. See [[memory/zero-page]] for claim-more-zp patterns and the BASIC zp layout.

## Common pitfalls

- **OPT resets every block.** Each `[ ... ]` block enters at OPT=3. If you have two assembly blocks in one program, set OPT in each.
- **Missing colons in level 1.** `OPT 0 LDA #0 RTS` won't parse — needs colons or newlines.
- **Forward `LDA label`** with `label` < `&100` (zero page): assembler picks 3-byte absolute on pass 1 (label undefined), then 2-byte zp on pass 2. **All later labels shift by one byte** between passes → catastrophic. Fix: define zp variables (e.g. `count = &70`) before the assembly block.
- **DIM'd buffer too small** → pass-2 walks past end into BASIC variables → "No such variable". Allocate generously.
- **`OPT 7` remote assembly** is Level 2 only. Pre-1982 BASIC will error or ignore bit 2.

## BeebAsm

The community standard cross-assembler (Rich Talbot-Watkins, 2004 onwards) closely mirrors this syntax — almost all BBC BASIC inline assembly drops into BeebAsm with minor changes. The main additions BeebAsm provides:

- `ORG` / `SAVE` / `INCBIN` directives.
- No two-pass FOR loop needed (BeebAsm does multiple passes implicitly).
- Modern label syntax (`.label` still works; `label:` is also accepted in some modes).
- Conditional assembly via `IF`/`ENDIF`.
- Macros via `MACRO ... ENDMACRO`.
- `GUARD addr` to detect overflows past allocated regions.

Code written for BBC BASIC inline assembly usually ports to BeebAsm by:
1. Removing the `FOR pass% / NEXT pass%` loop.
2. Replacing `DIM code%` with `ORG code_addr`.
3. Adding `SAVE "FILE", start, end` at the bottom.

A dedicated [[tools/beebasm]] page is planned.

## See also

- [[sources/naug-ch02-basic-assembler]] — Full source page.
- [[memory/zero-page]] — Zero-page allocation.
- [[os/brk]] — BRK error message convention.
- [[hardware/6502-isa]] — Mnemonic / cycle reference.
- [[hardware/6502-addressing-modes]] — Mode mechanics.
