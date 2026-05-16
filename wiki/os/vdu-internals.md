---
title: VDU driver internals — variables + plot vector
type: os
tags: [vdu, internals, plot-vector, vduv, gxr, hplot, gaddr]
sources: [master-rm]
updated: 2026-05-16
---

# VDU driver internals — variables and primitive entry points

The MOS VDU driver maintains ~120 bytes of state and exposes a handful of internal entry points that user code can call from the **unknown PLOT codes vector** (`VDUV` at `&226/&227`). These entry points let custom graphics code reuse the MOS's shadow-aware addressing, masking, and clipping primitives instead of re-implementing them. They are not documented in the [[sources/master-arm]] but get a *very* detailed treatment in [[sources/master-rm]] Ch E.4.

For the user-facing VDU command reference see [[os/vdu]]. For the full PLOT k reference see [[video/plot-codes]].

## VDU variable storage map

The VDU driver scatters its state across three regions of the I/O processor:

| Region | Where | Purpose |
|---|---|---|
| Page 0 | `&D0-&E1` | Hot-loop pixel/text masks + screen pointers |
| Page 3 | `&300-&37F` | Main VDU variable block (accessed by `OSBYTE &A0`) |
| Second-32K | `&8800-&88FF` | ECF patterns + soft chars (Master) |
| Second-32K | `&8400-&87FF` | Flood-fill workspace (Master) |

Master sideways-RAM also holds default character ROM at `&B900-&BFFF` (used when soft chars are reset).

### Reading variables — `OSBYTE &A0`

```asm
LDA #&A0
LDX #variable_number    ; e.g. &10 for graphics cursor X
JSR &FFF4
; X = low byte; Y = high byte (or next byte for 1-byte vars)
```

**Faster alternative if you know code is on the I/O processor (not parasite)**: read directly from `&300+X` (low) / `&301+X` (high). The unknown-PLOT-codes vector is guaranteed to run on the host, so direct reads are safe there.

⚠ Neither path is reliable from an interrupt service routine — the variables may be mid-update.

## VDU variable list (`&300-&37F`)

`(p)` = internal pixel coordinates; `(e)` = external (user) coordinates.

| Addr | Bytes | Variable |
|---|---|---|
| `&00` | 2 | Graphics window left column (p) |
| `&02` | 2 | Graphics window bottom row (p) |
| `&04` | 2 | Graphics window right column (p) |
| `&06` | 2 | Graphics window top row (p) |
| `&08` | 1 | Text window left column |
| `&09` | 1 | Text window bottom row |
| `&0A` | 1 | Text window right column |
| `&0B` | 1 | Text window top row |
| `&0C` | 2 | Graphics origin X (e) |
| `&0E` | 2 | Graphics origin Y (e) |
| `&10` | 2 | **Graphics cursor X (e)** — externally-visible position |
| `&12` | 2 | Graphics cursor Y (e) |
| `&14` | 2 | Previous graphics cursor X (p) |
| `&16` | 2 | Previous graphics cursor Y (p) |
| `&18` | 1 | Text cursor X (chars from left); during cursor-edit / unknown-PLOT: see notes |
| `&19` | 1 | Text cursor Y (chars from top); similar dual-use semantics |
| `&1A` | 1 | Y-offset for `GADDR` so that `(ZMEMG),Y` addresses correct byte |
| `&1B-&23` | 9 | **VDU queue** — `&23` is the most-recent byte; earlier bytes precede |
| `&24` | 2 | Graphics cursor X (p) |
| `&26` | 2 | Graphics cursor Y (p) |
| `&28-&49` | 34 | Workspace — but `&38` must not be used in MODE 7/135 |
| `&4A` | 2 | Address 6845 uses to display text cursor |
| `&4C` | 2 | Bytes per character row of text window |
| `&4E` | 1 | MSB of first byte of screen RAM |
| `&4F` | 1 | Bytes per character |
| `&50` | 2 | Address of byte in top-left corner (= R12/R13 mirror, [[video/hardware-scrolling]]) |
| `&52` | 2 | Bytes per character row of whole screen |
| `&54` | 1 | MSB of screen memory size |
| `&55` | 1 | Current screen mode (0-7, no shadow bit) |
| `&56` | 1 | Memory mode code: 0=20K, 1=16K, 2=10K, 3=8K, 4=1K |
| `&57` | 1 | Text foreground colour mask |
| `&58` | 1 | Text background colour mask |
| `&59` | 1 | 0 if plotting foreground; 8 if background |
| `&5A` | 1 | Current graphics plot mode (usually set from one of next two, reduced MOD 16) |
| `&5B` | 1 | Foreground plot mode (last VDU 18 with colour < 128) |
| `&5C` | 1 | Background plot mode (last VDU 18 with colour ≥ 128) |
| `&5D` | 2 | Address of routine processing current VDU sequence |
| `&5F` | 1 | R10 value to revert to when leaving cursor edit |
| `&60` | 1 | (num colours) − 1, or 0 in MODE 7 |
| `&61` | 1 | **(pixels/byte) − 1, or 0 if not graphics** — non-zero ⇒ graphics mode (test for "am I in graphics?") |
| `&62` | 1 | Mask for leftmost pixel in a byte |
| `&63` | 1 | Mask for rightmost pixel in a byte |
| `&64` | 1 | Cursor-edit output X (or input X inside unknown-PLOT vector) |
| `&65` | 1 | Cursor-edit output Y |
| `&66` | 1 | Cursor control flags (set by VDU 23,16) |
| `&67` | 1 | Dot pattern (set by VDU 23,6) |
| `&68` | 1 | Current state of dot pattern |
| `&69` | 1 | 0 if currently-plotting colour is solid; non-zero if ECF |
| `&6A` | 1 | 0 if foreground solid; non-zero if foreground ECF |
| `&6B` | 1 | 0 if background solid; non-zero if background ECF |
| `&6C` | 1 | Top bit set when cursor is in "column 81" pending state |
| `&6D` | 1 | Foreground graphics colour (last VDU 18) |
| `&6E` | 1 | Background graphics colour (last VDU 18) |
| `&6F-&7E` | 16 | **Software copy of current palette** |
| `&7F` | 1 | Reserved |

