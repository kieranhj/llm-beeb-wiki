---
title: What a real RGB monitor shows (visible window, black-level clamp)
type: video
tags: [monitor, crt, rgb, overscan, back-porch, clamp, rvi, hsync, real-hardware]
sources: [beeb-port-kit-hardware-facts-2026-11]
machines: [Master 128]
updated: 2026-11-18
---

# What a real RGB monitor shows

The 6845 and the Video ULA decide what is *sent*; the monitor decides what is *seen*. Two things about that matter to raster code that pushes the picture to its edges or puts video where the BBC normally has none: **how much of the line and field the tube shows**, and **how the monitor finds its black level**. Neither is modelled by any emulator.

Everything here is from KC's two real Master 128s and their monitors, photographed through phX's hardware-test disc, 2026-11-14/15 ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1 "Monitors"; `phX/docs/hwtest.md` "Results"), except the overscan entry (1942). Two monitors is a sample of two: treat the numbers as these monitors', not every monitor's.

## By-eye accuracy

Real-hardware results are read **by eye from a CRT** (photographs of test cards): good to about a pixel or a character, **not a cycle**. KC's "first colour seen" at an edge is coarser than one R2 step (two steps of R2 should move the picture 2 characters). Write timing that must be exact to the cycle is measured in an emulator; the monitor answers "is it visible" and "is it the right colour" ([[sources/beeb-port-kit-hardware-facts-2026-11]] intro).

## The visible window

Test geometry: R1 = 96 characters (MODE 2-style, 0.5 µs each), 268 displayed lines, R7 placing line 0 32 lines after VSync's start.

| | Sony RGB CRT (original Master) | CUB RGB CRT (Cherry Master) |
|---|---|---|
| Visible, R2 = 103 | characters 0 to ~92.5; lines 0 to ~264 | characters 0 to ~94.5; lines 0 to 267 |
| Visible, R2 = 105 | ~1 to ~93.5 | all 96 characters, both edges just on |
| RVI strays 1-4 µs left of the picture | not seen with the picture's colours | seen |
| Lit back porch | shifts every colour of the line (see below) | not disturbed |

- **Neither monitor shows characters 96-99 of an R1 = 100 line at any R2 tried.** The CUB shows ~2 characters more than the Sony. **Design for the narrower window.**
- The Sony loses the bottom ~3 lines (265-267 of 268) with line 0 just on — the picture is about a line taller than it shows.
- R2 moves the picture sideways; on the Sony R2 = 105 was the most even (about 1 character lost left, 2.5 right) (`phX/docs/hwtest.md` "R2").

## Overscan: 272 lit lines in a 312-line field

**A 50 Hz field can light 272 lines, not 256, and the overscan comes out of blanking, not out of the field** ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1 "Overscan"). 1942 runs a 256-line playfield and a 16-line panel below it with 40 lines of blanking (against PAL's nominal 25, about 15 lines of margin); the field stays 39,936.00 cycles (3,993,600 over 100 fields, jsbeeb). R7 moves the picture up and down the tube for free; light the panel's first and last lines so a real display shows the extent. **Played on a real Master 128 and display from 2026-09-28** (KC). **jsbeeb shows overscan happily, which proves nothing about a TV.** How 1942 keeps the scroll's variable adjust out of sight is on [[techniques/vertical-rupture]].

## The black-level clamp: keep the back porch black

**The Sony takes its black level in the back porch just after HSync.** Anything non-black there shifts every colour of that line — white shown as blue or magenta, green lost, cyan as blue. The CUB is not disturbed by a lit back porch.

How it was separated from the other explanations (three cards, Sony; `phX/docs/hwtest.md` "Results: tests F-H"):

| Card | What it does | Result | Rules out / in |
|---|---|---|---|
| F | as the failing RVI card, but the burnt lines shown black | right | not HSync cut at the wrap |
| G | HSync whole inside a 112-character line, the porch lit (C0 112-121, 1-10 characters after HSync's end at 110) | wrong | not "video inside HSync" — it is the porch |
| H | the Clown's geometry, lit only from C0 120 | right | the clamp window ends before C0 120 |

**Rule (phX decision 41): keep the back porch black**, from HSync's start to ~8 characters after it. This bites [[techniques/rvi]] in particular: a burn straight after the long line leaves HSync running through the burnt lines (they never reach C0 = R2) and their displayed characters light the porch. **Nothing blanks video during HSync on the BBC**: a displayed character inside HSync or the porch is sent at full colour (cards C and G), so keeping the porch black is the program's job.

## Strays: video the BBC sends where you did not expect it

RVI's burnt lines display their characters 0..R0 while R1 is above R0, so a 2-character burnt line shows its character 0 some 1-4 µs left of the picture ([[techniques/rvi]]). **The CUB shows these strays; the Sony did not with the picture's colours** (on the Sony they showed only as roughness at the left edge while the palette was white). Blank them in memory (a black column) or with the ULA's teletext-bit delay ([[hardware/video-ula]]); don't rely on the monitor hiding them.

A related monitor fact from the same tests: **a 6845 frame that ends on a 2-character (R0 = 1) line is not usable** — the Sony lost sync altogether and the CUB synced "with uncomfortable bending" (card L). End RVI frames on a long line ([[hardware/crtc-internal-counters]]).

## RGB, not composite

The tests were designed for RGB (the Master's 6-pin DIN). On composite or UHF the PAL encoder smears 2-pixel features into colour fringes, and because composite carries the sync in the same signal, video during HSync can disturb the line's timing — a ragged or bent right edge — where RGB, with separate sync, just shows or blanks it (`phX/docs/hwtest.md` "The monitor"; stated, not separately measured). Say which input a result was taken on.

## No emulator models a monitor

**jsbeeb draws every displayed character at full colour wherever it falls** — strays, a lit back porch and characters beyond the tube's edge all look fine — and nothing models a clamp or a visible window ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1). Emulators answer what the BBC sends; only a real monitor answers what is seen. b2 is the emulator that showed a misplaced (right-length, wrong-phase) field that rolls a TV ([[tools/emulators]]), but that is sync, not the picture's edges or colour.

## See also

- [[techniques/rvi]] — the technique most exposed to the clamp and to strays.
- [[hardware/crtc-6845]], [[hardware/crtc-6845-advanced]] — R1, R2 and the knife edges measured on the same Masters.
- [[techniques/vertical-rupture]] — overscan and frame shapes.
- [[video/modes]] — the standard 640 × 256 picture these windows are compared against.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
