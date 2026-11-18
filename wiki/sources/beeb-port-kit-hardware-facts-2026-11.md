---
title: BBC Micro hardware facts, measured — beeb-port-kit (November 2026)
type: source
author: Kieran Connell (KC)
date: 2026-11-18
urls:
  - https://github.com/kieranhj/beeb-port-kit
local: beeb-port-kit docs/hardware-facts.md and docs/gotchas.md at kit commit 4490a91 (not copied into raw/)
supersedes-in-part: beeb-port-kit-hardware-facts
ports:
  - Paradroid (C64 → BBC Model B)
  - Edge Grinder (C64 → BBC Master 128)
  - 1942 (arcade → BBC Master 128, unpublished)
  - Stryker's Run (BBC game rebuilt from disassembly, Master 128 and Model B)
  - Isometrikum and Square Roots (Amstrad CPC 4K demos → Model B + SWR and Master, unpublished)
  - phX (Amstrad CPC 6128 demo → Master 128, unpublished)
tags: [measured, crtc, rvi, ma13, video-ula, palette, monitor, acccon, shadow-ram, andy, hazel, wd1770, nmi, break, mos-workspace, sn76489, via-timers, jsbeeb, b2, beebjit, b-em]
updated: 2026-11-18
---

# Source: BBC Micro hardware facts, measured (beeb-port-kit, November 2026)

## Bibliographic

