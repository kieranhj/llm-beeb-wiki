---
title: NAUG Ch2 — BASIC Assembler
type: source
parent: [[sources/naug]]
pages: 13-21
section: §2
tags: [basic-assembler, opt, equ, labels, macros, user-zero-page]
updated: 2026-05-13
---

# NAUG Ch2 — The BASIC Assembler

Holmes & Dickens, *The New Advanced User Guide*, pp.13-21. Reference for the **BBC BASIC inline assembler** — square-bracketed `[ ... ]` blocks inside BASIC programs that assemble to machine code. This is the assembler the wiki's code examples target (a near-superset of which is BeebAsm).

## BASIC version landscape

- **Level 1 BASIC** (1981): original Model B. No EQU{B,W,D,S}, no remote assembly (O%).
- **Level 2 BASIC** (1982+): adds EQU directives and remote assembly via `O%`. Default on later Model B, B+, Electron.
- **Level 4 / 40 BASIC** (Master 128 / Compact): essentially Level 2 + lowercase register/EQU names.

The wiki defaults to Level 2 conventions. If targeting unexpanded Model B with old BASIC, note Level-1 limitations (no EQU, no `O%`).

## Block delimiters

```basic
P% = code_addr
[
OPT pass
.label  LDA #&00
        STA &70
        RTS
]
```

Assembler statements live between `[` and `]`. Each statement: optional label (prefixed `.`), mnemonic, optional operand, optional comment after `\`. Statements separated by newlines or `:` (colon).

## OPT — pass / behaviour control

```basic
OPT n
```

Bits of `n`:

| Bit | Set means |
|---|---|
| 0 | Listing enabled (printed during assembly) |
| 1 | Errors enabled ("Branch out of range", "No such variable", etc.) |
| 2 | **Remote assembly** — code lands at `O%` while labels resolve from `P%`. Level 2 only. |

Common patterns:

- `OPT 0` — pass 1: silent, errors suppressed (so forward references that look "undefined" on pass 1 don't fault).
- `OPT 3` — pass 2: listing + errors. Pass 1 has populated all labels; pass 2 picks up genuine mistakes.
- `OPT 7` — pass 2 with remote assembly (e.g. assembling a paged-ROM image into RAM, will be blown to EPROM).

Standard two-pass idiom:

```basic
FOR pass% = 0 TO 3 STEP 3
  P% = code_addr           : REM source-of-label-values
  O% = build_addr          : REM where the bytes land (if OPT 7)
  [
  OPT pass%
  ; ... assembly ...
  ]
NEXT pass%
```

**Reset OPT in each new bracketed block** — every entry to the assembler reinitialises OPT to 3.

## P% (and O%) — location counter

- `P%`: 32-bit BASIC integer that the assembler increments as it emits bytes. Treated as the "where this code will run" address — used to compute label values and relative branch offsets.
- `O%`: 32-bit BASIC integer used when `OPT` bit 2 is set. Holds the address where bytes actually land (separate from where they'll execute).

Common mistake: code grows past the DIM'd buffer. Pass-2 assembly walks off the end into BASIC's variable storage, producing "No such variable" errors as labels suddenly mean nothing. Allocate generously or use `DIM code% size`.

After assembly, `P%` points to the first free byte after the assembled code. Useful for chaining data after code (e.g. embedded strings).

## Labels

Prefix a BASIC variable name with `.` to define a label at the current `P%`:

```basic
.entry  LDX #0
.loop   LDA data,X
        ...
        BNE loop
```

`.entry` creates a BASIC integer variable `entry` = `P%` at that point. The label is then usable as a normal BASIC variable (`CALL entry`, `PRINT ~entry` to dump address, etc.).

**Label names follow BASIC variable rules**: case-sensitive, can't shadow BASIC keywords, can end with `%` (integer) or `$` (string — pointless for code).

## Forward references — the two-pass dance

When the assembler encounters `BNE loop` before it's seen `.loop`, on pass 1 `loop` is "No such variable". With `OPT 0` (errors disabled), the assembler emits a placeholder (zero offset usually) and continues. Pass 2 (`OPT 3`) re-encounters with `loop` now defined and emits the correct offset.

Genuine out-of-range branches surface on pass 2 as "Branch out of range" — which is exactly the error you want.

## EQU directives (Level 2 only)

Reserve / initialise bytes within the code stream:

| Directive | Reserves | Operand |
|---|---|---|
| `EQUB val` | 1 byte | Numeric expression |
| `EQUW val` | 2 bytes (little-endian) | 16-bit value |
| `EQUD val` | 4 bytes (little-endian) | 32-bit value |
| `EQUS str` | `LEN(str)` bytes | String literal or `$`-variable |

Examples:

```basic
.msg    EQUS "Hello"     \ 5 bytes
        EQUB 13          \ CR terminator
        EQUB 0           \ extra zero
