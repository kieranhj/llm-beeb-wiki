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

## Hardware

- [[hardware/6502]] — CPU entity: registers, flags, machine variants (NMOS 6502 / 65C12 / R65C02), reset/interrupt vectors.
- [[hardware/6502-isa]] — Full instruction-set reference: per-mnemonic addressing modes, bytes, cycles, opcodes. Performance summary at end.
- [[hardware/6502-addressing-modes]] — Mode mechanics: 12 NMOS modes + 2 65C12 additions. Worked examples, page-crossing penalty, mode-cost summary, zp forward-reference trap.
- [[hardware/crtc-6845]] — 6845 CRTC entity: register map, per-mode values, screen-start lever, light pen, wrap-around.
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

## Memory

- [[memory/memory-map]] — 64KB layout, SHEILA device addresses, user RAM sub-regions, machine-specific extras.
- [[memory/paged-rom]] — `&FE30` paging register, sideways ROM/RAM, ANDY (Master), why you must never poke `&FE30` directly.
- [[memory/shadow-ram]] — ACCCON `&FE34` (B+ vs Master), shadow bank, HAZEL, double-buffered animation on Master.
- [[memory/zero-page]] — Page 0 allocation (BASIC/user/OS/VDU/FS), user zp at `&70-&8F`, strategies for claiming more, 65C12 `(zp)` advantage.
- [[memory/os-workspace]] — Pages 1, 2, 3, 8, 9, B, C, D: buffers, vectors, OS variables, VDU workspace, NMI, function keys. What to save/restore when bypassing MOS.

## Video

- [[video/modes]] — Mode summary: resolution, bpp, screen base, screen size, byte→pixel layout (MODE 2 interleaving), address arithmetic.
- [[video/hardware-scrolling]] — R12/R13 lever, vertical & sideways scroll, hardware wrap-around, MODE 7 correction, vsync timing, OS shadow-copy issue.

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

## Techniques

- [[techniques/fast-animation]] — MODE 2 byte-move sprites, pre-shifted sprite tables, hardware-scroll as foundation, vsync sync.
- [[techniques/custom-modes]] — Roll your own resolution/colour by reprogramming CRTC + Video ULA directly. Five-step recipe, MOS-bypass discipline, what breaks (OSWRCH, cursor, light pen), BREAK survival.

## Tools

- [[tools/basic-assembler]] — BBC BASIC inline assembler cheatsheet: OPT bits, P%/O%, labels, EQU directives, two-pass dance, FN-macro pattern, BeebAsm porting notes.

## Synthesis

- [[synthesis/mode-8-16colour-lf]] — Community "MODE 8" (80×256, 16 colours, 10 KB) recipe. MODE 5 CRTC + Video ULA control = `&E0`. Derivation of bpp from R1 ÷ ULA-chars ratio.