- **Documents:** `docs/hardware-facts.md` (1,904 lines) and `docs/gotchas.md` (1,199 lines) from Kieran Connell's *beeb-port-kit* (MIT licence), at kit commit `4490a91` (2026-11-18). This is the second ingest of the kit's facts: [[sources/beeb-port-kit-hardware-facts]] covers the 2026-09-06 version (kit `ebbfe0d`, 750 lines, Paradroid and Edge Grinder); this page covers everything added since (`git diff ebbfe0d 4490a91`).
- **Not copied into `raw/`.** The wiki reads the kit file at that commit; if KC wants a frozen local copy, it belongs in `raw/notes/` by hand.
- **Instruments:** jsbeeb through an MCP (pinned 2.10.2 for most of the period; earlier entries 2.5.0), **jsbeeb main 2.21.1 / 2.22.x** (the jsbeeb maintainer's real-Master fixes: MA13 flip #1859, the 1770's end-of-command timings #1860, palette and R8 timing #1868), beebjit, b2, and **KC's two real Master 128s**: the original with a Sony RGB CRT and a Cherry Master with a CUB RGB CRT, driven by phX's hardware-test disc and judged by eye (to about a character / a pixel).

## Summary

Four new projects' measurements on top of Paradroid and Edge Grinder. **1942** (Master; the first port built with the kit) adds the 1770 driven directly, the BREAK that clears RAM under MOS 3.20, the MOS's low-RAM use, 272-line overscan and real-Master shadow switching. **Stryker's Run** adds the frame-end latch at C0 = 1, ACCCON D = 1 below `&3000` reading ANDY in jsbeeb, the MOS costs a game pays, and keyboard/MOS corners. **Isometrikum and Square Roots** add T1 raster fires for a CPC demo, the NOP slide, 304-line frames, software bass, and VideoNuLA for a CPC palette (emulator only). **phX** is the big one for the Master's video: a cycle-exact raster demo that drove the 6845 at its knife edges on two real Masters through a hardware-test disc, settling questions the wiki had left open (the palette is a 2 MHz access; mid-frame shadow switching is clean at the character; shadow below `&3000` reads HAZEL) and overturning others (MA13 addressing on the Master, the 1770's READ ADDRESS completion, `&028C` on the Master). The gotchas file adds traps found by those ports; mostly process, filed here only where they are hardware.

## Key technical claims (by kit section)

- **§1 6845:** CRTC writes land on 1 MHz boundaries (even C0), 6 cycles back to back (jsbeeb); R8 display-on early on a real Master; entering one-line frames only in the last line after C0 = 1; last-line latch at C0 = 1 (jsbeeb) and a write at C0 54 safe on real Masters; a frame may not end on a 2-character line (Sony loses sync, CUB bends); RVI's one-slot R0 writes and displayed burnt lines; MA13 in a 2 MHz mode on the Master: alternate characters `XOR &40` / `XOR &C0` by scanline, the phase following the 1 MHz clock; the monitors' visible windows and the Sony's back-porch black clamp; 272-line overscan (1942).
- **§2 Video ULA:** `&FE21` is a 2 MHz access, 4 cycles, measured on real Masters; palette and `&FE20` writes land **early** on a real Master — KC's eye ~1 MODE 2 pixel, jsbeeb 2.22.1's #1868 model `4 - p` texels into the previous character (**unresolved**); MODE 1 palette index from bits 7, 5, 3, 1 with 1s shifted in; VideoNuLA for a CPC palette (emulator only).
- **§3 System VIA:** T1 latch chaining (no drift), the NOP slide, chained IRQs losing VSyncs.
- **§4 Master:** ACCCON D acts at the character written on real Masters; D = 1 below `&3000` reads HAZEL (real Master; ANDY below `&1000` in jsbeeb/b2); bits 5-7 never set (jsbeeb ignores them; real effect not observed); `tsb`/`trb` versus composing every write; X redirects CPU reads of `&3000-&7FFF`; ANDY's MOS use measured; HAZEL after OSBYTE 140; `&028C` reads `&FF` at a `*RUN` boot on the Master.
- **§5 Model B SWR:** probing results; banks 4-7 are RAM on a stock Master (cited from phX).
- **§6 MOS and DFS:** reclaimable workspace revised; MOS 3.20 BREAK clears RAM only if IER = 0 or `&0258` = 2/3; the BREAK intercept at `&0287` (overwritten by a program's own page-2 code in two projects); low RAM a game owning IRQ1V and the NMI may use; **the 1770 driven directly**: `&FE24` bits, the FDRIVE step rate, 30 ms settle on every E command (1770; 15 on a 1772), **a real 1770 raises READ ADDRESS's INTRQ almost at once after the sixth byte** (FM 33 / 168 / 360 µs after the last DRQ for READ ADDRESS / READ SECTOR / WRITE SECTOR, the jsbeeb maintainer's Master), so an edge-triggered DRQ-OR-INTRQ NMI can be lost; nested NMIs; the loader technique.
- **§8 Timing:** the T1 constants for the CPC demos; phX's whole demo on one cadence; periodic-noise bass at N/15; the SN write at 32 cycles a byte (real WE hold unmeasured).
- **§9-10:** ZX0 / ZX02 / Shrinkler compared; beebasm gotchas.
- **§11 Emulators:** jsbeeb pin vs main; `frameCount` counts only C4 = R6 and drives the web display's phosphor decay; `bitmapY` steps at HSync; RAM zeroed in jsbeeb, junk on real hardware; beebjit models MA13's MA6 only; b-em wrong below `&3000`.
- **§12 Not measured:** hardware-test cards M, N, F, R results; MFM timings; the R8 strip width; which scanline parity takes `XOR &C0`; DRAM refresh under R0 = 0 — **not filed as fact**.

## Contradictions and corrections surfaced

- **Settled:** `&FE21` is 2 MHz (the wiki's position; Edge's "1 MHz" claim retired) — [[hardware/video-ula]], [[timing/cycle-stretching]].
- **Corrected:** C0 "once per µs" (CPC arithmetic) — [[hardware/crtc-internal-counters]]; R0 = 1 "2 µs, no display" — [[techniques/rvi]]; "4c stretched" palette/ACCCON and "8c stretched" CRTC writes — [[techniques/raster-splits]], [[techniques/vertical-rupture]], [[techniques/hexwab-stable-raster]], [[techniques/checkerboard-zoom]], [[techniques/parallax-bars]]; R8 "immediate" — [[hardware/crtc-6845]]; Master MA13 "MA6 or MA7 by RA0" — [[hardware/address-translation]], [[techniques/chunky-mode]]; "MA11=1, MA12=0 teletext flag" — MA13; "no shipped RVI / R0 = 0" — [[techniques/rvi]], [[techniques/crtc-counter-freeze]]; `&FE24` bits 2-4, the E settle, the INTRQ-as-completion rule, sample code comments — [[hardware/wd1770]]; Master "ships with no SWR" and ANDY "dangerous" — [[memory/paged-rom]]; `&028C` on the Master — [[memory/os-workspace]]; `*FX 200` as the BREAK cure — [[os/break-intercept]]; IRQ paging "60-80 cycles" (+16 measured) — [[hardware/sn76489]], [[memory/paged-rom]]; "real hardware untested" for shadow switching — [[memory/shadow-ram]], [[tools/emulators]].
- **Open, both recorded:** where a palette write lands on a real Master (KC's eye vs #1868); the FORCE INTERRUPT "16 µs SD / 32 µs DD" pairing (looks inverted; no 1770 datasheet in `raw/`); IER read-back bit 7 (kit `&53` vs [[hardware/via-6522]], likely a harness artefact).
- Source summaries [[sources/accc-compendium]] and [[sources/chunky-mode-notes]] keep their own claims, with a "Contradicted by" note.

## Filed into

- [[hardware/crtc-6845]], [[hardware/crtc-6845-advanced]], [[hardware/crtc-internal-counters]], [[hardware/video-ula]], [[hardware/address-translation]]
- [[timing/cycle-stretching]], [[timing/field-timing]], [[timing/via-timers]]
- [[techniques/rvi]], [[techniques/raster-splits]], [[techniques/vertical-rupture]], [[techniques/crtc-counter-freeze]], [[techniques/hexwab-stable-raster]], [[techniques/chunky-mode]], [[techniques/parallax-bars]], [[techniques/kefrens-bars]], [[techniques/single-rasterline-rupture]], [[techniques/triggered-vsync]], [[techniques/copper-bars]], [[techniques/checkerboard-zoom]], [[techniques/zx0-loading]]
- [[video/monitor-crt]] — **new**: what a real RGB CRT shows (visible windows, the back-porch clamp, strays)
- [[video/modes]], [[video/hardware-scrolling]]
- [[hardware/wd1770]], [[hardware/master-overview]], [[hardware/system-via]], [[hardware/via-6522]], [[hardware/sn76489]], [[hardware/6502]]
- [[memory/shadow-ram]], [[memory/paged-rom]], [[memory/os-workspace]], [[memory/zero-page]], [[memory/memory-map]]
- [[os/break-intercept]], [[os/interrupts]], [[os/sound]], [[os/keyboard]], [[os/disc-formats]]
- [[tools/emulators]] — rewritten: jsbeeb versions, jsbeeb vs a real Master, b2, beebjit, b-em
- [[sources/accc-compendium]], [[sources/chunky-mode-notes]] — "Contradicted by" notes
- [[index]], [[log]]

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
