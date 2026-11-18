---
title: Emulators — jsbeeb (MCP), b2, beebjit, b-em
type: tool
tags: [emulator, jsbeeb, b-em, b2, beebjit, mcp, debugging, measurement, real-hardware]
sources: [beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11, twisted-brain, stardot-sn76489-sampled, via-timer-chip-level-refs]
updated: 2026-11-18
---

# Emulators — jsbeeb (MCP), b2, beebjit, b-em

What the emulators do that real hardware does not, and what each can see that the others cannot. Everything on this page was **measured while building BBC ports** by Kieran Connell (KC) with Claude Code sessions: [Paradroid](https://github.com/kieranhj/paradroid-beeb) (C64 → Model B) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (C64 → Master 128), August-September 2026 ([[sources/beeb-port-kit-hardware-facts]] §11); then **1942** (arcade → Master 128, Sept-Oct 2026), **[Stryker's Run](https://github.com/kieranhj/strykers-run)** (a 1986 BBC game rebuilt, Master 128 and Model B + SWR, Oct 2026), the CPC demos **Isometrikum** and **Square Roots** (Model B + 32K SWR and Master, Nov 2026, emulator-only so far) and **phX** (CPC demo → Master 128, Nov 2026, run on **KC's two real Master 128s**) ([[sources/beeb-port-kit-hardware-facts-2026-11]] §11, gotchas classes 5-6). The primary instrument is jsbeeb through an MCP (a tool interface that boots a disc, sets breakpoints, reads memory and registers, counts cycles, screenshots, and captures SN76489 writes). For which emulators are cycle-accurate enough for single-scanline work, see [[techniques/single-rasterline-rupture]] and [[sources/twisted-brain]].

The rule the ports worked to: **measure, do not recall** — set the registers, look at the screen, read memory back, confirm, then build on it. The emulator is the instrument; this page is its calibration sheet. **And put real hardware in the loop at the first layer that touches the disc, the CRTC or BREAK**: everything 1942 and phX found on real Masters that jsbeeb did not is listed under "jsbeeb versus a real Master" below.

## jsbeeb versions — which one a fact is true of

**The kit's jsbeeb facts are on the pinned jsbeeb 2.10.x (the MCP's pin, 2.10.2) unless an entry says otherwise, and jsbeeb main 2.22.x differs on a real Master's behalf.** In November 2026 the jsbeeb maintainer, from his own Master and phX's hardware-test reports, changed three things on main (2.22.1, commit `c97b2c75`) ([[sources/beeb-port-kit-hardware-facts-2026-11]] §11; `phX/BUGS.md` header, `phX/CLAUDE.md` "Two jsbeeb"):

| Change on main 2.22.x | Issue | Pin (2.10.x) behaviour, now known wrong for a real Master |
|---|---|---|
| **The MA13 alternate-character flip** in a 2 MHz mode | #1859 (main 2.22.0) | MA13 fetches one byte per character; phX's Bobs, re-laid for the flip, read 640 of 640 on main and 0 of 640 on the pin |
| **Palette, `&FE20` and R8 writes landing a character early** | #1868 (2.22.1) | palette/ULA/R8 writes take effect at the character written, offset 0 |
| **The 1770's timings** | #1860 | READ ADDRESS's INTRQ ~96 µs after the sixth byte (a real 1770: almost at once) |

The 6845's counters, the one-slot RVI writes and the field length agree between 2.10.2 and main 2.21.1 for everything phX does. phX runs its suite on both (the pin, and main through `JSBEEB_SRC` pointed at a checkout's `src`) and answers a real-Master question on main; expected pictures can differ per version (its sine scrollers and Multi-FX carry one set for each). **Date every figure with the jsbeeb it ran on**: between 2.5.0 and 2.10.x Stryker's Run's front-end harness's key presses, timed by frame, landed on another page — wait on game state, not frames (Stryker's Run decision 72).

