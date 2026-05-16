---
title: PLOT codes (VDU 25 k)
type: video
tags: [plot, vdu, graphics, primitives]
sources: [bbc-user-guide, master-arm]
updated: 2026-05-16
---

# PLOT codes — VDU 25 k reference

`PLOT k, x, y` (BASIC) ≡ `VDU 25, k, xlo, xhi, ylo, yhi`. `k` selects one of 256 graphics primitives operating on the current graphics cursor + the point (x, y).

The User Guide (1982) documented `k = 0-95`; the Master extends with `k = 96-255` for the new rectangle / parallelogram / circle / ellipse / flood-fill primitives. Codes routed to **unknown PLOT codes** are dispatched via `VDUV` (`&226`) — see [[os/calls]].

## Structure of `k`

Codes 0-95 follow a uniform 8-byte grouping pattern; the low 3 bits select the **draw mode**, the next bits select the **operation**:

| Bit 7-3 | Bit 2-0 | Operation |
|---|---|---|
| 0 (codes 0-7) | 0..7 | **Line / move** with current colour |
| 1 (codes 8-15) | 0..7 | Same, but **omit last point** (for invert-XOR cleanup) |
| 2 (codes 16-23) | 0..7 | Same, **dotted line** |
| 3 (codes 24-31) | 0..7 | Same, dotted + omit last point |
| 4-7 (codes 32-63) | — | Reserved for Graphics Extension ROM |
| 8 (codes 64-71) | 0..7 | **Plot single point** |
| 9 (codes 72-79) | 0..7 | **Horizontal line fill left+right until non-background** |
| 10 (codes 80-87) | 0..7 | **Filled triangle** (uses last 2 points + (x,y)) |
| 11 (codes 88-95) | 0..7 | **Horizontal line fill right until background** |

Within each group, `k mod 8` selects:

| k mod 8 | Mode | Colour |
|---|---|---|
| 0 | move **relative** | — |
| 1 | draw line **relative** in current **foreground** |
| 2 | draw line **relative** in **logical inverse** |
| 3 | draw line **relative** in current **background** |
| 4 | move **absolute** | — |
| 5 | draw line **absolute** in current **foreground** |
| 6 | draw line **absolute** in **logical inverse** |
| 7 | draw line **absolute** in current **background** |

"Logical inverse" = `(num_colours - 1) - logical`, i.e. 0↔1 in 2-colour modes, 0↔3 / 1↔2 in 4-colour modes, 0↔15 / 1↔14 / etc. in 16-colour mode.

## Master extensions (PLOT 96-255)

Per [[sources/master-arm]] Ch 6 + App 2:

| Range | Operation |
|---|---|
| 96-103 | **Filled rectangle** — corners at graphics cursor and (x, y) |
| 104-111 | Horizontal line fill (variant of 72-79) |
| 112-119 | **Filled parallelogram** — vertices: old cursor, current cursor, (x, y), and 4th calculated parallel |
| 120-127 | Horizontal line fill (variant of 88-95) |
| 128-143 | **Flood fill** starting from (x, y) — stops at boundary defined by sub-code |
| 144-151 | **Circle outline** centred on graphics cursor, radius to (x, y) |
| 152-159 | **Filled circle** |
| 160-167 | **Arc** — line fill from cursor through (x, y) sweeping to last point |
| 168-175 | **Filled arc** (pie segment) |
| 176-183 | **Filled chord segment** (arc with straight chord) |
| 184-191 | **Ellipse outline** |
| 192-199 | **Filled ellipse** |
| 200-207 | Reserved |
| 208-231 | Currently undefined — reserved for application |
| 232-239 | Reserved |
| 240-247 | **Acornsoft sprites** (via VDU 23,27 driver) |
| 248-255 | Reserved / application |

The full taxonomy follows the same low-3-bit "mode + colour" convention as 0-7, so `PLOT 96` = move + rectangle (no-op), `PLOT 97` = filled-rectangle in foreground, `PLOT 101` = filled-rectangle in foreground (absolute), etc.

## Common patterns

### Move-then-line

```basic
MOVE 100, 100         : REM PLOT 4, 100, 100
DRAW 500, 300         : REM PLOT 5, 500, 300
```

The two-step move + draw pattern. Equivalent to `PLOT 4, ...` then `PLOT 5, ...`.

### XOR-sprite via dotted-line cleanup

```basic
GCOL 3, 1             : REM EOR mode, foreground
PLOT 5, X, Y          : REM draw line foreground (XOR onto screen)
REM ... timing / movement ...
PLOT 13, X, Y         : REM PLOT 5 but with last point omitted
```

The "omit last point" variants (k = 8-15, 24-31) avoid leaving a stray pixel when XOR-drawing back over a previously-drawn line.

### Filled triangle

```basic
MOVE 100, 100         : REM PLOT 4 — first vertex
MOVE 500, 100         : REM PLOT 4 — second vertex (replaces graphics cursor)
PLOT 85, 300, 400     : REM filled triangle (last 2 visited + this)
```

This is the canonical primitive for **textured / filled polygons** before Master added native rectangle/circle support.

### Single point

```basic
PLOT 69, 500, 500     : REM point at absolute (500, 500) in foreground
PLOT 71, 500, 500     : REM same point in background (erase)
PLOT 70, 500, 500     : REM same point in inverse colour (toggle)
```

`PLOT 70` is the classic single-pixel XOR — repeating it removes the pixel cleanly.

## Performance notes

- PLOT primitives go through the MOS VDU driver and (from BASIC) the interpreter dispatch overhead. From BASIC, `PLOT 69` takes hundreds of microseconds per point on a 2 MHz Model B — too slow for real-time animation of more than a few hundred points per frame (measure on your target machine if precise figures matter; the cost varies by mode, pixel position, and clipping window).
- For per-frame sprite work, **bypass the VDU driver** and write screen RAM directly. See [[techniques/fast-animation]] for the byte-move sprite pattern, [[techniques/custom-modes]] for direct-CRTC bypass.
- The "horizontal line fill until colour" primitives (PLOT 72-79, 88-95) are surprisingly cheap — useful for filling complex polygon scanlines without writing your own fill routine. Worth measuring against a hand-coded scanline filler if you're doing 2D polygon work.
- Flood-fill (PLOT 128-143, Master only) is **slow** — recursive in classic implementations. Avoid in tight loops; pre-render fills into an off-screen buffer if needed.

## Cross-references

- [[os/vdu]] — VDU 25 invocation; VDU 24 sets the graphics clipping window for PLOT.
- [[hardware/video-ula]] — palette (logical colour) mechanics; logical-inverse computation.
- [[video/modes]] — coordinate range per mode (external coords 0-1279 × 0-1023; internal pixel ranges differ).
- [[techniques/fast-animation]] — when to leave PLOT for direct byte moves.
- [[techniques/custom-modes]] — when to leave the VDU driver entirely.
- [[sources/bbc-user-guide]] Ch 33 (BASIC PLOT keyword) + Ch 29 (Advanced Graphics).
- [[sources/master-arm]] Ch 6 + App 2 — Master-era PLOT extensions.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
