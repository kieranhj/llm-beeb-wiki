---
title: NAUG Ch13 — Video/Graphics System
type: source
parent: [[sources/naug]]
pages: 172-224
section: §13
tags: [video, crtc, 6845, video-ula, palette, scrolling, modes]
updated: 2026-05-13
---

# NAUG Ch13 — Video/Graphics System

Holmes & Dickens, *The New Advanced User Guide*, pp.172-224. The chapter has three layers:

- **§13.1** OS-level video support: VDU codes, OSWORD/OSBYTE calls relating to the screen, palette, vsync, character definitions.
- **§13.2** Zero page and page 3 VDU workspace.
- **§13.3** Video hardware: 6845 CRTC and Video ULA — direct register programming for fast scrolling, animation, raster effects.
- **§13.4** Screen memory maps (one diagram per MODE).

## Key claims captured

- Two video chips: **6845 CRTC** at Sheila `&FE00/&FE01` and **Acorn Video ULA** at Sheila `&FE20/&FE21` (§13.3).
- Vsync rate: 50 Hz on UK BBC (§13.1.10 p189).
- `OSBYTE &13` (call &FFF4, ind &20A) waits for vertical sync — `*FX 19`. User trapping of IRQ1 can break it (§13.1.10).
- `OSBYTE &9A` (X=value) writes Video ULA control register (`&FE20`) AND keeps the OS shadow copy at `&34A`(?) consistent. Always use this rather than direct STA — required for Tube compatibility (§13.1.8 p187, §13.3.13).
- `OSBYTE &9B` (X=value) writes Video ULA palette register (`&FE21`) AND keeps OS copy consistent. Value actually written is `X EOR 7` (§13.1.8 p188).
- VDU 23,0,R,V,0,0,0,0,0,0 writes V into 6845 register R via the VDU stream — works across Tube (§13.3.3 p196).
- Hardware wrap-around: when the 6845 fetches video data at an address ≥ `&8000`, hardware adds an offset back into RAM. The offset is selected by 2 bits on the **System VIA** (§13.3.10 p200, points to §22.3).
- R12,R13 contain `screen_address / 8` — actual address divided by 8 because there are 8 lines per character cell (modes 0-6). MODE 7 uses a different correction: `high_byte - &74 EOR &20` → R12; low byte → R13 (§13.3.11 p202).
- Direct screen writes don't work across the Tube; second processor cannot reach screen RAM. Direct writes also need shadow-screen handling on B+/Master (ACCCON register) — §13.3.1 p194-195.

## Filed into

- `[[hardware/crtc-6845]]` — 6845 entity + register reference, with per-mode register values.
- `[[hardware/video-ula]]` — Video ULA entity, control register, palette mechanics, mode encoding.
- `[[video/modes]]` — Mode summary table + screen memory maps.
- `[[video/hardware-scrolling]]` — Vertical/sideways scroll, wrap-around, MODE 7 quirk, vsync timing.
- `[[techniques/fast-animation]]` — MODE 2 byte-move technique, MODE 0 shift, hardware-scroll as substrate.
- `[[memory/os-workspace]]` — Page 3 VDU workspace + zero-page VDU bytes captured here. `[[memory/zero-page]]` has the page-0 detail.

## Open follow-ups

- §13.2 page-3 VDU workspace fully filed into `[[memory/os-workspace]]` after Ch6 ingest.
- §13.1.6 character-explosion (`*FX 20`) detail captured only at the headline level — write a dedicated `[[techniques/exploding-font]]` page if it comes up.
- VDU 23,n function table (Master, n=2..16) summarised — full ECF pattern detail not extracted.
- PLOT number table (§13.1.4) summarised but not filed back as a dedicated page — most PLOT details belong with VDU 25 docs, not performance work.