.table  EQUW &FFFE
        EQUW &FFFC
        EQUD &12345678
```

The assembler uses the **least significant** part if you EQUB a value > 255 (no warning). EQUS doesn't auto-null-terminate — add `EQUB 0` if you need it.

Level 1 workaround: drop out of the assembler with `]`, use BASIC's `?`, `!`, `$` operators to poke bytes/words/strings at `P%`, then re-enter `[`:

```basic
P% = entry          : [ OPT pass : ... : ]
$P% = "string"      : P% = P% + LEN($P%) + 1     : REM null-terminated
[ OPT pass : ... : ]
```

## BRK + error message convention

```basic
.error  BRK
        EQUB &FF        \ error number
        EQUS "Something went wrong"
        EQUB 0          \ null terminator
```

When BRK fires, MOS reads the byte after BRK as the error number and the following bytes as an error message (null-terminated). See `[[os/brk]]` for the full BRKV protocol.

## CALL and USR — entering code from BASIC

```basic
CALL entry              : REM jumps to entry, returns via RTS
                          REM also passes A%/X%/Y%/C% as register values
A% = 64 : X% = 0 : Y% = 0
CALL entry              : REM A=64, X=0, Y=0, C=0 on entry

result% = USR(entry)    : REM returns A/X/Y/C packed into a 32-bit value
```

On entry from CALL:
- A = `A% AND &FF`
- X = `X% AND &FF`
- Y = `Y% AND &FF`
- C = `C% AND 1`

`CALL` can also pass a parameter block at `&600` describing additional BASIC arguments (type-tagged). Less commonly used.

`USR` returns a 32-bit value composed of `(C<<24) | (Y<<16) | (X<<8) | A`. Inverse of the entry register pack.

## Conditional assembly + macros

Both are just BASIC. Wrap blocks of `[ ... ]` in BASIC IFs:

```basic
IF debug_enabled THEN [ OPT pass : LDA &70 : JSR print_byte : ]
```

Or use FN / PROC to define reusable macros that emit code:

```basic
DEF FNsave_regs(opt%)
[ OPT opt% : STA save_a : STX save_x : STY save_y : ]
= opt%

; in main assembly:
.entry  OPT FNsave_regs(opt%)
        ... routine ...
```

The trick: return `opt%` from the function so `OPT FNsave_regs(opt%)` lands the value of the OPT directive correctly while letting the function emit code as a side effect.

## User zero page

`&70-&8F` (32 bytes) reserved for user machine code — safe to use while BASIC is loaded. Touching `&00-&6F` (BASIC's zp workspace) requires understanding that BASIC won't survive after your code returns unless you preserve it. See `[[memory/zero-page]]` for the wider story.

## Filed into

- `[[tools/basic-assembler]]` — Cheatsheet for OPT / P% / labels / EQU / two-pass idiom / FN-macro pattern.
- Updates: `[[os/brk]]` — BRK error message convention cross-link confirmed.
- Updates: `[[memory/zero-page]]` — user zp `&70-&8F` already documented; cross-link confirmed.

## Open follow-ups

- **BeebAsm dialect** — modern cross-assembler that closely mirrors this syntax. Worth its own page under `[[tools/beebasm]]` (planned) covering the diffs: directives that don't exist in BBC BASIC (`SAVE`, `INCBIN`, `ORG`, `GUARD`), modern bracket-free syntax, no two-pass FOR-loop boilerplate.
- **CALL parameter block at `&600`** — documented at the headline level; if BASIC ↔ assembler parameter passing matters, expand from User Guide reference.
