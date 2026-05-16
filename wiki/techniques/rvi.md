---
title: RVI (per-line C9 selection via R0=1 micro-cycles)
type: technique
tags: [crtc, rupture, rvi, r0, c9, single-scanline, last-line, hsync]
sources: [accc-compendium, twisted-brain]
updated: 2026-05-16
---

# RVI — per-line C9 selection via R0=1 micro-cycles

A technique for **selecting which scanline (`C9` value, 0..7) within a character row is displayed on each visible line of the screen**. This is a strict superset of [[techniques/single-rasterline-rupture]] — instead of displaying every line as `C9=0`, you can pick any `C9` per line.

Used on BBC for accessing the **full 32 KB of CRTC-addressable RAM** on a freely-chosen per-scanline basis (vs the C9=0-only "1 byte per character cell" subset that single-scanline rupture is limited to). On the Master, the addressable pool effectively doubles via ACCCON shadow-RAM switching — see [[hardware/address-translation]] for the CRTC's address space and [[memory/shadow-ram]] for the Master's display-source toggle. Useful for twister-style effects that need offset + raster choices independently, large pre-rendered data sets that can't fit in 1/8 of screen RAM, and effects that want to walk every byte of memory per visible line.

Name caveat: the BBC scene calls this "RVI" by analogy to the Amstrad CPC technique of the same name. **What we call "RVI" on the BBC is technically R.V.L.L. in the CPC compendium's CRTC-0 taxonomy** — R.V.I. proper is a different (CRTC-1) technique using R0=0. The naming sticks for historical reasons. See [[sources/accc-compendium]] for the full CPC-scene taxonomy.

## Why it's hard on CRTC 0

In single-scanline rupture ([[techniques/single-rasterline-rupture]]) every visible line is a "Last Line" with C9=0. Useful, but it limits you to the first byte of each character row in screen RAM — losing the other 7 bytes of address space the chip would normally fetch as C9 walks 0..7.

To recover the other 7 bytes per character row, we need to display *different* C9 values on different visible lines, but with R12/R13 still updateable per line. CRTC 1 lets you do this with R0=0 (the simple R.V.I. recipe). On CRTC 0, R0=0 freezes C9 entirely (see [[techniques/crtc-counter-freeze]]) so a different approach is required.

## The mechanism

Per [[sources/accc-compendium]] §13.2.7 (R.V.L.L. case study), on CRTC 0:

