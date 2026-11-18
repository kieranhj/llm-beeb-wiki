---
title: Paged ROM / Sideways RAM
type: memory
tags: [paged-rom, sideways-rom, sideways-ram, andy]
sources: [naug-ch12-memory, beebwiki-andy, master-arm, master-rm, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# Paged ROM / Sideways RAM

The 16 KB window at `&8000-&BFFF` is **paged** — at any moment it holds one of 16 possible banks ("sideways ROMs" or "sideways RAMs"). The active bank is chosen by the **ROM paging register** at SHEILA `&FE30`.

## The paging register (`&FE30`)

```
bit:   7    6    5    4    3    2    1    0
       RAM  -    -    -    PR3  PR2  PR1  PR0
```

- **Bits 0-3 (PR0-PR3)**: ROM/RAM bank number (0-15).
- **Bit 7 (RAM select)**:
  - **Master**: when set, swaps in 4 KB of private RAM ("**ANDY**") at `&8000-&8FFF` — MOS uses this during graphics ops.
  - **B+**: when set, swaps in 12 KB of paged RAM at `&8000-&AFFF`. Can hold ROM images (loadable as the current language with `*FX 142,128`, but not retained across BREAK).
  - **Model B / Electron**: bit 7 is unused.

The Master ARM ([[sources/master-arm]] Ch 3) explicitly notes bits 4-6 of ROMSEL are reserved (always 0) — don't write them.

## Master ROM organisation (matrix-decoded)

Per [[sources/master-arm]] Ch 3 page 32, the Master's 16 ROM slots are *not* sixteen independent sockets. They are matrix-decoded:

- **Slots 4-7** are paired into two 32 KB ROM positions on the board. The least significant bit of ROMSEL picks the upper vs lower 16 KB of each 32 KB ROM. (So slots 4+5 share a 32 KB chip; slots 6+7 share a 32 KB chip.)
- **Slots 0-3** are similarly paired into two 32 KB positions on a "cartridge ROM" data path.
- **Slots 8-15** live in a single 128 KB ROM on a separate data bus (this is where MOS, BASIC, the editor, and the on-board utilities live).
- **Sideways RAM**: on a **stock Master 128, slots 4-7 are 4 × 16 KB sideways RAM**; links can select ROM in their place (deselecting the corresponding RAM in 32 KB pairs). phX's boot checks banks 4-7 are RAM before it loads and runs on KC's two stock Master 128s (`phX/docs/design-backbone.md` "B3 built" boot table; `phX/docs/memory-map.md` "Measured": `*ROMS` shows 4-7 as the sideways RAM; [[sources/beeb-port-kit-hardware-facts-2026-11]] §4 "Real hardware"). The Paradroid port, which needs four 16K banks, ran on a real Master 128 in September 2026, and jsbeeb's Master model has RAM in 4-7. The Master Compact ships with 4 KB SWR (ANDY only).
  > **Corrected 2026-11-18.** This line said "the Master 128 ships with **none**" (attributed to [[sources/master-arm]] Ch 3 p32); it is contradicted by every stock Master measured. Whether the ARM page says that or the transcription misread a link table has not been re-checked.

You don't usually need to care about this from software — ROMSEL is uniform 0-15 — but the matrix matters if you're populating ROM sockets: certain ROM-slot combinations require physical link changes.

## **DO NOT** write `&FE30` directly

The MOS owns this register. It pages ROMs in and out *often* — for example, every time a `*` command is processed, every paged-ROM service call, every language-ROM call. If you write to `&FE30` without coordinating, the **current language ROM may be swapped out**, and the next instruction fetched from `&8000-&BFFF` will be from the wrong bank. The machine crashes immediately.

Use OSBYTE / service-call APIs instead. See [[os/paged-roms]] for the ROM header format, language vs service distinction, and the three safe ways to call into another ROM:

- `OSRDRM` (`&FFB9`) — single-byte read from any slot.
- `OSBYTE &8F` — issue a paged-ROM service call.
- **Extended vectors** — permanent intercept; MOS handles paging on every dispatch.

See [[os/service-calls]] for the complete service-call reason-code table.

## Standard ROM allocations (Model B with DFS + BASIC)

| Slot | Typical content |
|---|---|
| 15 | BASIC (highest priority) |
| 14 | (free) |
| ... | (free) |
| 0-13 | Filing systems, utilities — DFS usually 0 |

Slot numbers reflect **priority order** — higher number = higher priority for handling service calls. The currently active "language" ROM is selected at boot from whichever ROM has type bit indicating it's a language (Ch17).

## Sideways RAM (SWR)

B+ and Master can have some sideways slots populated with RAM instead of ROM. **`OSBYTE &44`** tests which banks contain writable memory:

```asm
LDA #&44 : JSR &FFF4
; on exit: X bits 0-3 set for banks 4-7 that are RAM
```

The OS test method (per §12.2 p159-160): switch in the candidate bank via `&FE30`, write a byte at `&80xx` (within the bank), read it back. If the read matches, the bank is RAM.

**Measured in practice (Paradroid, 2026-08-29 — [[sources/beeb-port-kit-hardware-facts]] §5):** on a **Model B, do not assume banks 4-7 are the RAM** — the "banks 4-7" wording above is the OSBYTE's own frame. KC's emulator had sideways RAM in slots 0-3; a game that assumed 4-7 unpacked its banks into slots that were not there, every `*LOAD` appeared to succeed, and the first call into bank code crashed. Probe at boot instead — see "Measured in practice" below.

**`OSBYTE &45`** returns which SWR banks are allocated as "extended addressing" (used as workspace by ROMs).

SWR is commonly used to:
- Load a ROM image from disk into RAM and use it like a real ROM (no need to physically program an EPROM during development).
- Provide extra workspace to filing systems / utilities via pseudo-addresses.

### Master sideways-RAM addressing modes (`*SRDATA` / `*SRROM`)

Per [[sources/master-rm]] Ch G.7, the Master's 4 × 16 KB SWR banks can be addressed in two ways, **set per-bank** via `*SRDATA <bank>` (data-style) or `*SRROM <bank>` (ROM-style, default):

- **Absolute addressing** (ROM-style): bank n appears at `&8000-&BFFF` when ROMSEL = n. Read/write via direct CPU access. Used when the bank holds an executable ROM image.
- **Pseudo addressing** (data-style): the 4 banks are aliased as one **contiguous 64 KB block** addressed by special pseudo-addresses, accessible only via `*SRREAD` / `*SRWRITE` (and their OSWORD `&05`/`&06` equivalents). Bank ID = W/X/Y/Z corresponds to ROMs 4/5/6/7:

| Pseudo address range | bank ID | ROM slot |
|---|---|---|
| `&00000` - `&03FEF` | W | 4 |
| `&03FF0` - `&07FDF` | X | 5 |
| `&07FE0` - `&0BFCF` | Y | 6 |
| `&0BFD0` - `&0FFBF` | Z | 7 |

(The 16-byte gaps reserve ROM-header space; you can't pseudo-address bytes that would land on a ROM type/copyright/entry-point header.)

This lets you treat a contiguous 64 KB of SWR as a flat data store from BASIC or assembly without managing ROMSEL by hand — useful for large lookup tables, sprite banks, sample data, etc. The trade-off is that pseudo-addressed banks can't simultaneously be executed as ROM images.

## Why this matters for performance

- The 16 KB at `&8000-&BFFF` is **prime real estate** — fast (no Tube indirection), addressable directly, and you have 16 banks of it. Performance-critical code that doesn't fit in main RAM can live in a sideways ROM/RAM.
- **Cross-bank calls are expensive**: invoking code in a different ROM requires a paging-register write (a few cycles), which means you must temporarily own `&FE30`. The MOS provides `OSRDRM` for read access and a paged-ROM service-call dispatcher; *direct* JSRs into another ROM require disabling IRQs and carefully managing `&FE30`.
- ANDY (Master, 4 KB at `&8000-&8FFF`) is **always-available private RAM** invisible to most software — useful for fast-access lookup tables in performance code on Master.

## ANDY — accessing the paged RAM area

| Machine | Size | Range | Notes |
|---|---|---|---|
| B+ | 12 KB | `&8000-&AFFF` | Top of shadow RAM (above the 20 KB shadow screen). Bit 7 of `&FE30` selects. |
| Master 128 / Compact | 4 KB | `&8000-&8FFF` | MOS workspace (see AllMem `&8000-&8FFF` workspace breakdown) — but the MOS touches only three of its 16 pages, each on one particular event; **all 4K is usable** by a program that avoids those events after filling it (measured map below). |

**Access methods** (from [[sources/beebwiki-andy]]):

1. **Direct paging**: write `&FE30` with the top bit set, then access `&8000+`. Same caveats as any direct `&FE30` write — prefer OSBYTE `&8F` or use only inside SEI.
2. **OSWORD `&05`** — read byte at extended address `&FFFExxxx` (xxxx = ANDY offset).
3. **OSWORD `&06`** — write byte at the same address form.

The `&FFFE`-prefix form is a Tube-safe convention.

**MOS scan rule:** MOS does not search ANDY for languages or service-ROM images. Code placed at `&8000` in ANDY cannot be entered via `*command` dispatch — JSR directly with the right ROMSEL value already set.

**B+ shadow trick:** on the B+ specifically, the paged-in ANDY window at `&A000-&AFFF` exposes a 4 KB chunk of the shadow display memory. Writing here directly modifies what the shadow screen displays — useful for fast back-buffer fills. Behaviour with shadow display disabled is undocumented.

See [[memory/memory-map]] for the wider layout. See [[memory/shadow-ram]] for screen-area RAM bank-switching (`&FE34` ACCCON), which is a separate mechanism.

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Paradroid keeps four 16K sideways-RAM banks of data and code on a Model B; Edge Grinder uses slots 4-7 plus ANDY and HAZEL on a Master 128.

### ANDY, measured

- **ANDY is 4K at `&8000-&8FFF`, selected by ROMSEL bit 7, and it overlays ONLY that 4K.** Writing `&AA` to `&8000` with bank 4 selected and `&55` to `&8000` with `&84` selected gives back `&55` under `&84` and `&AA` under `4`; `&9000` is the selected bank either way. **The test has to be machine code**: BASIC is itself the ROM at `&8000`, so paging ANDY in from a BASIC session removes the interpreter mid-statement and hangs (Edge, 2026-09-04, jsbeeb, from 6502 in main RAM; [layer-7-music.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-7-music.md)).
- **The loader cannot write into ANDY while the filing system is running**; Edge Grinder loads the ANDY stream before its last file and unpacks it afterwards (Layer 7, 2026-09-04). Same rule as HAZEL on [[memory/shadow-ram]].
- **What the MOS actually writes in ANDY (1942, 2026-09-11, jsbeeb Master 128, MOS 3.20, 1770 DFS — [[sources/beeb-port-kit-hardware-facts-2026-11]] §4; [1942-beeb docs/andy.md](https://github.com/kieranhj/1942-beeb/blob/master/docs/andy.md)).** Machine code in main RAM paged ANDY as the kit's `unpack_andy` does, filled it, and checked it around each event:

  | Page | Written by | Free for a program that... |
  |---|---|---|
  | `&80` | the soft-key buffer: `*KEY 1 HELLO` put "HELLO" at `&8022` | never issues `*KEY` after filling it |
  | `&81`-`&87` | nothing tried (1,792 bytes) | always |
  | `&88` | **`&8800`-`&882F` on every mode change and every soft BREAK**: 48 bytes of MODE 1's colour patterns and pixel masks; `&8830`-`&88FF` untouched | fills ANDY after its last mode change and reloads after a BREAK |
  | `&89`-`&8E` | nothing tried (1,536 bytes) | always |
  | `&8F` | user-defined characters: `VDU 23,224,...` wrote 8 bytes | never defines a character after filling it |

  **None of these wrote to ANDY:** 26 OSFILE loads, `*CAT`, a second of MOS sound (`SOUND 1,-15,100,20`), PRINT, half a second idle. So **all 4K is usable** by a program that fills ANDY after its one mode change, never calls `*KEY` or `VDU 23` afterwards, and reloads after a BREAK; 1942 loads its text code at `&8000` on that basis. One that changes mode in play or keeps the MOS's VDU running has `&81`-`&87` and `&89`-`&8E` (3,328 bytes), plus `&8830` up and `&8F` if it defines no characters. **Not measured:** real hardware, MOS 3.5, ADFS/MMFS, other user-defined characters, the key buffer's full length. Measurement trap: a fill over `&80` corrupts the key buffer, so a later `*KEY` fails "Bad key".
  > **Contradiction:** the ANDY table above (from the AllMem breakdown / ARM) calls ANDY "reserved for MOS use, user writes dangerous" and lists `&8000-&83FF` as a soft-key buffer "not available for any other use" and `&8900-&8FFF` as soft character definitions. The measurement agrees on *which* MOS features live there but shows they write only when used — the reservation is real only for a program that keeps using those features.
- **A map of what the MOS leaves is not a map of what is free**: once ANDY was measured free, a 116-byte routine moved in and its first `jsr` ran into 1942's own text tables (first byte `&00`: BRK, "Mistake") — read what the *port* already put there (1942 BUGS #24, #29; kit gotchas class 3).
- **Code that reads ANDY lives in main RAM**: with ANDY paged, the first 4K of the paged bank is hidden. An IRQ that pages anything must save and restore ROMSEL with the ANDY bit included (1942, 2026-09-11).
- **ROMSEL with bit 7 set from a stale copy pages ANDY over the DFS**: on the Master under a `*RUN` boot, `&028C` read `&FF`, and restoring ROMSEL from it did exactly that. Save ROMSHAD (`&F4`) instead (phX, 2026-11-14, jsbeeb Master MOS 3.20; `phX/docs/hwtest.md` "Traps found on the way"). See [[memory/os-workspace]].

### Model B sideways RAM: probe, do not assume

- **Do not assume banks 4-7** (see the note under "Sideways RAM" above). On a machine that has 4-7 (jsbeeb, the development desk) the assumption is right by coincidence (2026-08-29, KC's emulator configuration; [intro.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/intro.md)).
- **Probe at boot, with stnicc-beeb's method**: sixteen DISTINCT values, because a board decoding three select bits answers for N and N+8 with the same RAM (bank aliasing); a second, latched pass for Solidisk boards, which want the index in the User VIA and `&FE32` too, run only when the first pass found fewer than four. **Probe only banks the MOS found no ROM in** (`&02A1`, the ROM type table): the probe writes a byte at `&8008`, and doing that to a live utility ROM or a sideways-RAM filing system hangs a working machine. Select the bank (`STY ROMSEL`) before reading the byte you save, or the restore stage puts bank 0's byte into every RAM bank (built and measured 2026-08-29, jsbeeb `B-DFS1.2` with eight RAM banks, and a Master; [layer-13-compatibility.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-13-compatibility.md)).
- **Take the four highest-numbered RAM banks**: the banks that matter to other people sit low, and on a machine with exactly 4-7 the answer is unchanged (decided 2026-08-29, KC).
- **ROMSEL (`&FE30`) is write-only on a Model B: read ROMSHAD (`&F4`) instead.** Reading `&FE30` back gave `&FE` on jsbeeb's `B-DFS1.2` and the right bank (4) on its Master, which has a readable copy. ROMSHAD is the byte an IRQ saves and restores anyway (kit, 2026-09-11, jsbeeb — [[sources/beeb-port-kit-hardware-facts-2026-11]] §5).
- **A ROM image in sideways RAM can be the fourth bank if the game fills it last.** ZMMFS copies MMFS into the highest free RAM bank and marks it in `&02A1`; with exactly three clean banks the kit's probe takes the highest marked bank that passes MMFS's own RAM test (flip `&8006`, read back, flip back). The game then owes two things: fill that bank after its last filing-system call, and zero its `&02A1` byte first (Paradroid, 2026-09-10, issue #18 item 9).
- **The kit's probe results** (`lib/test/probe_test.6502`, fresh jsbeeb machine each, 2026-09-11):

  | Machine | Printed | Handover at `&0A00` |
  |---|---|---|
  | `B-DFS1.2` | `Sideways RAM found: 7 6 5 4 3 2 1 0` / `Using banks: 4 5 6 7` | `A5 04 05 06 07` |
  | `Master` | `found: 7 6 5 4` / `Using banks: 4 5 6 7` | `A5 04 05 06 07` |
  | `Master`, bank 7 marked as a ROM image | as above, plus "(The last holds a ROM image, which will be overwritten)" | `A5 04 05 06 07`; bank 7's `&8006` put back (`&82`); its `&02A8` byte left for the game to zero |
  | `Master`, banks 6 and 7 marked | `found: 5 4` / `...found 2` / `(Set LK18 and LK19 west?)` | untouched (`00`) |

  **A test ROM image needs a service entry that returns**: a marked `&02A1` byte makes the MOS call that bank's `&8003` with every service call, and a bank of zeros BRKs there and loops. `RTS` at `&8003` and a type byte at `&8006` suffice. The Solidisk refusal and a real ZMMFS machine are not tested.
- **A bank-number handover at `&0A00` (the printer buffer) survives BASIC dispatching the next exec line, DFS loading over `&1100-&2FFF`, and MODE 1's clear of `&3000-&7FFF`.** It does NOT survive a program that unpacks tables over `&0400-&1BFF`; that is how the 4-7 assumption crept back in (2026-08-29, jsbeeb; `&0A00` reads `FF` after both refusal paths).

### Paging discipline

- **Only one bank is visible at a time, and the IRQ fires with whatever the foreground has paged.** An IRQ that needs a bank must save the ROMSEL shadow (`&F4`), page, and restore both; writing the shadow first is what keeps the claim consistent (Paradroid's sound tick, 2026-08-21, jsbeeb; [layer-11e-sound.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-11e-sound.md)). **The paging itself costs +16 cycles**: phX's music tick (save `&F4`, page bank 4 into ROMSEL and `&F4`, restore both) went from a mean of 152 to 168 cycles, worst 524 to 540, 1,299 of 1,299 ticks identical (November 2026, jsbeeb Master, `verify_music.mjs`; `phX/docs/memory-map.md` — [[sources/beeb-port-kit-hardware-facts-2026-11]] §5). *(Corrected 2026-11-18: this entry said "~60-80 cycles of overhead", Paradroid's estimate for the whole tick's overhead, not a measurement of the paging.)* This is the practical form of "**DO NOT** write `&FE30` directly" above for a program that has taken IRQ1V and owns the machine.
- **Bank code may call main RAM freely; main RAM may call into a bank only with that bank paged**, and a bank routine may not call main-RAM code that pages a different bank and restores somebody else's. Both ports broke the second rule within a day of writing it down (Paradroid's resident depacker, 2026-08-29; Edge's `bank_call`, 2026-09-06; [layer-9h-keyredef.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-9h-keyredef.md)).
- **The DFS ROM is paged in at `&8000` during a filing-system call**, so a bank cannot be loaded at `&8000` even uncompressed; stage below and copy or unpack (Paradroid Layer 13d, jsbeeb). See [[techniques/zx0-loading]].
- **jsbeeb's `B-DFS1.2` model has eight sideways RAM banks; a Master model has 4-7** ([[tools/emulators]]).
- **Move the banks to find the bugs that depend on where they are.** Stryker's Run's game banks moved from 4-7 to 0-3 (jsbeeb `B-DFS1.2`'s eight banks, `SWR_POKE`) exposed a scroll path that had paged bank 0 for seven days — harmless while bank 0 was empty — and a table walk that ran off its table into the bank numbers (Stryker's Run BUGS #16, #17, 2026-10-24/25, jsbeeb 2.10.2; kit gotchas class 6).
- **With code in two sideways banks at `&8000`, an emulator address hook fires in both**, and on the Master before boot it fires in a ROM — gate every hook on ROMSEL (Isometrikum, Stryker's Run; kit gotchas class 5). See [[tools/emulators]].

### Paging on the Master (1942, Stryker's Run, phX — 2026)

- **HAZEL can stay paged for the whole of play**: put ACCCON Y into the base every run-time ACCCON write ORs in, and HAZEL code and data need no paging and no mask (1942, played on a real Master; phX the same). See [[memory/shadow-ram]].
- **ANDY and HAZEL paged through play, plus four sideways banks** is 1942's shipped configuration on a real Master 128 (Gotek 2026-09-28, real drive 2026-10-12, KC).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
