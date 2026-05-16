# Wiki Index

Content catalog. Routing table for queries — start here, then drill into pages.

## Sources

- [[sources/naug]] — The New Advanced User Guide (Holmes & Dickens, Adder, 458pp). Foundational reference. Ingested chapter-by-chapter.
- [[sources/naug-ch05-6502-isa]] — NAUG Ch5: 6502 instruction set (p35-106). Cycle counts, opcodes, 65C12 + R65C02 differences.
- [[sources/naug-ch12-memory]] — NAUG Ch12: Memory (p162-171). Map, paging, sideways RAM, shadow RAM, ACCCON, HAZEL.
- [[sources/naug-ch13-video]] — NAUG Ch13: Video/graphics (p172-224). 6845 CRTC, Video ULA, palette, hardware scrolling, fast animation, screen memory maps.
- [[sources/naug-ch22-vias]] — NAUG Ch22: System and User/Printer 6522 VIAs (p387-408). Ports, addressable latch, T1/T2 timers, shift register, IFR/IER.
- [[sources/naug-ch08-interrupts]] — NAUG Ch8: Interrupts (p131-142). IRQ chain, IRQ1V/IRQ2V, MOS dispatch order, BRK protocol, IRQ bit masks.
- [[sources/naug-ch03-04-arithmetic-addressing]] — NAUG Ch3+Ch4: 2's complement, BCD, addressing modes (p22-34). JMP (ind) NMOS bug detail; 65C12 mode additions.
- [[sources/naug-appendix-ab]] — NAUG Appendix A + B: OSBYTE / OSWORD directory tables (p443-448). Index, not detail; detail backfilled per chapter.
- [[sources/naug-ch06-os-introduction]] — NAUG Ch6: OS introduction (p107-125). Vectored entry points, OSBYTE/OSWORD protocol, zero page + page 2 / 3 allocation, OSHWM.
- [[sources/naug-ch17-paged-roms]] — NAUG Ch17: Paged ROMs (p290-333). Header format, language vs service, service-call dispatch, extended vectors, OSRDRM, RFS, 100Hz polling.
- [[sources/naug-ch07-events]] — NAUG Ch7: Events (p126-130). EVNTV, 10 event codes, OSEVEN, handler conventions.
- [[sources/naug-ch09-buffers]] — NAUG Ch9: Buffers (p143-153). INSV/REMV/CNPV, 9 buffer IDs, OSBYTE wrappers, hooking patterns.
- [[sources/naug-ch21-sound]] — NAUG Ch21: Sound + speech (p379-386). OSWORD &07/&08, SN76489 chip-level details, slow-bus direct-write dance.
- [[sources/naug-ch11-hardware]] — NAUG Ch11: Hardware overview (p157-161). System block diagram, consolidated SHEILA table across all machines.
- [[sources/naug-ch14-keyboard]] — NAUG Ch14: Keyboard (p225-239). Three numbering schemes (ASCII / INKEY / IKN), scan, auto-repeat, soft keys, status byte.
- [[sources/naug-ch18-tube]] — NAUG Ch18: Tube / 2nd processor (p334-358). Tube ULA registers, OS dispatch over Tube, &406 entry, claim/release, data-transfer protocol.
- [[sources/naug-ch16-filing]] — NAUG Ch16: Filing systems (p257-289). Standard FS API, per-FS variations, DFS/ADFS catalogue formats, WD1770 FDC direct programming.
- [[sources/naug-ch23-1mhz-bus]] — NAUG Ch23: 1MHz bus + cartridges (p409-425). FRED/JIM, bus signals, clock-stretching gotchas + clean-up circuits, Master cart slot at 2 MHz, 27513 128 KB EPROMs.
- [[sources/naug-ch02-basic-assembler]] — NAUG Ch2: BBC BASIC inline assembler (p13-21). OPT bits, P%/O%, labels, EQU directives, two-pass dance, CALL/USR conventions.
- [[sources/naug-ch10-escape]] — NAUG Ch10: ESCAPE handling (p154-156). OSBYTE `&7C`/`&7D`/`&7E`, suppression flags `&C8`/`&E5`/`&E6`, character remap `&DC`.
- [[sources/naug-ch15-serial]] — NAUG Ch15: Serial I/O (p240-256). RS232/RS423 standards, 5-pin DIN pinout, 6850 ACIA, Serial ULA, baud-rate OSBYTEs.
- [[sources/naug-ch19-clocks-cmos]] — NAUG Ch19: Clocks/Timers/CMOS (p359-371). System clock + interval timer, Master 146818 RTC + 50-byte CMOS, alarm IRQ via LK4.
- [[sources/naug-ch20-adc]] — NAUG Ch20: ADC system (p372-378). µPD7002 chip, conversion timing, joystick reading, Master Compact's switched-not-analogue simulator.
- [[sources/naug-ch24-misc]] — NAUG Ch24: Miscellaneous (p426-438). BREAK intercept `&F7-&F9`, reset types, printer UPTV, `*CODE`/`*LINE` via USERV, machine identification, NETV/KEYV.
- [[sources/allmem-ripley-harston]] — AllMem: BBC System Memory Map (Ripley/Harston, 2016). Byte-level catalogue of MOS workspace across BBC/Electron/Master variants. Authoritative cross-check for `&00`-`&FF`, `&0200`-`&02FF`, `&0300`-`&03FF`, buffer pages, `&FE00-&FEFF`, MOS jumpblock.
- [[sources/beebwiki-address-translation]] — BeebWiki: Address translation (mdfs.net). The discrete-logic translator: CPU/TTX/HI-RES modes, IC 32 + IC 39 wraparound mechanism, per-mode subtract amounts, MODE 7 formula.
- [[sources/beebwiki-crtc]] — BeebWiki: CRTC (mdfs.net). 6845 register map + Acorn quirks (R10 BLK encoding, MODE 7 R12/R13 XOR `&54`, 6845S variant).
- [[sources/beebwiki-video-ula]] — BeebWiki: Video ULA (mdfs.net). Shift-register / palette-CAM mechanics, undefined 80@1MHz / 10@2MHz behaviour, default palette write tables, hardware history (Ferranti / VLSI / VideoNuLA).
- [[sources/beebwiki-andy]] — BeebWiki: ANDY (mdfs.net). B+ 12 KB / Master 4 KB paged RAM area; OSWORD `&05`/`&06` extended-addressing access; B+ shadow-display window at `&A000-&AFFF`.
- [[sources/beebwiki-cycle-stretching]] — BeebWiki: Cycle stretching (mdfs.net). Mechanism + complete list of 1 MHz peripheral addresses; variable 2c/3c penalty per access; phase-aligning notes.
- [[sources/hd6845sp-hitachi-datasheet]] — Hitachi HD6845R/HD6845S datasheet (primary chip-level reference). Register encodings, programming restrictions, anomalous-rewrite table, HD6845S-vs-HD6845R differences, reset behaviour.
- [[sources/saa5050-references]] — Combined SAA5050 references (Wikipedia, HandWiki, mdfs.net Teletext Controls, BeebFpga VHDL model). Substitutes for the image-only Mullard datasheet PDF (`raw/manuals/SAA5050.pdf`).
- [[sources/retrosoftware-smooth-vscroll]] — Talbot-Watkins, "How to do the smooth vertical scrolling" (retrosoftware.co.uk, 2008). Vertical rupture + R5 sub-row scroll technique. Includes BeebASM + BBC BASIC demos.
- [[sources/retrosoftware-fast-mult]] — Talbot-Watkins, "Fast multiplication routines" + "Fast fixed-point multiplication library" (retrosoftware.co.uk, 2008-09). Half-square LUT + base-127 signed fixed-point. Full BeebASM library.
- [[sources/chunky-mode-notes]] — Tom Seddon's "mythical chunky mode" page + Julian Brown's 2015 Stardot post on real-hardware behaviour. Combined notes on driving the CRTC from MODE 7 RAM while in graphics modes.
- [[sources/twisted-brain]] — kieran's 15-part write-up of the Bitshifters Twisted Brain demo (Stardot, 2018). First BBC demo to use extensive single-rasterline CRTC vertical rupture. Foundation reference for modern Beeb demo techniques.
- [[sources/hexwab-stable-raster]] — hexwab's "Cycle-exact display diddling" post (Retrosoftware, 2016). The canonical 2-cycle-precision stable-raster technique: narrowing-loop sync + T1 free-run + per-IRQ latch-read jitter compensation.
- [[sources/accc-compendium]] — Serge Querné's *Amstrad CPC CRTC Compendium* (Logon System, v1.7 2023). 284-page chip-internal cycle-by-cycle reference for the 6845. CPC "CRTC 0" = BBC's HD6845S/SP — canonical reference for chip-internal CRTC behaviour.
- [[sources/master-arm]] — Acorn *Advanced Reference Manual for the BBC Master Series* (~1986, 292 pages). Canonical reference for Master 128 / Compact / ET / Turbo. Ingested chapter-by-chapter.
- [[sources/bbc-user-guide]] — Acorn *BBC Microcomputer System User Guide* (Coll, 1982, 522 pages). Original Model B end-user manual. Mostly BASIC tutorial (out of scope); canonical for VDU control codes / PLOT codes / error messages.
- [[sources/bbc-service-manual]] — Acorn *BBC Microcomputer Service Manual* (1982-85, 90 pages). Electrical-level circuit description + repair / link options for Model A/B PCB issues 1-7. Cross-checks for chip pages.

