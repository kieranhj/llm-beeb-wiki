---
title: "AllMem: BBC System Memory Map (Ripley / Harston)"
type: source
tags: [memory-map, reference, workspace, mos]
updated: 2026-05-14
---

# AllMem — BBC System Memory Map

**Author:** Jon Ripley, updated by J.G. Harston
**Edition used:** 18-Jun-2016
**File:** `raw/AllMem.txt`
**Scope:** A complete byte-level catalogue of MOS workspace use across the BBC A/B/B+, Electron, Master 128, Master ET, and Master Compact. Covers zero page, pages 1-3, buffer pages 8-D, sideways ROM areas, FRED/JIM/SHEILA, and the MOS jumpblock.

## Summary

This is the single most useful low-level reference for "what owns this byte?" — finer-grained than the NAUG memory chapter (which is more discursive) and authoritative on BBC/Electron/Master differences. Per-byte coverage, with per-machine variants called out side-by-side. Particularly strong on:

- Zero page subdivisions (Econet/NMI/CFS/VDU partitioning) — more precise than NAUG.
- The full OSBYTE-variables table at `&236-&28F` (every fxNNN ↔ address ↔ purpose mapping).
- Extended vector table at `&0D9F-&0DEF`.
- Sideways-ROM workspace conventions for the `&0DF0-&0DFF` private workspace high-byte register.
- Electron-specific deltas (ULA register copies, ROM manager workspace).

## Key technical claims (with citations to file lines)

Citations are line numbers in `raw/AllMem.txt`.

### Zero page partitioning (lines 13-130)

- `&0000-&008F` Language workspace — full 144 bytes, not just `&00-&6F` (which is what NAUG implies when listing the "USER `&70-&8F`" carve-out).
- `&0090-&009F` Econet private workspace.
- `&00A0-&00A7` Current NMI owner's workspace. `&00A0` conventionally stores previous NMI owner ID.
- `&00A8-&00AF` **Transient command space** (NOT generic "OS scratch" — used by `*command` invocations).
- `&00B0-&00BF` Filing system scratch space.
- `&00C0-&00CF` Filing system workspace.
- `&00D0-&00E1` VDU workspace.
- `&00E2-&00E3` CFS/RFS private workspace.
- `&00E4-&00FF` General MOS workspace.

### VDU zero page detail (lines 68-88)

- `&00D0` VDU Status (= OSBYTE `&75`). Bits: 0=printer, 1=scroll-disabled, 2=paged, 3=software-scroll, 4=shadow (Master only), 5=VDU 5, 6=cursor split, 7=VDU disabled.
- `&00D1` Graphics pixel mask.
- `&00D2` Text colour OR mask. `&00D3` Text colour EOR mask.
- `&00D4` Graphics colour OR mask. `&00D5` Graphics colour EOR mask.
- `&00D6-&00D7` **Graphics character cell**.
- `&00D8-&00D9` **Top scan line**.
- `&00DA-&00DF` Temporary workspace.
- `&00E0-&00E1` BBC/Electron: Row multiplication; Master: General workspace.

### Critical OS workspace at `&00E4-&00FF` (lines 106-130)

