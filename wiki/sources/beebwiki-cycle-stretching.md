---
title: "BeebWiki: Cycle stretching"
type: source
tags: [timing, cycle-stretching, 1mhz, slow-bus, performance]
url: https://beebwiki.mdfs.net/Cycle_stretching
updated: 2026-05-14
---

# BeebWiki — Cycle stretching

**URL:** https://beebwiki.mdfs.net/Cycle_stretching

## Summary

Brief but high-value page. Documents the BBC's mechanism for slowing the 6502 clock when accessing 1 MHz peripherals — and crucially, the **complete list of devices that trigger stretching**. We previously documented this only for `&FC`/`&FD` (FRED/JIM) on [[hardware/1mhz-bus]]; in fact it applies to most of `&FE00-&FEFF` (SHEILA) too. This is critical performance information: every `LDA &FE40` (System VIA) or `LDA &FE00` (CRTC) costs more than a normal `LDA abs`.

## Key technical claims

### Bus speeds

- **I/O bus**: 2 MHz (CPU's normal speed).
- **DRAM bus**: 4 MHz (shared with CRTC).
- **1 MHz peripherals**: stretched.

### Devices that force 1 MHz access

| Address range | Device |
|---|---|
| `&FE00-&FE07` | 6845 CRTC |
| `&FE08-&FE0F` | 6850 ACIA |
| `&FE10-&FE17` | Serial ULA |
| `&FE18` | STATID (Econet station ID, BBC B/B+) |
| `&FE40-&FE5F` | System VIA |
| `&FE60-&FE7F` | User VIA |
| `&FEC0-&FEDF` | µPD7002 ADC (BBC B/B+) |
| `&FC00-&FCFF` | FRED (1 MHz bus) |
| `&FD00-&FDFF` | JIM (1 MHz bus) |
| IC 100 ROM | 2 MHz default; 1 MHz via link S18 |

(Everything *not* on this list runs at 2 MHz: main RAM, sideways ROM, MOS ROM, the Video ULA `&FE20-&FE2F`, the Tube `&FEE0-&FEFF`, the 8271/1770 FDC, the ACCCON / ROMSEL / NMI / Memory-control registers in `&FE30-&FE3F`.)

### Mechanism

When the CPU accesses a 1 MHz address: IC 23 raises pin 8, connecting to IC 33 pin 1, which modifies the 6502's ΦIN input — extending the current cycle to **twice or three times** its normal length.

> The ambiguity occurs because the cycle may have started in or out of sync with the 1 MHz clock.

So a single instruction that accesses a 1 MHz peripheral pays a variable extra cost depending on when in the 1 MHz phase the access lands. In the worst case the CPU stalls until the next 1 MHz tick before the access completes, then the access itself takes a full 1 MHz cycle (= 2 CPU cycles).

### Practical performance impact

- A normal `LDA abs` (4 cycles) costs **5-6 cycles** when targeting a stretched address.
- `INC abs` (6 cycles) costs **7-9 cycles** at a stretched address (RMW = two bus cycles, both stretched).
- Tight VIA polling loops, IRQ handlers that touch IFR/IER, and any per-frame CRTC writes pay this penalty on every access.
- The variability (2c vs 3c stretch) makes cycle-exact code involving 1 MHz peripherals *non-deterministic* unless you sync to the 1 MHz phase first (e.g. by reading a known-stretched address to align).

## Cross-check against existing wiki

| Claim | Wiki state | Resolution |
|---|---|---|
| `&FC`/`&FD` accesses are stretched | covered in [[hardware/1mhz-bus]] | confirmed |
| Stretching also applies to CRTC/ACIA/Serial-ULA/VIAs/ADC | **NOT documented** | **add to a new [[timing/cycle-stretching]]** |
| Stretch is 2× or 3× depending on phase | only "2 cycles" hand-waved on 1mhz-bus.md | **clarify** |
| Mechanism: IC 23 → IC 33 → 6502 ΦIN | not documented | add to source-page; mention briefly in entity page |
| Video ULA, ACCCON, Tube, FDC, ROM are NOT stretched | implicit but not stated | **add explicit "what is NOT stretched" note** to new page |

## Filed into

- Created: [[timing/cycle-stretching]] — new dedicated page.
- Updated: [[hardware/1mhz-bus]] — clarify variable 2-3 cycle penalty; cross-link to new page; note that the same mechanism applies to most SHEILA addresses, not just FRED/JIM.

## Notes

The "2 or 3 cycles" wording is important. The Advanced User Guide (cited by BeebWiki, p443) gives the timing in detail; we should also revisit AUG when ingested. NAUG §11.1 lists peripheral addresses but does not call out which ones cost a stretch.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
