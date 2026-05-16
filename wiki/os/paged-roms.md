---
title: Paged ROMs — Software System
type: os
tags: [paged-rom, rom-header, language-rom, service-rom, sideways-rom]
sources: [naug-ch17-paged-roms]
updated: 2026-05-13
---

# Paged ROMs — Software System

How code in the `&8000-&BFFF` window participates in the MOS. For the **hardware** side (paging register `&FE30`, sideways RAM testing, ANDY, why never write `&FE30` directly) see [[memory/paged-rom]]. This page is about the **software contract**.

## Header format

Every paged ROM starts with this layout (NAUG §17.1 p284):

```
offset  bytes  field
  0       3    JMP <language_entry>   ; or 00 00 00 if not a language
  3       3    JMP <service_entry>
  6       1    ROM type byte
  7       1    copyright string offset
  8       1    binary version number (0-255)
  9      [t]   title string
  9+t     1    00
 10+t    [v]   version string ("1.00")
 10+t+v  1    00
 11+t+v  [c]   copyright string — MUST start "(C)" (&28 &43 &29)
 11+t+v+c 1   00
 12+t+v+c 4   Tube relocation address
 ...           code and data
```

MOS uses the **copyright string starting at offset 7's address** to detect that a slot contains a ROM (not random RAM noise). The "(C)" sequence is essential.

## ROM type byte (offset 6)

```
bit 7: has service entry         (almost always set)
bit 6: is a language             (init on reset; Master strict about this)
bit 5: has Tube relocation       (relocated when copied to 2nd processor)
bit 4: (Electron) firm-key expansion
bits 3-0: processor type
        0 = 6502 BASIC
        1 = 6502 Turbo
        2 = 6502 code (non-BASIC)
        3 = 6800
        8 = Z80
        9 = 32016
        &B = 80186
        &C = 80286
        &D = ARM
```

Typical values:
- **Language ROM** (BASIC-like): `&C2` (lang + service + 6502)
- **Service-only ROM** (DFS, utility): `&82` (service + 6502)
- **BASIC**: `&40` (language but **no** service — the historical anomaly)

## Language vs service ROMs

| | Language | Service |
|---|---|---|
| Entry | JMP at offset 0 | JMP at offset 3 |
| Called on | Reset (highest-priority lang), `*<name>` after service call &04 | Every service-call event |
| Owns | User RAM `OSHWM..HIMEM`, `&400-&7FF`, zp `&00-&8F` | Nothing; allocated workspace via service call &01/&02 |
| Reset behaviour | Re-entered on soft reset (still selected) | Re-initialised via service call &03 (auto-boot) |
| On Tube | Code copied to second processor; service code is **not** | Always runs in I/O processor |

Most ROMs are both. The header just specifies both entries — `JMP language_entry` at offset 0 and `JMP service_entry` at offset 3 — and the service entry handles whatever service calls the ROM cares about.

## Language ROM entry

When MOS enters a language ROM at offset 0:

- `A` = `&01` always.
- `C` (carry) = 0 if entered from reset (BREAK), 1 otherwise.
- Use `OSBYTE &FD` to read last-BREAK type (0=soft, 1=power-on, 2=hard).
- **Stack pointer is undefined** — reinitialise with `LDX #&FF : TXS`.
- Zero page `&00-&8F` is the language's private zone.
- `&400-&7FF` is the language's private workspace.
- HIMEM defaults to the bottom of screen RAM (or `&8000` in shadow modes).

There is **no return** from the language entry — it's a `JMP` to the language's main loop. To "exit" a language, the user runs another `*<name>` command which generates a service call &04 elsewhere, after which MOS does a soft reset and re-enters the new language.

## Service ROM entry

When MOS calls the service entry at offset 3:

- `A` = reason code (see [[os/service-calls]]).
- `X` = this ROM's slot number (0-15).
- `Y` = call-specific parameter.

The service routine must:

1. Check `A` against the reason codes it handles.
2. If claiming: do the work, **set `A=0`**, restore X/Y, `RTS`.
3. If not claiming: leave `A`, `X`, `Y` unchanged, `RTS`.

MOS scans ROMs in **descending priority** (slot 15 first, slot 0 last). First claim wins.

