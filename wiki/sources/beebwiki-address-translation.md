---
title: "BeebWiki: Address translation"
type: source
tags: [memory, dram, address-translation, crtc, video, scrolling]
url: https://beebwiki.mdfs.net/Address_translation
updated: 2026-05-14
---

# BeebWiki — Address Translation

**URL:** https://beebwiki.mdfs.net/Address_translation
**Page edited:** 2022-05-06
**Original contributor:** User:beardo (2007-03-20)

## Summary

The single most important reference for understanding how the BBC's discrete-logic address translator (IC 8-15, IC 32, IC 39) maps the CPU's 16-bit address space and the CRTC's `MA0-MA13`/`RA0-RA2` outputs onto the 15-bit DRAM address space (`DA0-DA14`). The page also explains *why* the BBC has this translator (rather than a ULA), and how the wraparound mechanism for hardware scrolling is implemented.

## Key technical claims

### DRAM organisation

- 15-bit DRAM address space, diplexed onto a 7-bit bus running at 8 MHz (two addresses per 4 MHz cycle).
- `DA14` = bank select (Model A: single bank, `DA14` unused).
- `DA13-DA7` = column address; `DA6-DA0` = row address.
- The R/~W line is gated by buffer ICs and only lowered when the column address is transmitted AND the CPU is writing.

### Three translation modes

Selected by combining the 2 MHz monotonic clock and the CRTC's `MA13`:

| 2 MHz | MA13 | Mode | Path |
|---|---|---|---|
| Low | x | **CPU** | A0-A14 → DA0-DA14 direct (no DRAM refresh guarantee) |
| High | High | **TTX VDU** | MA → SAA 5050 input |
| High | Low | **HI RES** | MA, RA → Video ULA input |

CPU mode gating: ROW via IC 12, COL via IC 13.
TTX mode gating: ROW via IC 10, COL via IC 11.
HI RES mode gating: ROW via IC 8, COL via IC 9.

### CPU mode

Direct A → DA mapping. **No automatic DRAM refresh** — refresh is provided "incidentally" by the video fetches in TTX/HI RES modes.

### TTX VDU mode (MODE 7)

| DA14 | DA13-DA10 | DA9-DA7 | DA6 | DA5-DA0 |
|---|---|---|---|---|
| AA3 | all 1 | MA9-MA7 | MA6 ⊕ ~1MHz | MA5-MA0 |

- MOS programs `MA11=1, MA12=0`, so `AA3=1` always in MODE 7.
- `MA6` is XORed with the 1 MHz clock so two distinct bytes are fetched per microsecond. IC 15 delivers one to the SAA 5050, discards the other. **Result:** all 128 DRAM rows are refreshed every scanline → max refresh interval **88 µs**. Without this trick it would be 1.96 ms (DRAM out of spec).

### HI RES mode (MODES 0-6)

| DA14-DA11 | DA10-DA3 | DA2-DA0 |
|---|---|---|
| AA3-AA0 | MA7-MA0 | RA2-RA0 |

Where `AA3-AA0` (adjusted address) = `MA11-MA8` with the wraparound correction applied (see below).

**Maximum refresh intervals per mode:**
- MODES 0-2: 480 µs
- MODES 4-5: 488 µs
- MODE 3: 608 µs
- MODE 6: 616 µs

### Wraparound mechanism

When the CRTC's MA12 overflows (i.e. `MA` would cross into ROM space), hardware substitutes a wraparound address by subtracting a mode-dependent amount from MA. The mechanism:

1. **State:** System VIA addressable latch (IC 32) carries 2 bits (C0, C1) encoding display size.
2. **Decode:** Logic gates produce a one's-complemented "2K-unit count" feed for IC 39.
3. **Subtract:** IC 39 (quad adder) subtracts from the relevant address lines.
4. **Diplex:** Result fed to IC 9.

**Wraparound table:**

| MA12 | C1 | C0 | Subtract | Restart addr | Modes |
|---|---|---|---|---|---|
| 0 | x | x | 0 | n/a | 0-6 |
| 1 | 0 | 0 | `&4000` | `&4000` | 3 |
| 1 | 0 | 1 | `&2000` | `&6000` | 6 |
| 1 | 1 | 0 | `&5000` | `&3000` | 0,1,2 |
| 1 | 1 | 1 | `&2800` | `&5800` | 4,5 |

The "restart address" column is the bottom-of-screen RAM the wraparound jumps back to.

### Address formulas

**MODES 0-6:**
```
unwrapped_phys_addr = (MA << 3) | (RA & 7)
```
The screen-start address you write to R12/R13 must therefore be **divided by 8** (the address is in character-cell units of 8 scanlines). Addresses ≥ `&8000` wrap via the IC 32/39 mechanism above. RA ranges 0-7 in normal modes; in MODES 3/6 the gap scanlines blank.

**MODE 7:**
```
phys_addr = ((MA & 0x800) << 3) | 0x3C00 | (MA & 0x3FF)
```
- Screen RAM is `&3C00-&3FFF` or `&7C00-&7FFF`, depending on top bit of MA.
- 6845 is programmed with start `&2000-&23FF` (displays `&3C00-&3FFF`) or `&2800-&2BFF` (displays `&7C00-&7FFF`).
- `RA` is ignored — same MA is held across all scanlines of a teletext character row.
- 1K wrap by ignoring `0x400` bit.

**Special case:** start address `&2400` accesses `&3C00-&3FFF` then `&7C00-&7FFF` as one 2K linear buffer.

### Why the BBC has this hardware (rationale)

- CPU, Video ULA, and SAA 5050 all need different presentations of memory.
- Display must support hardware scrolling with virtual address wrapping.
- Display memory (variable size by mode) must relocate to *end of RAM* so user memory stays contiguous and minimally disturbed by mode changes.
- Done in SSI logic (not ULA) for cost/yield.

### Per-machine variants

- **Electron:** Address translation absorbed into the ULA's video block. No hardware scrolling, no Teletext (MODE 7 software-rendered).
- **Model B+:** Adds shadow RAM as an alternate display buffer; translator preserved.
- **Master:** Full memory-management ULA with backwards compatibility for B/B+ behaviour.

## Filed into

- Created: [[hardware/address-translation]] (new entity page, primary host).
- Cross-references: [[hardware/system-via]] (IC 32 = addressable latch — already documented), [[video/hardware-scrolling]] (replaces hand-wavy "subtract 2 bits on the latch" with the real table).

## Notes

This is the authoritative source on the wraparound. NAUG §13.3.12 explains it in passing; this page gives the actual subtract amounts and the IC numbers.
