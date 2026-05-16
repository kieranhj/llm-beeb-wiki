---
title: OS Workspace (Pages 1, 2, 3)
type: memory
tags: [workspace, mos, vectors, page-two, page-three]
sources: [naug-ch06-os-introduction, naug-ch13-video, allmem-ripley-harston, master-arm, master-rm]
updated: 2026-05-16
---

# OS Workspace — Pages 1, 2, 3

Beyond zero page ([[memory/zero-page]]), MOS occupies three more pages of low RAM. Knowing the layout matters when:

- You want to **read MOS state** without using OSBYTEs (faster lookups).
- You want to **bypass MOS** for a particular function and need to know what state to restore.
- You're writing code that lives in low RAM and want to avoid clobbering MOS variables.

## Page 1 (`&0100-&01FF`) — Stack

The 6502 hardware stack. BBC firmware initialises SP to `&FF`; the stack grows downward from `&01FF`. SP wraps within page 1 on overflow with no trap, so deep recursion or unbalanced pushes silently corrupt earlier stack frames.

When MOS calls into your code via OSWRCH/OSRDCH/IRQ/etc, the upper portion of page 1 contains the return-address chain. Don't touch it.

## Pages 8-9 (`&0800-&09FF`) — Buffers

From NAUG §6.6 p114:

| Range | Use |
|---|---|
| `&800-&83F` | Sound workspace |
| `&840-&84F` | Sound channel 0 |
| `&850-&85F` | Sound channel 1 |
| `&860-&86F` | Sound channel 2 |
| `&870-&87F` | Sound channel 3 |
| `&880-&8BF` | Printer buffer (distinct region — NOT shared with sound) |
| `&8C0-&8FF` | Envelope storage 1-4 (13 bytes each + 3 spare) |
| `&900-&9BF` | RS423 output buffer — OR Envelopes 5-16 — OR (overlap) CFS/RFS BPUT sequential output buffer |
| `&9C0-&9FF` | Speech buffer — overlapped by CFS/RFS BPUT output buffer when CFS active |

## Page B (`&0B00-&0BFF`) — Function keys

| Range | Use |
|---|---|
| `&B00-&B10` | Soft key pointers (one per function key) |
| `&B11-&BFF` | Soft key definition strings |

## Page C (`&0C00-&0CFF`) — User character definitions

8 bytes per character × 32 characters = 256 bytes for ASCII 128-159 (or 224-255 on imploded font).

## Page D (`&0D00-&0DFF`) — NMI + Econet

| Range | Use |
|---|---|
| `&D00-&D5F` | NMI handling code (filing systems install here) |
| `&D60-&D7F` | Econet workspace |
| `&D80-&D91` | Unused on most machines |
| `&D92-&D9E` | Reserved for trackerball |
| `&D9F-&DEF` | Extended vector table (paged-ROM-claimed extra vectors) |
| `&DF0-&DFF` | ROM workspace bytes (per-ROM private workspace pointer) |

NMI handlers are page-aligned at `&D00`. Disc filing systems and Econet share the NMI; claim/release protocol is via paged-ROM service calls (Ch17, pending).

## Page 2 (`&0200-&02FF`) — OS vectors + OS variables

From NAUG §6.6.2:

| Range | Use |
|---|---|
| `&200-&235` | OS vector table (see [[os/calls]]) |
| `&236-&28F` | OS variables — accessible via OSBYTE `&A6-&FF`. Direct read is faster than OSBYTE. |
| `&290`-`&291` | *TV vertical adjust + interlace |
| `&292-&296` | TIME — first copy (dual-clock to allow atomic 5-byte read) |
| `&297-&29B` | TIME — second copy |
| `&29C-&2A0` | Interval timer (OSWORDs `&03`/`&04`) |
| `&2A1-&2B0` | Paged ROM table (OSBYTE `&AA`/`&AB`) |
| `&2B1-`onwards | INKEY countdown, OSWORD `&00` workspace, ADC LSB/MSB tables, event enable flags, two-key rollover, buffer pointers, CFS state, OSFILE control blocks |

