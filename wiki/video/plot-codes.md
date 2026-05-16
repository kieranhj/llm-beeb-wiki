---
title: PLOT codes (VDU 25 k)
type: video
tags: [plot, vdu, graphics, primitives]
sources: [bbc-user-guide, master-arm, master-rm]
updated: 2026-05-16
---

# PLOT codes — VDU 25 k reference

`PLOT k, x, y` (BASIC) ≡ `VDU 25, k, xlo, xhi, ylo, yhi`. `k` selects one of 256 graphics primitives operating on the current graphics cursor + the point (x, y).

The User Guide (1982) documented `k = 0-95`; the Master extends with `k = 96-255` for the new rectangle / parallelogram / circle / ellipse / flood-fill primitives. Codes routed to **unknown PLOT codes** are dispatched via `VDUV` (`&226`) — see [[os/calls]].

## Structure of `k` — the precise semantics

Per [[sources/master-rm]] Ch E.3, when a PLOT command is parsed the parameters are transformed and **the low 3 bits of k select coordinate-handling + colour mode independently**:

### `k mod 8` — coordinate mode and colour selection

| k mod 8 | Coordinate | Colour / plot mode |
|---|---|---|
| 0 | **Relative** to last visited point | "terminate rapidly": move old cursor → current, current → (x,y) — *no plot* (for fills/unknown codes: colour undefined, plot mode 5 "leave unchanged") |
| 1 | **Relative** | Last-set foreground colour + its plot mode (last VDU 18 with colour < 128) |
| 2 | **Relative** | Colour undefined; plot mode 4 (invert) — i.e. "draw in inverse" |
| 3 | **Relative** | Last-set background colour + its plot mode (last VDU 18 with colour ≥ 128) |
| 4 | **Absolute** | (same as 0: terminate rapidly) |
| 5 | **Absolute** | Last foreground |
| 6 | **Absolute** | Invert |
| 7 | **Absolute** | Last background |

This is why **`PLOT 4, x, y` = MOVE** (move-absolute, no plot) and **`PLOT 5, x, y` = DRAW** (draw-absolute in foreground colour). After every plot, the old cursor moves to where the current cursor was, then the current cursor moves to (x,y) — this 2-cursor history is what enables 2-point primitives (triangles, rectangles, parallelograms) and 3-point primitives (arcs, sectors).

### `k DIV 8` — operation group

| `k DIV 8` | k range | Operation |
|---|---|---|
| 0 | 0-7 | **Solid line** (both endpoints included) |
| 1 | 8-15 | Solid line (**last endpoint omitted** — for repeat-XOR cleanup) |
| 2 | 16-23 | **Dotted line** (both endpoints; pattern restarted) |
| 3 | 24-31 | Dotted line (last endpoint omitted; pattern restarted) |
| 4 | 32-39 | Solid line (**initial point omitted**) |
| 5 | 40-47 | Solid line (both endpoints omitted) |
| 6 | 48-55 | Dotted line (initial omitted; pattern **continued** from previous) |
| 7 | 56-63 | Dotted line (both omitted; pattern continued) |
| 8 | 64-71 | **Single point** at (x,y) |
| 9 | 72-79 | **Horizontal line fill** L+R until non-background |
| 10 | 80-87 | **Filled triangle** (old cursor, current cursor, (x,y)) |
| 11 | 88-95 | Horizontal line fill R only until background |
| 12 | 96-103 | **Filled rectangle** (current cursor + (x,y) as opposite corners) — Master |
| 13 | 104-111 | Horizontal line fill L+R until **foreground** — Master |
| 14 | 112-119 | **Filled parallelogram** — Master |
| 15 | 120-127 | Horizontal line fill R until **non-foreground** — Master |
| 16 | 128-135 | **Flood fill** to non-background — Master |
| 17 | 136-143 | Flood fill to foreground — Master |
| 18 | 144-151 | **Circle outline** (centre = current cursor; (x,y) on circumference) — Master |
| 19 | 152-159 | **Filled circle** — Master |
| 20 | 160-167 | **Circular arc** (centre = old cursor; current cursor = arc start; (x,y) direction defines arc end on circle; anticlockwise) — Master |
| 21 | 168-175 | **Filled chord segment** (arc + straight chord) — Master |
| 22 | 176-183 | **Filled sector** (pie slice: arc + 2 radii to centre) — Master |
| 23 | 184-191 | **Move/copy rectangle** (special k handling; see below) — Master |
| 24 | 192-199 | **Ellipse outline** — Master |
| 25 | 200-207 | **Filled ellipse** — Master |
| 26 | 208-231 | Reserved (routed to unknown PLOT vector) |
| 27 | 232-239 | Reserved for Acornsoft sprites |
| 28-31 | 240-255 | **Application-reserved** — routed through `VDUV` (`&226/&227`) with C=0, A=k |

### "Logical inverse" colour

When using `k mod 8 = 2` or `6`, the colour written is the **logical-inverse** of what's already there: `inverse(logical) = (num_colours - 1) - logical`. So 0↔1 in 2-colour modes, 0↔3 / 1↔2 in 4-colour modes, 0↔15 / 1↔14 / etc. in 16-colour mode. This is the cheapest way to draw "XOR" overlays that cleanly remove themselves on a second draw — though for performance work you usually want VDU 18 EOR mode (GCOL 3) instead.

### Move/copy rectangle (PLOT 184-191) — special k handling

