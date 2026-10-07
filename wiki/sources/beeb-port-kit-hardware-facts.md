---
title: BBC Micro hardware facts, measured — beeb-port-kit
type: source
author: Kieran Connell (KC)
date: 2026-09-06
urls:
  - https://github.com/kieranhj/paradroid-beeb
  - https://github.com/kieranhj/edge-beeb
local: raw/notes/beeb-port-kit-hardware-facts.md
ports:
  - Paradroid (C64 → BBC Model B) — https://github.com/kieranhj/paradroid-beeb
  - Edge Grinder (C64 → BBC Master 128) — https://github.com/kieranhj/edge-beeb
tags: [measured, crtc, vertical-rupture, video-ula, nula, system-via, via-timers, keyboard, shadow-ram, andy, hazel, sideways-ram, dfs, osfile, mos-workspace, zx0, beebasm, jsbeeb, b-em, b2]
updated: 2026-09-07
---

# Source: BBC Micro hardware facts, measured (beeb-port-kit)

## Bibliographic

- **Document:** `docs/hardware-facts.md` from Kieran Connell's *beeb-port-kit* (MIT licence), dated 2026-09-06. Local copy: `raw/notes/beeb-port-kit-hardware-facts.md` (750 lines, 12 sections).
- **Author:** Kieran Connell (KC), with the measurements taken by Claude Code sessions driving the jsbeeb MCP under KC's direction.
- **The two ports it draws on:**
  - **Paradroid** — C64 → BBC **Model B**, [github.com/kieranhj/paradroid-beeb](https://github.com/kieranhj/paradroid-beeb). Layers 3-13, August 2026. MODE 1, three-cycle rupture, 10K hardware-scrolled strip, sideways-RAM probing, ZX0 loader, SN76489 sound driver. Confirmed running on a real Master 128 on 2026-09-06.
  - **Edge Grinder** — C64 → BBC **Master 128**, [github.com/kieranhj/edge-beeb](https://github.com/kieranhj/edge-beeb). Layers 0-9, September 2026. MODE 2, two-cycle rupture, shadow-RAM double buffer, ANDY + HAZEL + sideways banks for a 349-second VGI tune, VideoNuLA test build.
- **Instrument:** jsbeeb through an MCP (breakpoints, memory/register reads, cycle counts, screenshots, SN76489 capture) as the primary instrument; b-em and b2 as cross-checks; a real Master 128 where the entry says so.

## Summary

A reference of facts about the 6845, the Video ULA and VideoNuLA, the System VIA, the Master's ACCCON/ANDY/HAZEL, Model B sideways RAM, the MOS and DFS workspace, keyboard internal key numbers, 6502 timing constants, ZX0 in-place unpacking, beebasm 1.11 and the emulators — **every entry stating the fact, then how and when it was established, then linking the port document where it is written up.** The document's rule is *measure, do not recall*: several entries contradict what the ports' author believed beforehand (a scanline is 128 CPU cycles not 64; `R6 = 0` is not a blank; the display wrap sizes are not powers of two; jsbeeb does boot an unpadded SSD), and each cost a wrong build before it cost a measurement. Section 12 lists claims the ports state but did not measure, so they are not mistaken for the rest.

For this wiki the value is twofold: it supplies **empirical confirmation with dates and instruments** for claims the wiki had only from manuals, and it fills gaps the manuals do not cover at all (per-register CRTC write windows inside a rupture, the R5 trap, Master mid-frame bank switching, emulator behaviour, assembler gotchas).

## Key technical claims (by section)

Section numbers are the document's. Every claim below carries its date and instrument in the raw file; the wiki pages cite the port and the write-up file.

### §1 The 6845 CRTC

- CRTC start address = screen address / 8; one CRTC unit is 8 bytes; a hardware-scrolled area is a 1-D ring, not a 2-D grid; R12/R13 half-update if sampled between the two writes. (Paradroid Layer 3, jsbeeb.)
- **Per-register write windows in a rupture**: R4 inside its own cycle before C4 reaches it; R6, R7, R12/R13 inside the *previous* cycle; R5 anywhere but not near a boundary. Symptoms when wrong are recorded (R7 late → VSync never fires and the picture rolls; R6 late → display enable is a flip-flop cleared on match and cannot be re-raised). (Paradroid Layer 3; reconfirmed Edge 2026-09-02.)
- Rows must sum to 39 (312 lines): 1,000 fields in 39,936,000 cycles exactly.
- R7 for the panel cycle must be written at VSync, not at the first timer fire (7-row panel cycle reached stale R7 and fired a second VSync). (2026-08-21.)
- **R5 trap**: written after the adjust count has passed the new value, the 5-bit counter wraps — ~29 extra scanlines. R5 is sampled at cycle end. Timer fires should overshoot cycle boundaries by a few rows.
- R8 `&30` blanks, `&00` unblanks, immediately, part-way across a scanline; **`R6 = 0` leaks one row**; `R1 = 0` blanks and kills the row; R8 blanking does not hide the CRTC cursor (`R10 = &20` does); interlace must be off for a rupture.
- The display window must fit inside ONE hardware wrap (the translator subtracts once, does not iterate); a 16K buffer with 640-byte rows does not wrap on a row boundary.
- Switching frame shapes mid-frame costs malformed fields (38,378 / 49,154 / 6,168-cycle fields measured); a right-length field can still be misplaced — **b2 rolled and KC photographed it; jsbeeb showed no fault**; a two-cycle ↔ four-cycle change from main-loop code costs one 272-line field; a rupture shape with nobody servicing timers runs at roughly double rate.

### §2 Video ULA and palette

- `&FE21` takes `(logical << 4) OR (physical EOR 7)`; 4-colour modes need four entries per logical colour. MOS default MODE 2 palette is logical n → physical n for all sixteen. A mid-frame `&FE21` write lands wherever the raster is. A per-scanline loop opening with a 1 MHz write is phase-stable (stated, not separately measured).
- MODE 1 byte layout: adjacent 4-pixel columns are 8 bytes apart, not 1 ("this cost a build"). MODE 2: right pixel in bits 6,4,2,0, left in 7,5,3,1.
- **VideoNuLA**: default composes `&FE21` then `&FE23`; `&FE22 = &11` selects logical mapping (measured on real hardware first, 2026-09-05); entries go to `&FE23` as `[index<<4|red]`, `[green<<4|blue]`; `&FE22 = &40` resets.

### §3 System VIA

- **Display wrap table**, line 4 / line 5 of the addressable latch: 0/0 → `&4000` (16K), 1/0 → `&6000` (8K), 0/1 → `&3000` (20K), 1/1 → `&5800` (10K); written as `#4`/`#12` and `#5`/`#13` to `&FE40`. (Edge 2026-09-04; 10K case independently in Paradroid.)
- T1 continuous mode, not T2, for raster timing; T1 ticks at 1 MHz, 64 per scanline; a `&FE44` read in a VSync-locked loop is near-constant under the MOS; a T1 stopwatch difference is only modular while the counter does not pass zero; T2's two bytes can roll between reads.
- VSync CA1 serviced ~4 scanlines after the edge; polling `&FE4D` bit 1 races the MOS; with interrupts down, polling works; taking IRQ1V outright needs every other source disabled.
- Direct keyboard read: 69 cycles vs 243 through `OSBYTE &81`; Port A shared with the SN76489 write path safely if the IRQ saves/restores DDRA and ORA (0 of 8,192 polls disturbed); **phantom keys** on real hardware (Z X K M L together phantomed C).

### §4 Master 128

- ACCCON D flips cleanly in the VSync handler; **the display bank can be switched inside a frame** (jsbeeb only, b-em unchecked); the wrap applies inside whichever bank is displayed; nothing displayed may live below `&3000` (jsbeeb and b-em disagree; hardware untested); shadow RAM is a free staging area at boot.
- **ANDY** is 4K at `&8000-&8FFF`, ROMSEL bit 7, overlaying only that 4K; the test must be machine code (BASIC lives at `&8000`). The loader cannot write into ANDY while the filing system runs.
- **HAZEL** is the filing system's workspace: take it and BREAK must clear memory (`OSBYTE 200, X=3`); OSFILE cannot write into it; `&FFFE` reads `&E59E`; bank `&BFFF` and HAZEL `&C000` are adjacent and both visible.
- `&0C00`, `&0800-&0BFF` and `&0400-&07BF` are reclaimable, verified by sentinel.
- A real Master 128 runs the Paradroid port (2026-09-06).

### §5 Model B sideways RAM

- Do not assume banks 4-7 (KC's emulator had 0-3); probe with sixteen distinct values, latched second pass for Solidisk, only banks the MOS found no ROM in (`&02A1`); take the four highest; a bank-number handover at `&0A00` survives BASIC exec, DFS loads and `VDU 22` but not a program unpacking over `&0400-&1BFF`; the IRQ fires with whatever the foreground has paged; bank code may call main RAM, main RAM may call a bank only with it paged.

### §6 MOS and DFS workspace

- Reclaim table for `&0100-&017F`, `&0400-&07FF`, `&0800-&0BFF`, `&0A00`, `&0C00`, `&0D00-&0D5F`, `&0D9F+`, `&0DF0`, `&0E00-&10FF`, `&1100-&18FF`, each with when it is yours and the trap.
- **The MOS plays your data as notes** if IRQ1V is handed back with a charset over `&0800`; `OSBYTE &D2` does not stop it; `OSBYTE &0F, X=0` before uninstalling does. The 100 Hz IRQ writes `&0800-&08FF` (a staged ZX0 stream was corrupted).
- `VDU 22` clears `&3000-&7FFF` and re-enables R8 and the cursor. OSFILE writes catalogue addresses back into its parameter block. Every `*LOAD` before taking IRQ1V. **The MOS's disc code needs VSync** (8271 status poll at `&ACAE` hung with R7 parked). DFS ROM is paged in at `&8000` during a filing-system call. DFS throughput ~0.07 s/sector + ~0.7 s spin-up (jsbeeb's disc model). OSFILE of 21K ≈ 130 fields. beebasm lays files in SAVE order. `!BOOT` EXEC stream feeds INKEY/OSRDCH. `*FX 4,1`, `*FX 229,1`. Seven-character filenames.

### §7 Keyboard internal key numbers

- Measured table for A-Z, `/`, `:`, cursor keys, SHIFT, CTRL, RETURN, SPACE, ESCAPE (jsbeeb Master 128, 2026-09-06; Paradroid's table agrees on every key). Method: `OSBYTE 121` from key 16; keys 0-2 via `INKEY`, internal = (-INKEY) - 1.
- `OSBYTE &7A` no-key return: NAUG says X = 0, jsbeeb's MOS returns `&FF`. Edge-triggered keys must not block waiting for release.

### §8 6502 cycles and timing constants

- `LDA abs,X` and `LDA zp,X` both 4c; `LDX zp,Y` is legal and cheaper than `LDX abs,Y`; IRQ latency swings by more than a few cycles; self-modified base addresses argue against unrolling.
- **One scanline = 128 CPU cycles** (64 µs); field = 39,936 cycles; MODE 1 display cycles 0-79, blanking 80-127; ~24 µs blanking window for a CRTC write; the two ruptures' T1 constants; phase must be taken from the emulator, not arithmetic.

### §9 ZX0 compression

- A stream may share memory with its output only while the reader stays ahead of the writer — track `max(write_index − bytes_consumed)`; a 20K screen cannot be unpacked in place from inside itself; compressed data does not compress again; compression roughly pays for a loading picture and no more on a 1770 DFS; ~40k cycles per 1K to unpack.

### §10 beebasm 1.11

- No `IFDEF`; symbol defined twice is an error; stderr for progress; `SAVE` without a working `-do` drops loose files; `CLEAR` releases the overwrite check, `GUARD` catches overrun; undefined symbol assembled absolute in pass 1; no `INCLUDE` inside `{}`; local label shadows a global silently; `SKIP` emits nothing; `ALIGN` pad economics; `INCLUDE`/`INCBIN` from the working directory; one 64K image; constants resolve in file order; `TIME$`; the symbol dump; proving a change mechanical.

### §11 Emulators

- **jsbeeb (MCP)**: RAM powers up zeroed; `cycles_run` is the requested count when a breakpoint fires (use `elapsed_cycles`); a run starting on a breakpoint returns `cycles_run` 0; snapshots stop mid-routine; screenshots crop to the content bounding box; `read_memory` returns the paged bank; boots an unpadded SSD; emulates the NuLA palette but not its scrolling/attribute modes; needs VSync for the 8271 poll; `frame_count` counts CRTC frames; `B-DFS1.2` has eight SWR banks; `read_sound_state` and SN76489 capture confirmed the 4 MHz clock.
- **b-em / b2**: b-em shows garbage below `&3000` with D set where jsbeeb displays it; b2 shows a misplaced field jsbeeb cannot; b-em caught a two-scanline error; b-em has not seen the Master mid-frame switch; only b2's debug build has an HTTP API (`doc/Debug-version.md`); b-em is launched as a Master with `-m3`.

### §12 Stated but not measured

- What `OSBYTE &81` masks; the SN76489 periodic-noise register path; the reverse transition out of a rupture; the Master mid-frame switch / wrap-in-bank / below-`&3000` on real hardware; DFS timings as jsbeeb's model; the keyboard phantom instrumented. Carried into the wiki as `(unverified — ...)` marks.

## Contradictions and corrections surfaced

Per the wiki's rule, existing text is **kept** and the measurement is added beside it with a dated "Flagged" note saying which is which.

- **[[techniques/smooth-vertical-scroll]]** says the addressable-latch setup is "bit 4 cleared, bit 5 set → 20K screen wraparound at `&4000`". The raw `smoothscroll.bas` (line 230, `LDX#4:STX&FE40:INX:STX&FE40`) writes `4` then `5` to `&FE40` — both lines *cleared* — and the measured table gives 0/0 → `&4000`, **16K** (a 20K screen wraps to `&3000`). Flagged beside the table; the demo's own `&4000/8` wraparound check is consistent with 16K.
- **[[techniques/vertical-rupture]]** annotates `LDA #12 : STA &FE40` as "clear bit 4" and `LDA #13` as "set bit 5". Both writes *set* their line (`(1 << 3) | 4`, `(1 << 3) | 5`); 1/1 is the 10K wrap to `&5800`, which is what the demo wants. The code is right; the comments are flagged beneath the listing.
- **[[os/keyboard]]** says `OSBYTE &7A` returns "0 if none"; NAUG (and this wiki's own [[sources/naug-ch14-keyboard]] for `&79`) say `&FF`, and jsbeeb's MOS returns `&FF` (Paradroid, 2026-08-26). Flagged: treat both as idle.
- **[[timing/via-timers]]** says the MOS uses System VIA T1 "every 20 ms". [[os/interrupts]] and [[os/sound]] on the same wiki say 100 Hz, and the measurement sides with them: T1 fires every 20,000 CPU cycles = 10 ms, exactly half a frame (Paradroid, 2026-08-26 — the near-constant `&FE44` seed). Flagged.
- **[[hardware/6502-addressing-modes]]** says `zp,X` is "cheaper than `abs,X` (saves 1c, 1 byte)"; its own cost table says both are 4c, and so do the cycle tables as Paradroid's RAM pass used them (2026-08-25): `abs,X` and `zp,X` are both 4. It saves a byte and the page-crossing risk, not a cycle. Flagged.
- **[[os/break-intercept]]** / **[[os/escape]]** call `*FX 200,1` the canonical game-launcher setting. It is — unless the program takes HAZEL, in which case BREAK must clear memory (`*FX 200,3`) or a soft BREAK leaves a machine with no DFS. Added as a caveat, not a reversal.
- **The port contradicts the wiki, and the wiki wins:** Edge Grinder's title-page write-up calls a `STA &FE21` a write "on the 1 MHz bus" and credits the phase-stability of a per-scanline loop to it. [[timing/cycle-stretching]] (from BeebWiki) has the Video ULA as a 2 MHz, unstretched device. The port's statement is a stated rationale — its pad constant was tuned by eye — not a measurement (§12 material), so the wiki's claim stands and the disagreement is recorded on [[hardware/video-ula]] and [[timing/cycle-stretching]] as something to measure directly.
- No measured fact contradicted the wiki's cycle counts, register bit assignments or addend table; the wrap table in [[hardware/system-via]] and [[hardware/address-translation]] agrees with the measurement bit for bit, and every internal key number in [[os/keyboard]]'s quick-reference table agrees with the measured table.

## Filed into

- [[hardware/crtc-6845-advanced]] — rupture write windows, R5 trap, R8/R6/R1 blanking, frame-shape switching
- [[hardware/crtc-6845]] — R6 = 0 leak, cursor under R8 blank
- [[techniques/vertical-rupture]] — measured rules for a two/three-cycle rupture; latch comment fix
- [[techniques/smooth-vertical-scroll]] — latch row fix
- [[hardware/address-translation]] — measured wrap table; single subtraction
- [[hardware/system-via]] — wrap table, VSync latency, keyboard/sound sharing, phantoms
- [[timing/via-timers]] — T1 vs T2 for rasters, seed and stopwatch traps; "every 20 ms" flagged
- [[timing/cycle-stretching]] — the `&FE21` / 1 MHz-bus disagreement recorded, wiki's claim kept
- [[timing/field-timing]] — **new**: scanline/field cycle constants, IRQ latency, the two ruptures' T1 constants
- [[hardware/video-ula]] — palette facts, mid-frame writes, VideoNuLA registers
- [[video/modes]] — MODE 1 / MODE 2 byte layouts as measured
- [[video/hardware-scrolling]] — ring model, R12/R13 half-update, window inside one wrap
- [[memory/shadow-ram]] — ACCCON D in-frame switch, wrap inside bank, below `&3000`, HAZEL rules
- [[memory/paged-rom]] — ANDY measured, Model B SWR probing, bank/IRQ/call rules
- [[memory/os-workspace]] — reclaimable workspace table, 100 Hz IRQ writes, handover byte
- [[os/keyboard]] — measured IKN table, `&7A` idle value, phantom keys, measuring method
- [[os/interrupts]] — taking IRQ1V outright, disc before IRQ1V, VSync needed by DFS
- [[os/filing-systems]] — OSFILE parameter-block write-back, HAZEL, DFS ROM at `&8000`, throughput, `!BOOT` EXEC stream
- [[os/break-intercept]] — HAZEL caveat on `*FX 200`
- [[os/escape]] — `*FX 229,1` when measuring keys
- [[os/sound]] — the MOS plays your data as notes; `OSBYTE &0F` flush
- [[os/vdu]] — `VDU 22` clears `&3000-&7FFF`, resets R8/R10
- [[hardware/sn76489]] — Port A sharing measured; capture confirms the 4 MHz clock
- [[hardware/6502-addressing-modes]] — `abs,X` = `zp,X` = 4c; `LDX zp,Y`
- [[techniques/zx0-loading]] — **new**: in-place unpacking rule, staging, what compression buys
- [[tools/beebasm]] — **new**: beebasm 1.11 gotchas
- [[tools/emulators]] — **new**: jsbeeb MCP, b-em, b2 behaviour as measured
- [[tools/basic-assembler]] — link to the new beebasm page
- [[hardware/master-overview]] — pointer to the measured Master facts
- [[index]]
- [[log]]

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
