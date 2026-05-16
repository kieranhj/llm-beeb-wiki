---
title: 6845 CRTC Internal Counters (C0/C4/C9/C5)
type: hardware
tags: [crtc, 6845, internal-state, c0, c4, c9, c5, vma, last-line, additional-management]
sources: [accc-compendium, hd6845sp-hitachi-datasheet]
updated: 2026-05-16
---

# 6845 Internal Counters

The CRTC's behaviour is best understood not in terms of its **registers** (R0-R17, the things you write) but in terms of its **internal counters and states** — what the chip actually maintains and tests as the beam scans. Most "weird" 6845 behaviour stops being weird once you know how the counters update.

This page is the foundation for [[hardware/crtc-6845]] / [[hardware/crtc-6845-advanced]] and every rupture technique on the wiki. Primary source: [[sources/accc-compendium]] (Amstrad CPC CRTC Compendium, which describes "CRTC 0" — the chip family the BBC's HD6845S/SP belongs to).

## The counters

| Counter | Width | Counts | Bounded by |
|---|---|---|---|
| `C0` | 8 | character columns within a scanline | resets at C0=R0+1 |
| `C4` | 7 | character rows within a frame | resets at "Last Line" or overflows at 127 |
| `C9` | 5 | raster lines within a character row | resets at C9=R9+1 (with caveats) |
| `C5` | 5 | rasters within the vertical-adjustment period | counts after Last Line if R5>0 |
| `VMA` | 14 | current video memory address | loaded from R12/R13 at frame start |
| `VMA'` | 14 | next-row video memory address | helper for row advancement |

`C0` increments once per microsecond (every horizontal character clock). `C9` increments when `C0` overflows. `C4` increments when `C9` overflows (in normal use). `VMA` advances by 2 bytes per displayed microsecond.

The 14-bit memory address sent to the bus is composed of `VMA` and bits 0-2 of `C9` — see [[hardware/address-translation]] for how those 14 bits land in DRAM space on the BBC.

## The states

The chip maintains internal **states** which are tested and updated during specific phases of each scanline:

### "Last Line"

Armed when `C9=R9 AND C4=R4`. The chip evaluates this **only when C0<2** on CRTC 0 (the first 2 µs of the scanline). Once armed, it determines that the *next* scanline starts a new frame: `C9` resets to 0, and `C4` resets to 0 unless additional-management kicks in.

**Critically: register writes that land after C0≥2 cannot change the Last-Line verdict for that scanline.** This is the precise mechanism behind the "R4-on-final-scanline" behaviour documented on [[techniques/kefrens-bars]] — what looks like a chip bug is the chip refusing to re-evaluate a state it's already decided.

### "Additional Management"

If Last Line is armed AND `R5>0` (or the interlace-line condition is true), the chip enters additional-management mode after the last visible scanline of the frame. It generates extra scanlines after R5 + interlace-line rules, during which `C5` increments and `C4` exceeds `R4` temporarily before resetting at end-of-adjustment.

On CRTC 0, `C4` is incremented exactly **once** during additional management, regardless of R5's value. The end-of-adjustment is gated on `C9+1=R5`.

## Cycle-by-cycle of the first 3 µs of a CRTC 0 scanline

From the compendium §13.2.1 — explains why so much subtle behaviour clusters at C0<2:

| C0 | What the chip does |
|---|---|
| `C0=0` | C4 and C9 update according to states decided on the previous scanline. Test C9=R9 and C4=R4 to set up "Last Line" arming for next scanline. R4/R9/R5/R8 writes that land here are honoured for the Last-Line test. |
| `C0=1` | C9 management re-authorised for the next C0=R0. If R0=0, C9 stays frozen. Last-Line state can still be set/cancelled by R4/R9 writes that land here. |
| `C0=2` | Decision: if Last Line is armed, the chip determines whether to enter Additional Management (test R5, test interlace-line condition). After C0≥2, **the Last-Line verdict is locked** — register writes no longer change it for this scanline. |
| `C0=3..R0` | Normal display fetch. R0/R1/R2 writes that land here affect this scanline's display/sync; R4/R9 writes are *honoured for storage* but don't change this scanline's Last-Line behaviour. |

## Per-register write-window summary (CRTC 0)

Compiled from compendium §11-§20:

| Register | Effective on the current scanline if written... |
|---|---|
| R0 (horiz total) | Anywhere up to the displayed C0. Setting R0=0 or R0=1 has dramatic side effects on C9 / additional-management — see [[techniques/crtc-counter-freeze]] (planned) and [[techniques/rvi]] |
| R1 (chars displayed) | Anywhere; affects when DISP-EN drops this scanline |
| R2 (hsync position) | Anywhere up to C0=R2; sliding R2 mid-scanline is delicate |
| R3 (sync widths) | During the active HSYNC or VSYNC. Writes that don't change the comparison condition are ignored |
| R4 (vert total) | Only at C0<2 for Last-Line evaluation. Writes after C0≥2 are stored but don't change the Last-Line verdict |
| R5 (vert adj) | Up to C0=2 of the last frame line for the count to apply this frame |
| R6 (vert displayed) | Anywhere; affects when row display gates off |
| R7 (vsync position) | C0vs<2 to set the C4=R7 trigger for this scanline. Writing R7=C4 at C0vs<2 *blocks* VSync; at C0vs≥2 *triggers* it mid-line. See [[techniques/triggered-vsync]] (planned) |
| R8 (interlace + skew) | Anywhere — skew bits OK; interlace bits only safe at frame boundary |
| R9 (rasters per row) | Only at C0<2 for Last-Line evaluation. Otherwise same as R4 |
| R12/R13 | Anywhere — immediate write to register, but **loaded into VMA only when C4=C9=C0=0** (i.e. at frame start) |

## How this maps to existing wiki concepts

- **R12/R13 are "latched"** (existing wiki phrasing) — more precisely: written immediately but loaded into `VMA` only when `C4=C9=C0=0`.
- **R4 doesn't take effect immediately in 1-scanline cycles** (existing wiki "mystery") — the chip's Last-Line test happens at C0<2 of each scanline; in a 1-scanline cycle, every scanline is both display and would-be Last Line, and any R4 write after C0=2 is ignored for that scanline's Last-Line verdict.
- **"Read R12 then R13 within one frame"** ([[hardware/crtc-6845]] existing advice) — the VMA load happens at C4=C9=C0=0, so both bytes must be in R12/R13 by then. Writing R12 and R13 within a single frame's vblank period is safe; straddling the frame boundary is not.
- **"Mid-frame rewrites are NG" in the Hitachi datasheet** — the datasheet is conservative because the cycle window in which each register CAN be safely written depends on per-register details the datasheet doesn't fully specify. The compendium fills in those details for CRTC 0.

## Counter overflow / freeze behaviours

- **C4 overflow** (§12.2): C4 is 7 bits wide, can exceed R4 up to 127 before wrapping. Happens when "Last Line" is not armed but C9=R9. The chip doesn't reset C4 because the explicit reset condition `(Last Line AND not Additional Management)` is false.
- **R0=0 freeze** (§13.2.4): setting R0=0 freezes C9 (and via knock-on, C4, C5). Register writes to R4/R5/R9 are ignored during the freeze; R8 still considered each C0=0; R7 still tested each C0=0. Foundation of [[techniques/crtc-counter-freeze]] (planned).
- **Freeze of additional adjustment line** (§13.2.3): if R0=0 lands during R5 additional-management, the chip stays mid-adjustment indefinitely.
- **Freeze of VSync** (§13.2.2): writing R0<2 on the line before C4=R7 prevents the VSync from triggering for that frame. Unlocking requires changing R7 or letting C4 increment.

## See also

- [[hardware/crtc-6845]] — register summary, per-mode values, programming interface.
- [[hardware/crtc-6845-advanced]] — anomalous-rewrite verdicts reframed using this model.
- [[sources/accc-compendium]] — the primary source for everything above. Read it directly when investigating an unusual chip behaviour.
- [[techniques/single-rasterline-rupture]], [[techniques/kefrens-bars]], [[techniques/rvi]] — techniques that depend on understanding this model.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