Per [[sources/master-rm]] Ch E.3 (this group breaks the usual k MOD 4 colour convention):

| k | Operation |
|---|---|
| 184/185 | Move rectangle, **relative** |
| 186/187 | Copy rectangle, **relative** |
| 188/189 | Move rectangle, **absolute** |
| 190/191 | Copy rectangle, **absolute** |

Source rectangle = opposite corners at old + current graphics cursors. Destination = bottom-left at (x,y). **Move** clears the source area outside the destination to background; **copy** leaves the source alone. Any source pixels outside the graphics window are treated as background.

This is the BBC's "bit-blit" — useful for sprite-stamping, scrolling sub-regions, and double-buffered animation when combined with shadow RAM.

## Geometric primitives — precise definitions

These are the Master / GXR-era primitives, exactly as specified in [[sources/master-rm]] Ch E.3. The wiki used to attribute them to Master ARM Ch 6 + App 2 — that's where Acorn's older docs are; the MRM is the canonical user-level spec.

### Circles (144-151 outline, 152-159 filled)

- **Centre** = current graphics cursor position
- **Point (x,y)** = a point on the circumference
- Radius = distance from centre to (x,y)

Filled circle is "exactly bounded" by its outline: every pixel that would be lit by the outline is included, every pixel inside is included, no pixel outside.

⚠ Radius limit: in some modes very-large radii suffer numerical errors; reliable up to **radius < 16384** external units.

### Arcs / chord segments / sectors (160-183)

These are 3-point primitives — they use **old cursor + current cursor + (x,y)** to define a partial circle:

- **Centre** = old graphics cursor
- **First arc endpoint** = current graphics cursor
- **Second arc endpoint direction** = (x,y) direction from centre (the line from centre through (x,y) intersects the circle at the second endpoint)
- Arc goes **anticlockwise** from first to second endpoint

| Codes | Primitive | What's filled |
|---|---|---|
| 160-167 | **Arc** (outline only) | Just the curve |
| 168-175 | **Filled chord segment** | Area bounded by the arc + straight chord between endpoints |
| 176-183 | **Filled sector** | Pie slice: area bounded by the arc + 2 radii to centre |

Useful pattern: set graphics cursor to centre, MOVE to first arc point, PLOT to define second arc direction.

### Ellipses (184-191 outline, 192-199 filled)

Axis-aligned only (natively). Per Ch E.3 definition:

- **Centre** = old graphics cursor
- **X coordinate of current cursor** = X coordinate of one of the two horizontal intercepts (i.e. ellipse half-width along centre's horizontal axis)
- **(x,y) point** = the *highest* point of the ellipse if it lies above centre, otherwise the *lowest* point — the Y coordinate of the current cursor is **ignored**

So you supply: centre, half-width-X, half-height-Y. ⚠ Numerical inaccuracy starts to bite for half-height > ~2500 external units.

**For rotated ellipses**, the MRM gives a worked BASIC PROC (Ch E.3 p202) using cos/sin shear:

```basic
DEFPROCellipse(cx%, cy%, semimajor, semiminor, angle, type%)
LOCAL cosang, sinang, maxy, shearx, slicewidth
cosang  = COS(RAD(angle))
sinang  = SIN(RAD(angle))
maxy    = SQR((semiminor * cosang)^2 + (semimajor * sinang)^2)
shearx  = (semimajor^2 - semiminor^2) * cosang * sinang / maxy
slicewidth = semimajor * semiminor / maxy
MOVE cx%, cy%
MOVE cx% + slicewidth, cy%
IF type% = 0 THEN plotcode% = 197 ELSE plotcode% = 205
PLOT plotcode%, cx% + shearx, cy% + maxy
ENDPROC
```

`type% = 0` → outline (PLOT 197 = ellipse-outline, absolute, foreground); `type% != 0` → solid (PLOT 205 = solid-ellipse, absolute, foreground).

### Flood fill (128-143)

- **128-135**: flood from (x,y) until **non-background** pixels found
- **136-143**: flood from (x,y) until **foreground** pixels found
- Flood spreads orthogonally (NESW), **not diagonally**
- Will abandon if: area too complex, fill colour can itself be filled (e.g. PLOT 131/135 with VDU 18 mode 0 background-leave), or ESCAPE pressed
- Uses `&8400-&87FF` in MOS sideways RAM as workspace (Master second 32 KB)

### Horizontal line fill (72-79, 88-95, 104-111, 120-127)

Four variants, each scanning horizontally from (x,y) until a boundary pixel:

| Codes | Direction | Stops at |
|---|---|---|
| 72-79 | Left + right | non-background |
| 88-95 | Right only | background |
| 104-111 | Left + right | non-foreground (foreground colour) — Master |
| 120-127 | Right only | foreground — Master |

After fill, old/current cursors are set to L/R endpoints of the line filled. **Readable via OSWORD A=13** — useful for polygon-scanline fills where you query the fill extent and then move on.

If the seed pixel is the wrong colour, the cursors are set to indicate an error state (cursors not on the same horizontal line, or current = (x,y) + old one pixel left).

### Triangle (80-87)

Fills triangle with vertices at **old cursor, current cursor, (x,y)**. "Exactly bounded" — pixels on the boundary lines are included; nothing outside.

### Parallelogram (112-119)

Vertices in cyclic order: **old cursor, current cursor, (x,y), 4th-point**. 4th-point is calculated in *internal pixel coords* (not external) to guarantee parallel sides: `4th = (x,y) − current + old`.

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
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