## Hardware

- [[hardware/6502]] — CPU entity: registers, flags, machine variants (NMOS 6502 / 65C12 / R65C02), reset/interrupt vectors.
- [[hardware/6502-isa]] — Full instruction-set reference: per-mnemonic addressing modes, bytes, cycles, opcodes. Performance summary at end.
- [[hardware/6502-addressing-modes]] — Mode mechanics: 12 NMOS modes + 2 65C12 additions. Worked examples, page-crossing penalty, mode-cost summary, zp forward-reference trap.
- [[hardware/crtc-6845]] — 6845 CRTC entity: register map, per-mode values, screen-start lever, light pen, wrap-around.
- [[hardware/crtc-6845-advanced]] — Anomalous-rewrite table (which registers tolerate mid-frame writes), R12/R13 sample phase, split-screen primitives, field timing.
- [[hardware/video-ula]] — Acorn Video ULA: control register, palette mechanics, cursor width, logical-colour expansion rules per mode.
- [[hardware/via-6522]] — 6522 VIA generic: register map (ORA/ORB/DDR/T1/T2/SR/ACR/PCR/IFR/IER), IRA vs IRB asymmetry, IER set/clear protocol.
- [[hardware/system-via]] — System VIA @ `&FE40`: slow peripheral bus, addressable latch, vsync/keyboard/light-pen/ADC IRQs, hardware-scroll wrap addend table.
- [[hardware/user-via]] — User/Printer VIA @ `&FE60`: printer port pinout, user port pinout, PB7 audio, PB6 pulse counting.
- [[hardware/sn76489]] — TI SN76489 sound chip: 3 tones + 1 noise, frequency math, byte formats, direct slow-bus write sequence.
- [[hardware/tube-ula]] — Tube ULA: 4 register pairs (status + data), R3 FIFO, IRQ/NMI sources, host vs parasite addressing.
- [[hardware/1mhz-bus]] — Expansion bus reference: FRED/JIM/SHEILA, pinout, clock-stretching, clean-up circuits, cartridge slot variant, performance use cases.
- [[hardware/wd1770]] — Floppy disc controller: register map, command types I-IV, status bits, NMI-per-byte protocol, direct sector read sequence.
- [[hardware/6850-acia]] — Motorola 6850 UART: status/control registers, clock divider, RTS/IRQ controls, word-format encodings.
- [[hardware/serial-ula]] — Acorn serial ULA: baud-rate encoding, RS423/cassette switch, cassette motor control.
- [[hardware/cmos-rtc]] — Master-only 146818 RTC: register layout, alarm/periodic/UE IRQ sources, slow-bus access, LK4 enable.
- [[hardware/upd7002-adc]] — NEC µPD7002 4-channel 12-bit ADC: status/start register, 8-bit vs 12-bit modes, EOC IRQ on System VIA CB1.
- [[hardware/address-translation]] — Discrete-logic CPU/CRTC → DRAM mapper. CPU/TTX/HI-RES modes, IC 32 + IC 39 hardware-scroll wraparound, MODE 7 formula, per-mode DRAM refresh intervals.
- [[hardware/crtc-internal-counters]] — The C0/C4/C9/C5/VMA internal state model that underpins all 6845 behaviour. Last Line + Additional Management states. Per-register write-window summary. Foundation page for everything CRTC.
- [[hardware/saa5050]] — Mullard teletext character generator (MODE 7 pixel source). 12×20 cells, full control-code table, set-after vs set-at semantics, hold-graphics quirks, BBC integration.
- [[hardware/master-overview]] — BBC Master 128 hardware orientation. 65C12 CPU, 128 KB DRAM, ACCCON, what changed vs B/B+, where things live.

