---
title: Emulators — jsbeeb (MCP), b-em, b2
type: tool
tags: [emulator, jsbeeb, b-em, b2, mcp, debugging, measurement]
sources: [beeb-port-kit-hardware-facts, twisted-brain, stardot-sn76489-sampled, via-timer-chip-level-refs]
updated: 2026-09-06
---

# Emulators — jsbeeb (MCP), b-em, b2

What the emulators do that real hardware does not, and what each can see that the others cannot. Everything on this page was **measured while building two C64-to-BBC ports** by Kieran Connell — [Paradroid](https://github.com/kieranhj/paradroid-beeb) (Model B) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (Master 128) — using jsbeeb through an MCP (a tool interface that boots a disc, sets breakpoints, reads memory and registers, counts cycles, screenshots, and captures SN76489 writes). Source: [[sources/beeb-port-kit-hardware-facts]] §11. For which emulators are cycle-accurate enough for single-scanline work, see [[techniques/single-rasterline-rupture]] and [[sources/twisted-brain]].

The rule the ports worked to: **measure, do not recall** — set the registers, look at the screen, read memory back, confirm, then build on it. The emulator is the instrument; this page is its calibration sheet.

## jsbeeb (via the MCP)

### Machine state

- **RAM powers up zeroed.** Uninitialised state that is 0 on every emulated boot is garbage on real hardware and survives BREAK. It hid a white briefing and a white title in Paradroid three times in two days. Test: seed the byte before a SHIFT+BREAK autoboot, or run something that writes over the area first. (Paradroid, 2026-08-28 and 2026-08-30, [`docs/intro.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/intro.md).)
- **`read_memory` returns whatever bank is paged at that instant.** A sample taken inside a sprite draw returned bank 5's empty space, which read exactly like the player having been wiped. Check ROMSEL's shadow at `&F4` first. Reading the Master's shadow RAM from the CPU side likewise follows ACCCON's X bit. (Paradroid Layer 7 combat; Edge 2026-09-04, [`docs/layer-6e-titles.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-6e-titles.md).)
- **The `B-DFS1.2` model has eight sideways RAM banks; a Master model has 4-7.** A program that assumes 4-7 is right by coincidence on both. (Paradroid, 2026-08-29, [`docs/layer-13-compatibility.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-13-compatibility.md).) See [[memory/paged-rom]] for the probe.

### Cycle counting and breakpoints

- **`cycles_run` is NOT the actual count when a breakpoint fires** — it returns the number requested. Use `elapsed_cycles` from `read_registers`; that one is exact. (Paradroid, 2026-08-20, [`docs/raster-timing.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/raster-timing.md).)
- **A run that starts with the PC already on a breakpoint returns immediately with `cycles_run` 0** (the next call moves on). Read, clear the breakpoint that just fired, run. Breakpoints DO fire under `run_for_cycles`; an older note saying otherwise was wrong. (Paradroid 2026-08-20; Edge 2026-09-02, [`docs/layer-2-display.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-2-display.md).)
- **A `run_for_cycles` snapshot can stop the CPU mid-routine.** A buffer dump caught a half-written strip and reported 16 differing bytes that were not a bug; an oracle redraw of >500,000 cycles was sampled before it finished. Idle a few frames after releasing a key; take both halves of a diff inside one pass with breakpoints. (Paradroid Layer 3 and 2026-08-20.)
- **`frame_count` counts the CRTC's own frames, not 50 Hz ones** — it climbs 14 in 258k cycles when the CRTC is left free-running in a short rupture shape. (Paradroid, 2026-08-31.)
- **Timing method that worked:** a breakpoint pair differencing `elapsed_cycles` for a routine's cost; `run_frames(1)` stepping with `elapsed_cycles` per field to find malformed fields (see [[timing/field-timing]]); the phase of a `STA &FE01` against a `run_frames` anchor, differenced mod 128, to place a CRTC write inside a scanline.

### Display

- **Screenshots crop to the active display's content bounding box.** Builds are not to the same scale, absolute row positions move when the display start moves, and one scanline is about 2 framebuffer pixels. Judge geometry by poked patterns, and **verify against the buffer, not the screenshot**: redraw what should be there from the model and diff it byte for byte. (Paradroid Layer 3; Edge 2026-09-02.)
- The scanline component of a timing question cannot be read from screenshots better than ±2 lines; it was KC spotting two wrong lines on b-em that pinned Paradroid's VSync latency (see [[hardware/system-via]]).
- **jsbeeb emulates the VideoNuLA palette** — `?&FE23=&78 : ?&FE23=&88` gives mid grey, and sixteen distinct 12-bit entries come back under logical colour mapping (`&FE22 = &11`). **Its NuLA scrolling and attribute modes are NOT emulated.** The belief that a NuLA build could not be tested in jsbeeb is what let a palette-mapping mistake reach real hardware. (Edge, 2026-09-05, [`docs/layer-8b-nula.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-8b-nula.md).) See [[hardware/video-ula]].
- **A Master's display below `&3000` with ACCCON D set**: jsbeeb displays it; b-em shows garbage on alternate frames; real hardware untested. Nothing displayed should live there. (Edge, 2026-09-02, decision 17.) See [[memory/shadow-ram]].
- **The Master mid-frame bank switch** (ACCCON D flipped inside a frame, taking effect at the next character fetch) is a jsbeeb result only; **b-em has not been checked**. See [[memory/shadow-ram]].

### Disc

- **jsbeeb WILL boot an unpadded SSD.** An earlier note in Paradroid claimed it would not and blamed a hang in the DFS FDC poll at `&ACAE` on beebasm's image ending mid-track; KC corrected it on 2026-09-01. Padding to 200K (204,800 bytes) is convention and robustness — and a published size that differs from the last publish is a useful signal that the wrong file went out. ([`CLAUDE.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/CLAUDE.md), [`docs/layer-4-player.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-4-player.md).)
- **jsbeeb needs VSync for the 8271 poll.** With CRTC R7 parked so VSync never fires, `*LOAD` hangs at `&ACAE`. It reproduces from BASIC, so it is not the game. (Paradroid Layer 3, [`docs/bug-map-corruption.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/bug-map-corruption.md).) See [[os/filing-systems]].
- **DFS throughput under jsbeeb's disc model** is ~0.07 s/sector plus ~0.7 s spin-up once per idle path; flagged as the emulator's model, not measured on hardware. See [[os/filing-systems]].
- **OSFILE loading 21K on the emulated 1770 DFS takes ~130 fields**, with the PC in the DFS NMI routine at `&0D50` for most of it. That is not a crash. (Edge, 2026-09-02.)

### Sound

- **`read_sound_state` and the SN76489 write capture are the instrument for sound**: CH0 tone 284 = 440.1 Hz confirmed the 4 MHz chip clock and `N = 125000 / f`; a 246-cycle window between a volume write and a silence write showed up as a 50 Hz crackle in the capture before it was heard (and was then heard on b2 by KC). (Paradroid 2026-08-21, [`docs/layer-11e-sound.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-11e-sound.md); Edge 2026-09-04, [`docs/layer-7-music.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-7-music.md).) See [[hardware/sn76489]].

### The MCP itself

- The MCP timed out on its first connection in one session and was fine after a `/mcp` reconnect. ([`docs/layer-0-toolchain.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-0-toolchain.md).)
- **A test that pages ANDY in must be machine code**: BASIC is itself the ROM at `&8000`, so paging ANDY from a BASIC session removes the interpreter mid-statement and hangs. Poke a routine into main RAM and `CALL` it. (Edge, 2026-09-04.) See [[memory/paged-rom]].
- Measuring keys from a BASIC session: `*FX 4,1` first or the cursor keys edit, `*FX 229,1` or BASIC eats ESCAPE. See [[os/keyboard]].

## b-em

- **Shows garbage on alternate frames for a displayed area below `&3000` with the shadow D bit set**, where jsbeeb displays it. Real hardware untested. (Edge, 2026-09-02, b-em run by KC.)
- **Caught a two-scanline top-edge error that jsbeeb screenshots could not resolve.** (Paradroid Layer 3, b-em, KC.)
- **Has not seen the Master mid-frame bank switch or Edge Grinder's four-cycle title rupture.** Decision 17 (below-`&3000`) is why that matters: the two emulators are known to disagree on Master video fetch edge cases.
- Launched as a Master with `-m3` (Edge's `build.ps1 -Run`).
- Historically the accuracy leader; [[sources/twisted-brain]] and [[techniques/single-rasterline-rupture]] record that it has not kept up with jsbeeb / b2 / beebjit on the latest cycle-stretching findings as of 2026.

## b2

- **Shows a misplaced (right-length, wrong-phase) field that jsbeeb does not.** With the CRTC free-running in a 13-row tail shape whose VSync is at row 5, the first VSync after an aligned switch came at line 104 instead of 312 — one short field and one roll on the TV. **jsbeeb showed no fault; b2 rolled and KC photographed it.** b2 is the instrument for TV-resync questions. (Paradroid, 2026-08-31, [`docs/raster-timing.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/raster-timing.md).) See [[techniques/vertical-rupture]].
- **Only b2's debug build carries an HTTP API** (`peek` for buffer diffs, paste, loading a disc), documented in [`doc/Debug-version.md`](https://github.com/tom-seddon/b2/blob/master/doc/Debug-version.md) in the b2 tree. Paradroid's NuLA plan notes that reading the endpoints out of the binary got the port wrong and missed half of them: **read the document first.** ([`docs/nula-plan.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/nula-plan.md).)
- Heard the 50 Hz sound crackle that the jsbeeb capture had already shown (Edge, 2026-09-04).

## Which instrument for which question

| Question | Use | Why |
|---|---|---|
| Cycle cost of a routine | jsbeeb breakpoints + `elapsed_cycles` | exact; `cycles_run` is not |
| Is a field the right length? | jsbeeb `run_frames(1)` + `elapsed_cycles` | 39,936 or it is malformed |
| Is a right-length field in the right *phase*? | **b2** | jsbeeb does not roll; b2 does |
| Where does the top edge really sit? | b-em, by eye (KC), then jsbeeb | screenshots are ±2 lines |
| Did the code draw what it should? | jsbeeb `read_memory` diff against an oracle | not the screenshot |
| What is the sound chip doing? | jsbeeb `read_sound_state` / write capture | shows glitches before you hear them |
| Master video below `&3000`, in-frame bank switch | jsbeeb and b-em **disagree**; hardware needed | decision 17 |
| Anything NuLA scrolling/attribute | real hardware only | not emulated |

## See also

- [[tools/beebasm]] — the assembler these ports were built with, and its traps.
- [[timing/field-timing]] — the cycle constants the measurements are expressed in.
- [[techniques/single-rasterline-rupture]] — emulator accuracy for single-scanline work.
- [[sources/beeb-port-kit-hardware-facts]] — the source, with every date and write-up.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