## Page-0 VDU workspace

| Addr | Name | Purpose |
|---|---|---|
| `&D0` | `STATE` | VDU status byte — **don't modify directly** |
| `&D1` | `ZMASK` | Pixel mask |
| `&D2` | `ZORA` | Text OR mask |
| `&D3` | `ZEOR` | Text EOR mask |
| `&D4` | `ZGORA` | Graphics OR mask (usable as workspace when not plotting) |
| `&D5` | `ZGEOR` | Graphics EOR mask |
| `&D6-&D7` | `ZMEMG` | Graphics pointer |
| `&D8-&D9` | `ZMEMT` | Text pointer |
| `&DA-&DB` | `ZTEMP` | Temporary |
| `&DC-&DD` | `ZTEMPB` | Temporary |
| `&DE-&DF` | `ZTEMPC` | Temporary |
| `&E0-&E1` | `ZTEMPD` | Temporary — used otherwise in pre-Master BBC micros |

Per [[sources/master-rm]] Ch E.4: when the unknown-PLOT-codes vector is entered on the I/O processor, these locations are guaranteed to belong to the VDU driver. Routines indirecting the vector into a sideways ROM (via extended vector to `&FF39`) face a different memory map — see "Sideways ROM intercept" below.

## Second-32K layout (Master only, visible when unknown-PLOT-codes vector is active)

The MOS sideways-RAM is paged in during unknown-PLOT-codes handling:

| Range | RAM/ROM | Purpose |
|---|---|---|
| `&8400-&87FF` | RAM | VDU workspace (flood-fill scratch) |
| `&8800-&8807` | RAM | ECF pattern 1 definition (8 bytes) |
| `&8808-&880F` | RAM | ECF pattern 2 |
| `&8810-&8817` | RAM | ECF pattern 3 |
| `&8818-&881F` | RAM | ECF pattern 4 |
| `&8820-&8827` | RAM | Current foreground ECF or solid colour |
| `&8828-&882F` | RAM | Current background ECF or solid colour |
| `&8830-&88BF` | RAM | VDU workspace |
| `&88C0-&88FF` | RAM | Reserved |
| `&8900-&89FF` | RAM | Current definitions of chars `&20-&3F` |
| `&8A00-&8AFF` | RAM | Chars `&40-&5F` |
| `&8B00-&8BFF` | RAM | Chars `&60-&7F` |
| `&8C00-&8CFF` | RAM | Chars `&80-&9F` |
| `&8D00-&8DFF` | RAM | Chars `&A0-&BF` |
| `&8E00-&8EFF` | RAM | Chars `&C0-&DF` |
| `&8F00-&8FFF` | RAM | Chars `&E0-&FF` |
| `&B900-&BFFF` | ROM | Default character definitions (mirror of soft-char RAM layout) |

## The 8 VDU primitive entry points (`&C000-&C015`)

These live in MOS ROM and are **only callable when the memory map is in the correct state** — which is guaranteed on entry to the unknown-PLOT-codes vector and *not generally true elsewhere*. Call them via `JSR &C0xx`.

### `&C000` — load screen byte (shadow-aware)

```asm
JSR &C000   ; LDA (ZMEMG),Y but routed correctly for shadow mode
```

17 cycles; +1 if page boundary crossed. The shadow-aware equivalent of an indirect-indexed load — handles ACCCON D/E/X automatically.

### `&C003` — store screen byte (shadow-aware)

```asm
JSR &C003   ; STA (ZMEMG),Y, shadow-aware
```

18 cycles. Same idea for writes.

### `&C006` — `PLBYTE`

```asm
JSR &C006   ; plot ZMASK into byte at (ZMEMG),Y using ZGORA/ZGEOR colour masks
```