## Memory

- [[memory/memory-map]] — 64KB layout, SHEILA device addresses, user RAM sub-regions, machine-specific extras.
- [[memory/paged-rom]] — `&FE30` paging register, sideways ROM/RAM, ANDY (Master), why you must never poke `&FE30` directly.
- [[memory/shadow-ram]] — ACCCON `&FE34` (B+ vs Master), shadow bank, HAZEL, double-buffered animation on Master.
- [[memory/zero-page]] — Page 0 allocation (BASIC/user/OS/VDU/FS), user zp at `&70-&8F`, strategies for claiming more, 65C12 `(zp)` advantage.
- [[memory/os-workspace]] — Pages 1, 2, 3, 8, 9, B, C, D: buffers, vectors, OS variables, VDU workspace, NMI, function keys. What to save/restore when bypassing MOS.

## Video

- [[video/modes]] — Mode summary: resolution, bpp, screen base, screen size, byte→pixel layout (MODE 2 interleaving), address arithmetic.
- [[video/hardware-scrolling]] — R12/R13 lever, vertical & sideways scroll, hardware wrap-around, MODE 7 correction, vsync timing, OS shadow-copy issue.
- [[video/plot-codes]] — VDU 25 PLOT k reference, k=0-95 (User Guide) + k=96-255 (Master extensions). Filled triangles/rectangles/circles/ellipses/flood fill.

