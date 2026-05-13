---
title: Shadow RAM & ACCCON
type: memory
tags: [shadow-ram, acccon, hazel, double-buffer]
sources: [naug-ch12-memory]
machines: [BBC B+, Master 128, Master Compact]
updated: 2026-05-13
---

# Shadow RAM & ACCCON

On B+ and Master, an additional 20 KB of RAM lives at `&3000-&7FFF` in a parallel "shadow" bank. The 6845 can read from it, the CPU can read/write to it, the VDU driver can target it — independently selectable. This is the foundation for both **freed-up main RAM in shadow modes** and **double-buffered animation** on Master.

**Not present on Model B or Electron.**

## ACCCON — `&FE34`

ACCCON is the access-control register. Layout differs between machines:

### B+

```
bit:   7    6    5    4    3    2    1    0
       -    -    -    -    -    -    -    S
```

Just one functional bit:
- **S** — set: shadow RAM both written-to-by-VDU and displayed-by-6845; cleared: main RAM for both.

### Master 128 / Master Compact

```
bit:   7    6    5    4    3    2    1    0
       IRR  TST  IFJ  ITU  Y    X    E    D
```

| Bit | Name | Effect when set | Effect when clear |
|---|---|---|---|
| 0 | **D** | 6845 displays from shadow RAM | 6845 displays from main RAM |
| 1 | **E** | VDU driver writes go to shadow RAM | VDU driver writes go to main RAM |
| 2 | **X** | CPU sees shadow at `&3000-&7FFF` | CPU sees main at `&3000-&7FFF` |
| 3 | **Y** | HAZEL: 8 KB filing-system RAM at `&C000-&DFFF` | MOS VDU driver code at `&C000-&DFFF` |
| 4 | **ITU** | Internal Tube enabled | External Tube |
| 5 | **IFJ** | FRED/JIM (`&FC00-&FDFF`) routed to cartridge | Routed to 1 MHz bus |
| 6 | **TST** | Hardware test mode (do not set) | Normal |
| 7 | **IRR** | Forces an IRQ to the CPU | After IRQ processed |

## The "running from where you switch from" trap

When you flip **X** (CPU view of `&3000-&7FFF`), if your code is running from anywhere inside `&3000-&7FFF`, the next instruction fetch goes to the **other** bank — which probably contains screen pixels, not code. **Crash.**

Always do bank-switching from code that lives:
- in zero page (very tight) or stack;
- in `&0E00-&2FFF` (user RAM below the screen);
- in MOS ROM (won't help you control it though);
- in `&8000-&BFFF` (sideways ROM/RAM);
- in `&C000-&FBFF` (MOS).

For the same reason, ACCCON's **Y** (HAZEL) must be cleared before the next character output, or the VDU driver code is missing.

## Use cases

### Free up main RAM (B+ / Master shadow MODE 0)

Select a shadow MODE (128-135 = MODE 0-7 with shadow forced) or `*SHADOW` + a normal mode. The 6845 reads the shadow bank; `&3000-&7FFF` in main RAM is now free for user code. On a Model B in MODE 0 you have ~5 KB for code; on B+ shadow MODE 0 you have ~25 KB.

### Double-buffered animation (Master only)

Master's split of **D** (display source) and **E** (VDU-writes destination) plus the user OSBYTEs `&6C`/`&70`/`&71` lets you:

1. Display from bank A (D=0).
2. Direct all VDU writes to bank B (`OSBYTE &70` X=2 if A is main, or X=1 if A is shadow). Equivalently set/clear E.
3. Render the next frame into bank B.
4. Flip: switch D so 6845 shows bank B, redirect VDU writes to bank A.

The visible frame is never half-drawn. Vsync alignment still required (see `[[video/hardware-scrolling]]` vsync section) for the flip itself.

Note: **B+ cannot do this** — its single S bit ties together "write" and "display". Master is required for clean double-buffering.

### Direct screen writes (bypassing VDU)

If you write directly to screen RAM (e.g. `STA &5800,Y` for MODE 4) instead of using OSWRCH, you must:

- On Model B: nothing extra — main memory always.
- On B+ with shadow on: writes hit main RAM, but display is shadow. **Your writes are invisible.** Either deselect shadow first or use B+ in non-shadow mode.
- On Master: set ACCCON's **X** bit (or use `OSBYTE &6C` X=1) so the CPU sees shadow at `&3000-&7FFF`, then write, then clear X (or `OSBYTE &6C` X=0). Don't run the switching code from `&3000-&7FFF`.

## Helper OSBYTEs (Master only)

| OSBYTE | Function |
|---|---|
| `&6C` | Select CPU view of `&3000-&7FFF`: X=0 main / X=1 shadow |
| `&70` | Select VDU-write target: X=0 default / 1 main / 2 shadow |
| `&71` | Select 6845 display source: X=0 default / 1 main / 2 shadow |
| `&72` | Force shadow regardless of mode (B+ + Master): X=0 force / X≠0 normal |
| `&FA` | Read/write the OSBYTE `&70` flag |
| `&FB` | Read/write the OSBYTE `&71` flag |
| `&EF` | Read/write the OSBYTE `&72` flag |

Prefer the OSBYTEs over raw ACCCON writes — the MOS keeps an internal copy and uses it to manage IRQ entry/exit and VDU output. Direct ACCCON writes will desync that copy and produce odd VDU behaviour.

## HAZEL (Master)

8 KB of RAM at `&C000-&DFFF` overlaying MOS VDU driver. Selected by ACCCON **Y**. Designed for filing-system workspace — DFS on Master can put its tables there instead of stealing pages from `&0E00`, raising PAGE for the user. Must be cleared before VDU output resumes.
