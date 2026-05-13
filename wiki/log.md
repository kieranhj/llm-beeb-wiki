# Log

Append-only. Each entry starts with `## [YYYY-MM-DD] <op> | <title>` so it greps cleanly:

```
grep "^## \[" wiki/log.md | tail -10
```

---

## [2026-05-13] bootstrap | Wiki scaffolded
- Created: CLAUDE.md (schema), raw/{articles,manuals,notes,discord,assets}/, wiki/{hardware,memory,video,timing,os,techniques,tools,synthesis,sources}/, wiki/index.md, wiki/log.md
- Notes: BBC Micro performance wiki. Sources: web articles, PDF manuals, personal notes, Discord threads.

## [2026-05-13] ingest (index) | The New Advanced User Guide — book-level entry
- Created: wiki/sources/naug.md (master source page with full chapter TOC, citation convention, ingest plan)
- Updated: wiki/index.md (added Sources section)
- Source: raw/manuals/New_Advanced_User_Guide.pdf (458pp, OCR'd, Holmes & Dickens, Adder)
- Mode: chapter-by-chapter — no chapter content extracted yet. Per-chapter ingests will populate entity/concept pages and cite back via `[[sources/naug-ch<N>-<slug>]]`.
- Appendices A (OSBYTE) and B (OSWORD) queued for full-table extraction into `wiki/os/osbyte.md` and `wiki/os/osword.md`.
- Next: pick first chapter to ingest in depth.

## [2026-05-13] ingest | NAUG Ch5 — 6502 Instruction Set (p35-106)
- Created: wiki/sources/naug-ch05-6502-isa.md, wiki/hardware/6502.md, wiki/hardware/6502-isa.md
- Updated: wiki/sources/naug.md (Ch5 → [x]), wiki/index.md (Sources + Hardware)
- Key facts: cycle=0.5µs @ 2MHz / 0.33µs @ 3MHz / 0.25µs @ 4MHz. 65C12 adds (zp), BRA, STZ, INC/DEC A, PHX/PHY/PLX/PLY, TRB/TSB, JMP (abs,X), BIT extras. JMP (ind) bug-fixed on 65C12 (+1c). 65C12 BCD costs +1c. R65C02 BBR/BBS/RMB/SMB hand-assemble only.
- Open: NMOS BRK does NOT auto-clear D (handlers must); confirm whether all BBC NMOS chips are exactly "6502A" timing for RMW abs,X.

## [2026-05-13] ingest | NAUG Ch13 — Video/Graphics (p172-224)
- Created: wiki/sources/naug-ch13-video.md, wiki/hardware/crtc-6845.md, wiki/hardware/video-ula.md, wiki/video/modes.md, wiki/video/hardware-scrolling.md, wiki/techniques/fast-animation.md
- Updated: wiki/sources/naug.md (Ch13 → [x]), wiki/index.md (+Sources, +Hardware, +Video, +Techniques)
- Key facts: 6845 @ &FE00/&FE01, Video ULA @ &FE20/&FE21. R12/R13 = screen_addr DIV 8 (modes 0-6). MODE 7 correction: R12 = (hi - &74) EOR &20. Hardware wrap selected by 2 SystemVIA Port A bits. OSBYTE &9A/&9B for Tube-safe ULA writes (&9B XORs value with 7). Vsync 50Hz, OSBYTE &13 / *FX 19 to wait. MODE 2 layout: P2d/P1d/P2c/P1c/P2b/P1b/P2a/P1a — byte = 2 px = ideal sprite unit.
- Deferred: page-3 VDU workspace dense — file into [[memory/vdu-workspace]] after Ch12. PLOT number table summarised only; ECF detail skipped.

## [2026-05-13] ingest | NAUG Ch12 — Memory (p162-171)
- Created: wiki/sources/naug-ch12-memory.md, wiki/memory/memory-map.md, wiki/memory/paged-rom.md, wiki/memory/shadow-ram.md
- Updated: wiki/sources/naug.md (Ch12 → [x]), wiki/index.md (+Memory section)
- Key facts: paging reg &FE30 (low 4 bits ROM bank, bit 7 = ANDY on Master / paged RAM on B+); ACCCON &FE34 differs between B+ (S only) and Master (D/E/X/Y/ITU/IFJ/TST/IRR); shadow RAM is 20K at &3000-&7FFF B+/Master only; HAZEL = 8K at &C000-&DFFF on Master via Y bit; OSBYTE &44 tests SWR, &6C/&70/&71/&72 control Master shadow access for double-buffering.
- Warning recorded: never write &FE30 directly (MOS-managed); never run bank-switching code from the bank being switched.

## [2026-05-13] ingest | NAUG Ch22 — VIAs (p387-408)
- Created: wiki/sources/naug-ch22-vias.md, wiki/hardware/via-6522.md, wiki/hardware/system-via.md, wiki/hardware/user-via.md, wiki/timing/via-timers.md
- Updated: wiki/sources/naug.md (Ch22 → [x]), wiki/index.md (+Hardware, +Timing)
- Key facts: VIAs at &FE40 (System) and &FE60 (User). Timers decrement at 1MHz (NOT 2MHz CPU clock). T1 timeout = (N+2)*1µs. System VIA addressable latch (PB0-3) handles sound /WE, speech/CMOS, keyboard /WE, scroll-addend (B4/B5), CAPS/SHIFT LEDs. Vsync = CA1 (IFR bit 1), keyboard = CA2, ADC EOC = CB1, lightpen = CB2. IER write protocol: bit 7 = set/clear selector.
- Cross-link payoff: addressable latch B4/B5 = scroll wrap addend per mode (matches §13.3.10 wrap-around story).

## [2026-05-13] ingest | NAUG Ch8 — Interrupts (p131-142)
- Created: wiki/sources/naug-ch08-interrupts.md, wiki/os/interrupts.md, wiki/os/brk.md
- Updated: wiki/sources/naug.md (Ch8 → [x]), wiki/index.md (+OS/MOS section)
- Key facts: NMI @ &FFFA→&D00; IRQ/BRK @ &FFFE; BRKV @ &202; IRQ1V @ &204; IRQ2V @ &206. MOS poll order = 6850 → System VIA → User VIA. On entry to user handler, A is in &FC (NOT register). Vsync is CA1 (50Hz) — flash colour + RS423 timeout. 100Hz timer = System VIA T1 — drives TIME/sound/key/INKEY. IRQ masks: &E7 user VIA, &E8 6850, &E9 sys VIA, &CB Electron ULA. Hard rule: SEI window > 2ms = undefined behaviour. BRK = byte-after-BRK address in &FD/&FE; RTI skips error-number byte; NMOS does NOT auto-CLD (handler must).
- Cross-link payoff: confirms via-timers.md claim that System VIA T1 = 100Hz MOS sound; clarifies CA1 vs T1 (50/100Hz frequently confused).

## [2026-05-13] ingest | NAUG Ch3 + Ch4 — Arithmetic & Addressing Modes (p22-34)
- Created: wiki/sources/naug-ch03-04-arithmetic-addressing.md, wiki/hardware/6502-addressing-modes.md
- Updated: wiki/sources/naug.md (Ch3 + Ch4 → [x]), wiki/index.md, wiki/hardware/6502.md (JMP ind bug detail, D-flag discipline section), wiki/hardware/6502-isa.md (cross-link)
- Key facts: NMOS JMP (&xxFF) bug — high byte fetched from same page, not next; 65C12 fixes it (+1c). CLD before MOS calls is mandatory. 65C12 BCD = +1c (correct N/V/Z update). zp forward-reference assembler trap — define zp vars before the block. Page-cross penalty hits loads only; stores at worst case.

## [2026-05-13] ingest | NAUG Appendix A + B — OSBYTE / OSWORD directory (p443-448)
- Created: wiki/sources/naug-appendix-ab.md, wiki/os/osbyte.md, wiki/os/osword.md
- Updated: wiki/sources/naug.md (App A + B → [x]), wiki/index.md
- Approach: appendices are directory only — semantics come from referenced chapters. Each OSBYTE/OSWORD entry links to its source-page if chapter already ingested; otherwise lists (ChNN, pending).
- Already-linked: most Ch12 memory + Ch13 video + Ch8 interrupts OSBYTEs are now actively cross-referenced from os/osbyte.md.

## [2026-05-13] ingest | NAUG Ch6 — OS Introduction (p107-125)
- Created: wiki/sources/naug-ch06-os-introduction.md, wiki/memory/zero-page.md, wiki/memory/os-workspace.md, wiki/os/calls.md
- Updated: wiki/sources/naug.md (Ch6 → [x]), wiki/index.md (+memory entries, +os/calls)
- Key facts: full OS vector + entry-point table at &FF**/&20*. User zp = &70-&8F (32 bytes). VDU zp = &D0-&E1. IRQ A-save = &FC. OSBYTE/OSWORD A/X/Y stashed at &EF/&F0/&F1 during call. OSHWM via OSBYTE &83/&B3/&B4. Unknown OSBYTE → ROM service call &07; unknown OSWORD → service &08 (or USERV for &E0-&FF).
- Closes the [[memory/vdu-workspace]] stub left by Ch13; replaces it with the consolidated [[memory/os-workspace]] page covering pages 1/2/3/8/9/B/C/D.
- Performance angle (per feedback memory): zero-page and os-workspace pages lead with "claim more zp / bypass MOS" patterns; OS-calls page documents NVWRCH/NVRDCH non-vectored variants and pre-render-strings as faster than OSWRCH.

## [2026-05-13] ingest | NAUG Ch17 — Paged ROMs (p290-333)
- Created: wiki/sources/naug-ch17-paged-roms.md, wiki/os/paged-roms.md, wiki/os/service-calls.md
- Updated: wiki/sources/naug.md (Ch17 → [x]), wiki/index.md, wiki/memory/paged-rom.md (added safe-call mechanisms section pointing to new pages)
- Key facts: ROM header = 16+t+v+c bytes; offset 0 = JMP lang_entry, offset 3 = JMP service_entry; type byte at offset 6 (bit 7=service, bit 6=language). MOS scans ROMs slot 15→0 priority on service call. Three safe ways to call cross-ROM: OSRDRM (one byte), OSBYTE &8F (issue service call), extended vectors (permanent intercept at &200+2n → &FF00+3n stub → extvec table). 100Hz polling = service call &15, gated by semaphore (OSBYTE &16/&17/&B9). OSBYTE &A4 verifies a ROM image. *FX 142 (OSBYTE &8E) enters a language ROM.
- Closes the [[sources/naug-ch17-paged-roms]] stubs scattered across hardware/system-via, memory/paged-rom, os/osbyte. OSBYTEs &8E/&8F/&A4/&A8-&AB/&BA/&BB/&FC now have detailed source pages.

## [2026-05-13] lint | wiki health check + corrections
- Stale links fixed:
  - [[memory/vdu-workspace]] → [[memory/os-workspace]] in sources/naug-ch06-os-introduction.md, sources/naug-ch13-video.md, video/hardware-scrolling.md, memory/memory-map.md
  - [[sources/naug-ch17]] → [[sources/naug-ch17-paged-roms]] in os/interrupts.md
  - [[sources/naug-ch04]] → [[sources/naug-ch03-04-arithmetic-addressing]] in sources/naug-ch05-6502-isa.md
- Cleanup: removed self-correcting prose in memory/os-workspace.md (page 1 section had wrong table + apology; now correctly describes page 1 as stack-only, with pages 8-9 buffers detailed below).
- Anchors: simplified "## Summary (NAUG §5.2 p38)" → "## Summary" and "## R65C02-only quick reference" → "## R65C02-only" in hardware/6502-isa.md so wikilink anchors `#summary` and `#r65c02-only` resolve cleanly.
- Closed open follow-up: naug-ch05-6502-isa.md page-crossing-on-stores question now resolved (documented in 6502-addressing-modes.md).
- **Substantive bug fix**: MODE 1/5 pixel layout in video/modes.md was wrong — I claimed "two pixels per byte" but MODE 1/5 are 4 bpp packing 4 pixels per byte. Rewrote with correct `[M0 M1 M2 M3 L0 L1 L2 L3]` interleaved layout, single-pixel mask table, and a derivation note from Video ULA serialiser behaviour (NAUG §13.3.13). Also fixed swapped MODE 1/MODE 2 pixels-per-byte-step values in the "6845 chars" section.
- No orphans found. No contradictions found across high-risk shared facts (ACCCON, vsync vs T1, JMP (ind), 65C12 deltas).
- Stubs intentionally left: hardware/crtc-6845-advanced, techniques/raster-splits, techniques/pixel-plot, techniques/exploding-font, video/palette.

## [2026-05-13] synthesis | custom screen mode design (288×192 4-colour)
- Query: "how do I set up a 288×192 4-colour custom mode, list all registers and gotchas".
- Synthesised from: hardware/crtc-6845, hardware/video-ula, hardware/system-via, video/modes, video/hardware-scrolling, memory/os-workspace, memory/shadow-ram, os/interrupts, techniques/fast-animation. All facts recoverable from the wiki — no gaps.
- Filed back: wiki/techniques/custom-modes.md (general recipe scaffold, MOS-bypass-leaning per feedback). Worked-example synthesis page deferred.
- Updated: wiki/index.md (+techniques/custom-modes).

## [2026-05-13] ingest | NAUG Ch7 + Ch9 + Ch21 — Events, Buffers, Sound
- Created: wiki/sources/naug-ch07-events.md, wiki/sources/naug-ch09-buffers.md, wiki/sources/naug-ch21-sound.md, wiki/os/events.md, wiki/os/buffers.md, wiki/os/sound.md, wiki/hardware/sn76489.md
- Updated: wiki/sources/naug.md (Ch7, Ch9, Ch21 → [x]), wiki/index.md (+sources +Hardware/sn76489 +OS/{events,buffers,sound})
- Key facts:
  - EVNTV at &220. 10 event types (0=o/p buf empty, 1=i/p buf full, 2=char in, 3=ADC done, 4=vsync, 5=interval timer 0, 6=ESCAPE, 7=RS423 err, 8=Econet, 9=user). OSBYTE &0E/&0D enable/disable, OSEVEN @ &FFBF to fire user events.
  - 9 buffer IDs (0=kbd, 1/2=RS423 i/o, 3=printer, 4-7=sound chans, 8=speech). Vectors INSV/REMV/CNPV at &22A/&22C/&22E. OSBYTE &0F flush class, &15 flush specific, &80 read status (X = &FF-id, collides with ADC read), &8A insert, &91 get, &98 examine, &99 insert into input.
  - SN76489: 3 tone + 1 noise, mixed on chip, on System VIA slow bus driven by addressable latch line 0. Frequency = 125000/N Hz (10-bit N). Volume 0-15 inverted (0=max). Latch byte = `1 R2 R1 R0 d3 d2 d1 d0`, data byte = `0 X F9..F4`. Direct write = SEI + DDRA=&FF + STA &FE41 + pulse line 0 low 8µs+ + CLI.
  - OSWORD &07 SOUND (8-byte block, channel/amp/pitch/dur each 16-bit). OSWORD &08 ENVELOPE (14 bytes). 100Hz IRQ drives buffers→chip. Latency ≤10ms — bypass for sub-frame timing.
- Cross-links payoff: System VIA addressable-latch line 0 (already documented) now connects to sn76489 direct-write dance. Buffer events (0/1/2) connect to events page. 100Hz T1 attribution (via-timers + interrupts) now confirmed as the sound-service driver.

## [2026-05-13] ingest | NAUG Ch11 + Ch14 + Ch18 — Hardware overview, Keyboard, Tube
- Created: wiki/sources/naug-ch{11-hardware,14-keyboard,18-tube}.md, wiki/os/keyboard.md, wiki/os/tube.md, wiki/hardware/tube-ula.md
- Updated: wiki/sources/naug.md (Ch11, Ch14, Ch18 → [x]); wiki/memory/memory-map.md (SHEILA table fleshed out with Electron ULA, INTOFF/INTON, FDC ranges, Master FDC at &FE24/&FE28, Econet station at &FE18); wiki/index.md.
- Key facts:
  - Ch11 confirmed the SHEILA table; Electron-only additions at &FE00-&FE0F (ULA) and &FE18-&FE1A (ADC); B+/Master INTOFF &FE38, INTON &FE3C.
  - Ch14 three key-numbering schemes: ASCII (OSRDCH), INKEY negative (OSBYTE &81 scan), IKN (OSBYTE &78/&79/&7A). INKEY = IKN EOR &FF. Model B &79 scans non-ascending; others scan ascending. BREAK wired direct to 6502 reset, not in matrix.
  - Ch18 Tube ULA: 4 register pairs on host &FEE0-&FEE7, parasite &FEF8-&FEFF. R3 FIFO for bulk. R1=OSWRCH/events/ESCAPE, R2=other OS calls, R3=data transfer, R4=control. &406 entry: claim/release with reason &C0/&80 + caller_id. Bulk transfer reasons 0-7 (single byte, byte pairs, 256-byte blocks, execute) with per-transfer init + per-byte delays. Parasite OS dispatch is round-trip — OSWRCH from parasite ~10× slower. Tube auto-explodes fonts on host (OSHWM bumps by &600).
- Cross-link payoff: Tube docs now reference ACCCON ITU bit on Master (already in shadow-ram.md). NVWRCH/NVRDCH non-vectored variants in os/calls.md now have an explicit "skip Tube" use case. Keyboard ties into System VIA CA2 IRQ + slow-bus addressable-latch line 3.

## [2026-05-13] synthesis | "MODE 8" — 16-colour LF mode (80×256 in 10 KB)
- Query: "how would I set up a 16-colour low-frequency 'MODE 8'?"
- Filed: wiki/synthesis/mode-8-16colour-lf.md
- Updated: wiki/index.md (+Synthesis section)
- Key insight: bpp = R1 ÷ ULA-displayed-chars. MODE 5 (R1=40, chars=20) → bpp=2. To reach bpp=4 (16-colour) on MODE 5's RAM, halve ULA chars to 10 (bits 2-3 = `00`). Resulting ULA value `&E0`.
- Cross-link payoff: confirms the bpp-from-ratio derivation already implicit in hardware/video-ula.md's expanded per-mode table.
- Caveat noted: bpp-from-ratio rule derivable but not explicitly stated in NAUG; worth real-hardware verification.

## [2026-05-13] ingest | NAUG Ch23 + Ch16 — 1MHz bus + Filing systems
- Created: wiki/sources/naug-ch23-1mhz-bus.md, wiki/sources/naug-ch16-filing.md, wiki/hardware/1mhz-bus.md, wiki/hardware/wd1770.md, wiki/os/filing-systems.md
- Updated: wiki/sources/naug.md (Ch16, Ch23 → [x]), wiki/index.md (+sources, +hardware/{1mhz-bus,wd1770}, +os/filing-systems)
- Key facts:
  - 1MHz bus: FRED at &FC, JIM at &FD (256-byte paged via &FCFF). CPU 2MHz stretched to 1MHz on &FC/&FD access. Two glitch problems (P/Q decoding + double-access) addressed by NOR-RS-latch or D-FF clean-up circuits. OSBYTE &92-&97 = Tube-safe FRED/JIM/SHEILA access. OSBYTE &6B selects 1MHz bus (X=0) or 2MHz Master cartridge (X=1).
  - Filing systems: 7 standard (CFS, RFS, DFS, NFS, Telesoft, IEEE, ADFS) + Master FS-handler. Vectors at &212-&21E. OSFILE actions 0-7, 255. OSFIND modes 0/64/128/192. OSARGS for pointer/length/flush. OSGBPB for bulk transfer + directory listing.
  - WD1770 FDC: regs at &FE28-&FE2B (Master) / &FE84-&FE87 (B+). Drive ctrl at &FE24 / &FE80. NMI per byte during sector R/W; handler must service in 32µs (DD) / 64µs (SD). Command types I-IV. Don't poll status — it can clear pending NMI.
- Bypass-MOS paths now documented: OSWORD &7F (DFS direct FDC command) → faster than OSGBPB for sector-level access; direct 1770 + own NMI handler for maximum control.
- Cross-link payoff: 1MHz bus connects to memory/memory-map.md FRED/JIM/SHEILA + memory/shadow-ram.md ACCCON IFJ + os/osbyte.md &6B/&92-&97. WD1770 connects to os/interrupts.md NMI handling + os/paged-roms.md NMI claim/release service calls.

## [2026-05-13] lint | post-Ch16/Ch23 wiki health check
- Fixed: `[[memory/vdu-workspace]]` brackets → backticks in sources/naug-ch06-os-introduction.md line 15 (last stale ref).
- Fixed: os/buffers.md storage range — was claiming `&800-&9BF`, now correctly spans `&800-&9FF` with sub-range breakdown.
- Removed `[[video/palette]]` stub link from hardware/video-ula.md — content was always on that page; replaced with reference to planned [[techniques/raster-splits]].
- No contradictions found across high-risk shared facts (ACCCON, Tube ULA addrs, WD1770 addrs, addressable-latch lines, 100Hz/50Hz attribution, NMI &D00, R3 sync widths, MODE 1/5 pixel layout).
- No orphans.
- Remaining intentional stubs: crtc-6845-advanced, techniques/{raster-splits,exploding-font,pixel-plot}, video/teletext-mode, os/z80-2p, synthesis/custom-mode-288x192. All "planned" or conditional.

## [2026-05-13] ingest | NAUG Ch2 + Ch10 + Ch15 — BASIC assembler, Escape, Serial
- Created: wiki/sources/naug-ch{02-basic-assembler,10-escape,15-serial}.md, wiki/tools/basic-assembler.md, wiki/os/escape.md, wiki/hardware/6850-acia.md, wiki/hardware/serial-ula.md, wiki/os/serial.md
- Updated: wiki/sources/naug.md (Ch2/10/15 → [x]), wiki/index.md (+sources, +hardware {6850,serial-ula}, +os {escape,serial}, +tools section now has basic-assembler)
- Key facts:
  - Ch2: OPT bits 0=listing, 1=errors, 2=remote-assembly (L2 only). Two-pass FOR loop pattern (pass 0 silent, pass 3 listing+errors). EQU{B,W,D,S} for inline data. CALL register passing via A%/X%/Y%/C%. User zp `&70-&8F`.
  - Ch10: ESCAPE = system condition. OSBYTE `&7C` clear, `&7D` set, `&7E` clear+effects. `&C8` packs ESCAPE-disable (bit 0) + BREAK-clears-memory (bits 1-7). `&DC` remaps ESCAPE char. `&E5` treats ESCAPE as ASCII. `&E6` suppresses `&7E` side-effects.
  - Ch15: 5-pin DIN pinout (GND/CTS/TD/RD/RTS). 6850 ACIA at &FE08-&FE09 + status/ctrl/rx/tx. Serial ULA at &FE10 (write-only), bits = motor/RS423-vs-cass/rx-baud/tx-baud. Baud codes 0-8 = 9600/75/150/300/1200/2400/4800/9600/19200. OSBYTEs `&07`/`&08` baud, `&9C` 6850 ctrl, `&B5` RS423 mode, `&CB` handshake threshold, `&CD` RS423/cass select, `&F2` ULA shadow read.
- Cross-link payoff: ESCAPE event 6 (already in os/events.md) now has detailed handler page. BASIC assembler reference fills the "code examples target what dialect" gap that prior pages implicitly relied on. 6850 IRQ dispatch (already documented in os/interrupts.md as first in MOS chain) now has full chip-level register reference.

## [2026-05-13] lint | YAML & in frontmatter (hardware pages)
- Fixed: 8 hardware pages had `sheila: [&FExx, &FEyy]` which YAML parses as malformed named anchors. Quoted to `["&FExx", "&FEyy"]`. Affected: 6850-acia, crtc-6845, serial-ula, system-via, tube-ula, user-via, video-ula, wd1770.
- Memory: feedback_yaml_ampersand_quoting.md saved so future ingests use the quoted form by default.

## [2026-05-13] ingest | NAUG Ch19 + Ch20 + Ch24 — Clocks/CMOS, ADC, Misc/BREAK
- Created: wiki/sources/naug-ch{19-clocks-cmos,20-adc,24-misc}.md, wiki/os/{clocks,adc,break-intercept,printer}.md, wiki/hardware/{cmos-rtc,upd7002-adc}.md
- Updated: wiki/sources/naug.md (Ch19/20/24 → [x]), wiki/index.md (+all new pages)
- **NAUG ingest now COMPLETE** (23 of 24 chapters + appendices A/B). Only Ch1 (beginner intro) intentionally skipped.
- Key facts:
  - Ch19: system clock + interval timer = 5-byte LSB-first values, dual-copy atomicity via OSBYTE `&F3`. OSWORD `&01-&04`. Master 146818 RTC at slow-bus: register A (UIP+rate), B (IRQ enables), C (flags read-once-clear), D (VRT). Alarm IRQs need link LK4 closed. 50 bytes CMOS RAM at addrs 14-63, MOS-allocated mostly through addr 45; user-safe at 46-49.
  - Ch20: µPD7002 ADC at &FEC0 (B/B+) or &FE18 (Master). 12-bit ~10ms, 8-bit ~4ms. Result left-justified in 16-bit ADVAL. OSBYTE `&80 X=0` returns last channel + fire bits (active-low). EOC IRQ on System VIA CB1. Master Compact: switches not analogue, `OSBYTE &BE` configures simulator.
  - Ch24: **BREAK intercept** via OSBYTE `&F7-&F9` JMP-installed at fixed 3-byte slot. Called twice per BREAK (C=0 pre-message, C=1 post-message). `OSBYTE &FD` returns last reset type (0/1/2). `OSBYTE &FF` startup options (MODE, NFS/DFS, drive timings). `OSBYTE &00`/`&81` machine + OS identification. `*CODE`/`*LINE` route through USERV (`&200`). UPTV (`&222`) for printer drivers.
- Cross-link payoff:
  - The BREAK-intercept stub referenced from custom-modes, paged-roms, many other pages — now resolved with os/break-intercept.md.
  - ADC EOC IRQ in os/interrupts (System VIA dispatch chain) — now has the chip-side detail.
  - Master RTC alarm IRQ joins the list of "advanced MOS-bypass timer sources" alongside via-timers.md.
- YAML convention applied correctly this batch: upd7002-adc.md uses `sheila: ["&FEC0", "&FEDF"]`; cmos-rtc.md has no `sheila` field (accessed via slow-bus through System VIA, not memory-mapped directly).

## [2026-05-13] lint | post-Ch19/20/24 wiki health check
- Fixed: os/adc.md said fire button bits return in A; corrected to X (OSBYTE preserves A; channel + fire bits share the same X byte). Added explicit masking notes (X AND &03 for fire, X AND &FC for channel).
- Fixed: os/adc.md Master Compact pin labels disambiguated to "User VIA PB0-PB4" (the System VIA also has PB pins, and bare "PB0" was ambiguous).
- Fixed: os/adc.md direct fire-button read claim downgraded — the IRA-vs-IRB read behaviour for input pins on the 6522 needs real-hardware verification. Replaced confident "LDA &FE40 + AND &30" example with a warning that points to via-6522.md and notes MOS uses the slow-bus protocol.
- No contradictions found in other high-risk checks (ADC EOC, BREAK reset types, buffer storage range, OSBYTE &80 ID-inversion).
- No orphans; smallest leaf pages (mode-8 synthesis, break-intercept, printer, 1mhz-bus) all healthy.
- Open question: 6522 IRB-vs-pin-read behaviour for input-mode pins. Worth verifying against W65C22 datasheet + Acorn MOS disassembly.
- Stubs still planned: techniques/{raster-splits, exploding-font, pixel-plot}, hardware/crtc-6845-advanced, video/teletext-mode, tools/beebasm, os/z80-2p, synthesis/custom-mode-288x192. `raster-splits` and `crtc-6845-advanced` have the most inbound refs (3 each) — write next when those topics come up.
