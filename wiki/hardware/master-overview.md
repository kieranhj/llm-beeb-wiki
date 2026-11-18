---
title: BBC Master Series — Hardware Overview
type: hardware
tags: [master, m128, architecture, overview]
sources: [master-arm, master-rm, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# BBC Master Series — Hardware Overview

Orientation page for the Master 128 (and variants: Compact, ET, Turbo). The Master is a superset of the Model B and B+: same MOS pattern, same VDU driver, same 6845 CRTC, but with a CMOS CPU, more RAM, and several reused control surfaces. This page is the "where does X live" map for chip-level work. Detail pages follow the same per-chip layout as for the Model B.

Primary source: [[sources/master-arm]] Ch 1.

## Core spec at a glance

| Component | Master 128 | Reference |
|---|---|---|
| CPU | **65C12** (CMOS, sometimes labelled "65SC12") @ 2 MHz (drops to 1 MHz only for slow-bus access) | [[hardware/6502]], [[hardware/6502-isa]] |
| RAM | 128 KB DRAM (4 × 4464) | [[memory/memory-map]] |
| ROM | 128 KB on-board + sideways slots | [[memory/paged-rom]] |
| Display RAM | 32 KB CRTC-addressable (same as Model B) + shadow via ACCCON | [[memory/shadow-ram]] |
| System VIA | 6522 @ &FE40 (sound, keyboard, RTC, screen control) | [[hardware/system-via]] |
| User VIA | 6522 @ &FE60 (user port, printer) | [[hardware/user-via]] |
| CRTC | 6845 (Hitachi HD6845SP — ACCC "type 0") | [[hardware/crtc-6845]] |
| Video ULA | VIDPROC ULA (functionally identical control surface to Model B Video ULA) | [[hardware/video-ula]] |
| Serial | 6850 ACIA + SERPROC | [[hardware/6850-acia]], [[hardware/serial-ula]] |
| ADC | µPD7002 (4 ch, 10-bit, 5 ms conversion) | [[hardware/upd7002-adc]] |
| RTC + CMOS | 146818 with battery backup, 50 bytes CMOS RAM | [[hardware/cmos-rtc]] |
| Internal Tube | Bus on `&FEE0-&FEFF`, CMOS levels, 2 MHz | [[os/tube]] |
| External Tube | Same protocol via Peripheral Bus Controller (PBC) on the 1 MHz bus | [[hardware/1mhz-bus]] |
| 1 MHz bus | Standard BBC 1 MHz bus, page-FC/FD allocations | [[hardware/1mhz-bus]] |
| User port | 8-bit bidirectional + 2 control lines, **unbuffered** | [[hardware/user-via]] |
| RS423 | Enhanced RS232C | [[hardware/serial-ula]] |
| Centronics | Standard parallel printer port (off User VIA) | [[hardware/user-via]] |
| Sound | SN76489AN (3 tones + 1 noise) — driven via System VIA SDB | [[hardware/sn76489]] |

## CPU is a 65C12, not an NMOS 6502

The Master uses the **CMOS 65C12** (sometimes badged "65SC12" — the silicon Acorn shipped is the GTE/CMD 65SC12). This is not the NMOS 6502 of the Model B:

- Added opcodes: `PHX`/`PHY`/`PLX`/`PLY`, `STZ`, `TRB`/`TSB`, `BRA`, `DEA`/`INA`, `BIT abs,X`, `BIT #imm`, `JMP (abs,X)`.
- Added addressing mode: `(zp)` — zero-page indirect without needing X or Y to be zero.
- Several NMOS bugs fixed (e.g. indirect-JMP page wrap; BRK now clears D).
- Slightly different cycle behaviour on a few instructions; the dummy-read patterns differ in places.

The Master's **main CPU does NOT have the Rockwell `BBR`/`BBS`/`RMB`/`SMB` opcodes** — those are R65C02-only, present in the 6502 second processor (3 MHz) and the Master Turbo 65C102 (4 MHz) co-processor, but **not** in the 65C12 fitted to the Master 128's main board (per [[sources/master-arm]] App 8). See [[hardware/6502-isa]] for the full per-instruction table including which opcodes are 65C12 vs R65C02 only. Any timing-critical code lifted from a Model B source needs to be re-checked against the 65C12 cycle table before being trusted on the Master.

## Bus speed and timing

The Master runs at 2 MHz for everything except slow devices, where it drops to 1 MHz exactly like the Model B (see [[timing/cycle-stretching]]):

- **2 MHz**: ROM, RAM (DRAM cycled at 4 MHz, multiplexed CPU↔CRTC), internal Tube.
- **1 MHz**: System VIA, User VIA, ACIA, SERPROC, ADC, 1 MHz bus peripherals, RTC.
- **Measured on real Masters (phX, 2026-11-14): the Video ULA's palette `&FE21` and ACCCON `&FE34` are 2 MHz accesses** — a back-to-back `sta`/`stx &FE21` run changed colour every 4 cycles, and ACCCON writes landed at odd as well as even characters. The CRTC (`&FE01`) is 1 MHz: every write lands on an even C0, back-to-back `sta &FE01` costs 6 cycles ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1, §2; detail on [[timing/cycle-stretching]]).

The DRAM↔CPU↔CRTC arbitration is the same as the Model B: 250 ns slots, two CPU accesses + two CRTC accesses per microsecond, CRTC fetches double as DRAM refresh. The video subsystem is fundamentally unchanged in timing.

## The slow data bus (Port A of System VIA)

Port A of the System VIA is the "slow data bus" — a single 8-bit bus routed to multiple slow peripherals selected by an 8-line addressable latch driven from Port B (PB0-PB3). Full layout in [[hardware/system-via]]. Master-specific reuse:

| SDB destination | Model B | Master |
|---|---|---|
| Latch line 1 | Speech READ | **CMOS R/W direction** |
| Latch line 2 | Speech WRITE | **CMOS DS strobe** |
| Port B PB6 | Speech "interrupt" (input) | **CMOS chip enable** (output) |
| Port B PB7 | Speech "ready" (input) | **CMOS address strobe** (output) |

No speech on the Master — those signals are reclaimed for the 146818. Sound and keyboard latch lines (0 and 3) are unchanged from Model B.

## What's gone

- **TMS5220 speech** — removed. Software calling speech OSWORDs gets a no-op.
- **Cassette tape interface** — physically present on Master 128 but removed on the Compact.
- **Cassette filing system** — not built into Master 128 MOS by default (ROM image available).

## What's new (vs B+)

- **128 KB DRAM** in a uniform map (B+ had 64 KB + 12 KB shadow + sideways RAM, fragmented).
- **CMOS configuration store** — `*CONFIGURE` writes settings that persist across power cycles.
- **ACCCON** at `&FE34` controls shadow RAM, Hazel ROM, Lynne mapping, and tube selection. Replaces the B+'s simpler shadow-control scheme.
- **Cartridge slots** (2) on the back — same bus as sideways ROM but with extra select signals.
- **Internal 65C102 second processor option** (Turbo).
- **LYNNE, HAZEL, ANDY** — three MOS-managed RAM regions:
  - **LYNNE** — 20 KB shadow display RAM, overlays `&3000-&7FFF` via ACCCON D/E/X (lives in DRAM at `&9000-&DFFF` of the second 64 KB). See [[memory/shadow-ram]].
  - **HAZEL** — 8 KB filing-system workspace, overlays MOS VDU driver at `&C000-&DFFF` via ACCCON Y.
  - **ANDY** — 4 KB private RAM, overlays sideways window at `&8000-&8FFF` via ROMSEL bit 7. See [[memory/paged-rom]].
- **Soft character definitions relocated** from `&0C00-&0CFF` (Model B Page C, costs OSHWM if exploded) to `&8900-&8FFF` in the second 32 KB (Master, free). See [[memory/os-workspace]] "second 32 KB workspace map" for the full breakdown.
- **Soft-key buffer relocated** from `&0B00-&0BFF` (Model B, ~256 bytes) to `&8000-&83FF` (Master, 1 KB). Old code that wrote function-key definitions directly into `&0B00` no longer works — use `OSCLI` `*KEY` instead.

## Where to go next

- Memory map detail (where ACCCON puts what): [[memory/memory-map]], [[memory/shadow-ram]].
- CPU instruction-set diff: [[hardware/6502-isa]] (65C12 / R65C02 split documented per-mnemonic).
- Screen display + CRTC multiplexer specifics: [[hardware/crtc-6845]], [[video/hardware-scrolling]].
- Internal Tube vs external Tube: [[os/tube]].
- B/B+/Master cross-model differences: [[synthesis/model-differences]].

## Measured on a Master 128 (2026)

[Edge Grinder](https://github.com/kieranhj/edge-beeb) is a C64 port built on the Master specifically (shadow-RAM double buffer, ANDY + HAZEL + four sideways banks for a 349-second tune, a VideoNuLA test build), and its measurements — all in jsbeeb through an MCP, real hardware only where stated — are filed where they belong: ACCCON, the in-frame display switch, HAZEL and BREAK on [[memory/shadow-ram]]; ANDY's true extent (4K, ROMSEL bit 7, overlaying only `&8000-&8FFF`, and why the test must be machine code) on [[memory/paged-rom]]; `&FFFE = &E59E` and the reclaimable low pages on [[os/interrupts]] and [[memory/os-workspace]]; the hardware-wrap sizes on [[hardware/system-via]]; the NuLA registers on [[hardware/video-ula]]; the measured internal key numbers on [[os/keyboard]]. Source: [[sources/beeb-port-kit-hardware-facts]]. A real Master 128 also runs the Model B [Paradroid](https://github.com/kieranhj/paradroid-beeb) port (reported by KC, 2026-09-06) — the first time either port ran on hardware rather than an emulator; real B, B+ and second processors remain untested.

### Later Master projects, on real hardware (2026-09 to 11)

From [[sources/beeb-port-kit-hardware-facts-2026-11]] §4 "Real hardware":

- **1942** (arcade → Master 128 only) **plays on a real Master 128** from a Gotek (2026-09-28) and a real 5.25" drive 1 at `*CONFIGURE FDRIVE 3` (2026-10-12): shadow double buffering, a mid-frame ACCCON D flip, HAZEL and ANDY paged through play, its own 1770 driver, background disc reads in play. What real hardware found that jsbeeb did not: the 1770's per-command head settle, the drive and step rate (see [[hardware/wd1770]]), BREAK not clearing RAM ([[os/break-intercept]]), a garbage line on a transition and a stage-28 lock-up. The kit's lesson: **put real hardware in the loop at the first layer that touches the disc, the CRTC or BREAK** — 1942's first real play was day 22 of 47.
- **phX** (CPC demo → Master 128 only) took that lesson from day one, on **KC's two Masters** (the original with a Sony RGB CRT, a Cherry Master with a CUB RGB CRT) through a hardware-test disc of 21 programs and a second of four (`phX/docs/hwtest.md`). Found on hardware and not in jsbeeb 2.10.2: palette and R8 writes acting early, the MA13 alternate-character flip, the monitors' black-level clamp and visible windows (on [[hardware/crtc-6845]], [[hardware/video-ula]]), the 1770's early READ ADDRESS INTRQ ([[hardware/wd1770]]). Cards 1-9 and A-E agreed on both Masters for every chip fact. Also measured real: ACCCON D mid-line acts at the character written; with D set the 6845 reads HAZEL below `&3000` ([[memory/shadow-ram]]); banks 4-7 are sideways RAM on a stock machine ([[memory/paged-rom]]).
- **Stryker's Run** (a 1986 BBC game rebuilt and optimised; Master 128 and Model B + SWR) is jsbeeb-and-b2 only so far: its HUD rupture seen on b2, the Model B build played on b2 (KC, 2026-10-23/25). Its Master MOS 3.20 facts (the tick's cost, VSync lost by chaining, HAZEL as data) are on [[os/interrupts]] and [[memory/shadow-ram]].
- **The Master MOS is not the Model B's in the corners**: `&028C` read `&FF` under a `*RUN` boot ([[memory/os-workspace]]); a `*RUN` from `!BOOT` arrives with interrupts disabled, so a boot program waiting in OSRDCH waits for ever until it does `CLI` (phX, jsbeeb Master).
- **A real Master's RAM powers up with junk that survives BREAK**; jsbeeb zeroes RAM and HAZEL ([[tools/emulators]]).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