## Workspace claim during reset

The first service calls a ROM sees, in order:

1. **`A=&01` absolute workspace claim**. Y = current top page (starts at `&E`). Increment Y by the number of pages of *fixed-position* workspace this ROM wants (the workspace is at `&E00 + sum_of_previous_claims`).
2. **`A=&02` relative private workspace claim**. Y = top page after all absolute claims. Each ROM stores its allocated workspace base at `&DF0 + slot_num` and increments Y by pages claimed.
3. **`A=&03` auto-boot**. Y = 0 means "this is auto-boot — boot if you're a filing system" — Y > 0 means "just initialise yourself". Highest-priority FS responds to Y=0 and loads `!BOOT`.

Pages 0-2, 5, 6, 7 of service-call ROMs use `&DF0` private-workspace pointers; the actual pages are allocated dynamically from `&E00` upwards.

## Calling code in another ROM

Three mechanisms (NAUG §17.4.3):

### 1. `OSRDRM` (`&FFB9`) — read a byte

```asm
LDA #lo : STA &F6
LDA #hi : STA &F7
LDY #rom_num
JSR &FFB9
; A = byte read
```

Cheap dispatch; the MOS handles paging. Not available across Tube.

### 2. Issue a paged-ROM service call via `OSBYTE &8F`

```asm
LDA #&8F
LDX #reason       ; service call reason code
LDY #y_param
JSR &FFF4
```

MOS scans the ROMs as usual. Some other ROM responds. Useful for: "any ROM, please claim NMI" (`reason=&0C`), "anyone want to do something with this *command" (`reason=&04`), etc.

### 3. Extended vectors — pre-arrange a permanent intercept

Point an OS vector (e.g. WRCHV `&20E`) at the OS's per-vector stub at `&FF00+vector_num*3`. The stub reads a 3-byte entry from the extended-vector table (`OSBYTE &A8/&A9` returns the base address) and pages in the named ROM before transferring control.

```
extended vector entry (3 bytes):
  +0  target address LSB
  +1  target address MSB
  +2  ROM number
```

To install:

```asm
; intercept vector number N (= (vec_addr - &200) / 2)
SEI
LDA #&A8 : LDX #0 : LDY #&FF : JSR &FFF4    ; X = extvec lo
STX zp_extvec
LDA #&A9 : LDX #0 : LDY #&FF : JSR &FFF4    ; X = extvec hi
STX zp_extvec+1
; write 3-byte entry at (zp_extvec) + 3*N
LDY #(3*N)
LDA #target_lo : STA (zp_extvec),Y
INY
LDA #target_hi : STA (zp_extvec),Y
INY
LDA my_rom_num : STA (zp_extvec),Y
; save old OS vector for chain
LDA &200+(2*N) : STA old_vec
LDA &201+(2*N) : STA old_vec+1
; point OS vector at &FF00 + 3*N
LDA #(&FF00 + 3*N) AND &FF : STA &200+(2*N)
LDA #(&FF00 + 3*N) DIV 256 : STA &201+(2*N)
CLI
```

After this, every call through the OS vector pages in your ROM and transfers to your handler. To chain to the previous handler, use the saved `old_vec` (which is normally an OS routine, not necessarily another ROM).

After hooking a vector, **issue service call `&0F`** to notify other ROMs that vectors have changed.

## Installing your own ROM into sideways RAM

On B+ / Master (and sideways-RAM-equipped Model B):

1. Build the ROM image (header + service entry + body) as a 16 KB binary.
2. `*LOAD <file> 8000` or `*SRLOAD <file> 8000 <slot>` (B+/Master *FX 67 etc.).
3. `OSBYTE &A4` (X+Y = `&8000`) to verify it's a valid 6502 ROM.
4. To make it the language: `OSBYTE &8E` (X = slot).

Sideways RAM persists across soft reset (BREAK) but is lost on power-off. *FX 142 (`OSBYTE &8E`) selection of a RAM-loaded language is also **not retained** across hard reset.

## See also

- [[os/service-calls]] — Full service-call reason-code table.
- [[memory/paged-rom]] — Hardware paging mechanics, `&FE30`, sideways RAM testing.
- [[os/calls]] — OS entry points and vectors.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
