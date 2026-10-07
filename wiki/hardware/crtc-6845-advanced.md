---
title: 6845 CRTC — Advanced
type: hardware
tags: [video, crtc, 6845, sheila, raster, performance]
sources: [hd6845sp-hitachi-datasheet, naug-ch13-video, accc-compendium, beeb-port-kit-hardware-facts]
sheila: ["&FE00", "&FE01"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-09-07
---

# 6845 CRTC — Advanced

Companion to [[hardware/crtc-6845]]. This page is for performance and raster-tight code: which registers tolerate mid-frame rewrites, sampling phases, raster split tricks. Primary sources: Hitachi HD6845S datasheet [[sources/hd6845sp-hitachi-datasheet]] (chip vendor's documentation, conservative) and the Amstrad CRTC Compendium [[sources/accc-compendium]] (cycle-by-cycle internal-state documentation for CRTC 0, which is the BBC's chip family).

**Read [[hardware/crtc-internal-counters]] first** — most of the rewrite-window verdicts below make immediate sense once you know the C0/C4/C9/C5 counter model and the C0<2 evaluation window.

## When can you rewrite each register mid-frame?

From the Hitachi datasheet "Anomalous Operations" table. **The verdicts below are the datasheet's, not ours** — they describe the chip operating outside Hitachi's guaranteed envelope, which is *exactly* where the interesting BBC raster work happens. Treat NG/prohibited entries as "experiment carefully and time the writes", not as "don't do this". Several techniques on this wiki (vertical rupture, smooth scroll, screen-blank-via-R8) demonstrably violate these verdicts and work reliably on real HD6845S silicon.

- **OK** — rewrite freely during display; effect is benign (worst case: one transient raster).
- **△ conditional** — rewrite is safe outside a specific phase window; inside it, expect transient flicker/glitch.
- **NG** — datasheet says visible disturbance; in practice, often workable if the write is timed during an adjacent cycle's blanking or retrace.
- **prohibited** — datasheet forbids; the BBC scene routinely ignores this for skew bits (R8 4-7) and others. Verify on real hardware before relying on it.

| Reg | Name | Verdict | Notes |
|---|---|---|---|
| R0 | Horizontal Total | **△** | Hitachi says NG, but the ACCC compendium documents extensive CRTC-0 R0 rewrite techniques: R0=0 freezes C9 (chip-freeze, see [[techniques/crtc-counter-freeze]]); R0=1 creates 2µs micro-frames (basis of [[techniques/rvi]] mid-HSYNC ruptures); writing R0 mid-scanline shortens the current scanline at the new value. The "disturbed" classification reflects that the chip doesn't fight you — what looks disturbed is the chip doing exactly what you asked, just in unconventional ways. |
| R1 | Horizontal Displayed | **OK** | One raster's DISPTMG may be shortened — invisible in practice. |
| R2 | Horizontal Sync Position | **NG** | HSYNC mis-placed or noisy. |
| R3 | Sync Widths | **△** | Pulse width may be cut short if rewritten while HSYNC/VSYNC is active. |
| R4 | Vertical Total | **△** | The chip evaluates the "Last Line" condition (`C9=R9 AND C4=R4`) **only when C0<2** on CRTC 0 ([[sources/accc-compendium]] §13.2.1). R4 writes that land after C0≥2 are stored but cannot change the Last-Line verdict for that scanline. In a 1-scanline-per-row CRTC cycle the practical consequence is severe: setting R4=N late in the final scanline doesn't shorten that scanline, so the frame runs 1 line over. See [[techniques/kefrens-bars]] for the 311-line rebalance fix. |
| R5 | Vertical Total Adjust | **△** | Avoid the **last char time of the raster**, or the adjust isn't applied. |
| R6 | Vertical Displayed | **OK** | Display may briefly inhibit; new value used from next field. |
| R7 | Vertical Sync Position | **△** | Precise behaviour per [[sources/accc-compendium]] §16.4.1: writing `R7=C4` at **C0vs<2** *blocks* VSync for that field (the second protection mechanism — see [[techniques/triggered-vsync]] when written); writing `R7=C4` at **C0vs≥2** *triggers* VSync immediately mid-line. R7 writes that don't change the `C4==R7` comparison are ignored. Not the datasheet-implied "NG"; just timing-specific. |
| R8 | Interlace & Skew | **prohibited** (interlace bits 0-1); **OK** (skew bits 4-7) | Interlace mode (bits 0-1) must not change during display. **Skew bits (4-7) are safe to rewrite mid-frame in practice on HD6845S** — used as a screen blank/unblank lever (`&F0`/`&C0`), see [[hardware/crtc-6845]] and [[techniques/smooth-vertical-scroll]]. Datasheet's blanket "prohibited" verdict is over-broad. |
| R9 | Maximum Raster | **△** | Same C0<2 evaluation window as R4: R9 writes participate in the Last-Line test only when C0<2. After C0≥2 the new value is stored but doesn't change this scanline's verdict. Per [[sources/accc-compendium]] §10. |
| R10 | Cursor Start | **△** | Avoid the last char time of the raster — cursor jitter / wrong blink rate temporarily. |
| R11 | Cursor End | **△** | Same as R10. |
| R12/R13 | Start Address | **OK** | Sampled in the **last raster period of the field**. Rewrite outside that window is safe. |
| R14/R15 | Cursor Position | **OK** | Rewrite during retrace for stable cursor; mid-display gives one frame of temporary glitch. |
| R16/R17 | Light Pen | read-only | — |

The datasheet notes: "the operations in this table are outside our guarantee and are regarded as materials for reference." Empirically the HD6845S is very consistent, and BBC demos have exploited the OK/conditional cases for decades.

**Measured refinement (2026, two ports — see "Measured in practice" below):** the datasheet's R5 verdict ("avoid the last char time of the raster") understates the danger zone. R5 is compared against a counter that counts *up*, so a write that lands after the count has passed the new value misses the match altogether and the adjust runs on to its 5-bit wrap — about 29 extra scanlines. Keep R5 writes away from *any* cycle boundary, not just the last character. Likewise the R6 "new value used from next field" and R7 "△" verdicts are consistent with, but weaker than, the rupture rule that both must be written in the cycle *before* the one they shape ([[sources/beeb-port-kit-hardware-facts]] §1).

## Mid-frame rewrites — what the BBC scene actually does

The Hitachi-datasheet framing of "rewrite only R12/R13 mid-frame" is the conservative envelope. In practice the BBC demo scene routinely rewrites **R0, R1, R4, R5, R6, R7, R8, R9, R12, R13** mid-frame, each within its own cycle-window constraints documented above. The whole [[techniques/single-rasterline-rupture]] family depends on R4/R6/R7 mid-frame writes producing the right CRTC-cycle shape, and [[techniques/rvi]] depends on aggressive R0 mid-scanline manipulation.

R12/R13 remain special because they're the only registers that drive the *display address* — the per-CRTC-cycle "show this memory next" lever. Everything else affects the *shape* of the cycle (its duration, its sync placement, its display extent).

## Sampling phase: when R12/R13 is read by the chip

The Hitachi datasheet says "R12 and R13 are used in the last raster period of the field." The ACCC compendium (§20.3.1) gives the precise counter condition: **`VMA' & VMA are loaded with R12/R13 when C4=0 AND C0=0`** — i.e. at the start of every new CRTC cycle. These are the same instant described from different angles.

In a non-interlaced PAL-style mode (R4=38, R5=0, R9=7), one CRTC cycle = one field = 312 raster lines, so VMA is loaded once per field. In a single-rasterline-rupture configuration (R4=0, R9=0), each new cycle is a separate scanline so VMA reloads every scanline — which is precisely what makes [[techniques/single-rasterline-rupture]] work.

**Implication for standard hardware scroll**: to update R12/R13 cleanly for the next frame, both bytes must be written before the C4=0, C0=0 instant. Anywhere in the visible display area is safe. The classic "wait for vsync, then update R12/R13" idiom works because vsync occurs well before the field-end VMA load.

**Implication 2**: if your write straddles the C4=C9=C0=0 instant (e.g. an IRQ in the middle of your two-byte write), the chip will load `(new R12, old R13)` for one field — half-updated. Mitigation: write both bytes within an SEI window, or write them at a known safe point well clear of the frame boundary.

## Split-screen tricks (per-frame R12/R13 changes)

Because R12/R13 are sampled only once per field, you **cannot** use them for raster splits within a single frame. For mid-frame screen-address changes you must trigger them differently:

1. **R12/R13 writes at the field-end sample**: simply reprogram once per frame. Standard hardware scroll. Cost: 2 stretched accesses = ~12c per field.
2. **R0 (HTC) and R4 (VTC) tricks**: officially NG, but a tightly-timed write to R0 can shorten the horizontal scan for a few lines, producing a "screen split" effect. Used in some demos. Requires raster-cycle-exact timing.
3. **R6/R7 mid-field rewrite**: marked OK / NG respectively in the datasheet. Some demos rewrite R7 to advance vsync; results are display-dependent.
4. **Indirect via the Video ULA**: palette flips at `&FE21` are *not* stretched ([[timing/cycle-stretching]]) and are the cheapest way to get mid-frame visual changes. Combine with R12/R13 once-per-frame.

For raster-line-exact timing, see [[techniques/raster-splits]] (overview of the split families) and [[techniques/hexwab-stable-raster]] (2-cycle-precision sync).

## Cursor as a raster signal

The CUDISP output is exposed via R10/R11. A cursor that covers all scanlines of a character row (CSL=0, CEL=Nr) effectively turns CUDISP into a "we're displaying this character cell" pulse. Combined with the cursor delay bits in R8 (offset 0/1/2 chars), this can be used as a hardware raster marker — useful for triggering external hardware or timing internal state changes to specific screen positions.

In MODE 7 the CUDISP delay is 2 characters (R8 bits 6-7 = 10), so the cursor signal trails the address generator by 2 char-times — matching the [[hardware/saa5050]]'s pipeline.

## Light pen as a horizontal-position latch

R16/R17 latch the current MA on LPSTB rising edge. Per [[hardware/system-via]] the LPSTB pin is connected to the analogue port's light-pen input (CA2 on System VIA via IFR bit 1). Software-controlled LPSTB pulses (e.g. via the user port wired back to the light-pen line) can capture the current display address at a known time — a form of raster snooping.

## Timing inside a field (PAL non-interlaced, default modes)

Reference values from MOS defaults — useful for raster work:

| Stage | Line range (R8=1, R5=0) |
|---|---|
| Visible display | 0 - 255 (256 lines = 32 chars × 8 scanlines in 8KB / 20KB modes) |
| Bottom border | 256 - 269 |
| VSYNC pulse | 270 - 271 (2 raster lines, R3 VSW=2) |
| Top border | 272 - 311 |
| **R12/R13 sample** | line 311 (last raster of field) |
| Field total | 312 lines (R4=38, R9=7, R5=0 → 39 × 8 = 312) |

At 64 µs/scanline, one field = 19.968 ms (just under PAL's 20 ms). VSYNC occurs at ~17.4 ms into the field; R12/R13 sample at ~19.9 ms.

For MODE 7 (R4=30, R5=2, R9=18): one field = 31 × 20 + 2 = 622 half-rasters ≈ 312 raster lines (same total — different cell shape). Sample still happens in the last raster period.

## See also

- [[hardware/crtc-6845]] — primary register reference.
- [[hardware/address-translation]] — how MA → DRAM address.
- [[hardware/video-ula]] — companion chip; preferred for raster-tight visual changes.
- [[timing/cycle-stretching]] — CRTC writes pay 1-2c extra; Video ULA writes do not.
- [[techniques/raster-splits]] — applying these primitives to produce split-screen effects.
- [[sources/hd6845sp-hitachi-datasheet]] — primary source for everything on this page.

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. This section is the empirical companion to the datasheet table above.

### Register write windows inside a rupture

The rules that held after two wrong builds ([Paradroid layer-3-scroll.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-3-scroll.md); reconfirmed on the Master 2026-09-02, [Edge layer-2-display.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-2-display.md), [Edge layer-6e-titles.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-6e-titles.md)):

| Register | Write it | Symptom when wrong |
|---|---|---|
| R4 | inside its **own** cycle, before C4 reaches the new value | the previous cycle trips over it — a stretched cycle; the tail cycle of Edge Grinder's titles hung its field-wait with the field counter frozen |
| R7 | inside the **previous** cycle | that row's compare has already happened, **VSync never fires**, the chip free-runs on the last cycle's shape and the picture rolls. R7 can be left constant if only one cycle ever reaches it (Edge, 2026-09-02) |
| R6 | inside the **previous** cycle | display enable is a flip-flop cleared on match; raising R6 afterwards does not bring the cycle's display back |
| R12/R13 | inside the **previous** cycle | latched at cycle start |
| R5 | anywhere in the cycle, but **not near a boundary** | the R5 trap, below |

Refinement (KC, 2026-09-07): the underlying rule for R6 and R7 is that the register must be written before C4 reaches the row it names. Inside the *current* cycle is fine as long as that row has not already passed; "previous cycle" is the safe form the ports used because their rows were early in the cycle. R12/R13 are latched at cycle start, so for those the previous cycle is the rule.

- **Rows must sum to 39 (312 scanlines) or the picture rolls.** `38 × 8 + 8 = 312` confirmed by counting VSyncs: 1,000 fields in 39,936,000 cycles exactly (Paradroid Layer 3, jsbeeb). Constants on [[timing/field-timing]].
- **R7 for the panel cycle must go in at VSync, not at the first timer fire.** With VSync moved to tail row 4 or 5, a 7-row panel cycle reached the stale R7 before fire 1 and fired a second VSync of its own, re-entering the handler mid-frame; the play area went black (Paradroid, 2026-08-21, jsbeeb).
- **Where VSync falls in the frame decides where the picture sits on the tube.** Moving VSync earlier in your frame moves the picture down; only the front/back porch split changes (Paradroid, 2026-08-21, by eye on b-em and jsbeeb).

### The R5 trap

- **Never write R5 near a cycle boundary.** The vertical adjust counts up and compares against R5; change it after the count has passed the new value and the match never happens, so the adjust runs on to its 5-bit wrap, about 29 extra scanlines. In Paradroid it stretched a 64-scanline panel cycle to 85. R5's legal window is the whole cycle: use the middle of it (Paradroid Layer 3, jsbeeb).
- **R5 is sampled at each cycle's end**, so a value must be in place between the sample it must not disturb and the one it serves (Paradroid Layer 3, three-cycle smooth vertical scroll).
- **Timer fires that must land in a cycle should overshoot the boundary by a few rows.** Sized to reach the boundary exactly, IRQ latency alone carried them into the previous cycle (Paradroid Layer 3, with a `DEBUG_RASTER` tint at each interrupt entry).

### R8, `R6 = 0`, `R1 = 0`, the cursor, interlace

- **R8's display-skew bits (`&30`) blank the display; `&00` turns it on.** It is the chip's own display enable, so there is no ULA serialiser artefact, and a write takes effect immediately: one landing in the displayed part of a scanline cuts that scanline part-way across (Paradroid Layer 3, jsbeeb). Confirms the "skew bits are safe" reading of the table above.
- **`R6 = 0` is NOT a blank: it leaks one row.** The row counter is compared at the end of a row, so row 0 displays whatever R6 says. Paradroid showed a 640-byte stripe of play buffer for the 3.7 s of a screen transition, and a top row full of a ZX0 stream at boot. Use R8 (2026-08-31, jsbeeb, twice, screenshotted; [loader-compression.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/loader-compression.md), [raster-timing.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/raster-timing.md)).
- **`R1 = 0` also blanks, and kills the row itself**, so it does not leak (Paradroid, 2026-08-31, jsbeeb).
- **R8 blanking does not hide the CRTC cursor.** A one-frame white dash appeared during loading with `R8 = &30`: the MODE 7 prompt cursor blinking. `R10 = &20` alongside the blank fixes it. `VDU 22` resets both R8 and R10 (Edge, 2026-09-02, jsbeeb, [layer-2-display.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-2-display.md)).
- **Interlace must be off (`R8 = 0`) for a rupture.** The MOS leaves MODE 1 at `R8 = 1` (interlace sync), which offsets VSync by half a scanline on alternate fields; timer intervals from VSync then land the split in a different place every other field (Paradroid Layer 3: consecutive fields render identically with interlace off).

### Switching between frame shapes

- **Writing a new R4/R5/R6/R7 set mid-frame costs malformed fields.** Paradroid measured 38,378 / 49,154 / 6,168-cycle fields (300, 384 and 48 lines) across a switch into the rupture, and one 376-line field on the way out. Aligning the writes to row 0 of a fresh frame (wait for VSync, spin 8 rows) made every field 39,93x (2026-08-31, jsbeeb, `run_frames(1)` stepping with `elapsed_cycles` per field; [raster-timing.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/raster-timing.md)).
- **A field of the right length can still be misplaced.** With the CRTC free-running in a 13-row tail shape whose VSync is at row 5, it VSyncs every 104 lines; the first VSync after an aligned switch came at line 104 instead of 312 — one short field and one roll. **jsbeeb showed no fault; b2 rolled and KC photographed it.** The fix suppresses VSync (`R7 = 255`) across the intermediate cycles (2026-08-31, b2 photograph then arithmetic). See [[tools/emulators]].
- **Changing between a two-cycle and a four-cycle rupture from main-loop code costs one malformed field** (272 lines against 312) when R7 and the display wrap are written outside the VSync handler (Edge, 2026-09-04, jsbeeb, stepping fields).
- **Leaving the CRTC in a rupture shape with nobody servicing the timers** runs the picture at roughly double rate: 14 CRTC frames of ~18,500 cycles in a 258,364-cycle window between the CRTC setup and the IRQ install. Switch the CRTC on next to the IRQ that drives it (Paradroid, 2026-08-31, jsbeeb).

### The display window and the hardware wrap

- **The display window must fit inside ONE hardware wrap.** The address translator subtracts its mode amount once, when MA12 goes high; it does not iterate. A window larger than the wrap span fetches from `&8000` upwards (ROM) at some scroll positions and shows garbage on the last rows. With the 10K wrap and 80-unit rows the strip is exactly 16 rows, so 16 displayed rows is the ceiling, and 1-scanline vertical scrolling costs one row of play area (Paradroid Layer 3, jsbeeb: at scroll offset 10200 the model predicted garbage from unit 5 of the bottom row onward, and that is where it started). Mechanism on [[hardware/address-translation]].
- **A 16K play buffer with 640-byte rows does not wrap on a row boundary** (16,384 / 640 = 25.6), so a sprite's columns can straddle `&8000` and stop being 8 bytes apart (Edge, 2026-09-03, arithmetic plus a sprite test in jsbeeb; [decisions.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/decisions.md) 21).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
