---
title: Cycle Stretching
type: timing
tags: [timing, cycle-stretching, 1mhz, slow-bus, performance, sheila]
sources: [beebwiki-cycle-stretching, naug-ch11-hardware, naug-ch23-1mhz-bus]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-05-14
---

# Cycle Stretching

The 6502 runs at 2 MHz. Several BBC peripherals run at 1 MHz. To bridge the gap, the BBC's clock generator **stretches** the 6502's ΦIN clock whenever the CPU addresses one of the slow devices — extending the current cycle to 2 or 3 normal-cycle lengths so the slow device has time to respond.

Net effect: every `LDA &FE40` (System VIA), every `LDA &FE00` (CRTC), every `LDA &FC00`/`&FD00` (1 MHz bus) is **5-6 cycles**, not 4. RMW instructions (`INC abs`, `LSR abs`, etc.) pay it on both bus cycles. This dwarfs almost every other concern in tight 6502 code that talks to peripherals.

## Which addresses are stretched

| Address range | Device | Stretched? |
|---|---|---|
| `&0000-&7FFF` | Main RAM | No (2 MHz) |
| `&8000-&BFFF` | Sideways ROM/RAM | No (2 MHz) |
| `&C000-&FBFF` | MOS ROM | No (2 MHz) |
| `&FC00-&FCFF` | FRED | **Yes** |
| `&FD00-&FDFF` | JIM | **Yes** |
| `&FE00-&FE07` | 6845 CRTC | **Yes** |
| `&FE08-&FE0F` | 6850 ACIA | **Yes** |
| `&FE10-&FE17` | Serial ULA | **Yes** |
| `&FE18` | STATID (Econet station ID, BBC B/B+) | **Yes** |
| `&FE20-&FE2F` | Video ULA | No (2 MHz) |
| `&FE30-&FE3F` | ROMSEL / ACCCON / Memory control | No (2 MHz) |
| `&FE40-&FE5F` | System VIA | **Yes** |
| `&FE60-&FE7F` | User VIA | **Yes** |
| `&FE80-&FE9F` | 8271 / 1770 FDC | No (2 MHz) |
| `&FEA0-&FEBF` | 68B54 Econet ADLC | No (2 MHz) |
| `&FEC0-&FEDF` | µPD7002 ADC (BBC B/B+) | **Yes** |
| `&FEE0-&FEFF` | Tube ULA | No (2 MHz) |
| `&FF00-&FFFF` | MOS jumpblock + 6502 vectors | No (2 MHz) |

(Source: [[sources/beebwiki-cycle-stretching]].)

**The Video ULA, the Tube, the FDC, and the ROMSEL/ACCCON registers are NOT stretched** — surprising-but-true. Video ULA palette writes (`STA &FE21`) cost a flat 4 cycles; CRTC register writes (`STA &FE01`) cost 5-6.

The Master cartridge slot via the `&FCFC-&FCFF` page-wide register can be switched to 2 MHz access (OSBYTE `&6B` X=1, or ACCCON `IFJ` bit) — see [[hardware/1mhz-bus]] Master cartridge section.

## How much it costs

The stretch is **variable**: 2 or 3 normal-cycle equivalents, depending on whether the access started in or out of phase with the 1 MHz clock. Worst-case timing for common instructions:

| Instruction | Normal cost | Stretched cost (worst case) |
|---|---|---|
| `LDA abs` / `STA abs` | 4c | 5-6c |
| `LDA abs,X` (no page cross) | 4c | 5-6c |
| `LDA (zp),Y` (no page cross) | 5c | 6-7c |
| `INC abs` / `LSR abs` (RMW) | 6c | 7-9c |
| `BIT abs` | 4c | 5-6c |

The extra is +1c or +2c per stretched bus cycle. RMW instructions touch the bus twice, so they get hit twice.

### Why 2 OR 3 cycles?

The CPU's 2 MHz clock and the 1 MHz peripheral clock are not phase-locked from the CPU's perspective. When a stretched access begins, the clock generator has to wait for the next 1 MHz rising edge before letting the cycle proceed:

- If the CPU's bus cycle started just before a 1 MHz edge: small extra wait → +1c overall.
- If just after: must wait nearly a full 1 MHz period → +2c overall.

In practice a tight loop that hits a stretched address each iteration sees both stretches alternating, but you can't predict which on a single access without phase-aligning first.

### Phase-aligning to the 1 MHz clock

Reading any stretched address forces the CPU into sync with the 1 MHz phase. After the access, the CPU's next action lands on a known 1 MHz boundary. So:

```asm
LDA &FE40       ; sync read — discard A; aligns next access to 1 MHz
                ; subsequent stretched accesses now have predictable cost
```

Useful before doing cycle-exact raster work that touches the System VIA timer (`T1`) or the CRTC.

## Mechanism (low-level)

When the CPU's address bus selects a 1 MHz address, IC 23 detects the match and raises pin 8. This connects to IC 33 pin 1, which gates the ΦIN signal feeding the 6502. The result: the current cycle is extended until the slow device has been given a full 1 MHz period to respond.

Devices on the I/O bus see normal 2 MHz timing; devices flagged as 1 MHz see slow timing; the CPU sees an extended cycle.

## Why this matters for performance code

- **Polling a VIA timer / IFR is expensive.** Every `LDA &FE4D` (System VIA IFR) is a stretched access. If you're tight-polling for vsync (CA1 = bit 1) you're paying 5-6c per check, not 4. Compare against using the IRQ.
- **CRTC reprogramming is expensive.** Writing R12/R13 for a hardware scroll = 4 stretched accesses (`STA &FE00`, `STA &FE01`, `STA &FE00`, `STA &FE01`) = 20-24c, not 16. Negligible per frame but adds up for split-screen or per-line tricks.
- **The Video ULA is FAST.** Palette flips for raster splits cost 4c per write — much cheaper than CRTC writes. Prefer the Video ULA for mid-frame work where possible.
- **VIA-based per-line timing is hard.** Setting up a T1 timer to fire on a precise scanline involves stretched writes whose total varies by 1-2c. Phase-align with a sync read first.
- **The Tube is fast.** Tube transfers via `&FEE0-&FEFF` are *not* stretched — the Tube ULA bridges the 2 MHz I/O bus and the 4 MHz parasite bus internally. This is part of why Tube I/O can compete with main-RAM access for bulk transfers.

## Comparison with the 1 MHz bus

The 1 MHz expansion bus (FRED `&FC`, JIM `&FD`) is the canonical "stretched" address space and the most discussed case (NAUG Ch23). What's often missed is that *the same mechanism applies to all SHEILA peripherals listed above*. The 1 MHz bus is just the externally-exposed end of the same slow-bus arrangement.

See [[hardware/1mhz-bus]] for the cartridge / FRED / JIM specifics, including the Master cartridge's optional 2 MHz mode.

## See also

- [[hardware/1mhz-bus]] — FRED/JIM in detail, cartridge slot.
- [[hardware/system-via]], [[hardware/user-via]], [[hardware/crtc-6845]] — the most-touched stretched peripherals.
- [[hardware/video-ula]] — fast (un-stretched) — preferred for raster tricks.
- [[hardware/tube-ula]] — un-stretched, useful for bulk Tube transfers.
- [[memory/memory-map]] — full address-space layout.
- [[sources/beebwiki-cycle-stretching]] — primary reference.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