- `&00EC` Internal key number (last). `&00ED` Internal key number (first/penultimate).
- `&00EE` Internal key of char ignored by OSBYTE `&79`, **AND** the 1 MHz bus paging-register RAM copy (dual-purpose).
- `&00EF / &00F0 / &00F1` OSBYTE/OSWORD A / X / Y reg values during a call.
- `&00F2-&00F3` OS text pointer (star commands, filenames).
- `&00F4` Currently selected ROM.
- `&00F5` Current PHROM or RFS ROM number.
- `&00F6-&00F7` PHROM/RFSROM/OSRDSC pointer.
- `&00F8-&00F9` BBC/Electron unused; **Master: Soft key expansion pointer**.
- `&00FA-&00FB` General OS workspace, used by buffer access code in interrupts.
- `&00FC` **Interrupt Temp A reg store**.
- `&00FD-&00FE` **Error message pointer**, initially set to language version string (NOT "post-BRK return pointer" — it's the address of the error text following a BRK).
- `&00FF` Escape flag (bit 7).

### OS vectors at `&0200-&0235` (lines 149-177)

Full 27-vector table. All present in our existing [[os/calls]] page; AllMem confirms.

### OSBYTE variables `&0236-&028F` (lines 179-287)

Each address `&023N` maps to fxNNN where NNN = address − `&023` mapped to OSBYTE number. The mapping is `&236 = fx166 = OS-var &A6`, then sequential.

**Examples (used to verify the wiki's "direct read" table):**

- `&024A` fx186 `&BA` ROM active last BRK.
- `&0261` fx209 `&D1` Speech suppression status.
- `&0262` fx210 `&D2` Sound suppression status.
- `&0269` fx217 `&D9` Screen lines since last page.
- `&027C` fx236 `&EC` Output stream character destination (set with FX3).
- `&027D` fx237 `&ED` Cursor key status (set with FX4).
- `&027E` fx238 `&EE` BBC/Electron unused; Master: keypad base.
- `&0242` fx178 `&B2` Keyboard semaphore (BBC/Master) / undefined (Electron).

### Page 2 misc workspace (lines 289-369)

- `&0290` VDU vertical adjust (*TV first parameter).
- `&0291` Interlace toggle (*TV second parameter).
- `&0292-&0296` TIME value 1, `&0297-&029B` TIME value 2 (5-byte dual-copy for atomic read).
- `&029C-&02A0` OSWORD 3/4 countdown timer.
- `&02A1-&02B0` Paged ROM type table.
- `&02B1-&02B2` INKEY countdown.
- `&02B3 / &02B4 / &02B5` OSWORD 0 max line length / min char / max char.
- `&02B6-&02BE` ADC channel value tables (BBC). Electron uses `&02F7-&02FF` instead.
- `&02BF-&02C8` Event enable flags.
- Buffer busy / start / end indexes differ BBC vs Master vs Electron — table at lines 326-336.

### Page 3 VDU workspace (lines 378-445)

- `&0300-&0307` Current graphics window (4 × 16-bit words: left col, bottom row, right col, top row — pixels).
- `&0308-&030B` Current text window (4 bytes: left, bottom, right, top — character cells).
- `&030C-&030F` Graphics origin (external coords).
- `&0310-&0313` Current graphics cursor (external).
- `&0314-&0317` Old graphics cursor (external).
- `&0318 / &0319` Current text cursor X / Y.
- `&031A` Line within graphics cell of cursor.
- `&031B` Graphics workspace / VDU queue.
- `&031F-&0323` **VDU queue** (5 bytes).
- `&0324-&0327` **Current graphics cursor (internal coords)**.
- `&0328-&032F` Bitmap read from screen by OSBYTE 135.
- `&0330-&0349` Graphics workspace.
- `&034A-&034B` **Text cursor address for 6845**.
- `&034C-&034D` **Text window width in bytes**.
- `&034E` High byte of bottom of screen memory.
- `&034F` Bytes per character for current mode.
- `&0350-&0351` **Screen display start address for 6845** (the OS's view of R12/R13).
- `&0352-&0353` Bytes per screen row.
- `&0354` Screen memory size high byte.
- `&0355` Current screen mode.
- `&0356` Memory map type: 0=20K, 1=16K, 2=10K, 3=8K, 4=1K.
- `&0357-&035A` Foreground/background text/graphics colours.
- `&035B / &035C` Foreground/background plot mode.
- `&035D-&035E` General VDU jump vector.
- `&035F` Cursor start register previous setting.
- `&0360` Number of logical colours − 1.
- `&0361` Pixels per byte − 1 (zero if text-only mode).
- `&0362 / &0363` Leftmost / rightmost pixel colour mask.
- `&0364 / &0365` Text input cursor X / Y.
- `&0366-&036E` BBC/Electron: teletext output cursor char + font explosion flags + font location MSBs for char groups 32-63, 64-95, … 224-255. Master: VDU 23,16 setting, VDU 23,6 dot pattern, ECF state, foreground/background graphics colour.
- `&036F-&037E` Palette for colours 0-15.
- `&037F` Unused (used by some shadow-RAM systems).

### Pages 8-9 buffers (lines 494-578)

- `&0800-&083F` Sound workspace.
- `&0840-&087F` Sound channel buffers (4 × 16-byte channels).
- `&0880-&08BF` Printer buffer (DISTINCT from sound area).
- `&08C0-&08FF` Envelopes 1-4 (13 bytes each + 3 spare).
- `&0900-&09BF` RS423 output buffer.
- `&09C0-&09FF` Speech buffer.
- `&0900-&09FF` overlap: CFS/RFS BPUT sequential output buffer (mutually exclusive with RS423/Speech).
- `&0900-&09BF` Envelopes 5-16 (same layout as 1-4, when used).
- `&0A00-&0AFF` Cassette/RS423 input buffer (NOT used by `LOAD`).

### Page B / Page C / Page D (lines 586-748)

- `&0B00-&0B10` Soft key pointers (17 bytes = ptr per fkey 0-15 + sentinel).
- `&0B11-&0BFF` Soft key strings.
- Master variant: `&0B00-&0BFF` Econet workspace (station, FS station, FS network, print server type string).
- `&0C00-&0CFF` BBC/Electron: Font for ASCII 128-159. Master: Econet workspace.
- `&0D00-&0D5F` NMI handler code + workspace. Claim via service-call 12 (OSBYTE `143,12,255`). MUST place `RTI` at `&0D00` if you own the workspace but don't handle hardware NMIs.
- Econet uses `&0D20-&0D5F` for scout/acknowledge packets when active.
- `&0D60-&0D67` Econet workspace.
- `&0D68-&0D7F` Master Econet / Electron expansion / Electron ROM manager workspace.
- `&0D80-&0D91` Econet-over-other-hardware workspace.
- `&0D92-&0D9E` Mouse / trackerball workspace.
- `&0D9F-&0DEF` **Extended vector table** — every standard vector mirrored as 3 bytes (address low, address high, ROM number). E.g. `&0DAE-&0DB0` XBYTEV.
- `&0DF0-&0DFF` **Sideways ROMs private workspace high-byte register**. ROM `x` has byte at `&0DF0+x`. Conventionally MSB of private workspace pointer. Bit 7 disables the ROM (workspace at `&8000-&FFFF` = ROM area = invalid).

### Master Andy workspace (lines 820-829)

`&8000-&8FFF` (Andy private RAM, ACCCON-bit selected):

- `&8000-&8020` Soft key string start addresses (16 × low byte + sentinel + 16 × high byte + sentinel).
- `&8022-&83FF` Soft key string data.
- `&8400-&87FF` VDU driver workspace.
- `&8800-&88FF` VDU variables.
- `&8900-&8FFF` Font definition, chars 32-255.

### Master Hazel workspace (lines 832-886)

`&C000-&DBFF` Sideways ROM shared / private workspace (claim via service call `&21` for shared, `&22` for private). Strictly: only filing systems can claim shared workspace here (via FSC 6 — vectors changing). Private workspace is per-ROM.

- `&DC00-&DCFF` OSCLI string buffer.
- `&DD00-&DEFF` Transient command workspace.
- `&DF00` Current filing system number.
- `&DF01` Active filing system number.
- `&DF02` Library filing system number.
- `&DF03` ROM number of current filing system.
- `&DF04-&DF05` Transient command line address.
- `&DF06-&DFC1` Up to 17 filing system info blocks (11 bytes each + terminator).
- `&DFC2-&DFDD` *LIST/*TYPE/*BUILD/*APPEND/*MOVE state.
- `&DFDE-&DFFF` Unused.

### Master DFS `OSWORD &7F` bug (line 856-858)

The Master DFS `OSWORD &7F` writes to page `&C2` **regardless of who owns the shared workspace**. Documented bug, worth noting if rolling custom Master ROMs.

### Page FE — SHEILA (lines 927-948)

Confirms our existing [[memory/memory-map]] table. AllMem additions:

- `&FE18-&FE1F` Station ID / NMI Control (BBC B / B+) vs ADC (Master) — note the **Master ADC is at `&FE18`, not `&FEC0`** (which holds the BBC's ADC).
- `&FE20-&FE2F` Video ULA **plus border control plus network NMI control**.
- `&FE24-&FE27` Disk control (Master).
- `&FE80-&FE9F`: 8271 FDC (B) / 1770 FDC + control (B+) / Videodisk SCSI (Master).
- `&FEC0-&FEDF`: ADC (B/B+) / "Network interface (not 6854 ADLC)".

### Page FF — MOS entry jumpblock (lines 951-981)

Full list of public entry points `&FFB3-&FFF9` plus hardware vectors `&FFFA-&FFFF` (NMIV, RESETV, IRQV). Master adds `OSWRSC` (`&FFB3`) for writing a byte to screen.

## Filed into

This ingest produces no new wiki pages — it's a reference cross-check. The audit findings are listed in [[synthesis/allmem-cross-reference-report]] (filing this back depends on user approval — see report).

Pages whose claims were validated against this source:

- [[memory/zero-page]]
- [[memory/os-workspace]]
- [[memory/memory-map]]
- [[os/calls]]
- [[os/buffers]]

Contradictions found are listed below for human review.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
