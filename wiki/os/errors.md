---
title: Error Messages and Error Numbers
type: os
tags: [errors, brk, error-codes, error-number, mos, basic]
sources: [bbc-user-guide]
updated: 2026-05-16
---

# Error Messages and Error Numbers

Every error reported on a BBC machine has an **error number** (1-byte value in `&FD`) and an **error message** (null-terminated string immediately after the BRK opcode that raised it). The error structure is documented in [[os/brk]].

`ERR` in BASIC returns the error number. `REPORT` in BASIC prints the error message. The MOS error-string lookup is by convention only — a paged-ROM can raise any error number with any message, and many do.

## BASIC error numbers (0-44)

These are the canonical Acorn BBC BASIC IV errors as shipped on every BBC machine. Per [[sources/bbc-user-guide]] Ch 46:

| Num | Hex | Message | Cause |
|---|---|---|---|
| 0 | `&00` | `No room` | Untrappable — all memory used |
| 1 | `&01` | `Out of range` | Branch out of range in assembler |
| 2 | `&02` | `Byte` | Assembler immediate operand > 255 (e.g. `LDA #345`) |
| 3 | `&03` | `Index` | Bad assembler index mode |
| 4 | `&04` | `Mistake` | Generic "couldn't make sense of input" |
| 5 | `&05` | `Missing ,` | Expected comma |
| 6 | `&06` | `Type mismatch` | Number expected, string offered (or vice-versa) |
| 7 | `&07` | `No FN` | `=FNname` outside function body |
| 8 | `&08` | `$ range` | Attempt to use `$` indirection at zero page |
| 9 | `&09` | `Missing "` | Unterminated string |
| 10 | `&0A` | `Bad DIM` | `DIM A(-3)` etc. |
| 11 | `&0B` | `DIM space` | Insufficient memory for array |
| 12 | `&0C` | `Not LOCAL` | `LOCAL` outside procedure/function |
| 13 | `&0D` | `No PROC` | `ENDPROC` without `DEF PROC` |
| 14 | `&0E` | `Array` | Reference to undeclared array |
| 15 | `&0F` | `Subscript` | Array index out of bounds |
| 16 | `&10` | `Syntax error` | Mis-terminated command |
| 17 | `&11` | `Escape` | ESCAPE key pressed |
| 18 | `&12` | `Division by zero` | `34/0` etc. |
| 19 | `&13` | `String too long` | >255 chars |
| 20 | `&14` | `Too big` | Numeric overflow |
| 21 | `&15` | `-ve root` | `SQR(-x)`, `ASN(>1)`, `ACS(>1)` |
| 22 | `&16` | `Log range` | `LOG(<=0)` |
| 23 | `&17` | `Accuracy lost` | Trig of very large angle (e.g. `SIN(1E7)`) |
| 24 | `&18` | `Exp range` | `EXP(>88)` |
| 25 | `&19` | `Bad MODE` | Mode change inside PROC/FN or insufficient memory |
| 26 | `&1A` | `No such variable` | Variable used before assignment |
| 27 | `&1B` | `Missing )` | Unbalanced bracket |
| 28 | `&1C` | `Bad hex` | `&y` etc. (invalid hex digit) |
| 29 | `&1D` | `No such FN/PROC` | Undefined FN/PROC call |
| 30 | `&1E` | `Bad call` | PROC/FN called incorrectly |
| 31 | `&1F` | `Arguments` | Wrong number of args |
| 32 | `&20` | `No FOR` | `NEXT` without `FOR` |
| 33 | `&21` | `Can't match FOR` | `NEXT` doesn't match `FOR` variable |
| 34 | `&22` | `FOR variable` | Non-numeric `FOR` variable |
| 35 | `&23` | `Too many FORs` | Nesting >10 |
| 36 | `&24` | `No TO` | `FOR X=1` (missing `TO`) |
| 37 | `&25` | `Too many GOSUBs` | Nesting >26 |
| 38 | `&26` | `No GOSUB` | `RETURN` without `GOSUB` |
| 39 | `&27` | `ON syntax` | Malformed `ON … GOTO/GOSUB` |
| 40 | `&28` | `ON range` | Control var <1 or >list length |
| 41 | `&29` | `No such line` | `GOTO`/`GOSUB` to non-existent line |
| 42 | `&2A` | `Out of DATA` | More `READ`s than `DATA` |
| 43 | `&2B` | `No REPEAT` | `UNTIL` without `REPEAT` |
| 44 | `&2C` | `Too many REPEATs` | Nesting >20 |

