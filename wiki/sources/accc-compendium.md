---
title: ACCC — The Amstrad CPC CRTC Compendium (v1.7)
type: source
local: raw/notes/ACCC1.7-EN.pdf
author: Serge Querné (Longshot / Logon System)
date: 2023-10-10
version: 1.7
url: https://shaker.logonsystem.eu/
tags: [crtc, 6845, reference, rupture, cpc, internal-counters, c0, c4, c9, c5, vma, vsync, hsync]
updated: 2026-05-16
---

# ACCC — The Amstrad CPC CRTC Compendium

284-page chip-internal-cycle-by-cycle reference for the 6845 CRTC across the five variants Amstrad used in the CPC range (their "CRTC 0"-"CRTC 4" taxonomy). Written by Serge Querné (Logon System) over 2021-2023. Tests verified against real silicon via the SHAKER benchmark suite (results at <https://shaker.logonsystem.eu/>).

**Why this matters for BBC work**: the Amstrad **CRTC 0** chip behaves identically to the BBC's **HD6845S/SP** for the purposes of every rupture / raster-split / sync trick documented in the wiki. The compendium is, by a wide margin, the most thorough description of CRTC 0 chip-internal behaviour in existence. Treat it as the canonical reference for any "why does the chip do X?" question.

## CPC ↔ BBC terminology key

The CPC scene formalised names for several rupture techniques. The BBC scene developed these techniques in parallel and uses different (or sometimes mistranslated) names. Mapping:

| CPC acronym | CPC term | What it is | BBC equivalent |
|---|---|---|---|
| R.L.A.L. | Rupture Ligne À Ligne | Make every visible line a "Last Line" so C9=C4=0 every line, allowing per-line R12/R13 changes | What we call [[techniques/single-rasterline-rupture]]. We don't use the R.L.A.L. acronym. |
| R.V.I. | Rupture Vertical Invisible | CRTC-1-specific technique using R0=0 + register juggling during HSYNC to select C9 per visible line | The CPC compendium says this is too messy on CRTC 0. The BBC technique we informally call "RVI" is actually closer to R.V.L.L. below — see [[techniques/rvi]] |
| R.V.L.L. | Rupture Verticale Last Line | The CRTC-0-friendly CRTC-equivalent of R.V.I.: use R0=1 micro-frames during HSYNC + Last Line semantics to select C9 per visible line | What the BBC scene calls "RVI". Documented on [[techniques/rvi]] under the BBC name with this cross-ref. |
| R.F.D. | Rupture For Dummies | CRTC-1-specific R5 trick for sub-row vertical scroll. Not BBC-applicable. | The BBC equivalent (R5 + 2-cycle vertical rupture for smooth vertical scroll) is on [[techniques/smooth-vertical-scroll]]. Different mechanism. |

The "RVI" mistranslation is benign: the BBC variant of the technique was developed independently with reference to French-language CPC material, and the morally-similar acronym stuck even though the CRTC-0 implementation is technically R.V.L.L. in the compendium's taxonomy.

## What this source teaches that's new to the wiki

### The CRTC internal counter model

The compendium describes the chip's behaviour in terms of internal counters:

- `C0` — horizontal character column (0..R0)
- `C4` — character row (0..R4)
- `C9` — raster within character row (0..R9)
- `C5` — vertical adjustment counter (used for R5 / interlace line)
- `VMA / VMA'` — current / next video memory address

…plus internal *states*:

- **"Last Line"** — armed when `C9=R9 AND C4=R4` (evaluated only when **C0<2** on CRTC 0)
- **"Additional Management"** — armed when Last Line is true and R5>0 or interlace-line condition met

Almost every "weird CRTC behaviour" the BBC scene has documented can be explained by tracing what happens to these counters and states on a cycle-by-cycle basis. We didn't have this model on the wiki before — see new page [[hardware/crtc-internal-counters]].

### The C0<2 evaluation window

**Single most important insight from the document for BBC work** (§13.2.1, p97):

> "When C0=0, then counters C4 and C9 are updated according to states decided on the previous line. […] When C0=1, then the management of C9 is again authorized for the next C0=R0. […] When C0=2, on the last line of frame, the CRTC determines if additional line management should take place."

So on CRTC 0, the chip's "Last Line" verdict is set during C0=0,1,2 only. Register writes that land after C0≥2 cannot change the verdict for that line. **This precisely explains the R4-on-final-scanline behaviour previously described as a "mystery" in our [[techniques/kefrens-bars]] page** — see that page for the updated explanation.

### Register update-window semantics

For each register R0-R12 the compendium specifies, with cycle precision and per CRTC type, what happens when you write the register during different C0 phases. CRTC 0 specifically:

- **R0** (§13.2): controls C0 increment; setting R0=0 freezes C9 (and most counters) until R0>0 again. Setting R0=1 creates 2µs micro-frames.
- **R4** (§12.2): only evaluated at C0<2 for Last Line determination.
- **R5** (§11): controls additional-line count; "freeze of additional adjustment line" if R0=0 during R5 period.
- **R7** (§16.4.1): R7=C4 write at C0vs<2 *blocks* VSync; write at C0vs≥2 triggers VSync immediately mid-line.
- **R9** (§11.7): cannot be safely modified between C0=0..1 of the "Last Line" line on CRTC 0.
- **R12/R13** (§20.3.1): immediate write but only loaded into VMA when `C4=C9=C0=0`.

### Novel-to-BBC techniques

Captured for future technique pages:

- **R0=0 chip freeze** (§13.2.4, §13.2.6) — explicitly freezes C9 and most counters. The BBC scene has experimented with this but no shipped demo uses it yet. To be documented in [[techniques/crtc-counter-freeze]] (Phase B).
- **Triggered VSync** (§16.4.1.1) — writing R7=C4 mid-line triggers VSync immediately, with the C3h counter starting at 0 from that point. To be documented in [[techniques/triggered-vsync]] (Phase B).
- **Blocked VSync gotcha** (§16.3, §16.4.1.1) — write R7 with the current C4 value when C0vs<2 blocks VSync for that field without it firing. Unlocking requires changing R7 again on a different C4. Important footgun for per-frame R7 manipulation.
- **Limitless VSync** (§16.6) — usually a bug (TV unlocks), but documents the second VSync-protection mechanism (C4/R7 equality-change check) that prevents it.

## Filtered chapter index (CRTC 0 + chip-agnostic only)

Chapters relevant to BBC (ignore subsections explicitly tagged "CRTC 1/2/3/4"):

| Doc pp | Topic | Wiki target |
|---|---|---|
| 32-35 | §6 Building a frame — counter model, video-pointer arithmetic | [[hardware/crtc-internal-counters]] |
| 36-41 | §7 Synchronization — VSync, fake VSync | [[techniques/triggered-vsync]] (planned) |
| 71-77 | §10 R9 counting | [[hardware/crtc-6845-advanced]] |
| 78-87 | §11 R5 counting + vertical adjustment | [[hardware/crtc-6845-advanced]], [[techniques/smooth-vertical-scroll]] |
| 88-95 | §12 R4 counting (CRTC 0: §12.2, §12.2.1 R.L.A.L.) | [[techniques/kefrens-bars]], [[techniques/single-rasterline-rupture]] |
| 96-121 | §13 R0 counting (CRTC 0: §13.2.x including freeze-of-VSync, freeze-of-C9, R0=0/1 case studies, R.V.L.L.) | [[techniques/rvi]], [[techniques/crtc-counter-freeze]] |
| 122-136 | §14 R3 sync widths | [[hardware/crtc-6845-advanced]] |
| 137-149 | §15 R2 hsync position | [[hardware/crtc-6845-advanced]] |
| 150-166 | §16 R7 vsync position + protection mechanisms | [[techniques/triggered-vsync]] |
| 167-179 | §17 R1 chars displayed | [[hardware/crtc-6845-advanced]] |
| 180-183 | §18 R6 vertical displayed | [[hardware/crtc-6845-advanced]] |
| 184-231 | §19 R8 interlace + skew | [[hardware/crtc-6845]] (already partially covered) |
| 232-235 | §20 R12/R13 video pointer | [[hardware/crtc-6845-advanced]] |
| 236-240 | §21 Read registers / status | not BBC-specific; CPC has status register at &BE00, BBC doesn't expose this |
| 243-258 | §23 Tips and tricks (chip-agnostic) | reference for [[techniques/single-rasterline-rupture]] etc. |
| 259-269 | §24 Fixed time / cycle counting | [[techniques/hexwab-stable-raster]] is the BBC analogue |
| 270 | §25 Z80A instruction durations | **Skip** — Amstrad-specific |
| 272-280 | §26 Interrupts | **Skip** — CPC uses Z80A IM2 + R52 line counter, BBC uses 6502 IRQ + System VIA |
| 281-283 | §27, §28 CRTC + CPC identification | reference for [[hardware/crtc-6845]] (HD6845R vs HD6845S already documented) |

## Open follow-ups

- **R.V.L.L. "hidden 2µsec ruptures" full worked code** — the compendium gives the recipe but no complete CRTC-0 code listing. Captured under [[techniques/rvi]].
- **Empirical verification on BBC HD6845SP** — the compendium's CRTC 0 behaviour matches the chip's design. Whether every cycle-by-cycle detail holds on the BBC's specific HD6845SP part vs the Amstrad's UM6845 (also classified "type 0") would warrant a SHAKER-style benchmark for the BBC. Tooling does not yet exist.
- **SHAKER portal** at <https://shaker.logonsystem.eu/> has photographs of test results per CRTC chip; useful when designing a BBC analogue.
- **R0=0 chip-freeze shipped use** — known to be experimented with on BBC, never shipped in a public demo. Worth a follow-up page when something does ship.

## Filed into

Phase A (this commit):
- [[hardware/crtc-internal-counters]] — NEW foundation page (the counter model).
- [[hardware/crtc-6845-advanced]] — refined: anomalous-rewrite table reframed via counter-window model.
- [[techniques/kefrens-bars]] — precise C0<2 mechanism replaces our hypothesis.
- [[techniques/single-rasterline-rupture]] — CPC-scene origin acknowledged (R.L.A.L.), terminology aliasing note.
- [[techniques/rvi]] — NEW: the BBC RVI technique, with CPC R.V.L.L. mapping.

Phase B (deferred):
- [[techniques/crtc-counter-freeze]] — NEW: R0=0 chip-freeze (experimental on BBC, no shipped use).
- [[techniques/triggered-vsync]] — NEW: R7 mid-line trigger + blocked-VSync gotcha.
- [[techniques/vertical-rupture]] — add Last-Line section + register-write windows.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