Master and Electron differ in the exact addresses of some of these — NAUG p115 has a side-by-side table.

### Useful direct reads

The OSBYTE-variable address is `&0236 + (osbyte_number - &A6)`. So `&D2` (sound suppression) lives at `&0236 + (&D2 - &A6) = &0262`. Worked examples:

| Addr | What | OSBYTE-var # |
|---|---|---|
| `&020E-&020F` | OSWRCH vector | — |
| `&024A` | ROM active at last BRK | `&BA` (fx186) |
| `&0261` | Speech suppression status | `&D1` (fx209) |
| `&0262` | Sound suppression status | `&D2` (fx210) |
| `&0277` | User VIA IRQ mask | `&E7` (fx231) |
| `&0279` | System VIA IRQ mask | `&E9` (fx233) |
| `&027C` | Output stream destination (FX3) | `&EC` (fx236) |
| `&027D` | Cursor key status (FX4) | `&ED` (fx237) |
| `&028C` | Current language ROM | `&FC` (fx252) |
| `&028D` | Last BREAK type | `&FD` (fx253) |

Exact addresses are stable across BBC/B+/Master — the formula above always holds. Reading directly is **faster** than calling OSBYTE (saves the dispatch overhead). For full table see [[sources/allmem-ripley-harston]] lines 179-287, or query `OSBYTE &A6/&A7` to get the base address dynamically (in case a future MOS shifts it).

## Page 3 (`&0300-&03FF`) — VDU workspace + filing buffers

From NAUG §13.2.2 (already in [[sources/naug-ch13-video]]):

| Range | Use |
|---|---|
| `&300-&30B` | Current graphics window (`&300`-`&307`, pixels) + text window (`&308`-`&30B`, chars) |
| `&30C-&30F` | Graphics origin (external coords) |
| `&310-&317` | Current + old graphics cursor (external coords) |
| `&318`-`&319` | Text cursor X / Y |
| `&31A` | Line within graphics cell of cursor |
| `&31B` | Graphics workspace / VDU queue control |
| `&31F-&323` | VDU queue (5 bytes) |
| `&324-&327` | Current graphics cursor (internal coords) |
| `&328-&32F` | Bitmap read from screen by OSBYTE 135 |
| `&330-&349` | Graphics workspace |
| `&34A-&34B` | Text cursor address for 6845 |
| `&34C-&34D` | Text window width in bytes |
| `&34E` | MSB of HIMEM (ignoring shadow) |
| `&34F` | Bytes per character (current mode) |
| `&350-&351` | **Top-left screen address as given to 6845** — this is the screen-start mirror for hardware scroll |
| `&352-&353` | Bytes per char row (current mode) |
| `&354` | Screen mode size in pages |
| `&355` | Current screen mode (ignoring shadow bit) |
| `&356` | Screen size code: 0=20K, 1=16K, 2=10K, 3=8K, 4=1K |
| `&35F` | Last 6845 cursor start register value |
| `&360` | Logical colours - 1 |
| `&361` | Pixels per byte - 1 (0 for text) |
| `&362`-`&363` | Bit masks for left-most and right-most pixel |
| `&366-&36E` | VDU 23 settings (Master ECF, dot patterns, etc.) |
| `&36F-&37E` | Font location bytes (MSB per font group) |
| `&37F` | Unused |
| `&380-`onwards | Colour palette copy (1 byte per logical colour), BPUT/BGET buffers, filing-system block headers, keyboard input buffer |

**`&350`/`&351` is the screen-start the OS thinks the 6845 has** — keep this in sync if you hardware-scroll directly, so subsequent OSWRCH lands at the right pixel row. Equivalent to `OSBYTE &A0, X=&50`.

## Bypassing MOS — what to save/restore

If you're going fully native (game / demo style, no return to BASIC):

- **You don't need to preserve anything.** Set SP, set zero page, set IRQ vectors, set MOS-tracked hardware state to whatever you want, run forever (or until `BRK`/reset).

If you're returning to BASIC after a routine:

