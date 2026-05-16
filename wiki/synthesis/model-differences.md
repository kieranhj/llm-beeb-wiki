---
title: BBC Model B / B+ / Master / Master Compact differences
type: synthesis
tags: [models, compatibility, b, b-plus, master, compact, differences]
sources: [master-arm, naug-ch11-hardware]
updated: 2026-05-16
---

# BBC Model B / B+ / Master 128 / Master Compact — what differs

Synthesised from [[sources/master-arm]] Appendices 1, 2, and 3 (which respectively cover Model B → B+, B/B+ → Master 128, and Master 128 → Master Compact). Use this as a quick lookup when a question is "does feature X work on machine Y?"

This page focuses on differences that **matter for performance / demo work**. Productivity-app differences (VIEW, Viewsheet, BASIC text editing) are out of scope.

## At-a-glance

| Feature | Model B | Model B+ | Master 128 | Master Compact |
|---|---|---|---|---|
| CPU | NMOS 6502 @ 2 MHz | NMOS 6502 @ 2 MHz | 65C12 (CMOS) @ 2 MHz | 65C12 @ 2 MHz |
| Main RAM | 32 KB | 64 KB (32 + 12 KB SWR + 20 KB shadow) | 128 KB | 128 KB |
| Sideways slots | 4 ROM | 4 ROM + 12 KB SWR (`&8000-&AFFF`) | 16 (4 + 12 internal) | 4 (3 × 16K + 1 × 16/32K) |
| Sideways RAM stock | 0 | 12 KB | 4 KB (ANDY) | 4 KB (ANDY) |
| Shadow RAM | No | 20 KB (single S bit) | 20 KB (LYNNE — D/E/X split) | 20 KB |
| HAZEL FS RAM | — | — | 8 KB at `&C000-&DFFF` | 8 KB |
| RTC | — | — | 146818 + 50 B CMOS | EEPROM only (1000 writes/loc, 128/256 B), **no clock** |
| FDC | 8271 (Intel) optional | 1770 (Western Digital) optional | 1770 | 1772 (faster) |
| Tube | Optional external | Optional external | External + **internal** (65C102 Turbo, 80186, Z80) | **No Tube** (connector deleted) |
| 1MHz bus | Yes | Yes | Yes | **No** (connector deleted) |
| User port | Yes | Yes | Yes | **Reduced** — only PB0-PB4 + 2 control bits on joystick port |
| Cassette FS | Built-in | Built-in | Built-in (image) | **Deleted** |
| Speech (TMS5220) | Optional | Optional | **Removed** (slot reused for RTC) | — |
| Analogue port (ADC) | Yes | Yes | Yes | **No** (digital joystick only) |
| Cartridge slots | — | — | 2 (standard) | 1 (expansion port, different pinout) |
| Composite video | Colour | Colour | Colour | **Monochrome only** |
| TV out | Yes | Yes | Yes | **No** |
| 6502 2P cycle time | 0.33 µs (3 MHz) | 0.33 µs | 0.33 µs / 0.25 µs (Turbo 65C102) | — |
| MOS version | 1.20 | 2.00 | 3.20 / 3.50 (Compact) / 4.x (ET) | 5.x |

## Memory map differences

### Address map summary

```
       Model B          Model B+         Master 128        Master Compact
  &7FFF screen end      same             same              same
  &3000 screen start    same             same + LYNNE      same + LYNNE
  &1900 typical DFS     same             &0E00 (HAZEL)     &0E00
        OSHWM
  &0E00 baseline        same             same              same
        OSHWM
```

### Soft character relocation (Master)

| Machine | Soft chars 224-255 stored at | Cost to OSHWM |
|---|---|---|
| Model B / B+ | `&0C00-&0CFF` (page C, in low RAM) | 256 bytes if exploded |
| Master 128 / Compact | **`&8900-&8FFF` in second 32 KB** | 0 bytes |

Code that writes directly to `&0C00`-area for font definitions does *not* work on Master — use OSWORD `&0A`/`&0B` or write to `&8900` directly (with appropriate paging).

### Soft-key buffer relocation (Master)

| Machine | Soft keys stored at | Cost to OSHWM |
|---|---|---|
| Model B / B+ | `&0B00-&0BFF` (page B, in low RAM) | up to 256 bytes |
| Master 128 / Compact | **`&8000-&83FF` in second 32 KB** | 0 bytes |

Same notice: direct `&0B00`-area pokes for `*KEY` definitions don't work on Master.

### ACCCON (`&FE34`) bit layout

