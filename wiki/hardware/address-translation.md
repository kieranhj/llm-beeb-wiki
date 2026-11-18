---
title: Address Translation
type: hardware
tags: [memory, dram, address-translation, video, scrolling]
sources: [beebwiki-address-translation, naug-ch12-memory, naug-ch13-video, bbc-service-manual, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
machines: [BBC Model A, BBC Model B, BBC B+, Master 128]
updated: 2026-11-18
---

# Address Translation

The BBC's discrete-logic address translator maps three different address spaces (CPU, CRTC + line counter, [[hardware/saa5050]] input) onto the 15-bit DRAM space. **This is what makes hardware scrolling work** — and the only reason you can write a 14-bit screen-start address to R12/R13 of the [[hardware/crtc-6845]] and have it land cleanly in screen RAM regardless of mode.

Implemented as SSI (small-scale integration) logic, not a ULA: ICs 8-15 (data + address gating), IC 32 (System VIA addressable latch — see [[hardware/system-via]]), IC 39 (quad adder for the wraparound). On the **Electron** the function is absorbed into the ULA, with restrictions (no hardware scroll, no Teletext fetch — MODE 7 is software-rendered). On the **Master** it lives in the memory-management ULA with B/B+ compatibility.

## DRAM address space

15-bit total (`DA0-DA14`). 7-bit bus diplexed at 8 MHz:

| Bit(s) | Field |
|---|---|
| `DA14` | Bank select (Model A: only one bank, `DA14` unused) |
| `DA13-DA7` | Column |
| `DA6-DA0` | Row |

R/~W is gated by the address-bus buffers and only drops when the column address is on the bus AND the CPU is writing.

## Three translation modes

Selected by the 2 MHz monotonic clock and the CRTC's `MA13`:

| 2 MHz | MA13 | Mode | Recipient | Gating ICs |
|---|---|---|---|---|
| Low | x | **CPU** | The CPU itself | ROW: IC 12 / COL: IC 13 |
| High | High | **TTX VDU** (MODE 7) | SAA 5050 Teletext chip | ROW: IC 10 / COL: IC 11 |
| High | Low | **HI RES** (MODES 0-6) | [[hardware/video-ula]] serialiser | ROW: IC 8 / COL: IC 9 |

CPU and video alternate at 2 MHz. CPU mode does **direct A → DA mapping** with no translation — meaning **no DRAM refresh is guaranteed by CPU access alone**. Refresh is provided incidentally by the video fetches in the other two modes.

## CPU mode

Trivial. `A0-A14` map straight to `DA0-DA14`.

## TTX VDU mode (MODE 7)

| DA14 | DA13-DA10 | DA9-DA7 | DA6 | DA5-DA0 |
|---|---|---|---|---|
| `AA3` | all 1 | `MA9-MA7` | `MA6 ⊕ ~1MHz` | `MA5-MA0` |

MOS programs MODE 7 such that `MA11 = 1, MA12 = 0`, which forces `AA3 = 1` always. The XOR of `MA6` with the 1 MHz clock fetches *two distinct bytes per microsecond* — IC 15 routes one to the SAA 5050 and discards the other. Side effect: **all 128 DRAM rows are refreshed every scanline**, giving a worst-case refresh interval of **88 µs** (well within DRAM spec). Without the XOR trick the worst case would be 1.96 ms — out of spec.

**Exploitable**: if you force TTX VDU mapping in a *graphics* mode (by setting R12/R13 to the teletext base while keeping the Video ULA in modes 0/1/2), the Video ULA sees **both** bytes per µs. Every other byte arrives from `addr XOR &40`. This isn't a bug — it's the foundation of [[techniques/chunky-mode]], a 1 KB chunky display with the EOR-64 interleave baked into the back-buffer layout. The Master adds a second layer: `XOR &40` on one scanline and `XOR &C0` on the next (measured; see "MA13 on the Master" below).

### MA13 on the Master (measured)

**Measured on a real Master (2026-11-15)** — [[sources/beeb-port-kit-hardware-facts-2026-11]] §1 "MA13 (teletext) addressing in a 2 MHz mode"; KC's Master (Sony RGB), phX hwtest card J, photographs read; `phX/docs/hwtest.md` "Results: tests I-L", `phX/docs/part-bobs.md`:

- **MODE 1 with MA13 set** (R12/R13 `&2028`, MA11 clear) reads the 1K at **`&7C00`**, RA ignored. (On a Model B the translator formula above would put MA11 = 0 at `&3C00`; on the Master the fetch came from `&7C00` — the `&3C00` block, and with it the `&2400` 2K-linear trick below, are Model B behaviour.)
- **Alternate characters fetch another byte.** The characters of one 1 MHz phase read `&7C00 + (MA AND &3FF)`; the others the same with **MA6 flipped on one scanline and MA6 and MA7 flipped on the next** — `XOR &40` / `XOR &C0`, **never MA7 alone**. Bits 8-9 never flip. Which RA parity takes which was not read (phX's second test disc, card M, asks; no result yet).
- **The flip follows the 1 MHz clock, not C0.** After phX's VSync lock the even characters flip; one 127-character line swapped them for good. **Every odd-length line since the boot moves the phase**, so a part that depends on it keeps every line even. "Mostly" the same at each power-on (KC) — to confirm over more power-ups.
- BeebWiki's *Address translation* has the MA6 half (the refresh fetch, above); the MA7 half on alternate scanlines is the Master's own (more DRAM rows to refresh, per phX's reading).
- **Emulators**: beebjit models MA6 only (on even ticks); jsbeeb 2.10.x and b2 model neither; jsbeeb main 2.22.0 (#1859) models the flip — phX's Bobs, laid out for it, read 640 of 640 there and 0 of 640 on jsbeeb 2.10.2.

*Superseded:* this page said "The Master adds an extra layer (MA6 vs MA7 toggle depending on RA0)", from [[sources/chunky-mode-notes]]' second-hand summary (Julian Brown, stardot 2015). The measured pattern is MA6 on one scanline and MA6+MA7 on the next.

This is why MODE 7 is special at the hardware level. The SAA 5050 only needs the same character cell address held across all 20 scanlines of a teletext row; the chip handles internal pixel generation. So `RA` is ignored; `MA` repeats per scanline.

## HI RES mode (MODES 0-6)

| DA14-DA11 | DA10-DA3 | DA2-DA0 |
|---|---|---|
| `AA3-AA0` | `MA7-MA0` | `RA2-RA0` |

`AA3-AA0` = `MA11-MA8` after the wraparound correction (see next section).

**Maximum DRAM refresh intervals** observed in each MODE — the all-modes-must-refresh-DRAM-within-2 ms constraint is comfortably met:

| Mode | Refresh interval |
|---|---|
| 0, 1, 2 | 480 µs |
| 3 | 608 µs |
| 4, 5 | 488 µs |
| 6 | 616 µs |
| 7 | 88 µs (per scanline) |

## Wraparound — the hardware-scroll mechanism

When the 6845's character address `MA` would step past `&8000` (i.e. into ROM space), hardware substitutes a wraparound address by **subtracting** a mode-dependent amount from `MA`. The selection of subtract amount is held in **two bits of the System VIA's addressable latch (IC 32)**, programmed at MODE-set time:

1. **State bits** `C0`, `C1` (latch outputs) encode the screen size.
2. **Decoder gates** produce a one's-complement "2K-unit count" that feeds the B-side of IC 39 (quad adder).
3. **IC 39** subtracts when `MA12` is high.
4. The result is diplexed onto the DRAM bus via IC 9.

| `MA12` | `C1 C0` | Subtract | Restart address | MODEs |
|---|---|---|---|---|
| 0 | xx | 0 (passthrough) | n/a | 0-6 (no wrap needed) |
| 1 | `00` | `&4000` | `&4000` | 3 |
| 1 | `01` | `&2000` | `&6000` | 6 |
| 1 | `10` | `&5000` | `&3000` | 0, 1, 2 |
| 1 | `11` | `&2800` | `&5800` | 4, 5 |

Each row's "restart address" is the first physical RAM address the wraparound substitutes for the would-be ROM address — i.e. the **bottom of the screen RAM block** for that mode size.

This is what makes hardware scrolling cheap: the BBC programmer can advance R12/R13 by a fixed offset every frame and never has to redraw the whole screen. The translator wraps the read transparently.

## Address formulas

### MODES 0-6

```
unwrapped_phys_addr = (MA << 3) | (RA & 7)
```

Two consequences:

- The screen-start address you write to R12/R13 must be **divided by 8** before programming (since `MA` is in 8-scanline character units, not bytes).
- If your computed start would step the fetched address ≥ `&8000`, the wraparound mechanism substitutes the bottom of screen RAM via the table above.

In MODES 3 and 6 the gap-scanlines (RA = 8/9 in MODE 3; RA = 8/9 in MODE 6) blank the display — `R9` (NSL) covers the full 9 or 9 scanlines but only 0-7 fetch valid data.

### MODE 7

```
phys_addr = ((MA & 0x800) << 3) | 0x3C00 | (MA & 0x3FF)
```

- The top bit of `MA` (MA11) selects between `&3C00-&3FFF` and `&7C00-&7FFF` blocks.
- 6845 is programmed with start address `&2000-&23FF` (displays `&3C00-&3FFF`) or `&2800-&2BFF` (displays `&7C00-&7FFF`).
- 1K wrap by ignoring the `0x400` bit of `MA`.
- `RA` is ignored — same `MA` is held across all 20 scanlines of a teletext character row.
- **Special trick (Model B):** programming start address `&2400` gives a 2K linear stream `&3C00-&3FFF` then `&7C00-&7FFF` — useful for double-buffered teletext. On a Master MA13 fetches were measured from `&7C00` with MA11 clear (above), so the `&3C00` half does not apply there ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1).

This is also the mechanism behind R12/R13's "XOR `&54`" rule documented on [[hardware/crtc-6845]]: writing the desired physical-RAM-address-divided-by-8 directly would land in the wrong region of the DRAM map; XORing flips the bits that drive `MA11` and the upper translator inputs into the `&2000-&2FFF` window the translator interprets as Teletext mode.

## Why this matters for performance code

- **Hardware scrolling**: pick R12/R13 wisely — moves of one character row (40 or 80 bytes) cost a single 6845 write and the translator handles the wrap. See [[video/hardware-scrolling]].
- **DRAM refresh**: the CPU-only mode does not refresh. If you ever stop video fetches (very unusual — MODE 7 with `MA12=0`?), you must refresh manually.
- **MODE 7 buffering**: on a Model B the `&2400`-start trick gives you a 2 KB linear teletext buffer if you want to double-buffer (not on the Master — above).
- **Custom modes**: if you change R12/R13 to a value that makes the hardware-scroll wraparound point at the wrong address (e.g. you set up a 16K mode via R6 but keep the 20K wraparound bits in the addressable latch), the bottom of the screen will display garbage from the wrong RAM region. Set the addressable latch via OSBYTE `&D5/&D6/&D7` or the 50/51/52 bits of System VIA Port B before reprogramming the 6845.

## See also

- [[hardware/system-via]] — IC 32 addressable latch (bits 4-5 = C0/C1 here).
- [[hardware/crtc-6845]] — what produces `MA0-MA13` and `RA0-RA2`.
- [[hardware/video-ula]] — the consumer of HI RES fetches.
- [[video/hardware-scrolling]] — how to use the wraparound for scrolling.
- [[memory/memory-map]] — DRAM layout.
- [[sources/beebwiki-address-translation]] — primary reference for this page.

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up.

- **The wrap table above holds, bit for bit, and the four sizes are NOT powers of two.** Measured on a Master 128 in jsbeeb by Edge Grinder (2026-09-04) from 6502 in main RAM, and the 10K case independently in Paradroid's Layer 3: with `C0` = latch line 4 and `C1` = latch line 5, 0/0 wraps `&8000` to `&4000` (16K), 1/0 to `&6000` (8K), 0/1 to `&3000` (20K, the MOS's own MODE 2 setting), 1/1 to `&5800` (10K). Written as `LDA #4` / `LDA #12` to `&FE40` for line 4 clear/set, `#5` / `#13` for line 5 ([Edge layer-6e-titles.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-6e-titles.md), [Paradroid layer-3-scroll.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-3-scroll.md)).
- **The subtraction happens once and does not iterate**, so a displayed window must fit inside one wrap span. A window larger than the span fetches from `&8000` upward (ROM) at some scroll positions and shows garbage on its last rows; with the 10K wrap and 80-unit rows the usable strip is exactly 16 rows (Paradroid Layer 3, jsbeeb — the model predicted garbage from unit 5 of the bottom row at scroll offset 10200 and that is where it started).
- **On the Master the wrap applies inside whichever bank is displayed.** With ACCCON D = 1 and the wrap at 8K, a display crossing `&8000` lands on *shadow* `&6000`, not main; Edge Grinder's title page runs one 8K ring in each bank (2026-09-04, jsbeeb only; no real-hardware confirmation). The `machines:` list above stops at the B+, but the same table was measured on the Master. See [[memory/shadow-ram]].
- A 16K buffer with 640-byte rows wraps mid-row (16,384 / 640 = 25.6), so a sprite's 8-byte column stride breaks across `&8000` (Edge, 2026-09-03).
- **With ACCCON D set, a CRTC address below `&3000` reads ANDY (`&8000-&8FFF`) and HAZEL, not main RAM** — jsbeeb 2.10 models it (`videoRead` ORs `&8000` into the address), Stryker's Run's HUD showed ANDY's bytes on every shadow field until D was cleared for its rows (2026-10-23), and **a real Master reads HAZEL there** (phX hwtest card I, 2026-11-15: lines over `&1800-&1AFF` showed HAZEL's green, not main RAM's blue). b-em's alternate-frame garbage was b-em's. Rule: D = 0 over any row below `&3000` ([[sources/beeb-port-kit-hardware-facts-2026-11]] §4; [[memory/shadow-ram]]). The wrap-inside-bank behaviour above is still jsbeeb-only.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