## Timing

- [[timing/via-timers]] — T1/T2 modes, periodic IRQ, raster splits, PB7 audio, pulse counting, MOS-sound conflict on System VIA T1.
- [[timing/cycle-stretching]] — Which addresses cost extra cycles (most of SHEILA, FRED, JIM); variable 2c/3c penalty; phase-aligning; what's NOT stretched (Video ULA, Tube, FDC, ROMSEL).

## OS / MOS

- [[os/interrupts]] — IRQ dispatch chain, IRQ1V/IRQ2V hooks, mask OSBYTEs (`&E7`/`&E8`/`&E9`/`&CB`), 50Hz vs 100Hz, 2ms SEI ceiling, NMI overview.
- [[os/brk]] — BRK protocol, Acorn error-message convention, BRKV install pattern, paged-ROM-raising-errors, NMOS CLD trap.
- [[os/osbyte]] — Complete OSBYTE `&00`-`&FF` directory. Each entry links to source page once that chapter is ingested.
- [[os/osword]] — Complete OSWORD directory: OS calls `&00`-`&0F`, filing-system `&7A`-`&80`, Tube `&FF`.
- [[os/calls]] — Master OS entry-point reference: OSWRCH/OSRDCH/OSCLI/OSFILE/etc + indirection vectors + bypass strategies.
- [[os/paged-roms]] — Paged ROM software contract: header, language vs service, calling into another ROM (OSRDRM / OSBYTE &8F / extended vectors), sideways-RAM install.
- [[os/service-calls]] — Complete service-call reason-code reference (`&00`-`&FF`).
- [[os/events]] — Event system: 10 event codes, EVNTV install pattern, event vs IRQ-vector trade-offs.
- [[os/buffers]] — FIFO buffers: 9 IDs, INSV/REMV/CNPV vectors, OSBYTE wrappers, hook patterns, buffer→event connection.
- [[os/sound]] — MOS SOUND/ENVELOPE OSWORDs, BELL OSBYTEs, suppression, MOS↔chip pipeline, when to bypass.
- [[os/keyboard]] — Three numbering schemes (ASCII/INKEY/IKN), scan calls, auto-repeat, soft keys, status byte, direct matrix scan.
- [[os/tube]] — Tube software protocol: detect (OSBYTE `&EA`), &406 entry (claim/release/transfer/execute), parasite OS dispatch table, OSWORD &05/&06, what changes when Tube active.
- [[os/filing-systems]] — OSFILE/OSARGS/OSBGET/OSBPUT/OSGBPB/OSFIND reference, per-FS variation summary, Master HAZEL FS-handler, MOS-bypass strategies for fast disc I/O.
- [[os/escape]] — ESCAPE handling: OSBYTE `&7C-&7E`, disable patterns for games, event 6 vs polling, side-effects of `&7E`.
- [[os/serial]] — RS232/RS423 MOS calls: input/output stream selection, baud rates, RS423 mode, handshake threshold, bypass paths.
- [[os/clocks]] — System clock + interval timer (5-byte / 100 Hz), OSWORD `&01-&04`, dual-clock atomicity (`OSBYTE &F3`), event 5 as one-shot.
- [[os/adc]] — Joystick + ADC reading: `OSBYTE &10/&11/&80/&BC/&BD/&BE`, conversion modes, event 3, Compact simulator config.
- [[os/break-intercept]] — BREAK / reset handling: `OSBYTE &F7-&F9` JMP intercept, reset types (`&FD`), startup options (`&FF`), game-launcher patterns.
- [[os/printer]] — Printer driver: `*FX 5` destinations, UPTV (`&222`), ignore character, custom printer hooks.
- [[os/vdu]] — Full VDU control code reference (VDU 0-31 + 127). Byte counts, semantics, VDU 23 sub-functions, VDU 18 GCOL modes.
- [[os/errors]] — Error number ↔ message reference. BASIC errors 0-44, CFS 216-223, MOS 250+, filing-system errors. BRK-raising pattern.