| Bit | B+ | Master |
|---|---|---|
| 0 | S (shadow on/off) | D (display from LYNNE) |
| 1 | unused | E (auto-shadow for CPU) |
| 2 | unused | X (force-shadow for CPU) |
| 3 | unused | Y (HAZEL on) |
| 4 | unused | ITU (internal Tube enable) |
| 5 | unused | IFJ (FRED/JIM → cartridge vs 1MHz bus) |
| 6 | unused | TST (factory test — leave 0) |
| 7 | unused | IRR (force IRQ) |

The B+ only has the single S bit (write `&80` to enable both display+VDU-write to shadow, `&00` for main). Master needs the D/E/X separation to enable double-buffered animation. See [[memory/shadow-ram]] for the full mechanism.

### ROMSEL (`&FE30`) RAM-select bit

| Machine | Bit 7 = 1 enables | Range |
|---|---|---|
| Model B / Electron | nothing (bit unused) | — |
| Model B+ | 12 KB paged RAM | `&8000-&AFFF` |
| Master 128 / Compact | 4 KB ANDY | `&8000-&8FFF` |

### Second 32 KB (Master only)

See [[memory/os-workspace]] "Master second 32 KB workspace map" for the full breakdown. Key chunks:
- `&3000-&7FFF`: LYNNE (shadow display)
- `&8000-&83FF`: soft-key buffer
- `&8400-&88FF`: VDU flood-fill workspace
- `&8900-&8FFF`: soft character definitions
- `&C000-&DBFF`: HAZEL (paged-ROM workspace)
- `&DC00-&DCFF`: MOS CLI buffer
- `&DD00-&DEFF`: transient utility workspace
- `&DF00-&DFFF`: MOS private workspace

## CPU differences

### Master uses 65C12 (CMOS)

