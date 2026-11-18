---
title: Zero Page
type: memory
tags: [zero-page, workspace, mos]
sources: [naug-ch06-os-introduction, naug-ch13-video, allmem-ripley-harston, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
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

From [[sources/naug-ch13-video]] §13.2:

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

(VDU character-cell *addresses* live in page 3, not zero page — see [[memory/os-workspace]] for `&034A-&034B` (text cursor 6845 address) and the graphics workspace at `&0330-&0349`.)

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

**Measured refinements** ([[sources/beeb-port-kit-hardware-facts-2026-11]] §6, after hexwab on paradroid-beeb #18):

| Range | Yours when | Note |
|---|---|---|
| `&A0-&A7` (NMI owner) | after `OSBYTE 140` has given you the NMI | measured unwritten by anything else through a whole game (1942, 2026-10-11, jsbeeb Master); 1942's and the kit's 1770 driver keep the NMI routine's saved A at `&A0` — but phX moved its A to the stack because a nested NMI overwrote it there (see [[hardware/wd1770]]) |
| `&A8-&AF` (MOS scratch) | after `OSBYTE 140`, **and only while you make no OS call** | not the filing system's, so 140 is not the whole story: an OS call may use it |
| `&B0-&CF` (filing system) | **after `OSBYTE 140`, and not before** — "turning off the filing system" means letting it detach | Paradroid used it without the call and ran only because Acorn's DFS did not mind; an Opus DDOS 3.45 hung (hexwab, real hardware) |
| `&BC`/`&BD` | measured free in play under a MOS that still runs (Stryker's Run, Master, watches over every phase) | a watch sees a zp read's address but not its value: check the source for indexed accesses |

**A program that owns everything can have almost all of it.** phX, after `*FX 140` with its own IRQ and NMI, played on KC's real Master, uses the whole zero page except `&A0` (its 1770 NMI's), `&F4` (ROMSHAD, written with ROMSEL every time) and `&FC` (the IRQ's saved A) — the MOS's `&E0-&FF` included (`phX/docs/memory-map.md`). That contradicts nothing below: "Don't bother with `&EF-&FF`" is for code that still calls the OS.

**Under an auto-allocator, an interrupt and the main loop must not share a routine.** Baron assumes code reachable from a `ZA_INTERRUPT` handler runs only inside it and may pack that handler's variables onto the routine's; Square Roots' music interrupt variables landed on a span routine's, and the first full run failed at record 207 (2026-11-08; kit gotchas class 3). And while a build must stay byte-identical, pin the zero page: removing one variable lets the allocator repack the rest (Isometrikum crunch rounds 1-3).

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

- [[hardware/6502-addressing-modes]] — Why zp is cheaper than abs.
- [[memory/memory-map]] — Where zp sits in the wider map.
- [[memory/os-workspace]] — Page 1 / 2 / 3 follow-on.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
