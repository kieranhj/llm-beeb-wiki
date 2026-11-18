---
title: Shadow RAM & ACCCON
type: memory
tags: [shadow-ram, acccon, hazel, double-buffer]
sources: [naug-ch12-memory, master-arm, master-rm, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
machines: [BBC B+, Master 128, Master Compact]
updated: 2026-11-18
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
| 0 | **D** | 6845 displays from LYNNE (shadow) | 6845 displays from main RAM |
| 1 | **E** | Auto-shadow: CPU access to `&3000-&7FFF` routes to LYNNE *iff* last opcode fetch was from `&C000-&DFFF` and this cycle is **not** an opcode fetch | CPU sees main always |
| 2 | **X** | Unconditional: CPU sees LYNNE at `&3000-&7FFF` for every access (including opcode fetch) | CPU sees main always |
| 3 | **Y** | HAZEL: 8 KB filing-system RAM at `&C000-&DFFF` overlays MOS VDU driver | MOS VDU driver code at `&C000-&DFFF` |
| 4 | **ITU** | Internal Tube enabled | External Tube |
| 5 | **IFJ** | FRED/JIM (`&FC00-&FDFF`) routed to cartridge | Routed to 1 MHz bus |
| 6 | **TST** | Hardware test mode (do not set) | Normal |
| 7 | **IRR** | Open-drain pull on NIRQ — forces IRQ to the CPU | Clear (no forced IRQ) |

Acorn-internal vocabulary used in the Master ARM ([[sources/master-arm]] Ch 3):

- **Region (a)** = `&3000-&7FFF` (the screen area, what LYNNE can overlay).
- **Region (b)** = `&C000-&DFFF` (the MOS VDU driver area, what HAZEL can overlay).
- **LYNNE** = the 20 KB shadow display RAM (in DRAM at `&9000-&DFFF`; physically distinct from main RAM at `&3000-&7FFF`).
- **HAZEL** = the 8 KB filing-system overlay RAM.

### How the E-bit "magic" works (the precise mechanism)

ARM Ch 3 page 31 shows the flowchart:

```
Wait until end of CPU clock cycle
   ↓
Was the last cycle an opcode fetch (SYNC=1) from &C000-&DFFF in RAM?
   No → access main memory at &3000-&7FFF
   Yes ↓
Is *this* cycle an opcode fetch?
   Yes → access main memory at &3000-&7FFF
   No  → read/write LYNNE
```

This is what makes shadow MODE "just work" when the MOS VDU driver writes to the screen: VDU driver code runs from `&C000-&DFFF` (region b), so its data accesses to `&3000-&7FFF` get auto-redirected to LYNNE — without the user code (which runs from `&0E00-&7FFF` or similar) needing to know. User code's opcode fetches from `&3000-&7FFF` still hit main, so user programs in that area work normally.

The dependency on "previous cycle was an opcode fetch" is the chip's way of distinguishing "VDU driver doing a screen write" from "VDU driver returning from RTS" (a stack pull, also not an opcode fetch but should go to stack). The MOS VDU driver always does *its* screen writes immediately after an instruction fetch from its own code region, so the heuristic catches the right case.

For unconditional CPU-side LYNNE access (e.g. user code wants to write directly to the shadow screen without going through the VDU driver), use **X**, not E.

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

The visible frame is never half-drawn. Vsync alignment still required (see [[video/hardware-scrolling]] vsync section) for the flip itself.

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

## Measured in practice — Edge Grinder on a Master 128 (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Edge Grinder is a shadow-RAM double buffer (a 16K play area in each of main and shadow at `&4000-&7FFF`, the display bit flipped in the VSync handler) that also takes HAZEL and ANDY for its music.

### ACCCON and the display

- **The shadow display bit (D, bit 0) flips cleanly inside the VSync handler**, so a main/shadow double buffer can be swapped in vertical blanking with the scroll address — the "double-buffered animation" above, done directly rather than through the OSBYTEs (2026-09-02, jsbeeb: 10 game frames in 20 fields with a two-field frame lock; [layer-2-display.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-2-display.md)).
- **The display bank can be switched INSIDE a frame, and D acts AT the character written — measured on real Masters.** Edge's first measurement: a VSync-synced delay loop flipping D put main RAM above the switch and shadow below it, with a step part way along the scanline the write landed in (2026-09-04, jsbeeb; [layer-6e-titles.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-6e-titles.md)). [[techniques/parallax-bars]] relies on the same switch. **Now real hardware** ([[sources/beeb-port-kit-hardware-facts-2026-11]] §2, §4):
  - **1942** keeps its 2-row panel in shadow only: a rupture fire in the horizontal blanking of the last play scanline sets D for the panel's 16 lines, the VSync hook clears it; its oracle saw the write land at `horizCounter` 74-82 in 792 of 798 fields, and the panel matched shadow's bytes 0 of 3,584 wrong with main's copy poked to a pattern (jsbeeb 2026-10-07; **real Master 128 2026-10-13**, KC: "the panel looks good on real hw"). 1942 decision 141.
  - **phX, KC's two real Masters, 2026-11-14 (hardware-test card A)**: D = 1 written mid-line at C0 48 and at C0 59 (odd) switches the display **at exactly that character, with no glitch character**, and D toggled in the blanking every line alternates whole lines cleanly; jsbeeb the same. An odd C0 means `&FE34` is a 2 MHz write. Unlike the palette (`&FE21`, which acts early on a real Master — see [[hardware/video-ula]]), D is character-aligned because it changes which memory the fetch reads. phX's spectrum analyser builds its bars on it.
  *(Until 2026-11-18 this entry said "jsbeeb only; real hardware is untested".)*
- **The hardware wrap applies inside whichever bank is displayed.** With D = 1 and the wrap at 8K, a display crossing `&8000` lands on shadow `&6000`, not main. One ring per bank (2026-09-04, jsbeeb). Still an emulator result only (kit §12). See [[hardware/address-translation]].
- **Nothing displayed below `&3000` while D is set: with D = 1 the video reads ANDY and HAZEL there, not main RAM** — measured on a real Master. The history:
  - Edge (2026-09-02): jsbeeb 1.x displayed a panel at `&2000` under both shadow states; b-em showed garbage on alternate frames ([decisions.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/decisions.md) 17). KC's hypothesis (2026-09-07): with D set a CRTC address below `&3000` reads ANDY/HAZEL.
  - **Stryker's Run (2026-10-23, jsbeeb 2.10)**: confirmed in emulation — jsbeeb 2.10's `videoRead` ORs `&8000` into the address when D is set. Its HUD row, a CRTC frame read from `&0B80`, showed **ANDY's** sprite bytes (`&8000-&8FFF`) on every shadow field until D was cleared from VSync through the HUD's frame and set in the horizontal blank after it; b2 showed it right after the fix ([strykers-run BUGS.md #15](https://github.com/kieranhj/strykers-run/blob/main/BUGS.md)). Its checks timed the writes rather than sampling what the video read, and missed it for a day.
  - **phX, KC's real Master, 2026-11-15 (hardware-test card I)**: D = 1 over CRTC addresses `&1800-&1AFF`, with main RAM there blue and HAZEL `&C800-&CAFF` green — the lines showed **green**. With D set the 6845 reads HAZEL below `&3000`, as jsbeeb and b2 have it; **b-em's alternate-frame garbage was b-em's** (`phX/docs/hwtest.md` "I", "Results: tests I-L").
  The rule now: **D = 0 over any displayed row below `&3000`**; displaying below `&3000` with D = 0 works. See [[tools/emulators]].
- **The shadow screen is 20K of RAM nobody is looking at while main is displayed**, so with D = 0 and X = 1 (CPU sees shadow) it is a free staging area for compressed streams at boot (2026-09-04; [layer-9-loader.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-9-loader.md)). See [[techniques/zx0-loading]].

### ACCCON discipline (1942, Stryker's Run, phX — 2026)

From [[sources/beeb-port-kit-hardware-facts-2026-11]] §4 and gotchas class 6:

- **X redirects every CPU access to `&3000-&7FFF`, not just the screen** — reads included. A renderer that draws into shadow with X set reads shadow's copy of any code or data in `&3000-&3FFF`, so that must be mirrored into shadow or kept below `&3000`, and anything the interrupt reads must be below `&3000` (the interrupt can land mid-draw). Stryker's Run keeps its IRQ's variables below `&3000` and audits the rest (`tools/shadowaudit.mjs`: every read in `&3000-&3FFF` with X set, called stale where shadow's byte differs from main's) (2026-10-16, jsbeeb 2.5.0; [decision 23](https://github.com/kieranhj/strykers-run/blob/main/docs/decisions.md)). And **X names the back buffer only while drawing**: game state in `&3000-&7FFF` read with X still on the back buffer is the other buffer's copy — 1942 ignored a stage-end hold on every other tick that way.
- **Two methods of sharing ACCCON between parties, and both are sound** (X belongs to the drawer, D to the VSync take or a panel fire, Y to HAZEL):
  - **Never read ACCCON back; compose every write** (1942): one writer ORs the parts together (`acc_x OR buf_live OR pan_on`) and masks interrupts across its own compose-and-store. A value the boot leaves in one ORed part is ORed into every write: 1942's `pan_on` lived on a MOS vector byte, was non-zero at boot, and put `game_init`'s state into shadow — every enemy block of every stage came a block early (1942 decisions 43, 141; BUGS #47; jsbeeb 2026-09/10).
  - **Change one bit in place with `tsb`/`trb`** (phX): "only `tsb`/`trb` or read-modify-write — Y must never drop", since its disc layer lives in HAZEL. A `tsb &FE34` does read ACCCON back, but as one instruction an IRQ cannot land between its read and its write, so an interrupt that changes ACCCON and restores it on exit cannot be undone by it; a multi-instruction `lda`/`ora`/`sta` must be masked. phX runs this way through the whole demo, played on KC's real Master (`phX/CLAUDE.md` Traps). See [[hardware/6502]].
  The point both agree on: no party may write a stale copy of another party's bit.
- **Never set ACCCON bits 5-7 (TST, IFJ, IRR — named per the table above).** jsbeeb ignores them, so a stray value there passes every emulator check; phX's analyser draw once wrote CRTC R0 values into ACCCON. **What a real Master does with them was NOT observed** — the rule is from the register's documented meaning (IRR forces an IRQ, TST is a test mode) and jsbeeb's silence, not from a failure on hardware. phX's `tools/acccon_watch.mjs` checks every ACCCON write over the whole demo (`phX/CLAUDE.md` Traps, B7 step 0).
- **A late frame flipped mid-field shears sprites, never a double-buffered scrolling background**: both buffers hold the same level bytes at the same addresses, so the cut cannot mark the scenery. 1942 flips at once rather than holding a field, except for text frames (a sheared caption reads as broken) (1942 decisions 64, 65; jsbeeb and KC's eye).
- **ACCCON's D/X double buffer is the Master's alone.** The B+'s CPU accesses to `&3000-&7FFF` follow the displayed screen, so it cannot draw one screen while showing the other; the Integra-B's 20K is the CPU's only. A Master shadow-double-buffered game goes to a Model B as one screen raced against the beam (Stryker's Run's Model B build draws in the 112 blank lines and behind the beam). On a Model B `&FE34` is a ROMSEL mirror, so every ACCCON write has to go. OSBYTE 0 with X = 1 names the machine (1 B, 2 B+, 3 Master 128; 5 Compact from the AUG only) (Stryker's Run 2026-10-24/25; the B+ and Integra-B from their documentation; the Model B build played by KC in b2).
- **`*SHADOW` then soft BREAK leaves ACCCON `&1B`** (D and E set, the display in shadow) under a game that assumes main is displayed: a blue strip, no panel. The kit template's boot now writes ACCCON itself and reads `&18` there (jsbeeb Master, 2026-09-11; paradroid-beeb #18 — kit §4 "Target configurations").

### HAZEL

- **HAZEL is the filing system's workspace. Take it, and BREAK must clear memory.** A soft BREAK out of the game gave `Acorn MOS` with no DFS banner and `*CAT` returned nothing. `OSBYTE 200, X=3` at the top of the program makes BREAK a power-on reset (bit 1) and disables ESCAPE (bit 0); afterwards BREAK gave a clean `Acorn 1770 DFS` and SHIFT+BREAK reloaded the game. Load HAZEL's contents LAST and touch the disc no more (2026-09-04, jsbeeb, before and after; [layer-7-music.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-7-music.md)). See [[os/break-intercept]].
- **OSFILE cannot write into HAZEL** (the MOS would be overwriting its own workspace from underneath itself); stage in RAM and copy or unpack up with Y set (stated as the reason for the staging design).
- **`&FFFE` on this Master reads `&E59E`**, above HAZEL's `&DFFF`, so paging HAZEL in cannot break interrupt dispatch (2026-09-04, jsbeeb, read out of the machine).
- **Sideways bank `&BFFF` and HAZEL `&C000` are adjacent and both visible at once** (different registers, different windows), so a pointer walking off the end of a bank lands in HAZEL and a data stream can lie across the join. Two of Edge Grinder's eleven music streams do (2026-09-04, jsbeeb: SN76489 captures match the reference across the join).
- ANDY (ROMSEL bit 7) is a separate mechanism, measured on [[memory/paged-rom]].
- **`&C300-&DEFF` is usable with DFS still working (pop-beeb's range), depending on what the program still asks of the filing system** (kit, 2026-09-11, jsbeeb Master 128 MOS 3.20, 1770 DFS; the OSFILE-load, `*CAT` and soft-BREAK figures matched 1942's independent run byte for byte — [[sources/beeb-port-kit-hardware-facts-2026-11]] §4). The window was filled with `page EOR offset` from main-RAM code and checked after each kind of call:

  | after | written inside `&C300-&DEFF` |
  |---|---|
  | OSFILE load, 8 KB file, ×4 | nothing |
  | OSFILE save and delete | nothing |
  | any `*` command (OSCLI) | `&DC00` up: the command line |
  | `OPENIN` + `BGET` | 32 bytes of `&C3` per open channel, plus a page per channel from `&C400` up |
  | soft BREAK | 10 bytes of `&C3`, 237 of `&DA` |

  DFS worked throughout with the whole window overwritten. `&C000-&C2FF` and `&DF00-&DFFF` hold DFS data at rest and change during calls — not usable. So: OSFILE only → all `&C300-&DEFF` (7K); plus `*` commands → lose `&DC`; plus open files → lose `&C3` and a page per channel; must survive a soft BREAK → lose `&C3` and `&DA`. 1942 uses `&C400-&D9FF`. **Not covered:** real hardware; MOS 3.5 (pop-beeb 1.2 moved off `&DA` for "DFS versions in MOS 3.5+"); MMFS (pop-beeb guards `&DAC0`); ADFS. This refines the Edge entry above, which took all 8K including DFS's own pages.
- **After `OSBYTE 140` HAZEL is all yours but two ranges the call itself touches**: `&C000-&C2FF` hold nothing anyone reads (1942 puts its own disc loader and catalogue cache there), and **`*FX 140` itself writes `&DA00-&DAE0`** (222 bytes, the same page a soft BREAK writes), so anything unpacked into `&DA` goes in after the call. **HAZEL can then stay paged for the whole of play** (Y in the base of every ACCCON write): 1942 across 42 OSFILE loads and a whole-game run, jsbeeb 2026-09-17/24, **played on a real Master** from a Gotek 2026-09-28 and a real drive 2026-10-12 (1942 decisions 96, 116). phX does the same.
- **A game that reads "spare" ROM space may be reading HAZEL.** The Master MOS leaves Y set through a game that never touches ACCCON, so `&C000-&DFFF` is HAZEL, not the MOS ROM. Stryker's Run's mountain layer reads data from `&C300` (meant as MOS ROM); on a Master it is whatever the DFS left there, so the mountains depend on the last disc activity — **jsbeeb boots with HAZEL zeroed**, and after a release disc's menu different bytes picked an untested sprite. Fill HAZEL alike in both machines of an A/B check (Stryker's Run BUGS #9, jsbeeb 2026-10-17 to 10-25, `tools/hazelwatch.mjs`: 1,242 reads of `&C301-&C56C`).
- **BREAK and HAZEL**: `*FX 200,2` is not enough with VIA interrupts enabled; the reliable form is the BREAK intercept. See [[os/break-intercept]].

### Low RAM reclaimed on the Master

- **`&0C00` (the MOS user-font page) and `&0800-&0BFF` (sound, serial, soft keys) are yours once the MOS interrupt is gone; `&0400-&07BF` (language workspace) once `*RUN` has handed over.** Both verified by sentinel (Layer 2 onward, September 2026). The Master keeps its real font and soft keys in the second 32K ([[memory/os-workspace]]), which is why these pages are free here.

A real Master 128 runs the Paradroid port (shadow RAM, a different `PAGE`, the 65C12 it does not use) — reported by KC 2026-09-06, the first time either port ran on hardware rather than an emulator.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
