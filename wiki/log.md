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
- Mode: chapter-by-chapter — no chapter content extracted yet. Per-chapter ingests will populate entity/concept pages and cite back via [[sources/naug-ch<N>-<slug>]].
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
- Fixed: [[memory/vdu-workspace]] brackets → backticks in sources/naug-ch06-os-introduction.md line 15 (last stale ref).
- Fixed: os/buffers.md storage range — was claiming `&800-&9BF`, now correctly spans `&800-&9FF` with sub-range breakdown.
- Removed [[video/palette]] stub link from hardware/video-ula.md — content was always on that page; replaced with reference to planned [[techniques/raster-splits]].
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

## [2026-05-14] ingest | AllMem.txt — Ripley/Harston BBC System Memory Map (18-Jun-2016)
- Created: wiki/sources/allmem-ripley-harston.md
- Reference-only ingest: byte-level catalogue of MOS workspace across BBC/Electron/Master variants. Most precise source we have for "what owns this byte?"
- Cross-referenced against: wiki/memory/zero-page.md, wiki/memory/os-workspace.md, wiki/memory/memory-map.md, wiki/os/buffers.md
- **Contradictions surfaced** (NOT auto-fixed; awaiting user approval):
  1. zero-page.md VDU table lists `&CB-&CE` as "Graphics character-cell address" and `&DD-&E0` as "Text character-cell address". Per AllMem these are filing-system workspace (&CB-&CE) and general OS workspace (&DD-&DF) — they are NOT VDU. Graphics character cell is `&D6-&D7`; top scan line `&D8-&D9`.
  2. zero-page.md "Critical OS" row for `&FD-&FE` says "Address after last BRK (post-BRK return pointer)". AllMem more accurate: "Error message pointer, initially set to language version string". Same physical content, but the wiki phrasing is misleading.
  3. os-workspace.md "Useful direct reads" table — ALL FOUR addresses wrong:
     - "&242 Output stream destination" → correct is `&27C` (`&242` is fx178 Keyboard semaphore).
     - "&269 Active ROM at last BRK" → correct is `&24A` (`&269` is fx217 Screen-lines-since-last-page).
     - "&27D Sound suppression" → correct is `&262` (`&27D` is fx237 Cursor-key status).
     - "&27E Speech suppression" → correct is `&261` (`&27E` is fx238 unused/keypad-base).
  4. os-workspace.md Page-3 row "&349-&34D cursor internal coords" conflates three entries: per AllMem, `&324-&327` is graphics cursor internal coords; `&34A-&34B` is text cursor address for 6845; `&34C-&34D` is text window width in bytes.
  5. os-workspace.md Page-8 row "`&880-&8BF` Printer buffer (alt usage of part of sound area)" — wrong. Per AllMem the printer buffer is distinct from the sound area: sound channels live at `&840-&87F`, printer at `&880-&8BF`, envelopes at `&8C0-&8FF`. Not alternate uses.
- Open question: should we expand zero-page.md `&EE` entry to note dual purpose (1MHz paging copy + OSBYTE-&79 key-ignore)? AllMem documents both.
- AllMem deserves to be cited from at least: memory/zero-page, memory/os-workspace, memory/memory-map, memory/paged-rom (DF0-DFF), os/calls (FF jumpblock), os/buffers (page 8-9 layout). Cite-list update pending fixes.

## [2026-05-14] fix | apply AllMem cross-reference fixes
- Updated: wiki/memory/zero-page.md — VDU table corrected (removed wrong &CB-&CE and &DD-&E0 rows; added &D6-&D7 graphics char cell, &D8-&D9 top scan line, &DA-&DF temp); critical OS table fixed (&FD-&FE = error message pointer, not "post-BRK return"); &EE expanded to dual purpose (1MHz paging copy + OSBYTE-&79 key-ignore); added &F8-&F9, &FA-&FB rows.
- Updated: wiki/memory/os-workspace.md — "Useful direct reads" all four wrong addresses corrected (&27C/&24A/&262/&261), added formula `&236 + (osbyte_num - &A6)`; Page-3 cursor row split into 6 correct entries; Page 8-9 buffer rows clarified (printer is distinct from sound).
- Updated frontmatter sources to cite allmem-ripley-harston: zero-page.md, os-workspace.md, memory-map.md.

## [2026-05-14] ingest | BeebWiki Hardware section: Address translation, CRTC, Video ULA
- Created sources: wiki/sources/beebwiki-address-translation.md, wiki/sources/beebwiki-crtc.md, wiki/sources/beebwiki-video-ula.md
- Created entity: wiki/hardware/address-translation.md (NEW page — wraparound mechanism finally explained: IC 32 latch C0/C1 → IC 39 quad adder, subtract amounts &4000/&2000/&5000/&2800 for MODES 3/6/0-2/4-5; MODE 7 phys = ((MA & 0x800) << 3) | 0x3C00 | (MA & 0x3FF); per-mode DRAM refresh intervals; MODE 7 MA6 ⊕ ~1MHz refresh trick).
- Updated: wiki/hardware/crtc-6845.md — fixed R10 BLK encoding (4-state field 00=off, 01=steady, 10=slow, 11=fast — old version misdescribed bit 6 / bit 5 split); added MODE 7 R12/R13 XOR &54 quirk with `(high - &74) EOR &20` formula; added 6845S variant section; cited beebwiki-crtc.
- Updated: wiki/hardware/video-ula.md — added MOS shadow addresses (&248 / &249); added clock-divider output pin reference (8/4/2/1 MHz on pins 7/6/5/4); added shift-register clock-rate-per-MODE table; documented 80@1MHz / 10@2MHz undefined behaviour; added default palette write-sequence tables for MODE groups; added hardware history (Ferranti, VLSI, VideoNuLA); cited beebwiki-video-ula.
- Updated: wiki/video/hardware-scrolling.md — replaced hand-wavy "adds an offset" with the real subtract amounts and pointer to address-translation.
- Updated: wiki/index.md (3 new sources, 1 new hardware entity).
- Contradiction logged but not "fixed": BeebWiki CRTC R0=127 across all modes is wrong; NAUG (and our existing table) correctly shows R0=63 for MODES 4-7. Source page documents the discrepancy.