1. **Make every visible line a "Last Line"** — set R4=0 or R9=0 with appropriate timing so that `C4=R4` and `C9=R9` are both true at C0<2 of every visible line. This arms a C9/C4 reset for the next line and starts each visible line with `C4=C9=0`.
2. **Use HSYNC time for "hidden" micro-cycles** — during the horizontal blanking period of a visible line, briefly set `R0=1` to create 2-µs micro-cycles. Each micro-cycle is a full CRTC scanline at the counter level: C0 increments to 1 then wraps, C9 increments by 1, no display happens (it's HSYNC).
3. **Advance C9 to the desired value** — fire N micro-cycles to make C9 reach the desired starting raster for the next visible line.
4. **Resume the visible line** — restore R0 to the normal value (typically 63), and the next visible line displays starting at the selected C9.
5. **Update R12/R13** — done during the first micro-cycle (when C0=0, C4=0 — VMA load condition satisfied per §20.3.1).

## Geometry

Per the ACCC §13.2.7 worked example, on a 64-µs scanline (R0=63, R2=50 normally):

| Desired C9 | R0 for hidden micro-cycles | Number of micro-cycles | Where they happen |
|---|---|---|---|
| 0 | — | 0 | (no micro-cycles needed) |
| 1 | 1 | 1 | C0=59..60 (within HSYNC area) |
| 2 | 1 | 2 | C0=57..60 |
| 3 | 1 | 3 | C0=55..60 |
| 4 | 1 | 4 | C0=53..60 |
| 5 | 1 | 5 | C0=51..60 |
| 6 | 1 | 6 | C0=49..60 |
| 7 | 1 | 7 | C0=49..62 (needs R0=49 reset on previous line) |

So **the visible-line work has to give up the last N×2 µs of HSYNC** to the micro-cycle activity, and R0 has to be reduced earlier as N grows. R2 must be set so HSYNC starts where the visible line ends (typically C0=49 to give a 14-µs hidden window).

The compendium's diagram (§13.2.7 p104) shows this with R3=15 for HSYNC width, R2=50 for centring (or R2=49 to allow C9=7 without HSYNC overlap).

## Why "make every line a Last Line"

The Last-Line trick is the CRTC-0-friendly equivalent of CRTC 1's R0=0 freedom. By ensuring `C4=R4=0` and `C9=R9=0` are satisfied at C0<2 of every visible line:

- The chip arms a C9 reset for next scanline.
- The arming uses the CURRENT R9 value (which is the new value you want for next line — set during the previous HSYNC's micro-cycles).
- Micro-cycles count up C9 from 0 to the desired value before the visible-line C0=0.

This avoids the messy R0=0 chip-freeze ([[techniques/crtc-counter-freeze]]) at the cost of the cycle-counting discipline of the R.L.A.L. exit recipe (see [[techniques/kefrens-bars]] for the analogous +1-raster trap).

## Address-update window

Per [[hardware/crtc-internal-counters]]:

> "On CRTC 0, `VMA' & VMA are loaded with R12/R13 when C4=0 AND C0=0`."

In RVI, this condition is satisfied at the start of every visible line (because each line begins with the Last-Line reset). So R12/R13 updates lodged during the previous HSYNC's micro-cycles take effect at the start of the new visible line, giving per-line independent screen-start.

## Comparison to single-scanline rupture

| Technique | C9 per line | C12/R13 update window | Code complexity |
|---|---|---|---|
| [[techniques/single-rasterline-rupture]] | Always 0 | Once per CRTC cycle (so per scanline) | Moderate |
| RVI (this page) | Selectable 0..7 | Once per CRTC cycle (per scanline) | High — micro-cycle bookkeeping |

If you only need C9=0 with per-line R12/R13 (the Twisted Brain effect family), use [[techniques/single-rasterline-rupture]]. If you specifically need to access all 16 KB of screen RAM per line (or pick arbitrary C9 for visual effects), use RVI.

## Use cases

- **Full 16 KB per-line access** — with C9 selectable 0..7 per line, all 8 bytes of every character row are addressable per visible raster.
- **Twister-style effects with finer than 32-row source pre-rendering** — narrow-screen + R12/R13 + C9 selection can pack rotations more tightly.
- **Texture-fill effects** that need specific stripe-pattern correspondence to scanlines without re-rendering pre-shifts.

## Implementation status (BBC)

Known: experimented with in the BBC scene; no shipped demo currently relies on it. Twisted Brain uses only the C9=0 variant ([[techniques/single-rasterline-rupture]]). A worked code listing would benefit from being included in `raw/code/` if any BBC implementer has a clean reference.

## Builds on / used by

- [[hardware/crtc-internal-counters]] — the C0/C4/C9 counter model and Last-Line semantics this technique exploits.
- [[techniques/single-rasterline-rupture]] — the simpler "always C9=0" subset.
- [[hardware/crtc-6845-advanced]] — R0/R4/R9 write-window summary for the underlying timing.
- [[sources/accc-compendium]] §13.2.7 — primary documentation (under the CPC-scene name R.V.L.L.).
- [[techniques/raster-splits]] — the broader family of mid-frame CRTC manipulation.

## Open follow-ups

- BBC-side worked example: any implementer who has shipped a clean RVI demo on BBC should drop a source listing into `raw/code/`.
- R.V.L.L. and (CPC) R.V.I. side-by-side comparison if anyone wants to port CRTC-1 RVI techniques to BBC equivalents.
- The "freeze of C9" / "freeze of additional adjustment line" mechanisms (ACCC §13.2.3, §13.2.4) provide alternative routes to similar per-line C9 control — would be interesting to compare.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