- Page 0: save `&70-&8F` and whatever else you touch (see [[memory/zero-page]]).
- OS palette (`&FE21` + page 3 colour palette copy at `&380+`): if you wrote `&FE21` directly, also write the same value (XOR 7) into the OS copy, or restore the original.
- `&350`/`&351` if you moved R12/R13.
- IRQ vectors `&204-&207` if you hooked them.
- Sideways ROM register `&FE30`: **never set** — see [[memory/paged-rom]].

If you're inside an IRQ handler:

- A is in `&FC` (MOS save). Don't touch.
- Keep your handler under 2 ms (NAUG §8.5 — [[os/interrupts]]).
- Don't call any OS routine.

## Master "second 32 KB" workspace map (`&3000-&DFFF` in LYNNE+ANDY+HAZEL)

The Master's 128 KB of DRAM splits into two 64 KB regions. The "second 32 KB" (the upper half of the second region, partially overlaid by paged ROMs in the CPU map) contains a mix of shadow display and MOS workspace. Per [[sources/master-arm]] Ch 11:

| Range | Use | Note |
|---|---|---|
| `&3000-&7FFF` | LYNNE shadow screen | Any portion not needed by the current mode is free; `*MOVE` will use it |
| `&8000-&83FF` | Soft-key expansion buffer | 1 KB — replaces the cramped `&0B00-&0BFF` allocation on Model B. Not available for any other use |
| `&8400-&88FF` | VDU workspace (flood-fill scratch) | Routines tag `&8601` to share; commercial software should avoid |
| `&8900-&8FFF` | **Soft character definitions** | **Moved from `&0E00+` on B/B+** — exploded font no longer steals from user RAM. Big PAGE win |
| `&C000-&DBFF` | HAZEL (paged-ROM workspace) | ROMs claim via service calls; static workspace requires filing-system pattern |
| `&DC00-&DCFF` | MOS CLI buffer | Corrupted by every `*` command |
| `&DD00-&DEFF` | Transient utility workspace | Used by user `*` commands and `*MOVE` |
| `&DF00-&DFFF` | MOS private workspace | Off-limits |

**The soft-character-definition relocation from `&0E00+` to `&8900` is one of the Master's biggest practical wins**: on a Model B, defining 32 custom characters cost 256 bytes of OSHWM. On Master those bytes live in the second 32 KB invisibly. Code that explicitly pokes `&0E00`-area font on a Model B needs a Master code path that targets `&8900` instead — see [[memory/memory-map]] for the broader map.

## Master vector additions (`&0D9F-&0DEF`)

Per ARM Ch 11, the Master allocates 80 bytes for **extended vectors** at `&0D9F-&0DEF`. These let a sideways-ROM intercept any vector with the routine *living in the ROM* — without the ROM having to be in slot 15 or whatever. Mechanism:

1. `OSBYTE &A8` (168) returns the start of the extended-vector space (`&0D9F`).
2. Write the per-vector triple at `extended_start + 3 × vector_index`: `<entry_low> <entry_high> <rom_slot_number>`.
3. Replace the normal vector at `&02xx` with `&FF00 + (vector_addr - &0200) × 3 / 2` — a special address the MOS recognises as "this dispatches via the extended vector triple".

This is how things like the Master's ADFS filing system, network filing system, and other complex ROM-resident handlers intercept vectors cleanly without trampling each other. The MOS handles ROM-bank switching on each dispatch via the extended vector.

Vector-number indexing (per ARM Ch 11 vector table): `vector_number = (vector_addr - &0200) / 2`. So OSWRCH (vector `&20E`) is vector number 7, OSWORD (`&20C`) is 6, OSBYTE (`&20A`) is 5, EVNTV (`&220`) is 16, etc.

## See also

- [[memory/zero-page]] — Page 0 detail.
- [[memory/memory-map]] — Big picture.
- [[os/calls]] — OS entry-point reference.
- [[os/interrupts]] — IRQ handler conventions and `&FC` usage.
- [[os/paged-roms]] — extended vectors install pattern (the high-level companion to the &0D9F-&0DEF detail above).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