## [2026-05-14] ingest | BeebWiki: ANDY + Cycle stretching
- Created sources: wiki/sources/beebwiki-andy.md, wiki/sources/beebwiki-cycle-stretching.md
- Created entity: wiki/timing/cycle-stretching.md (NEW page — first system-wide treatment of which SHEILA addresses pay the 1MHz penalty; documents 2c/3c variable cost depending on phase; lists what is NOT stretched: Video ULA, Tube, FDC, ROMSEL/ACCCON; phase-aligning trick via dummy stretched read).
- Updated: wiki/memory/paged-rom.md — added ANDY-access section (OSWORD &05/&06 with &FFFExxxx form, B+ &A000-&AFFF shadow-display window trick, MOS won't scan ANDY for languages); cited beebwiki-andy.
- Updated: wiki/hardware/1mhz-bus.md — corrected "2 cycles" to "1-2 extra cycles (variable)"; added cross-link to timing/cycle-stretching; clarified the same mechanism applies to most SHEILA peripherals; cited beebwiki-cycle-stretching.
- Updated: wiki/index.md — added 2 new sources, 1 new timing page.
- Headline new fact for performance code: every CRTC, ACIA, Serial ULA, VIA, ADC access pays the 1MHz stretch (5-6c instead of 4c). Video ULA writes (&FE20/&FE21) and Tube writes (&FEE0+) do NOT — preferred for tight raster work.

## [2026-05-14] lint | post-BeebWiki ingest health check & fixes
- Fixed: wiki/hardware/1mhz-bus.md — corrected stale "8 cycles per LDA abs / factor 2" to actual 5-6c per cycle-stretching page.
- Fixed: wiki/memory/memory-map.md — Master ANDY was wrongly attributed to ACCCON; it's ROMSEL bit 7 (consistent with paged-rom.md and beebwiki-andy).
- Fixed: broken link [[synthesis/mode-8]] → [[synthesis/mode-8-16colour-lf]] in wiki/sources/beebwiki-video-ula.md.
- Fixed: orphan wiki/synthesis/mode-8-16colour-lf.md — added inbound refs from wiki/techniques/custom-modes.md and wiki/hardware/video-ula.md.
- No-action items: BeebWiki R0=127 row stays a flagged discrepancy in source page only (ours matches NAUG and is correct); known stubs (raster-splits, crtc-6845-advanced, etc.) untouched; code-block dialect annotations all correct on spot-check.
- Suggested next sources to seek (likely on bitshifters/bbc-documents):
  - Master Reference Manual — for definitive ACCCON / ANDY / HAZEL paging confirmation.
  - Acorn Service Manual — for cycle-stretching IC schematics (IC 23 / IC 33) and address-translator IC numbering.
- Suggested next page-write candidate: `techniques/raster-splits` (5 inbound refs, well-supported by new cycle-stretching + via-timers pages).

## [2026-05-14] ingest | Hitachi HD6845R/HD6845S datasheet (raw/manuals/hd6845sp.pdf)
- Source: replaced unreadable raw/manuals/6845.pdf with text-searchable hd6845sp.pdf (482KB) from bitshifters/bbc-documents/ICs/6845 CRTC. Deleted two image-only duplicates.
- Created: wiki/sources/hd6845sp-hitachi-datasheet.md (primary chip reference).
- Created: wiki/hardware/crtc-6845-advanced.md — closes the long-planned stub. Body = full anomalous-rewrite table (R12/R13 sampled in last raster period of field, R8 dynamic rewrite prohibited, R0/R2/R7/R9 NG, R1/R6 OK, others conditional) + raster-split primitives + field-timing reference.
- Updated: wiki/hardware/crtc-6845.md:
  - **R10 BLK encoding CORRECTED** (was wrong since BeebWiki adoption two commits ago). Authoritative per datasheet Table 7: BP=00=non-blink(steady-on), BP=01=non-display(off), BP=10=16-field period (~3 Hz, FASTER), BP=11=32-field period (~1.5 Hz, slower). MOS default BP=10 → R10=&47 in graphics, =&52 in MODE 7 — matches BBC's visible flashing underline cursor.
  - Added: R9 takes Nr-2 in Interlace Sync & Video mode (MODE 7), not Nr-1.
  - Added: full HD6845S vs HD6845R differences section (6 features).
  - Added: Programming Restrictions section (inequalities, R0-even-in-interlace caveat, HSW=0 prohibited).
  - Added: Reset behaviour (first field anomaly — R12/R13 ignored on field 0).
  - Refined: Register Latching section now correctly notes per-register behaviour and points at the advanced page.
- Updated: wiki/index.md (1 new hardware entity + 1 new source).
- Headline contradiction (logged on source page): BeebWiki R10 BLK encoding is wrong on both 00/01 (swapped) and 10/11 (slow/fast labels inverted). Datasheet is primary; BeebWiki entry contradicts both datasheet and observable BBC behaviour. User verified empirically (all modes default to flashing underline cursor).

## [2026-05-14] ingest | SAA5050 — combined references (chip datasheet image-only)
- Downloaded raw/manuals/SAA5050.pdf (3.3MB) from bitshifters/bbc-documents/ICs/SAA5050 — image-only, not text-extractable. Stardot mirror also image-only. vd-view down, datasheetcatalog unreachable.
- No BeebWiki SAA5050 page exists.
- Substituted four text-bearing sources: Wikipedia Mullard_SAA5050, HandWiki Engineering:Mullard_SAA5050, mdfs.net Teletext Controls (J.G. Harston), Hoglet67 BeebFpga saa5050.vhd.
- Created: wiki/sources/saa5050-references.md (consolidated reference page with TODO to revisit when datasheet is OCR'd).
- Created: wiki/hardware/saa5050.md (new entity page) — 12×20 character cell on 5×9 ROM grid with diagonal smoothing, full &80-&9F control code table, set-after vs set-at semantics, hold-graphics bug, double-height pair rule, MODE 7 BBC integration details.
- Updated 5 pages with [[hardware/saa5050]] inbound links: crtc-6845, crtc-6845-advanced, video-ula, address-translation, video/modes.
- Updated: wiki/index.md (1 new hardware entity + 1 new source).
- Key new facts captured:
  - Control codes are stored with bit 7 set in BBC MODE 7 screen RAM (&80-&9F = teletext codes &00-&1F).
  - Set-after codes (most) occupy a cell as background-coloured space; set-at codes (Conceal, Hold Graphics, Steady, Black BG, New BG) affect the current cell too.
  - "Hold graphics bug": control codes inside hold-graphics state (except &9E itself) clear the held character.
  - Double-height pair rule: second-row character without &8D becomes invisible.
  - Flash rate ~0.78 Hz, 3:1 duty cycle, chip-internal counter reset by DEW each field.
  - No black text in practice (alpha-black control writes black-on-black space).

## [2026-05-14] fix | SAA5050 page — &3C00 alt address mischaracterised
- Fixed: wiki/hardware/saa5050.md — the &3C00 alternate MODE 7 screen RAM address is **not** "shadow" and exists only on the BBC Model B / B+ (Model A also has it via the same address translator). The dual-block addressing is a quirk of the discrete-logic address translator's MODE 7 path (MA11 selects top bit), not shadow RAM. Master's memory-management ULA does NOT replicate this quirk — MODE 7 lives at &7C00 only; shadow MODE 7 on Master uses ACCCON D/E/X bits to swap which physical bank &7C00 maps to. Electron has no quirk at all (MODE 7 is software-emulated).

## [2026-05-16] ingest | Retrosoftware — "How to do the smooth vertical scrolling" (Talbot-Watkins, 2008)
- Source: http://www.retrosoftware.co.uk/wiki/index.php/How_to_do_the_smooth_vertical_scrolling
- Archived: raw/articles/retrosoftware-smooth-vscroll.md
- Source code (user-supplied): raw/code/vrupt.6502 (BeebASM rupture demo, jbnbeeb 2015 rework) + raw/code/smoothscroll.bas (Talbot-Watkins original).
- Created: wiki/sources/retrosoftware-smooth-vscroll.md (full claim list + register table from smoothscroll.bas).
- Created: wiki/techniques/vertical-rupture.md (foundational split-screen technique — worked MODE 2 example with full IRQ + timer code, row-budget table, R7-NG-rewrite caveat).
- Created: wiki/techniques/smooth-vertical-scroll.md (R5 two-cycle trick for 1-scanline vertical motion — frame anatomy, walk-through of smoothscroll.bas, screen-on timer compensator).
- Updated: wiki/index.md (1 new source, 2 new techniques).
- Updated: wiki/video/hardware-scrolling.md — softened "sub-row not possible" claim and linked to smooth-scroll.
- Key new facts captured:
  - R4/R6/R7 are read fresh each CRTC cycle (not pre-latched), enabling mid-frame rewrites.
  - R7 mid-frame rewrites work in practice despite Hitachi's NG verdict, because writes settle during the *previous* cycle.
  - Total PAL scanlines invariant: Σ(R4+1)(R9+1) + ΣR5 = 312.
  - Two-cycle R5 split: R5_A = 8-line, R5_B = line.
  - VSync IRQ fires after VSync pulse width (default 2 scanlines), affecting timer compensator.
  - Status panel in second cycle = structural; provides timing tolerance for the cycle-switch interrupts.
- Open follow-ups: derive the smoothscroll.bas compensator constant `((5+V%)*512+6*64-93)`; clarify the cycle-A R8 write at line 510-520.

## [2026-05-16] ingest | Retrosoftware — Fast multiplication + Fast fixed-point (Talbot-Watkins, 2008-09)
- Sources:
  - http://www.retrosoftware.co.uk/wiki/index.php/Fast_multiplication_routines
  - http://www.retrosoftware.co.uk/wiki/index.php/Fast_fixed-point_multiplication_library
- Archived: raw/articles/retrosoftware-fast-{multiplication,fixed-point}.md
- Source code: raw/code/fastmult.6502 + raw/code/fixedpoint.6502 (saved from article listings).
- Created: wiki/sources/retrosoftware-fast-mult.md (combined source page for both articles — same author, same lineage).
- Created: wiki/techniques/multiplication.md (general 8×8 → 16-bit: shift-and-add baseline + half-square LUT, 4-table and 3-table variants, tradeoff table).
- Created: wiki/techniques/fixed-point.md (base-127 representation derivation, 4-way sign case-split, S8/S15 routines, 256-step angle convention with free sin/cos).
- Updated: wiki/index.md (1 source + 2 techniques).
- Key new facts captured:
  - Half-square identity: ab = f(a+b) − f(|a−b|) where f(x) = x²/4. The /4 is lossless.
  - 3-table optimisation: sqrlo512(n) = sqrlo256(n) XOR &80 when n odd (saves 256B at ~12c cost).
  - Base-127 fixed-point: maximises precision in signed 8-bit for [-1, +1] range. Powers of 2 (256/128/64) all have problems (overflow/asymmetry/waste).
  - /127 baked into the LUT: g(x) = x²/(4·127). Zero runtime divide cost.
  - Signed multiply via 4-way sign-combo case split: avoids final negation by reversing subtraction order. Uniform cycle cost across all sign combos.
  - 256-step angle (so 360° = 256): angle arithmetic via ADC, no modulo.
- Outbound references added: Toby Lobster's multiply_test + sqrt_test benchmark repos (https://github.com/TobyLobster/multiply_test, https://github.com/TobyLobster/sqrt_test) as the authoritative comparison sources for 6502 math.
- Open follow-ups: division/reciprocal page; S15×S15 or S15×S31 extension for larger-world perspective work.

## [2026-05-16] ingest | chunky-mode.txt (Tom Seddon's "mythical chunky mode" + Julian Brown 2015)
- Source: raw/notes/chunky-mode.txt (Seddon's modelb.bbcmicro.com tech page + Julian Brown's 2015 Stardot mailing-list post).
- Created: wiki/sources/chunky-mode-notes.md (combined source with both authors' claims and the open mystery flagged).
- Created: wiki/techniques/chunky-mode.md (framed as "high-res chunky IS achievable on Model B" with the EOR-64 interleave layout). Includes Seddon's chase-the-raster software workaround with cycle-budget breakdown.
- Updated: wiki/hardware/address-translation.md — added the "exploitable" note: the MA6-XOR-clock fetches *two* bytes per µs in TTX VDU mode, normally one discarded but the second is the foundation of chunky-mode tricks.
- Updated: wiki/index.md (1 source + 1 technique).
- Key correction during ingest: my initial summary described modes 0/1/2 chunky as "scrambled" / broken on Model B; user pointed out (and our own address-translation page already documents) that the second byte comes from `addr XOR &40` — deterministic, exploitable. Re-framed the technique as achievable, not broken.
- Genuine open mystery captured: the Model B's H/V sync corruption when TTXVDU is asserted in a non-MODE-7 graphics mode (Julian's hardware report). Separate from the address interleave. Speculated causes (IC 5 / IC 6 / IC 15 interaction) but no resolution. Needs scope work on real hardware.

## [2026-05-16] ingest | Twisted Brain demo write-up (kieran/Bitshifters, 2018) — 15 parts
- Source: https://stardot.org.uk/forums/viewtopic.php?t=15300 (kieran's multi-part technical write-up, Stardot 2018-06-27 onwards).
- Archived: raw/articles/twisted-brain-writeup.md (all 15 parts + key follow-up replies).
- Created: wiki/sources/twisted-brain.md (full source page with part-index table linking to each technique page).
- Created 8 new technique pages:
  - wiki/techniques/fx-framework.md (Part 1) — T1 stable-raster + module init/update/draw/kill interface + 312-line invariant.
  - wiki/techniques/single-rasterline-rupture.md (foundation for Parts 6-13) — generalises vertical-rupture from 2-3 cycles/frame to 64-256 cycles/frame; covers re-point vs beam-race patterns and constant-time discipline.
  - wiki/techniques/copper-bars.md (Parts 6+7 combined — same chassis, differing buffer/palette) — pre-rendered Bayer dither + hue rotation.
  - wiki/techniques/parallax-bars.md (Part 8) — 64-row buffer split main/SHADOW + mid-frame ACCCON switch.
  - wiki/techniques/vertical-blinds.md (Part 9) — double-buffered 160B mini-frame + linear line buffer + sink-loop constant-time.
  - wiki/techniques/kefrens-bars.md (Part 10) — true single-scanline beam-race accumulation + R4-on-final-scanline real-hardware quirk + 311-line rebalance fix.
  - wiki/techniques/checkerboard-zoom.md (Part 11) — ULA flash-bit toggle per raster for free colour inversion + unrolled MODE 1 partial-byte plot.
  - wiki/techniques/twister.md (Part 13) — R1=20 narrow display + R2 centring + 128 ribbon rotations + alternate-scanline stipple.
- Smaller parts captured on the source page rather than dedicated pages: Part 2 (Brain palette anim), Part 3 (text screens — same idea as copper, simpler), Part 12 (Bitshifters logo — applied case of single-rasterline rupture), Part 15 (memory stats).
- Updated wiki/techniques/vertical-rupture.md — cross-link to single-rasterline extension.
- Updated wiki/techniques/smooth-vertical-scroll.md — added "applied case: Smiley Drop" section linking Part 14.
- Updated wiki/hardware/crtc-6845-advanced.md — added the HD6845SP R4-on-final-scanline real-hardware quirk to the anomalous-rewrite table.
- Updated wiki/index.md — 1 new source + 9 new techniques.
- Key new technique-class captured: single-rasterline rupture as a *general pattern* (not just one effect). This is arguably the most important addition to the wiki so far — the entire modern Beeb-demo aesthetic depends on it.
- Real-hardware insight captured: the Kefrens R4-on-final-scanline mystery, which propagates as the Parallax timing bug unless the Kefrens kill function emits a 311-line rebalance frame. Real-hardware fix selectable from the BASIC loader in the shipped demo.
- Open follow-ups: hexwab's truly-stable-raster technique (used by Twisted Brain only at boot); BeebEm cycle-accuracy modernisation; the Twister parameter (spin/twist/knot) search heuristics.

## [2026-05-16] lint | comprehensive pass + fixes
- Lint pass run via subagent on the full wiki (~70 pages).
- Phase 1 (low-risk): bumped stale `updated:` dates on crtc-6845.md and crtc-6845-advanced.md to 2026-05-16; removed `[[sources/...]]` placeholder text in os/osword.md. Dialect-annotation lint item turned out to be a false alarm — all actual asm blocks are already tagged.
- Phase 2 (display-cycle accounting): the table in single-rasterline-rupture.md was using a confused "Cycles in display" column that disagreed with the math. Reworked into a 5-column table: Display cycles / Loop iterations / Total cycles / Visible scanlines / Final R4/R7. Added explanation that the FX framework enters at cycle 1, so loop = total − 2. Propagated to kefrens-bars (254→256 scanlines), checkerboard-zoom (added accounting note), vertical-blinds (clarified 128 = 127 + 1 final).
- Phase 3 (checkerboard ULA-flash): rewrote the flash-bit paragraph to match video-ula.md: bit 0 of `&FE20` only affects palette entries programmed with flash physical codes `&08`-`&0F`; the demo programs colours 8-15 as flash entries deliberately to repurpose this single bit as a per-raster colour-flip lever.
- Phase 4 (parallax loop count): added one-line accounting note explaining 64 = 1 (framework-entered) + 62 (looped) + 1 (final).
- Phase 5 (new pages):
  - Fetched http://www.retrosoftware.co.uk/forum/viewtopic.php?f=73&t=1007 → raw/articles/hexwab-stable-raster.md.
  - Created wiki/sources/hexwab-stable-raster.md (source page; credits hexwab, RichTW's CMOS-6502 correction, tricky's narrowing-loop idea).
  - Created wiki/techniques/hexwab-stable-raster.md (the 4-stage technique: interlace off, narrowing-loop sync, T1 free-run on User VIA, jitter compensation via latch read).
  - Created wiki/techniques/raster-splits.md (overview/index page covering all split families, resolving 5+ broken inbound references).
  - Updated broken links in crtc-6845-advanced.md, video-ula.md, custom-modes.md, fast-animation.md.
  - Updated fx-framework.md and twisted-brain.md to cross-link to hexwab page.
  - Updated index.md (1 new source + 2 new techniques).
- Remaining open: techniques/division, tools/beebasm, video/teletext-mode, synthesis/custom-mode-288x192, techniques/exploding-font, os/z80-2p — all referenced sparingly and not urgent.

## [2026-05-16] ingest | ACCC Compendium v1.7 (Querné / Logon System, 2023) — Phase A
- Source: raw/notes/ACCC1.7-EN.pdf (284 pages, chip-internal-cycle-by-cycle reference for the 6845 across 5 CRTC types). BBC's HD6845S/SP is in the CPC "CRTC 0" family covered extensively.
- Created: wiki/sources/accc-compendium.md (source page with CPC↔BBC terminology key + CRTC-0-filtered chapter index).
- Created: wiki/hardware/crtc-internal-counters.md (NEW foundation page: C0/C4/C9/C5/VMA counter model + Last Line / Additional Management states + per-register write-window summary).
- Created: wiki/techniques/rvi.md (NEW: BBC's "RVI" technique documented per ACCC §13.2.7 R.V.L.L. — per-line C9 selection via R0=1 micro-cycles + Last Line semantics).
- Refined: wiki/hardware/crtc-6845-advanced.md (added ACCC as source; reframed R0/R4/R7/R9 anomalous-rewrite verdicts using the C0<2 evaluation window; rewrote "mid-frame rewrites" section to reflect what the BBC scene actually does; reframed R12/R13 sample condition as C4=C9=C0=0).
- Refined: wiki/techniques/kefrens-bars.md (replaced "register-sample-window overlap" hypothesis with the precise C0<2 Last-Line evaluation mechanism per ACCC §13.2.1; cross-linked to R.L.A.L. exit recipe in §12.2.1).
- Refined: wiki/techniques/single-rasterline-rupture.md (added CPC R.L.A.L. terminology note; updated real-hardware-quirks section with precise C0<2 explanation).
- Updated memory: feedback_6845_single_scanline_register_overlap.md now references ACCC as primary source rather than describing as "mystery".
- Key new content captured:
  - The CRTC internal counter model (C0/C4/C9/C5/VMA/VMA') — not previously on the wiki.
  - The C0<2 evaluation window for Last Line — precisely resolves the R4-on-final-scanline behaviour.
  - BBC↔CPC terminology mapping: R.L.A.L. = our single-scanline-rupture; R.V.L.L. = our "RVI" (mistranslated); R.V.I. = CPC's CRTC-1 technique we don't use.
  - Per-register cycle-window write semantics for CRTC 0.
- Open follow-ups deferred to Phase B:
  - wiki/techniques/crtc-counter-freeze.md (NEW: R0=0 chip freeze — experimental on BBC, no shipped use).
  - wiki/techniques/triggered-vsync.md (NEW: R7 mid-line trigger + blocked-VSync gotcha).
  - wiki/techniques/vertical-rupture.md (add Last-Line section + register-write windows).
- ACCC's chip-agnostic chapters (§23 tips, §24 fixed-time) also worth referencing from existing pages where relevant.

## [2026-05-16] ingest | ACCC Compendium v1.7 — Phase B (R0=0 freeze, triggered VSync, vertical-rupture annotations)
- Created: wiki/techniques/crtc-counter-freeze.md (NEW: R0=0 chip freeze; documented as experimental on BBC, no shipped use. Covers C9 freeze, C4 "last hiccup", additional-management arming, VSync interaction, what's still running during freeze, candidate use cases).
- Created: wiki/techniques/triggered-vsync.md (NEW: R7=C4 mid-line trigger vs C0vs<2 block. Both VSync protection mechanisms documented. "Limitless VSync" as warning.).
- Refined: wiki/techniques/vertical-rupture.md — added register-write-windows table, Last-Line state section, R7-rewrite-caveat now uses precise C0vs<2 vs C0vs>=2 framing. Added accc-compendium to sources. Builds-on section expanded with new technique cross-refs.
- Updated wiki/index.md (2 new techniques).
- Phase A+B together: 5 new pages + 5 refined pages from ACCC ingest. The Compendium is now woven through the wiki's CRTC coverage as the canonical chip-internal reference.
- No new memory entries this phase — the ones from Phase A cover the relevant patterns.

## [2026-05-16] ingest | Master ARM Ch 1 (Architecture overview)
- Created: wiki/sources/master-arm.md (source page for the whole manual, with per-chapter status table).
- Created: wiki/hardware/master-overview.md (Master 128 orientation: 65C12, 128 KB DRAM, ACCCON, SDB Port B reuse for CMOS, what's new vs B+, what's gone).
- Updated: wiki/index.md (added source entry + hardware entry).
- Per-chapter ingest plan registered as tasks 54-65; will commit after each chapter.

## [2026-05-16] ingest | Master ARM Ch 3 (Memory Organisation)
- Refined: wiki/memory/shadow-ram.md — E-bit precise mechanism via ARM Ch 3 flowchart (last opcode fetch from &C000-&DFFF AND this cycle not an opcode fetch). Added Acorn region (a)/(b) + LYNNE/HAZEL vocabulary. master-arm to sources.
- Refined: wiki/memory/paged-rom.md — Master ROM matrix-decoding (slots 4-7 share 32 KB chips, slots 8-15 in 128 KB ROM on separate bus); ROMSEL bits 4-6 reserved. master-arm to sources.
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM Ch 4 (Slow Data Bus)
- Refined: wiki/hardware/cmos-rtc.md — sideways-ROM alarm-driver pattern via service calls &04 (Offer Command for *SETALARM) + &05 (Unknown Interrupt for AF response). Strobe-ordering reminder. master-arm to sources.
- Refined: wiki/hardware/system-via.md — master-arm added to sources (SDB control port table cross-checked).
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM Ch 5 (Keyboard Controller)
- Refined: wiki/os/keyboard.md — added KBDENC hardware section (free-run / column detection / row detection scan modes, nKBEN signalling, 10 ms rescan loop, direct-matrix scan note). master-arm to sources.
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM Ch 6 (Screen Display)
- Cross-checked: wiki/hardware/crtc-6845.md per-mode register table against ARM Ch 6 — no contradictions. master-arm added to sources.
- Updated: wiki/hardware/video-ula.md sources (cross-checked palette + control register).
- Refined: wiki/video/modes.md — added shadow modes 128-135 allocation table (20 KB fixed slot in LYNNE regardless of mode). master-arm to sources.
- Created: wiki/techniques/interlaced-640x512.md — Master 640×512 two-colour interlaced mode via CRTC interlace-sync-and-video + per-vsync ACCCON D toggle between main and LYNNE half-frames. ARM Ch 6 recipe.
- Updated wiki/index.md (1 new technique).
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM Ch 7 (User Port)
- Cross-checked: existing user-via.md / via-6522.md / via-timers.md against ARM Ch 7 — already comprehensive (all timer modes, shift register modes, ACR/PCR/IFR/IER, PB7 freq formula, T2 pulse count, CB1/CB2 handshake).
- Updated: wiki/hardware/user-via.md sources (master-arm added).
- ARM motor-control worked example noted in source-page table; not filed (outside performance/demo scope).

## [2026-05-16] ingest | Master ARM Ch 10 (1MHz Bus)
- Refined: wiki/hardware/1mhz-bus.md — added the `&00EE` zero-page RAM shadow of the JIM `&FCFF` paging register; IRQ-safe write sequence (update `&EE` BEFORE `&FCFF`) with worked save/restore pattern. master-arm added to sources.
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM Ch 11 (MOS)
- Refined: wiki/memory/os-workspace.md — added "Master second 32 KB" workspace map (soft-key buffer at &8000-&83FF, soft chars moved to &8900-&8FFF, MOS CLI buffer at &DC00-&DCFF, transient utility at &DD00-&DEFF). Added "Master vector additions" section documenting the extended-vector triple-table install procedure via OSBYTE &A8 and `&FF00 + (vector-&200) * 3 / 2` dispatch. master-arm added to sources.
- Refined: wiki/hardware/master-overview.md — flagged soft-char and soft-key relocation as user-facing wins.
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM Ch 12 (Tube / dual processor)
- Refined: wiki/os/tube.md — added full filing-system claimer-ID table (0=CFS, 1=DFS, 2=NFS-low, 3=NFS-FS, 4=ADFS, 5=TFS, 6=Reserved, 7=VFS, 8=SRM, 9=Z80, F=independent). Added 32-bit LOAD/EXEC file-address encoding section (&FFFF=host main, &FFFE=host shadow, &FFFFFFFF=*EXEC, &JKLM=parasite) with worked pattern for Tube-aware utility ROM addressing. master-arm added to sources.
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] ingest | Master ARM App 8 (65C12 instruction set)
- Cross-checked: wiki/hardware/6502-isa.md + wiki/hardware/6502.md + wiki/hardware/6502-addressing-modes.md against ARM App 8 — already accurate. Crucial split correctly captured: BBR/BBS/RMB/SMB are R65C02-only (6502 2P + Master Turbo 65C102), NOT in the Master's main 65C12. Cycle counts in units of 0.5/0.33/0.25 µs for 2/3/4 MHz variants confirmed.
- master-arm added to sources of 6502-isa.md + 6502.md.
- No new pages required.

## [2026-05-16] ingest | Master ARM Appendices 1+2+3 (model differences)
- Created: wiki/synthesis/model-differences.md — comprehensive cross-model comparison (B / B+ / Master 128 / Master Compact). At-a-glance table; ACCCON + ROMSEL bit-by-bit; soft-char + soft-key relocation; new Master OSBYTEs/commands; machine detection patterns; pitfalls when targeting all models.
- Updated wiki/index.md (synthesis section).
- Updated wiki/sources/master-arm.md filed-into log.

## [2026-05-16] lint | post-Master-ARM lint pass + fixes
Subagent lint pass against the 8-chapter Master ARM ingest. Fixed in this commit:

- wiki/hardware/master-overview.md — three substantive errors corrected:
  1. LYNNE incorrectly placed at &8000-&8FFF (that's ANDY). LYNNE is the 20 KB shadow at &3000-&7FFF. Now lists LYNNE / HAZEL / ANDY as three distinct regions with their correct addresses.
  2. Falsely listed Rockwell BBR/BBS/RMB/SMB as 65C12 opcodes. Master's main CPU is plain 65C12 — those are R65C02-only (6502 2P + Master Turbo 65C102).
  3. CPU clock row "@ 2 MHz / 1 MHz" garbled. Now "@ 2 MHz (drops to 1 MHz only for slow-bus access)".
  4. Soft-char relocation said "from &0E00+" — actually from &0C00-&0CFF (Page C). Corrected.
  5. Stale link to "[[hardware/65c12]] (forthcoming)" — repointed to existing [[hardware/6502-isa]].
  6. Stale link to "planned synthesis page from App 1-3" — repointed to live [[synthesis/model-differences]].

- wiki/memory/shadow-ram.md — typo in E-bit description (`&C000-&DFFF*` had stray asterisk instead of closing backtick); markdown was rendering as italics. Fixed. Bumped updated to 2026-05-16.

- wiki/os/keyboard.md — f1-f9 INKEY table was misleadingly listed as "-114 to -120" contiguous range. Actually f4 = -21 (`&EB`) and f7 = -23 (`&E9`) are out-of-sequence (matrix wiring). Now lists each fn key explicitly. Bumped updated to 2026-05-16.

- wiki/memory/paged-rom.md — bare ``` fence on OSBYTE &44 example tagged as `asm` and fixed `A = &44` to proper `LDA #&44`.

- Bumped `updated:` dates on cmos-rtc.md, os/tube.md, hardware/6502.md to 2026-05-16 (all touched during Master ARM ingest but date wasn't bumped).

Lint findings deferred / left for human:
- 0 orphan pages (clean).
- Top broken-link targets: tools/beebasm, techniques/division, hardware/65c12, techniques/exploding-font, video/teletext-mode. None critical; left as TODO markers.
- cmos-rtc.md Register A rate table has a suspect non-monotonic entry (122.07 µs nested between 3.9ms and 7.8ms). Likely a copy-paste from datasheet where order is non-obvious — left for cross-check against NAUG p361.
- synthesis/model-differences.md "Sideways slots" Master row says "16 (4 + 12 internal)" — phrasing ambiguous re cartridge-paired chips; left as cosmetic.
- Master ARM ingest complete: 8 commits + 1 lint commit. 1 new source page, 2 new technique pages, 1 new hardware page, 1 new synthesis page, refinements to ~12 existing pages.

## [2026-05-16] ingest | User Guide source page + Ch 34 (VDU drivers)
- Created: wiki/sources/bbc-user-guide.md (source page for the 522-page User Guide, per-chapter status table).
- Created: wiki/os/vdu.md — full VDU 0-31 + 127 control code reference. Byte counts per code; semantics; VDU 17/18/19/22/23/24/25/28/29/31 detailed sections; VDU 23 sub-function table including Master extensions; programmatic invocation patterns; cross-model differences.
- Updated wiki/index.md (1 new source + 1 new OS page).

## [2026-05-16] ingest | User Guide Ch 29 + Ch 33 (Advanced Graphics + PLOT keyword)
- Created: wiki/video/plot-codes.md — full PLOT k=0-255 reference. Codes 0-95 from User Guide (line variants, fills, triangles, single points, line-fill primitives); codes 96-255 from Master ARM Ch 6 (rectangle, parallelogram, circle, ellipse, flood fill, arc). Bit-field decomposition of k showing the move/draw/colour mode sub-pattern.
- Updated wiki/index.md (1 new video page).
- Updated wiki/os/vdu.md to point at the live plot-codes page (was "forthcoming").
- Updated wiki/sources/bbc-user-guide.md filed-into log.

## [2026-05-16] ingest | User Guide Ch 46 (Error messages)
- Created: wiki/os/errors.md — full BASIC error table (0-44 alphabetical, numerical, with cause), CFS errors 216-223, MOS errors 250+, common DFS/ADFS/NFS error conventions. Pattern for raising errors from user code via BRK + structure. Compatibility notes across BBC BASIC I-IV.
- Updated wiki/index.md (1 new OS page).
- Updated wiki/sources/bbc-user-guide.md filed-into log.

## [2026-05-16] ingest | User Guide Ch 42 + Ch 48 (FX/OSBYTE + Appendix cross-check)
- Cross-checked: wiki/os/osbyte.md against UG Ch 42 — UG's OSBYTE list is a subset of NAUG App A/B (already ingested) plus Master ARM additions. No new content.
- Cross-checked: wiki/os/keyboard.md against UG Ch 48 — ASCII/INKEY tables already in via NAUG Ch14 + Master ARM Ch 5.
- bbc-user-guide added to sources of: os/osbyte.md, os/keyboard.md.

## [2026-05-16] ingest | User Guide Ch 28 (Teletext) cross-check
- Cross-checked: wiki/hardware/saa5050.md against UG Ch 28 — UG is beginner intro level; technical detail already in saa5050.md (Mullard datasheet + BeebWiki + technical sources).
- bbc-user-guide added to saa5050.md sources.

## [2026-05-16] ingest | Service Manual source page + §3 (Detailed Circuit Description)
- Created: wiki/sources/bbc-service-manual.md (source page for the 90-page Service Manual covering Model B PCB issues 1-7).
- Refined: wiki/os/break-intercept.md — added "How MOS distinguishes cold-start from BREAK at the hardware level" subsection (555 timer general reset vs separate RC network for Reset A signal into System VIA on power-up only). bbc-service-manual added to sources.
- Refined: wiki/hardware/address-translation.md — bbc-service-manual added to sources (cross-confirmed IC numbers).
- Updated wiki/index.md (1 new source).

## [2026-05-16] ingest | Service Manual §5 + §7 (Links + Hardware Hints)
- Reviewed: SM §5 (selection links) — out of scope, historical PCB configuration only.
- Reviewed: SM §7.3 (Hardware Hints) — entries are end-user PCB mods (110 baud RS423 trick via S28 link, BREAK key disable via keyboard PCB link). No demoscene-relevant tricks worth filing as techniques.
- Updated wiki/sources/bbc-service-manual.md chapter index with cross-check status.

## [2026-05-16] lint | post-User-Guide / Service-Manual lint pass + fixes
Subagent lint pass against the 7-commit User Guide + Service Manual ingest. Fixes applied:

- wiki/os/vdu.md — fixed "OSWORD &FFF1" wording (was conflating the entry vector with a reason code); section now correctly distinguishes OSWRCH overhead vs custom-mode bypass. Added inline source citations for char-data address ranges (Model B vs Master) and Master VDU 23 extensions.
- wiki/os/break-intercept.md — removed invented "Master Memory Controller IC" claim that wasn't in any cited source. Bumped updated date to 2026-05-16.
- wiki/video/plot-codes.md — hedged uncited "200 µs per PLOT" timing claim. Now reads "hundreds of microseconds … measure on your target machine".
- wiki/os/errors.md — hedged BASIC II vs IV trappability claim.
- Replaced broken `[[reference_bbc_documents_repo]]` Obsidian-link with plain markdown URL across 3 source pages (bbc-user-guide, bbc-service-manual, master-arm).
- wiki/sources/naug-ch13-video.md — updated stale "PLOT not filed back" note to "filed into video/plot-codes".
- Added cross-links: os/calls → os/vdu + os/errors; os/brk → os/errors (new See also section); os/escape → os/errors.

Lint findings deferred / left for human:
- os/errors.md DFS/ADFS/NFS error table is hedged but specific rows (e.g. 198, 212) may be inaccurate. Marked clearly as non-authoritative.
- os/errors.md MOS errors 250+ table only has 251/253/254 — incomplete. Acknowledged.
- 0 orphan pages (no genuinely orphan content; new pages have cross-links from index plus the just-added See-also links).
- 0 contradictions remaining; 0 code-block dialect issues in new files.
## [2026-05-16] meta | Add LLM-disclaimer footer to all wiki pages
- Applied a uniform footer to all 119 wiki/*.md files. Footer states the wiki is LLM-generated under the LLM-Wiki methodology, may contain errors, and points readers to the bbc-documents GitHub archive for authoritative content.
- Footer is marked with `<!-- llm-wiki-footer -->` HTML comment for idempotent re-application.
- Updated CLAUDE.md schema to document the requirement for new pages.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*

## [2026-05-16] ingest | Master Reference Manual source page (Parts 1 + 2)
- Created: wiki/sources/master-rm.md — source page covering both volumes of the user/programmer-level Master Reference Manual (400 + 324 pages). Distinguished from the deeper [[sources/master-arm]] (Advanced Reference Manual). Per-chapter status table for all Part 1 + 2 chapters.
- Updated wiki/index.md with new source entry.

## [2026-05-16] ingest | MRM Part 1 Ch E.1-E.3 (VDU driver intro + commands)
- Extensively refined wiki/os/vdu.md:
  - Added parsing model intro (byte-range interpretation table) + OSBYTE &DA queue-length call
  - Expanded VDU 18 with GCOL mode 5 (leave unchanged) + complete ECF mode-byte encoding (16+n / 32+n / 48+n / 64+n) for the 4 ECF patterns
  - Significantly expanded VDU 23,n sub-function reference: 4-level cursor (VDU 23,1), ECF row-byte pixel mapping per bpp (VDU 23,2-5), dotted-line pattern (VDU 23,6), direct window scroll (VDU 23,7) with full d/z parameter tables, clear-block (VDU 23,8) with base-position codes (0,1,2,4,5,6,8,9,10), default ECF pattern table (VDU 23,11), simple ECF (VDU 23,12-15), cursor-movement-control flags (VDU 23,16) bit-by-bit with all 8 X/Y direction encodings and the "81-column" scroll-protect mode
- Extensively refined wiki/video/plot-codes.md:
  - Replaced PLOT k structure section with the precise MRM Ch E.3 semantics: k MOD 8 coord-and-colour mode table (relative/absolute + foreground/background/invert/leave), k DIV 8 operation group table covering all 32 groups
  - Added geometric primitive precise definitions: circles (centre = current cursor, radius limit < 16384), arc/chord/sector geometry (3-point centre/start/direction-of-end convention, anticlockwise), ellipses (centre = old cursor, X-intercept = current cursor X, (x,y) = highest/lowest point — Y of current ignored) with worked rotated-ellipse PROC from MRM p202
  - Move/copy rectangle special k handling (PLOT 184-191 breaks usual k MOD 4 colour convention; codes 184/185 move-rel, 186/187 copy-rel, 188/189 move-abs, 190/191 copy-abs)
  - Flood-fill workspace usage (&8400-&87FF in MOS sideways RAM on Master)
  - Horizontal line fill 4-variant table (background-stop vs foreground-stop, R-only vs L+R)
- master-rm added to sources of vdu.md + plot-codes.md.

## [2026-05-16] ingest | MRM Part 1 Ch E.4 (VDU variables + plot vector)
- Created: wiki/os/vdu-internals.md — comprehensive new page covering VDU driver internals from MRM Ch E.4:
  - Storage map (page 0 / page 3 / second 32K)
  - Full VDU variable table at &300-&37F with (p)/(e) coordinate annotation
  - Page-0 VDU workspace (&D0-&E1): STATE, ZMASK, ZORA, ZEOR, ZGORA, ZGEOR, ZMEMG, ZMEMT, ZTEMP, ZTEMPB, ZTEMPC, ZTEMPD
  - Master second-32K layout (ECF patterns at &8800+, soft chars at &8900+, ROM defaults at &B900+, flood-fill workspace at &8400-&87FF)
  - All 8 C000-area primitive entry points: load/store shadow-aware byte (&C000/&C003), PLBYTE (&C006), HPLOT (&C009), EIGABS (&C00C), WIND (&C00F) with the 9-position clipping table, GADDR (&C012), IEG (&C015)
  - Worked example re-implementing PLOT 64-71 single-point from VDUV
  - Sideways-ROM intercept caveats (filing-system RAM overlay + sideways ROM overlay breaks both the C000 entry points and the &8400-&8FFF data areas)
- Updated wiki/index.md (1 new OS page).
