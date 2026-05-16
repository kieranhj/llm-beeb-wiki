---
title: Open-Endpoint Chaining (Raster's polygon-friendly endpoint convention)
type: technique
tags: [graphics, line, polygon, wireframe, bresenham]
sources: [line-drawing-implementations, raster-source]
updated: 2026-05-17
---

# Open-Endpoint Chaining

Convention used by `raster.s`: each `draw_line` call draws pixels from start *up to but NOT including* the end. On return, the screen pointer and Y register are left positioned at the endpoint, ready for the next segment.

See [[techniques/bresenham-line]] for context. The other four line implementations (Elite, RTW, NJ, Tricky) all draw closed-interval lines including both endpoints.

## The problem it solves

Wireframe polygon rendering chains line segments sharing vertices: `A→B`, `B→C`, `C→A`. If each segment draws both endpoints (closed interval), vertex B gets drawn *twice* — once as the endpoint of `A→B`, once as the start of `B→C`.

In XOR-drawing mode (the standard for vector graphics on monochrome BBC), this is catastrophic: every shared vertex draws then *un-draws*. Polygons appear with missing corners.

The workarounds in closed-interval implementations:

1. **Skip the start of every-other segment** — caller logic, fragile, easy to get wrong.
2. **Re-plot vertices after drawing** — wastes cycles, requires tracking vertices.
3. **Use direct-write (not XOR) for vertices** — slower, breaks XOR-erase model.

Raster sidesteps the issue: draw the start, skip the end, let the next segment pick up the endpoint.

## The contract

From raster.s's header (lines 35-42):

```
draw_line draws pixels from (raster_x0,raster_y0) up to but NOT
including (raster_x1,raster_y1). On return, raster_base/Y are
positioned at (raster_x1,raster_y1), ready for the next segment
or a final pixel plot. Caller must:
  1. JSR init_base for the first point of a chain
  2. JSR draw_line for each segment (Y preserved through setup)
  3. Copy raster_x1→raster_x0, raster_y1→raster_y0 between segments
  4. Plot the final pixel of the chain using (raster_base),Y
```

The chain is closed by an explicit final pixel plot, *outside* the line-drawing loop.

## Performance side-effect

Beyond correctness, the convention has a perf benefit: `init_base` (the expensive screen-address-from-(X,Y) computation) is called *once per polyline*, not once per segment. The doc estimates ~30c saved per segment after the first.

For a 4-vertex polygon (4 segments + 1 close = 5 lines), the saving is 4 × 30c = 120c per frame per polygon. For an Elite-style cockpit with 20 polygons, that's 2400c per frame — about 6% of a 20ms frame budget.

## Why the other implementations don't do this

Elite, RTW, NJ, Tricky all set up the screen address inside `drawline` from the start coordinates. They are designed as *one-shot* primitives — caller supplies (x0,y0,x1,y1), routine draws it, no shared state. The init cost is paid every call.

This is a sensible default for non-polygon use cases:

- BASIC `MOVE`/`DRAW` (each call independent)
- Crosshairs, sights, individual rays
- Single-segment effects

Raster's convention is *worse* for one-shot calls (caller must `init_base` then `draw_line`, two calls instead of one). It's the polygon case where it shines.

## Caveats

- **Single-segment lines need extra code.** Caller must plot the final pixel separately if the line is intended to be closed.
- **Endpoint-state pollution.** Caller must not assume `raster_base`/Y are unchanged across `draw_line`. They're now part of the API.
- **XOR mode assumed.** If the caller is doing direct-write (set mode, not XOR), drawing vertices twice is harmless — open endpoints aren't needed. Adds a layer of API complexity for no gain in that mode.
- **Bresenham determinism.** "Last pixel not drawn" assumes Bresenham's pixel order is deterministic. If you reverse-draw a segment (swap start/end), the *opposite* endpoint becomes the open one — must be handled consistently across the polygon's edges or vertices will mismatch.

## Adapting to other implementations

The change is mechanical:

1. Decrement `count` by 1 at setup (one fewer pixel).
2. After the loop, ensure screen state (cursor / pointer / Y) is at the *un-drawn* endpoint position.
3. Document the caller contract.

For Elite, RTW, NJ, Tricky — this would be a 3-5 line patch and an API change. The doc (§9.2) flags this as portable.

## When to use it

- **Wireframe polygon rendering** in XOR mode. The main use case.
- **Vector fonts** where glyphs are polylines with shared interior strokes.
- **Anywhere line-drawing dominates the frame budget** and chained segments are common.

## When *not* to use it

- **Single-segment lines** (BASIC MOVE/DRAW). Two-call API is overhead.
- **Direct-write (non-XOR) mode.** No correctness benefit.
- **Mixed callers** where some need closed-interval and some need open. Pick one convention per routine; don't add a flag.

## Cross-references

- [[techniques/bresenham-line]] — the comparison page
- [[techniques/cumulative-mask-batching]] — NJ's perf trick
- [[techniques/carry-chain-invariant]] — Raster's other named innovation
- [[sources/raster-source]] — annotated source for raster.s
- [[sources/line-drawing-implementations]] — the comparative analysis

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
