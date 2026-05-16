---
title: Memory Map
type: memory
tags: [memory, address-space, fred, jim, sheila]
sources: [naug-ch12-memory, naug-ch13-video, allmem-ripley-harston, master-rm]
updated: 2026-05-14
---

# Memory Map

64 KB visible to the 6502 across all BBC family machines. The common layout:

```
&FFFF +--------------------------------------+
      | MOS ROM (vectors)              &FF00 | 256 B
&FF00 +--------------------------------------+
      | SHEILA -- memory-mapped I/O    &FE00 | 256 B
&FE00 +--------------------------------------+
      | JIM -- 1 MHz bus / cartridge   &FD00 | 256 B
&FD00 +--------------------------------------+
      | FRED -- 1 MHz bus / cartridge  &FC00 | 256 B
&FC00 +--------------------------------------+
      | MOS ROM                              | ~15 KB
&C000 +--------------------------------------+
      | Paged ROM / Sideways RAM (1 of 16)   | 16 KB
&8000 +--------------------------------------+
      | Screen RAM (mode-dependent base)     | up to 20 KB
&3000 +--------------------------------------+
      | User RAM + MOS workspace + lang/BASIC| 12 KB
&0000 +--------------------------------------+
```

Source: NAUG §12.1 p155-156.

## Sub-regions in user RAM (`&0000-&2FFF`)

| Range | Use |
|---|---|
| `&0000-&00FF` | Zero page. User zero page at `&70-&8F` (Ch2 §2.10). MOS uses most of the rest. |
| `&0100-&01FF` | Stack |
| `&0200-&02FF` | OS vectors, OS variables |
| `&0300-&03FF` | VDU driver workspace + filing system buffers (see [[memory/os-workspace]]) |
| `&0400-&07FF` | Currently-selected language (BASIC) workspace + OS workspace |
| `&0800-&08FF` | Sound / printer / keyboard buffers (default) |
| `&0900-&09FF` | RS423/cassette buffer |
| `&0A00-&0AFF` | Keyboard buffer |
| `&0B00-&0BFF` | User-defined function-key strings |
| `&0C00-&0CFF` | User-defined character definitions (ASCII 224-255) |
| `&0D00-&0DFF` | NMI handler (1 page) |
| `&0E00-…` | DFS / other filing system workspace, then user program (PAGE) |

`PAGE` (BASIC) / `OSHWM` (MOS) marks the start of user program memory. On Model B with DFS, that's typically `&1900`. Master with HAZEL filing-system RAM enabled, that's `&0E00` (DFS workspace moved into HAZEL).

## SHEILA address allocations (`&FE00-&FEFF`)

| Range | Device | Notes |
|---|---|---|
| `&FE00-&FE07` | [[hardware/crtc-6845]] 6845 CRTC (address @ `&FE00`, data @ `&FE01`) | All machines except Electron |
| `&FE08-&FE0F` | 6850 ACIA (serial) | All BBC; Electron only if serial expansion fitted |
| `&FE10-&FE17` | Serial ULA | All machines |
| `&FE18` | Econet station number | Master / Compact |
| `&FE18-&FE1A` | µPD7002 ADC | **Electron only** (ADC moves here on Electron) |
| `&FE20-&FE2F` | [[hardware/video-ula]] Video ULA (control @ `&FE20`, palette @ `&FE21`) | All machines |
| `&FE24` | Floppy disc control register | Master / Compact |
| `&FE28-&FE2F` | WD1770 FDC | Master / Compact |
| `&FE30-&FE33` | [[memory/paged-rom]] ROM paging register | All machines |
| `&FE34-&FE37` | [[memory/shadow-ram]] ACCCON register | B+ / Master / Compact |
| `&FE38` | INTOFF — Network NMI disable | B+ / Master |
| `&FE3C` | INTON — Network NMI enable | B+ / Master |
| `&FE40-&FE5F` | [[hardware/system-via]] System VIA | All machines |
| `&FE60-&FE7F` | [[hardware/user-via]] User/Printer VIA | All machines |
| `&FE80-&FE9F` | 8271 FDC (Model B) / 1770 FDC (B+/Master) | — |
| `&FEA0-&FEBF` | 68B54 Econet ADLC | If Econet fitted |
| `&FEC0-&FEDF` | µPD7002 ADC | BBC; on Master also Econet interface |
| `&FEE0-&FEFF` | [[hardware/tube-ula]] Tube ULA | All except Electron |

Most peripheral registers repeat (mirror) across their 32-byte block — only certain low addresses are functional.

## Per-MODE screen base

See [[video/modes]]. Range is always inside `&3000-&7FFF`; the base depends on screen size: `&3000` for 20 KB modes, `&4000` for 16 KB (MODE 3), `&5800` for 10 KB (MODE 4/5), `&6000` for 8 KB (MODE 6), `&7C00` for 1 KB (MODE 7).

## Machine extras beyond the common map

- **Model B**: as above. 16 KB MOS, 16 KB sideways for languages.
- **B+**: adds 20 KB shadow RAM and 12 KB paged RAM (bit 7 of `&FE30` selects). Total RAM 64 KB on B+, 128 KB on B+128.
- **Master 128**: 20 KB shadow RAM, **ANDY** (4 KB private at `&8000-&8FFF`, selected via ROMSEL `&FE30` bit 7), **HAZEL** (8 KB filing-system RAM at `&C000-&DFFF`, selected via ACCCON `Y` bit), 4 KB private MOS workspace, plus 16 sideways slots (some RAM, some ROM).
- **Master Compact**: similar with adjusted ROM map.
- **Electron**: Model-B-equivalent map; no shadow RAM, no Tube, video ULA combined with CPU clock generation. ADC moves to `&FE18-&FE1A`. Electron ULA functions at `&FE00-&FE0F`.

See [[memory/paged-rom]] and [[memory/shadow-ram]] for the details.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
