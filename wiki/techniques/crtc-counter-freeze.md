---
title: CRTC Counter Freeze (R0=0)
type: technique
tags: [crtc, r0, freeze, counters, experimental, raster, c9, c4]
sources: [accc-compendium]
updated: 2026-05-16
---

# CRTC Counter Freeze (R0=0)

**Experimental on BBC**: this technique has been explored on real hardware but is not used in any shipped demo as of 2026. Documented here for completeness — when the right use case appears, the recipe is ready.

Setting **R0=0** on CRTC 0 (the BBC's HD6845S/SP family) **freezes most of the chip's internal counters**. C0 stays at 0, C9 stops incrementing, C4 stops being managed (with one "last hiccup" exception). The chip becomes a near-statue. Restoring R0>2 unfreezes it; counters resume from where they were (subject to a couple of subtle armed-state quirks).

This is functionally distinct from [[techniques/rvi]] (which uses R0=1 mini-cycles to *advance* C9 invisibly during HSYNC) — R0=0 is the *suspension* lever, not the advancement lever.

Primary source: [[sources/accc-compendium]] §13.2.4, §13.2.6.

## Mechanics

When you write R0=0 while C0 is 0 (i.e. the current scanline has barely started):

1. **C0 stays at 0** — it never reaches 1 because there's no "next character clock" to advance to. The chip is stuck on the first µs of the scanline.
2. **C9 freezes** — C9 increment management is gated on C0 reaching 1, which never happens. Whatever value C9 had when R0=0 landed is preserved.
3. **C4 has one "last hiccup"** — if C9=R9 at the moment R0=0 takes effect, C4 increments **once** (the chip already armed this on the previous C0=0 evaluation). After that hiccup, C4 freezes too.
4. **R4/R5/R9 writes are ignored** during the freeze — they're stored in the registers but the chip doesn't read them.
5. **R8 is still considered each C0=0** — so interlace-mode bits still toggle effectively.
6. **R7 is still tested each C0=0** — but `C4` is frozen, so `C4=R7` only changes if you write R7.
7. **DISPTMG stays at whatever state it was in** — the display is stuck reading the same byte continuously (or stuck blanked, depending on where in the scanline R0=0 landed).
8. **VMA does not advance** — the CRTC keeps outputting the same address.

**To unfreeze**: write R0 back to a value ≥2 (≥1 still keeps additional-management armed weirdly). Increment management of C0 resumes from 0 onwards; other counters pick up from their frozen values.

## The "last hiccup" of C4

Per ACCC §13.2.6 exact wording:

> "If C9=R9 on C0=0 (when R0 goes to 0) then C9 is no longer managed, but C4 will however be incremented regardless of the value of R4. C4 is incremented without C9 returning to 0. Magical!"

So the exact frozen state of C4 depends on what C9 was at the moment of the freeze:

| State at moment R0=0 | C4 after freeze | Notes |
|---|---|---|
| C9 < R9 | unchanged | Clean freeze |
| C9 = R9 | C4 + 1 | The pre-armed increment fires, then everything freezes |
| C9 = R9 AND C4 = R4 | C4 + 1 AND additional-management armed | Both effects fire; additional-management persists into the unfreeze |

If additional-management was armed, it cannot be cancelled by C0=2 (because C0 never gets there). When you unfreeze, the chip is still in additional-management mode and will use R5 (not R9) for the next C9 reset. To clean up: write R5 = C9+1 before unfreeze, so the additional-management ends cleanly on the first post-freeze C0=0.

## VSync interaction

Important footgun from ACCC §13.2.2 + §16.4.1.2:

- If R0 (which was >2) becomes 0 on C0=0 of the first line where **C4=R7**, the VSync starts on C0=0 — but **the VSync line counter C3h is also frozen**. The VSync never ends if R3h was 1.
- If R0 becomes 1 (not 0) on that same line, VSync starts on C0=0 and the counter can increment (because C0 reaches 1 → C9 increments → C3h can advance). VSync ends after R3h scanlines as normal.

Practical implication: **don't freeze with R0=0 when a VSync is about to start**. Use R0=1 instead if you need to freeze during VSync-adjacent territory.

## What's still running during the freeze

- **System VIA / User VIA timers** — completely unaffected. T1 free-run, vsync IRQ flag, ADC conversions all proceed normally.
- **6502 execution** — completely unaffected. You're running normal code throughout the freeze.
- **Video ULA serialiser** — unchanged. It keeps serialising whatever byte the CRTC fed it last (which the CRTC is now feeding repeatedly because VMA doesn't advance). Visually this means a single 8-pixel horizontal stripe stuck where the beam was when freeze hit.
- **DRAM refresh** — **a serious concern**. The address translator's refresh-cycle behaviour ([[hardware/address-translation]]) relies on the CRTC actually scanning. When R0=0 freezes the CRTC, refresh patterns change. The ACCC compendium notes this; for CPC it's been characterised. For BBC it would warrant verification before any extended freeze (more than ~1 ms).

## Possible BBC use cases (speculative)

None are known to be shipped. Plausible candidates:

- **Synchronous burst-write windows** — freeze the CRTC for a few hundred µs while doing heavy data movement (e.g. fast bulk transfer to/from a peripheral), then unfreeze and let the display resume. Cleaner than blanking the display via ULA because the chip state is preserved exactly.
- **Music-player jitter elimination** — freeze the chip across a music-update boundary so any data-dependent timing in the music player doesn't propagate to display timing. Probably overkill in practice.
- **Per-frame screen disable** without losing CRTC state — set R0=0 for the whole display period of a frame, then restore. Effectively a "frame skip" with cycle savings.
- **Deliberate raster suspension as a debugging tool** — freeze the chip at a known point and inspect counter state via DRAM-refresh-via-MA observation (with a logic analyser).

The "right" use case is probably something none of the above. If you find one, this is the page to update.

## Don't confuse with

- **[[techniques/rvi]]** uses R0=1 (mini-cycles, C9 advances) — opposite intent.
- **R8 = `&F0` screen-blank** ([[hardware/crtc-6845]]) — visually similar (display goes black) but the CRTC keeps scanning normally; only DISPTMG is gated off.
- **Disabling the Video ULA** — affects serialisation, not the CRTC's counter state.

## Builds on / used by

- [[hardware/crtc-internal-counters]] — the C0/C4/C9 model that explains why R0=0 freezes the chip.
- [[hardware/crtc-6845-advanced]] — R0 mid-frame rewrite verdict updated to reference this technique.
- [[sources/accc-compendium]] §13.2.4 (freeze of C9), §13.2.6 (R0=0 case study) — primary documentation.
- [[techniques/triggered-vsync]] — sibling technique exploiting R7 (rather than R0) for chip-state control.
- [[techniques/rvi]] — the R0=1 sibling (advance C9 via mini-cycles).