Earlier version changes that moved measurements: **jsbeeb 1.9.0** stopped refusing unpadded SSDs; **jsbeeb 1.25.0** fixed `run_for_cycles` overrunning after a breakpoint (#1092); **jsbeeb 2.0** changed `keyDown`'s argument type (below); **2.3.1** made a bad key throw; **up to 2.3.x** the 1770 settled only after a spin-up (PR #1226 modelled the per-command E settle); **2.10** models the HD6845SP and the Master's D-bit fetch below `&3000`.

## jsbeeb (via the MCP)

### Machine state

- **RAM powers up zeroed — and so does the Master's HAZEL.** A real machine's RAM powers up with junk, and **the junk survives BREAK**. Uninitialised state that is 0 on every emulated boot hid a white briefing and a white title in Paradroid three times in two days (2026-08-28/30, [`docs/intro.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/intro.md)). phX's fix disc behaved differently on each of KC's real runs (three after a BREAK, one from cold), so its harnesses take `JUNK=seed` (every RAM junk, a soft BREAK, then the boot) and "nothing may read RAM it did not write" is a rule; the cold run's own causes are not established (`phX/docs/hwtest.md` "B7"). Stryker's Run's mountains are picked by bytes the DFS leaves in HAZEL: booted straight into the game on jsbeeb one sprite ever appeared; after a menu touched the disc, an untested one did, and users saw it first (BUGS #9). **Seed RAM non-zero — HAZEL too on a Master — and fill it alike in both machines of an A/B check.**
- **`read_memory` returns whatever bank is paged at that instant** — a sample inside a sprite draw returned bank 5's empty space, which read like the player wiped (Paradroid Layer 7; Edge 2026-09-04). **From jsbeeb-mcp 3.4.0** (#35) `read_memory` and `save_memory` report the paging they read under (`romsel`, and `acccon` on a Master) and take `bank` or `shadow` to read a particular one; prefer that to reading `&F4` and hoping.
- **The `B-DFS1.2` model has eight sideways RAM banks; a Master model has 4-7.** A program that assumes 4-7 is right by coincidence on both (Paradroid, 2026-08-29). The eight banks let a harness put a game in any four (Stryker's Run's `SWR_POKE`), which provoked a bank-select bug and a bank-as-data bug (BUGS #16, #17). See [[memory/paged-rom]].
- **`B-DFS1.2` is a free NMOS checker**: its 6502 core trips on any 65C02/65C12 opcode left in a Model B build (Stryker's Run, 2026-10-24/25, jsbeeb 2.10.2).
- **ROMSEL reads back on the Master but not the Model B**: `&FE30` read `&FE` on `B-DFS1.2` and the paged bank on Master. Read `&F4` (kit, 2026-09-11).
- **`save_state` / `restore_state` rewind memory, registers and the cycle count exactly — but not the keyboard.** A key held with `key_down` stays held across a restore; `key_up` it, or from jsbeeb-mcp 3.4.0 `release_all_keys`; `keyboard_state` lists every key the machine sees held. A state restores into any session of the same model, even one that never loaded the disc: one boot can seed many machines (kit, 2026-09-07).
- **jsbeeb's Master CMOS is `FDRIVE 0`** (byte 11 reads `&25`), so only real hardware exercises a driver's other step rates (kit §6).

### Cycle counting and breakpoints

- **`run_for_cycles` reports what it actually ran and runs on from a breakpoint — from jsbeeb-mcp 3.4.0.** On 3.3.0 and earlier `cycles_run` was the count *requested* (a request for 600,000 that a breakpoint stopped after 598 reported 600,000), and a run starting on a breakpoint returned 0 having advanced nothing (jsbeeb-mcp #25, #26, fixed in #30, released in 3.4.0 2026-09-07). On 3.4.0 a breakpoint stop sets `completed` false, `stopped_reason` `breakpoint`, and carries `elapsed_cycles`; a request for 600,000 returned `cycles_run` 38,948 and `elapsed_cycles` moved exactly 38,948. *(This page said "cycles_run is NOT the actual count" until 2026-11-18; that was true of ≤ 3.3.0.)*
- **`run_for_cycles` used to overrun after a breakpoint stop** (a 3,993,600-cycle request ran 4,553,339) — a jsbeeb bug (#1092), fixed in jsbeeb 1.25.0 / jsbeeb-mcp 3.4.0. Count fields from `elapsed_cycles`, never from the number requested, anyway.
- **Do not step frames with `run_for_cycles`**: a frame is 40,000 cycles with interlace on (the MCP default) but 39,936 with it off. Use `run_frames`.
- **A `run_for_cycles` snapshot can stop the CPU mid-routine** — a half-written strip showed 16 "differing" bytes; take both halves of a diff inside one pass with breakpoints (Paradroid Layer 3).
- **An address hook in sideways RAM must check ROMSEL**: with code in two banks at `&8000`, a hook fires in both, and on the Master before boot it fires in a ROM (Isometrikum; Stryker's Run's harnesses got 30 false failures from bank 6's code at bank 7's address). Gate every hook on ROMSEL and on the boot having happened (kit gotchas class 5).
- **A memory watch sees a zero-page read's address but not its value**, so a liveness count by watch counts by address; check the source for indexed accesses (Stryker's Run BUGS #12, jsbeeb 2.5.0).
- **`frame_count` (`Video.frameCount`) counts C4 = R6 matches and nothing else** — not VSync, not the frame's end (`video.js`). It climbs 14 in 258k cycles when the CRTC free-runs a short shape (Paradroid, 2026-08-31); a field whose display is cut by R8 and never reaches R6 does not count, and a frame that meets R6 twice counts two. **The web front end decays its PAL phosphor by that count** (`web/display.js`, since 2.1.0, blending with "lighten"), so on bbc.xania.org a demo whose frames never reach R6 turns white as every pixel keeps its brightest colour — while every headless harness passes, because `MachineSession` has no display. A real 6845 needs no R6 match. phX's rule: every part meets C4 = R6 exactly once a field inside lines R8 already blanks, and its frame checks fail unless the count steps one a field (jsbeeb 2.10.2 and main 2.21.1, 2026-11-14; `phX/docs/layer-3-6845.md`).
- **`video.bitmapY` (the raster row) steps at HSync, not at C0 = 0** (R2 = 100, width 8: about C0 104), so a harness grouping fetched bytes by raster row puts C0 104-127 with the NEXT line's display (phX, 2026-11-14).
- **Sample a harness at the port's own tick, not the emulator's frame**: Square Roots' 304-line field drifts against jsbeeb's 312-line frames and its music check differed every 39th tick until it hooked the tick (gotchas class 5).
- **Timing method that worked:** a breakpoint pair differencing `elapsed_cycles` for a routine's cost; `run_frames(1)` stepping with `elapsed_cycles` per field to find malformed fields (see [[timing/field-timing]]); the phase of a `STA &FE01` against a `run_frames` anchor, differenced mod 128, to place a CRTC write inside a scanline; and (phX) a probe that records every byte the video fetches with the CRTC's counters and every CRTC and `&FE21` write with its C0.

### Keyboard (harness side)

- **jsbeeb 2.0 changed `MachineSession.keyDown`'s argument** from a numeric browser `keyCode` (16 = SHIFT) to a `KeyboardEvent.code` string (`"ShiftLeft"`). On 2.0-2.3.0 the old number **silently pressed nothing**: SHIFT+BREAK stopped booting the disc, and every counter read its power-on value, which reads exactly like a dead game (`via.js`'s `set()` ends `if (!mapping) return;`, jsbeeb #1172). **2.3.1 throws** on a numeric code or an unknown name. **An all-zero harness result is a boot that did not happen** — check `&1900` (or your load address) before believing it (kit, 2026-09-23; `tools/jsbeeb_src.mjs` `keys()`).
- **jsbeeb-mcp 4.0.0 renamed the key names** (`K0`-`K9`, `CAPSLOCK`, no `BACKSPACE`/`QUOTE`/`EQUALS`); an unknown name is refused with the full list. Only the names moved: `X` still gives col 2, row 4, internal 66, INKEY -67 (cross-checks [[os/keyboard]]).
- **When every oracle fails at once, suspect the tools** — the `keyDown` change and an assembler listing-format change both read like a corrupt build (1942 BUGS #26).

### Display

- **Screenshots crop to the active display's content bounding box.** Judge geometry by poked patterns and **verify against the buffer, not the screenshot** (Paradroid Layer 3; Edge 2026-09-02). **Where the picture is in jsbeeb's framebuffer:** x = (R0 + 1 − R2 − (R3 AND 15)/2) × a character's width − 8, y = (lines − R7 × (R9 + 1)) × 2, a character 8 pixels wide at 2 MHz and 16 at 1 MHz, a scanline two rows. Every MOS mode 0-2 and 4-5 puts it at (200, 64), 640 × 512, on B and Master; not valid under a rupture (kit, 2026-10-25, jsbeeb 2.10.2, `template/tools/capture.mjs`).
- **Measure what the video reads, not when it was written**: Stryker's Run's HUD rupture writes were all correctly timed, but with ACCCON D set the video read ANDY below `&3000`, and the screenshots happened to be main-screen fields (BUGS #15).
- **jsbeeb emulates the VideoNuLA palette** (`?&FE23=&78 : ?&FE23=&88` gives mid grey; 16 distinct entries under `&FE22 = &11`). **Its NuLA scrolling and attribute modes are NOT emulated** (Edge, 2026-09-05). NuLA detection by timing works in it (a stock ULA decodes only A0, so `&44` to `&FE22` halves a MODE 7 field-count rate: stock 9,452 → 18,909 loops, `video_nula` 9,453 → 9,452 — Isometrikum, 2026-11-08; no real NuLA has seen that build). See [[hardware/video-ula]].
- **jsbeeb's `is1MHzAccess` makes `&FE20-&FE3F` a 2 MHz access, on the Master too** (read 2026-10-06, 1.25.0 and 2.3.1) — and KC's real Masters agree for `&FE21` and `&FE34` (phX, 2026-11-14). See [[timing/cycle-stretching]].
- **jsbeeb 2.10's 6845 (its HD6845SP model) starts VSync the instant C4 = R7**, so R7 = 0 may be written only once the last CRTC cycle is past its row 0 (Isometrikum's one-row case lands the write at 310:39 — the riskiest item there for real hardware, not yet tried). jsbeeb latches "last line" at C0 = 1, where a real Master's last-line latch holds at C0 54 (phX card 8). See [[hardware/crtc-6845]].
- **ACCCON bits 5-7 are ignored by jsbeeb**, so a stray value there passes every emulator check; what a real Master does with them was not observed. Watch every ACCCON write (phX `tools/acccon_watch.mjs`). See [[memory/shadow-ram]].
- **The Master's display below `&3000` with ACCCON D set**: jsbeeb 2.10's `videoRead` ORs `&8000` into the address (ANDY/HAZEL) — and **a real Master reads HAZEL there** (phX card I, 2026-11-15). jsbeeb 1.x had displayed main RAM there (Edge, 2026-09-02). See [[memory/shadow-ram]].

### Disc

- **jsbeeb boots an unpadded SSD** — since jsbeeb 1.9.0, guaranteed from jsbeeb-mcp 3.0.0 (jsbeeb's author, 2026-09-07); a 2,304-byte image boots as happily as a 204,800-byte one on `B-DFS1.2` and `Master`. An earlier note blamed a `&ACAE` hang on an image ending mid-track; KC corrected it 2026-09-01. **Padding to 200K is a publishing convention only** — a published size that differs from the last is a signal the wrong file went out (gotchas class 6: a workaround promoted to a rule that outlived its bug).
- **"jsbeeb needs VSync for the 8271 poll" — no longer reproducible.** Paradroid's `*LOAD` hung at `&ACAE` with R7 parked so VSync never fired (Layer 3, [`docs/bug-map-corruption.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/bug-map-corruption.md)); on jsbeeb-mcp 3.4.0 / jsbeeb 1.25.0, with VSync confirmed dead (IFR bit 1 never set), an 8 KB `*LOAD` ran to completion (2026-09-09). That was R7 alone, not Paradroid's rupture shape. See [[os/filing-systems]].
- **jsbeeb steps the head a track at a time and reads ~8.8K a second (~230 cycles a byte)**, so layout matters: re-laying Stryker's Run's files in load order cut 120 head steps to 32 (12.68 s → 12.38 s; 2026-10-24, jsbeeb 2.10.2). Earlier measures of jsbeeb's disc model: ~0.07 s/sector plus ~0.7 s spin-up once per idle path (Paradroid, 2026-08-29), and OSFILE loading 21K on the 1770 DFS taking ~130 fields with the PC in the DFS NMI routine at `&0D50` (Edge, 2026-09-02). A `*RUN` still at `&0D3F` after 50 frames is loading, not hung. **These are jsbeeb's model, not hardware.**
- **The 1770 model's settle and skew**: up to 2.3.x it settled only after a spin-up, so no emulator oracle saw a real 1770's per-command E settle (1942's background reads came late on hardware); **2.10.2 settles 30 ms on every command with E** and skews each track ~3 sectors on the last (phX, measured), so a loader cannot guess where sector 0 is. Main 2.22.1 reworked the timings (#1860); what that does to the settle and skew is not recorded. See [[hardware/wd1770]].
- **On a Master, a null IRQ1V handler across a 1770 DFS `*LOAD` hangs jsbeeb** in the MOS service-call dispatcher (`&EE72-&EE9C`); so do a changed System VIA T1 latch and T1's interrupt disabled. `SEI` across the call and a chaining handler that changes nothing both work (1942, 2026-09-13). The hangs are jsbeeb results, not yet checked on b2 or a real Master. See [[os/interrupts]].

### Sound

- **`read_sound_state` and the SN76489 write capture are the instrument for sound**: CH0 tone 284 = 440.1 Hz confirmed the 4 MHz chip clock and `N = 125000 / f`; a 246-cycle window between a volume write and a silence write showed up as a 50 Hz crackle in the capture before it was heard on b2 (Paradroid 2026-08-21; Edge 2026-09-04). See [[hardware/sn76489]].
- **Decode the captured writes, don't count them**: 1942 shipped three corrupted tunes whose write count was right (BUGS #66, #67).

### The MCP itself

- The MCP timed out on its first connection in one session and was fine after a `/mcp` reconnect ([`docs/layer-0-toolchain.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-0-toolchain.md)).
- **`run_until_prompt` stops at BASIC's `INKEY`**; use `run_frames` for a timed wait (1942's ANDY measurement, kit §4).
- **A test that pages ANDY in must be machine code**: BASIC is itself the ROM at `&8000` (Edge, 2026-09-04). See [[memory/paged-rom]].
- Measuring keys from a BASIC session: `*FX 4,1` first or the cursor keys edit, `*FX 229,1` or BASIC eats ESCAPE. See [[os/keyboard]].
- **Pin the MCP and the harnesses' jsbeeb.** The kit's harnesses once resolved the highest jsbeeb in the npx cache with the MCP unpinned, which is how the 2.0 `keyDown` change arrived unannounced; both are pinned now (`.mcp.json`; since 2026-10-21 the harnesses load the jsbeeb that pin installed).

## jsbeeb versus a real Master 128 — what only hardware showed (2026)

KC's two Masters (the original with a Sony RGB CRT, a Cherry Master with a CUB RGB CRT), through 1942's play-testing and phX's hardware-test discs (`phX/docs/hwtest.md`; real-Master entries are by eye on a CRT, to a pixel or a character, not a cycle). jsbeeb 2.10.2 unless stated ([[sources/beeb-port-kit-hardware-facts-2026-11]] §1, §2, §4, §6):

| Behaviour | Real Master | jsbeeb pin 2.10.2 | jsbeeb main 2.22.1 |
|---|---|---|---|
| Palette `&FE21` / ULA `&FE20` write mid-line | early: about one MODE 2 pixel (KC's eye) — or a whole MODE 2 character (the maintainer's Master, #1868); **unresolved**, phX card N has no result yet | at the character written | `4 - p` texels into the character before |
| CRTC R8 = 0 (display on) mid-line | a strip of the previous character shows | at the character written | one character early |
| ACCCON D mid-line | at the character written, odd or even C0 | same | same |
| MA13 set in a 2 MHz mode | alternate characters fetch with MA6 (one scanline) or MA6+MA7 (the next) flipped | one byte per character | flip modelled (#1859) |
| 6845 last-line latch for the next frame's R4 | holds at C0 54 | latches at C0 = 1 | (not recorded) |
| 1770 READ ADDRESS INTRQ after 6th byte | almost at once | ~96 µs | 33 µs, as the maintainer's Master measured |
| 1770 E settle | 15-30 ms every command | 30 ms every command | reworked (#1860) |
| RAM / HAZEL at power-on | junk, surviving BREAK | zeroed | zeroed |
| Monitor black-level clamp, visible window | Sony clamps in the back porch just after HSync (a lit porch shifts the whole line's colours); windows narrower than 96 characters | **not modelled** — every displayed character drawn at full colour | not modelled |

**No emulator models a monitor's clamp or its visible window, and jsbeeb shows overscan happily, which proves nothing about a TV** (1942's 272-line field, played on a real Master and display). Details: [[hardware/crtc-6845]], [[hardware/video-ula]], [[video/monitor-crt]].

## b2

- **The second opinion since 2026-09-07, with beebjit** (b-em retired; below).
- **Shows a misplaced (right-length, wrong-phase) field that jsbeeb does not.** With the CRTC free-running in a 13-row tail shape whose VSync is at row 5, the first VSync after an aligned switch came at line 104 instead of 312 — one short field and one roll on the TV; jsbeeb showed no fault, b2 rolled and KC photographed it. b2 is the instrument for TV-resync questions (Paradroid, 2026-08-31, [`docs/raster-timing.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/raster-timing.md)). See [[techniques/vertical-rupture]].
- **Agrees with jsbeeb and the real Master that D set reads HAZEL/ANDY below `&3000`** (Stryker's Run's HUD showed right on b2 after the fix, 2026-10-23); its HUD rupture and Model B beam-raced build were seen on b2 (KC, 2026-10-23/25).
- **Does not model the MA13 alternate-character flip** (kit §1; jsbeeb 2.10.x neither).
- **Only b2's debug build carries an HTTP API** (`peek` for buffer diffs, paste, loading a disc), documented in [`doc/Debug-version.md`](https://github.com/tom-seddon/b2/blob/master/doc/Debug-version.md); read the document, not the binary (Paradroid's NuLA plan).
- Heard the 50 Hz sound crackle that the jsbeeb capture had already shown (Edge, 2026-09-04).
- Neither jsbeeb nor b2 emulates the Integra-B (BeebEm does) (Stryker's Run, 2026-10-24).

## beebjit

- **Models the MA13 flip's MA6 half only** (the refresh fetch BeebWiki's *Address translation* describes); the MA7 half on the next scanline is not modelled (phX card J, kit §1). Shows a `&FE20` mode change a little left of the tick, as KC saw on a real Master (phX card B).
- Boot: `beebjit -0 game.ssd` (`-c CONFIG` for a saved machine configuration), from its help text (kit, 2026-09-07).

## b-em (retired 2026-09-07)

**b-em is no longer used (KC, 2026-09-07); the second opinion is b2 or beebjit.** Its observations are kept as history:

- **Shows garbage on alternate frames for a displayed area below `&3000` with the shadow D bit set.** jsbeeb 1.x displayed main RAM there; **a real Master reads HAZEL** (phX card I, 2026-11-15) — **b-em was the odd one out** (Edge, 2026-09-02, b-em run by KC). *(This page said "real hardware untested" until 2026-11-18.)*
- **Caught a two-scanline top-edge error that jsbeeb screenshots could not resolve** (Paradroid Layer 3, by KC's eye).
- **Never saw the Master mid-frame bank switch or Edge Grinder's four-cycle title rupture.** The switch is now measured on real Masters (1942's panel; phX card A).
- Launched as a Master with `-m3` (Edge's `build.ps1 -Run`).
- Historically the accuracy leader; [[sources/twisted-brain]] and [[techniques/single-rasterline-rupture]] record that it has not kept up with jsbeeb / b2 / beebjit on the latest cycle-stretching findings.

## Which instrument for which question

| Question | Use | Why |
|---|---|---|
| Cycle cost of a routine | jsbeeb breakpoints + `elapsed_cycles` (or `cycles_run` from MCP 3.4.0) | exact |
| Is a field the right length? | jsbeeb `run_frames(1)` + `elapsed_cycles` | 39,936 or it is malformed |
| Is a right-length field in the right *phase*? | **b2** | jsbeeb does not roll; b2 does |
| Does every field reach R6 (web display, `frame_count`)? | jsbeeb `frame_count` stepping one a field | the web phosphor decays by it |
| Did the code draw what it should? | jsbeeb `read_memory` diff against an oracle | not the screenshot |
| What did the video actually read? | a per-fetch probe (phX `probe_6845.mjs`) | write timing can be right while the fetch is wrong |
| What is the sound chip doing? | jsbeeb `read_sound_state` / write capture | shows glitches before you hear them; decode, don't count |
| Master video below `&3000` with D set | jsbeeb 2.10+ or b2 | both match the real Master; b-em does not |
| Palette / R8 mid-line edge, MA13 flip | **real Master**, then jsbeeb main 2.22.x | the pin is wrong; the two real measurements of the palette edge do not yet agree |
| 1770 end-of-command timing, head settle, step rate | **real Master** (and jsbeeb main for INTRQ timing) | the pin's INTRQ is ~96 µs late; CMOS FDRIVE is 0 |
| BREAK behaviour, power-on RAM | **real Master**; jsbeeb with `JUNK=seed` | jsbeeb zeroes RAM and HAZEL |
| Monitor clamp, visible window, overscan | **real CRT** | no emulator models a monitor |
| Anything NuLA scrolling/attribute | real hardware only | not emulated |

## See also

- [[tools/beebasm]] — the assembler the first two ports were built with, and its traps.
- [[timing/field-timing]] — the cycle constants the measurements are expressed in.
- [[techniques/single-rasterline-rupture]] — emulator accuracy for single-scanline work.
- [[sources/beeb-port-kit-hardware-facts]], [[sources/beeb-port-kit-hardware-facts-2026-11]] — the sources, with every date and write-up.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
