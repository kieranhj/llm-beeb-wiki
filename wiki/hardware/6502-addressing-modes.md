---
title: 6502 / 65C12 Addressing Modes
type: hardware
tags: [6502, 65c12, addressing-modes]
sources: [naug-ch03-04-arithmetic-addressing]
updated: 2026-05-13
---

# Addressing Modes

The 6502's small instruction set is leveraged by many addressing modes. Mode choice is the dominant factor in instruction cost: same operation, different modes vary 2-7 cycles. See [[hardware/6502-isa]] for the full per-mnemonic table.

## Modes

### Implicit (1 byte, no operand)

The instruction is its own operand. `RTS`, `NOP`, `TAX`, `INX`, etc.

### Accumulator (1 byte)

A is the target. `ASL A`, `LSR A`, `ROL A`, `ROR A`; 65C12 adds `INC A` / `DEC A` (aliases `INA` / `DEA`).

### Immediate (2 bytes) — `#value`

Constant embedded in the instruction stream. Cheapest "load":

```asm
LDA #&FF        ; 2c
LDX #count      ; assembler-time constant
```

### Absolute (3 bytes) — `addr`

Full 16-bit address. Default mode for the assembler when given a value ≥ `&100`.

```asm
LDA &3000       ; 4c
STA &FE21       ; direct hardware write
```

### Zero page (2 bytes) — `addr` where addr < `&100`

8-bit address, restricted to page 0. **1 cycle faster than absolute** because the high byte of the address is implicitly 0:

| Op | abs | zp | Saving |
|---|---|---|---|
| LDA | 4c | 3c | 1c |
| STA | 4c | 3c | 1c |
| ASL | 6c | 5c | 1c |
| INC | 6c | 5c | 1c |

Hot-loop variables, pointers, and counters belong in zero page. **MOS owns most of zp**; the user zero-page block is `&70-&8F` (NAUG §2.10 — pending Ch2 ingest). 65C12 (Master) also has more bytes available via the `(zp)` mode that frees X/Y from pointer duty.

The assembler picks zp automatically if the address is < `&100` and the operand is resolved on the first pass. If you forward-reference a zp variable, the assembler uses 16-bit absolute on pass 1 and emits a different opcode on pass 2 — silently corrupting all later labels. **Define zp variables before the assembly block** to avoid this trap (NAUG §4.8 p23).

### Indirect — `(addr)` (3 bytes, JMP only on NMOS)

The 16-bit operand points to a 2-byte pointer in memory. CPU loads the pointer and jumps there.

```asm
LDA #lo : STA &1900
LDA #hi : STA &1901
JMP (&1900)     ; goto address stored at &1900/&1901
                ; 5c on NMOS, 6c on 65C12
```

**NMOS bug**: if the low byte of `addr` is `&FF`, the high byte of the pointer is fetched from `addr & &FF00` instead of `addr+1`. So `JMP (&19FF)` reads LSB from `&19FF` and MSB from **`&1900`**, not `&1A00`. **Fixed on 65C12** (Master) — at the cost of +1c.

Avoidance: align jump-table pointers so they never end on `&FF`.

### Absolute,X / Absolute,Y (3 bytes) — `addr,X` or `addr,Y`

Effective address = 16-bit operand + X (or Y). X, Y are unsigned (0-255), so the offset is forward-only.

```asm
LDA &3000,X     ; 4c (+1 if (&3000 + X) crosses a page)
STA &7C00,Y     ; 5c always — stores pay the worst case
```

**Page-crossing penalty (+1c)** on loads. Hot loops that touch a 256-byte-aligned table avoid the penalty entirely.

### Zero page,X (2 bytes) — `zp,X`

Same as Absolute,X but address wraps within page 0:

```asm
LDA &80,X       ; 4c — A = mem[(&80 + X) AND &FF]
                ;     if X=&80, the access wraps to &00
```

Cheaper than `abs,X` (saves 1c, 1 byte). Use when the table fits in zero page.

`LDX` and `STX` use `zp,Y` instead of `zp,X` (the only instructions to do so).

### (Indirect,X) — `(zp,X)` — pre-indexed (2 bytes)

```asm
LDA (&60,X)     ; 6c
; addr_lsb = mem[(&60+X) AND &FF]
; addr_msb = mem[(&60+X+1) AND &FF]
; A = mem[addr]
```