## Techniques

- [[techniques/fast-animation]] — MODE 2 byte-move sprites, pre-shifted sprite tables, hardware-scroll as foundation, vsync sync.
- [[techniques/custom-modes]] — Roll your own resolution/colour by reprogramming CRTC + Video ULA directly. Five-step recipe, MOS-bypass discipline, what breaks (OSWRCH, cursor, light pen), BREAK survival.
- [[techniques/vertical-rupture]] — Multiple CRTC cycles per TV frame for split-screen / status panel. Worked MODE 2 example (16+23 rows). R12/R13 latching + R4/R6/R7 read-per-cycle as the mechanism.
- [[techniques/smooth-vertical-scroll]] — 1-scanline vertical scrolling via R5 + two-cycle rupture. Screen-on timer for rock-steady top edge. Builds on vertical-rupture.
- [[techniques/multiplication]] — Unsigned 8×8 → 16-bit: shift-and-add baseline (~113c) vs half-square LUT trick (~55c, 1 KB tables). Three implementations with tradeoff table.
- [[techniques/fixed-point]] — Base-127 signed fixed-point representation. Why ×127 beats ×64/128/256. 4-way sign case-split, S8×S8 (~58c), S15×S8 (~170c), free sin/cos.
- [[techniques/chunky-mode]] — 1 KB chunky display by routing CRTC fetches via MODE 7 RAM in a graphics mode. EOR-64 interleave for modes 0/1/2. Software workaround for Model B sync issue.
- [[techniques/fx-framework]] — Demo runtime: SEI + System VIA T1 free-run for stable raster, FX module interface (init/update/draw/kill), the 312-line invariant. Foundation from Twisted Brain.
- [[techniques/single-rasterline-rupture]] — Extreme vertical rupture: 64-256 CRTC cycles per frame, each 1-4 scanlines tall. Re-point R12/R13 or beam-race a tiny buffer. Foundation of most modern Beeb demo effects.
- [[techniques/copper-bars]] — Pre-rendered MODE 0 ordered-dither buffer + per-row R12/R13 selection + hue-rotation palette. Covers both Copper Bars and Plasma effects (Twisted Brain Parts 6+7).
- [[techniques/parallax-bars]] — 64-character-row pre-rendered MODE 1 buffer split main/SHADOW RAM, mid-frame ACCCON switch. The most timing-sensitive effect in Twisted Brain (Part 8).
- [[techniques/vertical-blinds]] — Double-buffered 160-byte mini-frame, beam-race the buffer between FX draws. Linear line-buffer pattern + sink-loop constant-time discipline (Part 9).
- [[techniques/kefrens-bars]] — True single-scanline beam-race accumulation of bars. R4-on-final-scanline real-hardware mystery + 311-line rebalance frame (Part 10).
- [[techniques/checkerboard-zoom]] — Per-raster ULA flash-bit toggle for free colour inversion + unrolled MODE 1 partial-byte plot (Part 11).
- [[techniques/twister]] — Narrow CRTC display via R1=20 + R2 centring + 128 prerendered ribbon rotations + alternate-scanline stipple for 4th colour (Part 13).
- [[techniques/hexwab-stable-raster]] — 2-cycle-precision sync via narrowing-loop + T1 free-run + per-IRQ latch-read jitter compensation. The next-precision-level alternative to fx-framework's ~8c jitter approach.
- [[techniques/raster-splits]] — Overview / index of raster-split families. Routes readers from "I want to do a raster split" to the right specific technique page.
- [[techniques/rvi]] — Per-line C9 selection via R0=1 micro-cycles + Last Line semantics. BBC's "RVI" naming aliased to the CPC R.V.L.L. taxonomy. Full 32 KB CRTC-addressable RAM per visible line (64 KB on Master via shadow).
- [[techniques/crtc-counter-freeze]] — R0=0 chip freeze. Experimental on BBC, no shipped use. Freezes C9 and most counters; sibling lever to triggered-vsync.
- [[techniques/triggered-vsync]] — R7=C4 mid-line trigger (immediate VSync) vs C0vs<2 block (VSync silently inhibited). Per-field sub-scanline VSync edge nudging.
- [[techniques/interlaced-640x512]] — Master-only 640×512 two-colour interlaced mode. CRTC interlace-sync-and-video + per-vsync ACCCON D toggle between main and LYNNE half-frames. ARM Ch 6 recipe.

## Tools

- [[tools/basic-assembler]] — BBC BASIC inline assembler cheatsheet: OPT bits, P%/O%, labels, EQU directives, two-pass dance, FN-macro pattern, BeebAsm porting notes.

## Synthesis

- [[synthesis/mode-8-16colour-lf]] — Community "MODE 8" (80×256, 16 colours, 10 KB) recipe. MODE 5 CRTC + Video ULA control = `&E0`. Derivation of bpp from R1 ÷ ULA-chars ratio.
- [[synthesis/model-differences]] — Cross-model comparison (B / B+ / Master 128 / Master Compact). Memory, CPU, FDC, video, IO. What's portable, what's not.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