Uses `ZTEMP` as workspace; preserves X, Y, V, C. This is the **single-pixel plot primitive** used throughout the VDU driver.

### `&C009` — `HPLOT` (horizontal line fast plot)

```asm
JSR &C009   ; horizontal line in current colour/ECF + plot mode
```

Pre-load two 4-byte areas at `&300+X` and `&300+Y` with endpoint coordinates (lowX, highX, lowY, highY format). If Y coords differ, the leftmost endpoint's Y is used. Only the portion inside the graphics window is plotted (both endpoints included).

The low-level primitive used by ALL MOS area fills. Uses `ZGORA`, `ZGEOR`, `ZMASK`, `ZMEMG`, `ZTEMP`, `ZTEMPB`, `ZTEMPC` as workspace. No registers preserved.

### `&C00C` — `EIGABS` (external → internal coords)

```asm
JSR &C00C   ; convert 4-byte external coord pair at &300+X to internal pixel coords
```

Subtracts graphics origin, then divides by appropriate power of 2 (mode-dependent). Uses `ZTEMP`; corrupts all registers + flags.

### `&C00F` — `WIND` (window clipping check)

```asm
JSR &C00F   ; classify 4-byte pixel-coord pair at &300+X relative to graphics window
; A returns position code (0 = inside; 1-10 outside in 9 directions)
```

Position codes:
```
 9 | 8 | 10
---+---+---
 1 | 0 | 2
---+---+---
 5 | 4 | 6
```

`A = 0` ⇒ inside the window. N and Z flags set per A. Preserves X.

### `&C012` — `GADDR` (pixel address)

```asm
JSR &C012   ; given pixel coords at &300+X, set up ZMEMG/Y/ZMASK/etc to address that pixel
```

⚠ **Don't call without first verifying the point is on-screen** (e.g. via `WIND`). On exit:

- `ZMEMG` = start of page containing the pixel
- `Y` (and VDU variable `&1A` = `&31A`) = offset of the byte within that page
- `ZMASK` = bitmask of the pixel within its byte
- `ZGORA` / `ZGEOR` = colour masks for current graphics plot mode + colour/ECF
- `X` = `Y MOD 7` = scan line within character row

Returns A=0, Z=1. Uses `ZTEMP`.

### `&C015` — `IEG` (internal → external graphics cursor)

```asm
JSR &C015   ; convert internal pixel cursor (&324-&327) back to external (&310-&313)
```

Call after your code generates a new graphics cursor position so that the two cursor copies (internal pixel + external user) stay in sync — otherwise relative plots will drift. Used internally e.g. after a character is printed in VDU 5 mode.

Uses no page-0 locations; corrupts all registers + flags.

## Worked example: re-implementing PLOT 64-71 (single point) from VDUV

Per [[sources/master-rm]] Ch E.4:

```asm
.POINT
  LDX #&20      ; address new point within VDU queue
                ; (left there on entry to unknown PLOT codes vector)
  JSR WIND      ; is point inside the graphics window?
  BNE END       ; return if not
  JSR GADDR     ; address the point now we know it's on-screen
  JSR PLBYTE    ; and plot it
.END
  RTS
```

This is the cleanest possible custom-PLOT implementation: it inherits the MOS's clipping, shadow-mode awareness, colour-mode handling, and ECF support for free. Substituting your own geometry computation for the WIND/GADDR/PLBYTE trio lets you add new primitives (e.g. anti-aliased lines, hardware-textured polygons) that integrate cleanly with the rest of the VDU system.

## Sideways-ROM intercept caveat

If the unknown-PLOT-codes vector is indirected into a sideways ROM via an extended vector (`&FF39` + extended-vector triple — see [[memory/os-workspace]] "Master vector additions"), MOS swaps the memory map *before* entering the ROM:

- Filing-system RAM occupies `&C000-&DFFF` (so the `&C000-&C015` entry points are **not accessible**).
- Sideways ROM occupies all of `&8000-&BFFF` (so the second-32K data areas `&8400-&8FFF` are **not accessible**).

You can work around this in two parts:

1. To use the entry points, *first* JSR into a small stub in main RAM (under `&8000`) that calls the MOS routines, then RTS back to the sideways ROM.
2. To access ECF pattern data / soft-char definitions, use OSWORD calls (`&05`/`&06` for sideways-RAM access — see [[memory/paged-rom]] ANDY section for the address-encoding convention).

This is awkward enough that direct unknown-PLOT-codes vector intercept (without sideways ROM) is the preferred pattern for performance-critical custom primitives.

## See also

- [[os/vdu]] — User-facing VDU command reference.
- [[video/plot-codes]] — PLOT k user reference.
- [[memory/os-workspace]] — Page 3 layout, Master second-32K full map.
- [[memory/shadow-ram]] — shadow-mode addressing the C000 entry points handle for you.
- [[techniques/custom-modes]] — when to leave the VDU driver entirely vs intercept its plot vector.
- [[sources/master-rm]] Ch E.4 — primary source.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
