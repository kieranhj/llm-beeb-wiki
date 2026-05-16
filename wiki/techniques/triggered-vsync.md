---
title: Triggered VSync (R7=C4 mid-line)
type: technique
tags: [crtc, vsync, r7, raster, mid-line, blocked-vsync]
sources: [accc-compendium]
updated: 2026-05-16
---

# Triggered VSync (R7=C4 mid-line)

Two related techniques on CRTC 0:

1. **Triggered VSync** — write `R7 = C4` mid-scanline (at C0vs≥2) to **start VSync immediately**, not at the next C0=0.
2. **Blocked VSync** — write `R7 = C4` at C0vs<2 to **inhibit VSync from firing at all** for that field, even though `C4=R7`.

Both are exploitations of the chip's VSync-protection mechanisms documented in [[sources/accc-compendium]] §16.3 and §16.4.1.1. The BBC scene hasn't shipped these as headline techniques (we don't know of a demo that uses them) but understanding them resolves a class of "why is VSync doing X" puzzles and unlocks some sub-line-precision sync tricks.

## The two VSync-protection mechanisms

The CRTC's VSync comparator (`C4=R7` → start VSync) has two anti-reentrancy interlocks (§16.3):

1. **R7-during-VSync ignore** — R7 writes while VSync is already active don't trigger a new VSync. This prevents nested / re-triggered VSyncs that would confuse the TV.
2. **Equality-change detection** — the chip only "considers" the `C4=R7` comparison when the equality has *changed* since last evaluated. Without this, an R4=0 setup (where C4 stays at 0 every line) would trigger VSync repeatedly forever. The equality-change happens when C4 increments OR R7 is written.

Mechanism (2) is the one we can exploit. Writing R7=C4 at the right C0vs phase either:
- "Triggers" VSync immediately (if C0vs≥2 — the equality-change is registered mid-line and the chip honours it), or
- "Blocks" VSync for that field (if C0vs<2 — the protection mechanism armed without the VSync firing).

`C0vs` here is the CRTC's internal horizontal counter as seen by the VSync comparator. On CRTC 0 it's the same as C0 for our purposes.

## Triggered VSync (C0vs≥2 write)

> "When R7=C4 with C0vs>1, the VSYNC is 'triggered' during the line. In this case, the row counter starts with 0. […] The total duration of the VSYNC is increased by the number of µsec corresponding to the calculation R0 − C0vs."
> — ACCC §16.4.1.1

Practical recipe:

```
1. Beam scanning some line N where you want VSync to start.
2. At C0vs ≥ 2 (mid-scanline), write R7 = C4 (the current row counter value).
3. VSync starts immediately from this point.
4. The C3h row-counter that times the VSync pulse starts at 0 from this point.
5. VSync ends after R3h × ~64 µs as normal — but the VSync edge has moved
   from "start of next scanline" to "wherever you wrote R7".
```

This gives you **horizontally sub-scanline precision** on when the VSync edge fires. The TV's vertical retrace timing depends on the VSync *edge*, not the row boundary, so this lets you nudge the displayed image up by a fraction of a scanline. Combined with [[techniques/smooth-vertical-scroll]] this would give finer-than-scanline vertical control if it were ever useful (most TVs don't resolve below a scanline anyway).

The extension of VSync duration by `R0 − C0vs` µs is a side effect — the chip times the pulse from when it actually started, not when it "should have" started at C0=0.

## Blocked VSync (C0vs<2 write)

> "If the modification of R7 with the value of C4 took place when C0vs<2, we are in a BLOCKED VSYNC. […] The VSYNC can no longer occur on the value of C4=R7 until an unblocking condition is produced."
> — ACCC §16.4.1.1

Mechanism: the equality-change-detection mechanism arms ("we've now seen C4=R7"), but the chip's R7 update timing means the VSync trigger itself misses the window. The chip then refuses to fire VSync for this `C4=R7` until either:

- `C4` changes (i.e. C4 increments past R7), or
- `R7` is changed to a different value, breaking the equality

**Practical consequence**: any code that writes R7 during the early-scanline window must be aware that the write might silently block VSync for that field. Specifically:

- VSync-resync code that aims to "trigger VSync now" by writing R7=C4 must do so at C0vs≥2.
- VSync-management code that updates R7 once per frame (e.g. modifying the VSync position dynamically) should avoid the C0vs<2 window on the scanline where C4=R7-1 would otherwise hit C4=R7.

If you find your VSync mysteriously stopping for one frame, this is a candidate cause. Recovery: write R7 to any *other* value, then back to the desired value (or wait for C4 to wrap).

## Limitless VSync (don't do this)

A different VSync pathology, documented in ACCC §16.6: by combining `R7=0`, `R4=0`, `R3h=0` (or other configurations that produce `C4=R7` repeatedly without C4 ever changing), you can make the chip generate VSync continuously. The TV cannot lock. Don't do this unintentionally.

CRTC 0 has both protection mechanisms (R7-during-VSync ignore + equality-change detection) so accidentally producing limitless VSync requires actively defeating both — possible but unlikely in normal code. CRTC 3/4 lack the second mechanism so they're easier to get into this state. Not directly relevant to BBC.

## When to reach for this

- **Per-field VSync-position adjustment without resyncing the framework** — write R7 at a known C0vs≥2 of the target scanline to move VSync edge by sub-scanline amounts.
- **Diagnostic: "why does VSync occasionally skip a frame?"** — if your framework writes R7 around the C4=R7 boundary, blocked-VSync may be the cause.
- **TV-sync experiments** — combined with [[techniques/hexwab-stable-raster]] you can precisely control where the displayed image sits vertically on the screen by nudging the VSync edge.

Most BBC raster effects don't need this — the standard "leave R7 alone after init" pattern of [[techniques/fx-framework]] sidesteps both the trigger and the block.

## Builds on / used by

- [[hardware/crtc-internal-counters]] — C4, R7, C3h counter semantics.
- [[hardware/crtc-6845-advanced]] — R7 row in the anomalous-rewrite table now references this page for the precise C0vs<2 vs C0vs≥2 dichotomy.
- [[sources/accc-compendium]] §16.3, §16.4.1.1 — primary documentation.
- [[techniques/crtc-counter-freeze]] — sibling technique exploiting R0 (rather than R7) for chip-state control.
- [[techniques/fx-framework]] — the standard "leave R7 alone" pattern that avoids both pathologies.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
