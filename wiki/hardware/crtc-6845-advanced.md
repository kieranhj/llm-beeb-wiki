---
title: 6845 CRTC — Advanced
type: hardware
tags: [video, crtc, 6845, sheila, raster, performance]
sources: [hd6845sp-hitachi-datasheet, naug-ch13-video, accc-compendium]
sheila: ["&FE00", "&FE01"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-05-16
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

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