Use case: jump table of pointers in zero page, indexed by X. Less common than `(zp),Y` because X is often busier.

### (Indirect),Y — `(zp),Y` — post-indexed (2 bytes)

```asm
LDA (&80),Y     ; 5c (+1 if page crossed)
; addr = mem[&80] | (mem[&81] << 8)
; A = mem[addr + Y]
```

**The workhorse of 6502 indirect addressing.** A pointer in zero page + Y offset = walk through an array of any length:

```asm
LDY #0
.loop
    LDA (src),Y
    STA (dst),Y
    INY
    BNE loop        ; copies up to 256 bytes
```

For arrays > 256 bytes, increment the high byte of the pointer and reset Y:

```asm
.next_page
    INC src+1
    INC dst+1
    DEX                 ; pages remaining
    BNE loop
```

### Relative (2 bytes) — `BNE label`

Conditional branches only. Signed 8-bit offset, range **-128..+127 from the byte after the branch instruction**.

Cycles: **2c base, +1c if taken, +2c if branching across a page**. So:
- Not taken: 2c
- Taken, same page: 3c
- Taken, new page: 4c

For tight inner loops, lay out so the **common path is the fall-through** (not taken).

Out-of-range error: invert the test and use JMP:

```asm
; Want: BNE far_label  (out of range)
    BEQ skip
    JMP far_label
.skip
```

### (Indirect) — `(zp)` — 65C12 only (2 bytes)

```asm
LDA (&80)       ; 5c
; addr = mem[&80] | (mem[&81] << 8)
; A = mem[addr]
```

Equivalent to `(zp),Y` with Y=0, but doesn't tie up Y. Big win when both X and Y are busy. Available for: ADC, AND, CMP, EOR, LDA, ORA, SBC, STA.

### (Absolute,X) — 65C12 only, JMP only (3 bytes)

```asm
JMP (&FE00,X)   ; 6c
; PC = mem[&FE00+X] | (mem[&FE00+X+1] << 8)
```

Pre-indexed indirect jump — pick from a table of 16-bit code pointers. The classic 65C12 jump-table idiom:

```asm
; X = subroutine index * 2
JMP (jump_table,X)
.jump_table
    EQUW sub0
    EQUW sub1
    EQUW sub2
    ...
```

Plus the inline-RTS trick to return: push (return_addr - 1) onto the stack before the indirect JMP, then the called routine's RTS returns to caller.

## Mode cost summary

For a load (LDA, AND, etc.) — pick by what's available:

| Mode | Bytes | Cycles | Use when |
|---|---|---|---|
| immediate | 2 | 2 | Value is known at assembly time |
| zp | 2 | 3 | Value lives in zp |
| zp,X / zp,Y | 2 | 4 | Indexed table in zp |
| `(zp)` (65C12) | 2 | 5 | Pointer in zp, no Y/X available |
| abs | 3 | 4 | Single named global |
| abs,X / abs,Y | 3 | 4 (+1p) | Indexed table > 256 bytes |
| `(zp,X)` | 2 | 6 | Jump table / pointer table in zp, X busy |
| `(zp),Y` | 2 | 5 (+1p) | Walk through any-size array |

Choose the cheapest mode that fits. The cycle differences compound fast in inner loops — converting a `LDA abs` (4c) to `LDA zp` (3c) and `LDA (zp),Y` (5c) to `(zp)` (5c, frees Y) saves measurable time across 10k iterations.

## Page-crossing penalty — what counts

For `abs,X`, `abs,Y`, and `(zp),Y`: if `(base & &FF00) != ((base + index) & &FF00)`, the chip needs an extra cycle to refetch the high byte. The penalty applies to:

- Loads: `LDA`, `LDX`, `LDY`, `ADC`, `SBC`, `AND`, `EOR`, `ORA`, `CMP`, `BIT`
- **Stores do not have the penalty** — they always take the worst-case cycle count (which is why the cycle counts in [[hardware/6502-isa]] for STA `abs,X` are 5c not "4c +1p").

To eliminate the penalty in hot loops:
- Align the table base to a page boundary (`&3000`, `&5800`, etc.).
- Or split the loop into a low-page and high-page half so the index never crosses.

See [[hardware/6502-isa]] for the full cycle table.