- **Added opcodes**: `BRA`, `DEA`/`INA`, `PHX`/`PHY`/`PLX`/`PLY`, `STZ`/`CLR`, `TRB`, `TSB`.
- **Added addressing mode**: `(zp)` — zero-page indirect without needing X or Y to be zero. Opcodes end `&x2`.
- **NMOS bugs fixed**: `JMP (ind)` page-wrap fixed (and now takes 6c not 5c); BRK clears D flag (NMOS doesn't); read-modify-write instructions don't do the spurious-write-then-write dummy cycle.

See [[hardware/6502-isa]] for the per-instruction tables. **R65C02 (Rockwell)** adds `BBR0..7`/`BBS0..7`/`RMB0..7`/`SMB0..7` on top of 65C12 — but Master's main CPU is **plain 65C12** (no Rockwell ops). Only the **6502 2P** (3 MHz) and **Master Turbo 65C102** (4 MHz) have those.

### Tube co-processor speeds

| Variant | Clock | Cycle | Where |
|---|---|---|---|
| Main 6502/65C12 (host) | 2 MHz | 0.5 µs | All models |
| 6502 SP (external) | 3 MHz | 0.33 µs | Model B+ / Master external Tube |
| Master Turbo 65C102 | 4 MHz | 0.25 µs | Master internal Tube |

## Filing system differences

| Operation | DFS (B) | DFS (B+, 1770) | ADFS (Master) | ADFS (Compact, 1772) |
|---|---|---|---|---|
| FDC | 8271 | 1770 | 1770 | 1772 |
| Direct FDC programming | Yes (8271) | Yes (1770) | Yes (1770) | Yes (1772) |
| Tracks | 40 / 80 | 40 / 80 | 80 / 80 | 80 (3.5") |
| Format/verify | external utility | in ROM | in ROM | in ROM |
| Sector skew | — | — | 9 | 4 |
| Sub-directories | No | No | Yes | Yes |

Master Compact's 1772 + sector skew 4 noticeably faster than Master 128's 1770. Software writing directly to FDC registers needs to know which chip is fitted — see [[hardware/wd1770]].

## Video differences

The CRTC (6845), Video ULA, and SAA5050 are functionally identical across B/B+/Master/Compact, so [[hardware/crtc-6845]], [[hardware/video-ula]], [[hardware/saa5050]], and all the demo techniques ([[techniques/vertical-rupture]], [[techniques/rvi]], [[techniques/single-rasterline-rupture]], etc.) **port unmodified** between models.

**Per-mode register defaults are identical** between B / B+ / Master — see [[hardware/crtc-6845]] table. Modes 128-135 are shadow modes 0-7 (B+ + Master only).

What differs:
- **Shadow modes** require B+ or Master.
- **Master Compact composite output is monochrome** — colour only via RGB.
- **Master's 640×512 interlaced 2-colour mode** ([[techniques/interlaced-640x512]]) requires both main and LYNNE banks — works only on Master 128 or Master Compact.
- **Hardware scroll-wraparound MASK bits** (HS0/HS1 on the System VIA addressable latch) are the same across all models, with the same per-mode values.

## IO differences

| Interface | Model B | B+ | Master 128 | Compact |
|---|---|---|---|---|
| System VIA (`&FE40`) | Yes | Yes | Yes | Yes — but Port B reused for CMOS / EEPROM |
| User VIA (`&FE60`) | Full | Full | Full | Reduced (PB5-7 on expansion, PB0-4 on joystick) |
| Centronics printer | Via User VIA | Via User VIA | Via User VIA | 24-pin Delta-ribbon socket |
| Serial RS423 | Yes | Yes | Yes | Optional (4 ICs to fit) |
| 1MHz bus | Yes | Yes | Yes | **No** |
| Cassette | Yes | Yes | Yes | **No** |
| Speech (`&FE60`-area) | Optional | Optional | **Removed** | — |
| RTC (`&FE40` slow bus) | — | — | 146818 + 50B CMOS | EEPROM only, no clock |

## New OSBYTEs / *commands on Master (vs B+)

| OSBYTE | Name | Function |
|---|---|---|
| `&6B` (107) | TUBESEL | Switch internal/external 1MHz bus or Tube |
| `&6C` (108) | SHADRAM | CPU view of `&3000-&7FFF`: main (0) / shadow (1) |
| `&6D` (109) | TEMPFS | Make temporary filing system permanent |
| `&70` (112) | WRSCRN | VDU writes to main (1) / shadow (2) |
| `&71` (113) | RDSCRN | CRTC reads from main (1) / shadow (2) |
| `&72` (114) | SHADOW | Set shadow state at next mode |
| `&A1` (161) | RDCMOS | Read CMOS RAM byte |
| `&A2` (162) | WRCMOS | Write CMOS RAM byte |
| `&A4` (164) | RDPROC | Check processor type |

New `*` commands include `*CONFIGURE`, `*STATUS`, `*INSERT`, `*UNPLUG`, `*SHADOW`, `*GO`, `*GOIO`, `*EX`, `*INFO`, `*ROMS`, `*SHOW`, `*SHUT`, `*MOVE`, `*COPY`, `*SRDATA`, `*SRROM`, `*SREAD`, `*SRWRITE`, `*BUILD`, `*APPEND`, `*CREATE`, `*DELETE`, `*REMOVE`, `*RENAME`, `*DUMP`, `*LIST`, `*PRINT`, `*TYPE`, `*TIME`.

## Detecting which machine

Best practice: `OSBYTE &81` (`INKEY-256`) with X=0, Y=255:

| X returned | Machine |
|---|---|
| `&00` | BBC Model A/B version 0.1 |
| `&01` | Electron |
| `&FA` | ABC |
| `&FB` | Model B+ (MOS 2.00) |
| `&FE` | BBC USA |
| `&FF` | BBC Model B (MOS 1.0/1.2) |
| `&FD` (253) | Master (MOS 3.x) |
| `&F7` (247) | Master (MOS 4.x — Econet Terminal) |
| `&F5` (245) | Master Compact (MOS 5.x) |

Or `OSBYTE 0` with X≠0: returns X=3 for Master 128.

For finer-grained processor detection (NMOS vs CMOS vs Rockwell), use `OSBYTE &A4` (164) — returns the processor type in X.

## Pitfalls when targeting "all models"

- Don't poke `&0B00-&0BFF` for soft keys (Master uses `&8000`).
- Don't poke `&0C00-&0CFF` for soft chars (Master uses `&8900`).
- Don't read `&FE40` Port B PB6/PB7 for speech (Master uses these for CMOS).
- Don't depend on RTC being present (Compact has no clock).
- Don't depend on cassette (Compact has none).
- Don't depend on 1MHz bus (Compact has none).
- Don't depend on full User VIA (Compact splits across two connectors).
- Don't depend on shadow RAM (Model B has none).
- Don't depend on ANDY (Model B has none; B+ has 12 KB; Master has 4 KB).
- Don't depend on Tube (Compact has none).
- Hardware scrolling, custom MODE, CRTC rupture techniques: **all portable across B/B+/Master/Compact** with no changes — these are pure 6845 + Video ULA + address translator work.

## See also

- [[hardware/master-overview]] — Master-specific hardware orientation.
- [[memory/shadow-ram]] — ACCCON deep dive.
- [[memory/paged-rom]] — ROMSEL + sideways RAM.
- [[memory/os-workspace]] — Master second-32K workspace map.
- [[hardware/6502]] — CPU variants and clock rates.
- [[sources/master-arm]] App 1, 2, 3 — source detail.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
