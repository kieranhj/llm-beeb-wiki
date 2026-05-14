---
title: Zero Page
type: memory
tags: [zero-page, workspace, mos]
sources: [naug-ch06-os-introduction, naug-ch13-video, allmem-ripley-harston]
updated: 2026-05-14
---

# Zero Page

The most valuable 256 bytes on the BBC. Zero-page addressing modes (zp, `zp,X`, `(zp,X)`, `(zp),Y`, 65C12 `(zp)`) are 1c-2c faster than absolute equivalents and 1 byte shorter. The right zero-page layout is the foundation of every fast loop.

## Allocation (Model B / B+ / Master, BASIC-loaded)

| Range | Owner | Use |
|---|---|---|
| `&00-&6F` | BASIC (or current language) | Language workspace — **off limits while a language is loaded** |
| **`&70-&8F`** | **USER** | 32 bytes free for user code. Safe to use from machine code called via `CALL` from BASIC. |
| `&90-&9F` | Econet | Network station, FS station, etc. |
| `&A0-&A7` | NMI | Network/disc filing-system NMI work |
| `&A8-&AF` | OS | OS temporary scratch |
| `&B0-&BF` | FS | Filing-system temporary scratch |
| `&C0-&CF` | FS | Filing-system workspace (current handle, etc.) |
| `&D0-&E1` | VDU | Per-cell pointers, masks (see VDU table below) |
| `&E2-`onwards | OS | CFS/RFS state, key buffer pointers, OSBYTE/OSWORD save, IRQ A-save |

## VDU-driver zero page (`&D0-&E1`)

From `[[sources/naug-ch13-video]]` §13.2:

| Addr | Use |
|---|---|
| `&D0` | STATS — VDU status byte (= OSBYTE `&75`) |
| `&D1` | ZMASK — current graphics-point bit mask |
| `&D2` | ZORA — text colour OR mask |
| `&D3` | ZEOR — text colour EOR mask |
| `&D4` | Graphics colour OR mask |
| `&D5` | Graphics colour EOR mask |
| `&D6`-`&D7` | Graphics character cell |
| `&D8`-`&D9` | Top scan line |
| `&DA`-`&DF` | Temporary workspace |
| `&E0`-`&E1` | BBC/Electron: Row multiplication tables ptr. Master: General workspace. |

(VDU character-cell *addresses* live in page 3, not zero page — see `[[memory/os-workspace]]` for `&034A-&034B` (text cursor 6845 address) and the graphics workspace at `&0330-&0349`.)

Touching these while the VDU driver is active = visible corruption.

## Critical OS locations

| Addr | Use |
|---|---|
| `&E7` | Auto-repeat countdown |
| `&EA` | Serial timeout counter |
| `&EC` | Last key press (internal key number) |
| `&ED` | Penultimate key press |
| `&EE` | 1 MHz bus paging-register RAM copy + internal-key-number to ignore (OSBYTE `&79`) |
| `&EF` | OSBYTE/OSWORD A value (during call) |
| `&F0` | OSBYTE/OSWORD X value |
| `&F1` | OSBYTE/OSWORD Y value |
| `&F2`-`&F3` | GSINIT/GSREAD string pointer |
| `&F4` | Copy of ROM select register (paging) |
| `&F5` | Speech PHROM / RFS ROM number |
| `&F6`-`&F7` | OSRDSC address |
| `&F8`-`&F9` | Master only: soft key expansion pointer (BBC/Electron unused) |
| `&FA`-`&FB` | General OS workspace, used by buffer access during interrupts |
| `&FC` | **A save during IRQ** |
| `&FD`-`&FE` | Error message pointer — initialised to language version string; after BRK, points at the error text following the BRK opcode |
| `&FF` | ESCAPE flag (bit 7 only) |

## Performance: claim more than `&70-&8F`

The 32-byte user block is rarely enough for serious work. Strategies for extending:

### Take over BASIC's zero page

If your code is the entire foreground (no `CALL` back to BASIC), all of `&00-&8F` is yours. Save the relevant bytes at the entry of your routine, restore at exit. This buys 144 bytes of zp. **Strict rule**: don't call OS routines that BASIC has hooked unless you've restored the relevant state.

### Take over filing-system / VDU zp regions

If you've turned off the filing system (e.g. by setting up your own NMI handler and managing the disc directly) you can reclaim `&B0-&CF`. If you're running your own video driver (direct screen writes), the VDU workspace at `&D0-&E1` is free.

The trade-off: **the more MOS state you displace, the more state you must restore on exit**. For code that runs to completion and resets the machine (games, demos), restoration is trivial — just `BRK` or `JMP &E00` (RESET). For code that returns to BASIC, you must save and restore.

### Don't bother with `&EF`-`&FF`

These are used during every IRQ, OSBYTE, OSWORD, BRK. Even with interrupts disabled, the first OS call after re-enabling them will trash this region. Leave it alone unless you're running entirely without MOS.

## A zp-save preamble

For code that returns to BASIC and uses zp `&00-&8F`:

```asm
.entry
    LDX #&8F
.save_loop
    LDA &00,X
    STA zp_save_block,X
    DEX
    BPL save_loop
    ; ... use any of &00-&8F freely ...
.exit
    LDX #&8F
.restore_loop
    LDA zp_save_block,X
    STA &00,X
    DEX
    BPL restore_loop
    RTS

.zp_save_block SKIP &90
```

144 bytes of save + 144 of restore = ~1500 cycles, paid once per routine entry/exit. Worth it for inner loops that benefit from zp pointers.

## 65C12 (Master): the `(zp)` mode is free zp

The 65C12 `(zp)` addressing mode (LDA/STA/etc. with no index register) means **you don't need X or Y to use a zp pointer**. This is a major efficiency win on Master:

```asm
; NMOS (and Master): walking a pointer requires Y
LDY #0
LDA (ptr),Y
INY
LDA (ptr),Y
...

; 65C12 only: walk by manually incrementing the pointer, no Y needed
LDA (ptr)
INC ptr
BNE skip : INC ptr+1
.skip
LDA (ptr)
...
```

Costs more cycles per increment (5c vs INY's 2c) but frees Y entirely — a huge win when Y is needed for the inner address-arithmetic.

## See also

- `[[hardware/6502-addressing-modes]]` — Why zp is cheaper than abs.
- `[[memory/memory-map]]` — Where zp sits in the wider map.
- `[[memory/os-workspace]]` — Page 1 / 2 / 3 follow-on.