Untrappable errors (`No room`, `Bad program`, `LINE space`, `Silly`, `Failed at N`, etc.) have no number — they exit to the BASIC prompt directly and can't be caught by `ON ERROR`.

## Cassette/CFS filing-system errors (216-223)

Raised by the cassette filing system when reading from tape:

| Num | Message | Cause |
|---|---|---|
| 216 | `Data?` | CRC error in file body — rewind, replay |
| 217 | `Header?` | CRC error in file header — rewind, replay |
| 218 | `Block?` | Unexpected block number — rewind, replay |
| 219 | `File?` | Unexpected filename in header |
| 220 | `Syntax` | Bad `*OPT` or similar |
| 222 | `Channel` | Use of unopened channel |
| 223 | `Eof` | End of file reached |

## MOS / sideways-ROM errors (250+)

Defined by the MOS / paged-ROM dispatch layer:

| Num | Message | Where raised |
|---|---|---|
| 251 | `Bad key` | `*KEY` syntax error |
| 253 | `Bad string` | `*` command string parse error |
| 254 | `Bad command` | No paged ROM recognised the `*` command |

## DFS / ADFS / NFS errors (varies)

Filing-system specific. Each filing-system ROM defines its own. Some common ones:

| Num | Message | Typical FS |
|---|---|---|
| 198 | `Disc fault` | DFS / ADFS |
| 199 | `Disc full` | DFS / ADFS |
| 200 | `Disc changed` | DFS / ADFS |
| 201 | `File locked` | DFS / ADFS |
| 202 | `Not open` | DFS / ADFS / NFS |
| 203 | `Not enabled` | DFS / NFS |
| 204 | `Bad name` | DFS / ADFS / NFS |
| 205 | `Bad drive` | DFS / ADFS |
| 206 | `Bad directory` | DFS / ADFS |
| 207 | `Bad attribute` | DFS / ADFS |
| 208 | `File exists` | DFS / ADFS |
| 209 | `Drive fault` | DFS / ADFS |
| 210 | `Disc read only` | DFS / ADFS |
| 211 | `Not found` | DFS / ADFS / NFS |
| 212 | `Channel` | DFS / ADFS |
| 213 | `End of file` | DFS / ADFS |
| 214 | `File not found` | DFS / ADFS / NFS |

These are not authoritative; cross-check against `*HELP` output from the active filing system on real hardware for the exact range. Each filing system has its own error-number convention; conflicts exist between e.g. DFS 200 and NFS 200.

## Raising errors from user code

Use the BRK + structure pattern (per [[os/brk]]):

```asm
BRK              ; trigger MOS error handler
EQUB error_num   ; error number
EQUS "Message"   ; null-terminated error string
EQUB 0
```

The MOS sets up `&FD` (pointer to message), `&FE` (return PC after BRK), `&F0` (saved SP), then calls `BRKV` (`&202`). Default BRKV in BASIC prints the message and exits to prompt.

To intercept an error from your own code, hook `BRKV` before the operation that might fail:

```asm
LDA #<my_handler  : STA &202
LDA #>my_handler  : STA &203
; ... do potentially-failing work ...
```

Restore `&202/&203` to the old values before returning. The standard pattern is to save them on entry and restore on RTS.

## Compatibility notes

- Error numbers 1-44 are **stable across BBC BASIC I, II, III, IV** (Model B → Master Compact).
- Error number 0 (`No room`) is documented as untrappable on Model B per [[sources/bbc-user-guide]] Ch 46 ("untrappable error"); behaviour on newer BASIC versions is undocumented in primary sources I've ingested — assume untrappable unless you can verify otherwise on the target machine.
- Cassette errors 216-223 only fire on machines that have CFS available (Master 128 has CFS as a ROM image; Master Compact has no CFS at all).
- DFS / ADFS / NFS errors are **per-ROM** — what error 200 means depends on which filing system is active.
- The `Silly` and `Failed at N` errors (from `RENUMBER`, `AUTO`) have no numbers and are never `ERR`-readable.

## See also

- [[os/brk]] — BRK structure, BRKV protocol, ROM-raising-errors pattern.
- [[os/calls]] — OSCLI / OSFILE / OSBYTE error-return conventions.
- [[sources/bbc-user-guide]] — Ch 46 (canonical BASIC error list).
- [[memory/zero-page]] — `&FD`/`&FE` (error pointer), `&F0` (saved SP).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
