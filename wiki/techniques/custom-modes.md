---
title: Custom Screen Modes
type: technique
tags: [crtc, video-ula, modes, screen-memory]
sources: [naug-ch13-video, naug-ch22-vias]
updated: 2026-05-13
---

# Custom Screen Modes

Roll your own resolution / colour / memory layout by reprogramming the 6845 CRTC and Video ULA directly. The seven standard modes (0-7) are just particular register configurations of these chips — there's nothing magical about them.

When you'd want a custom mode:

- **Reduce screen RAM** — squeeze the playfield into less than 20 KB to leave room for code (e.g. 256×192 in MODE-1-bpp at ~12 KB).
- **Non-standard aspect** — narrower or shorter image with proportionally larger border, for centred game windows or split-screen.
- **Match an arbitrary resolution** — porting from another machine, hitting a specific pixel grid.
- **Raster-rate mode switching** — flip ULA bits 2-3 (chars-per-line) or bit 4 (HF/LF clock) mid-frame for split-mode effects (Master Spy, Exile-style status bars).

This page is the **recipe**; for the *why* of each register, see [[hardware/crtc-6845]] and [[hardware/video-ula]].

## The five things you must set

1. **6845 CRTC** registers (`&FE00`/`&FE01`) — horizontal & vertical timing, displayed area, screen start.
2. **Video ULA control** (`&FE20`) — pixel clock rate, char width, cursor width.
3. **Video ULA palette** (`&FE21`) — 16 entries × 8 bits, with the per-mode expansion rule.
4. **Screen memory** — pick a base address; reserve the bytes; clear them.
5. **System VIA addressable latch** lines B4/B5 — hardware-scroll wrap addend (only if you'll hardware-scroll).

This page leans **MOS-bypass**: write the registers directly, accept that the OS workspace at page 3 is stale, and don't expect OSWRCH to work. See *MOS compatibility — what breaks* below for the (optional) workspace-patching path.

## Step 1: pick a starting mode

Issue `VDU 22,n` (the MOS-level mode change — there's no `*MODE` star-command) to put the machine into a known starting configuration, then patch the diffs you care about.

The starting mode you pick really only matters for two things:

- **Bits per pixel** — determines colour depth and pixel-packing layout (1, 2, or 4 bpp; see [[video/modes]]).
- **6845 pixel clock** — high-frequency (modes 0-3, 2 MHz char clock) or low-frequency (modes 4-7, 1 MHz char clock). This determines `R0` (horizontal total) and `R3` (sync widths) for you, plus the Video ULA's clock-select bit.

Everything else — display width, height, screen-RAM base, where the image sits in the frame — you'll override. Custom modes can be **overscanned** (more or fewer scanlines than the standard 256-line image, off-centre horizontally, etc.) as long as the totals still satisfy the PAL-rate timing (R0+1 char times per scanline at the chosen pixel clock; R4·(R9+1)+R5 scanlines per frame ≈ 312 for 50 Hz).

The hardware-scroll wrap addend and ULA palette baseline are set as side effects of `VDU 22,n` (see step 5). Convenient if you pick a starting mode whose addend already brackets your screen size; otherwise you'll override that too.

## Step 2: compute the geometry

Work in **characters, character rows, and scanlines** — not bytes/pixels. The CRTC thinks in those units.

Given desired dimensions `W` (horizontal pixels) × `H` (scanlines) and bits-per-pixel `bpp`:

```
pixels_per_char  = 8 / bpp                ; 1 CRTC char = 1 byte = 8 bits = N pixels
                                          ; 8 / 4 / 2 for 1bpp / 2bpp / 4bpp
horiz_chars      = W / pixels_per_char    ; → R1 (horizontal displayed)
scanlines_per_row = 8                     ; assuming default R9=7 (8 scanlines per char row)
char_rows        = H / scanlines_per_row  ; → R6 (vertical displayed)
screen_bytes     = horiz_chars * char_rows * scanlines_per_row
                 = horiz_chars * H
```

`R1` is the **horizontal displayed character count** — from the CRTC's perspective each character is exactly one byte fetched per scanline. So R1 also happens to equal "bytes per scanline" numerically, but you should think of it as chars-displayed.

`R6` is the **vertical displayed character row count**. With the default 8 scanlines per character row (R9=7), it equals `H / 8`.

If you change R9 (more or fewer scanlines per character row), the geometry math changes — typical use is increasing R9 for taller cells (modes 3 and 6 use R9=9 plus R5=2 for extra inter-row padding to space text readably).

## Step 3: patch the CRTC

Each register's unit is given in the column headers. R0/R1/R2 are in **chars** (CRTC characters, = bytes fetched per scanline). R4/R6/R7 are in **character rows**. R5/R9 are in **scanlines**. R12/R13 hold a 14-bit memory-address-÷-8.

| Reg | Unit | Set to | Notes |
|---|---|---|---|
| R0  | chars | leave at base mode's (127 HF / 63 LF) | Total chars per scanline = sets PAL hsync rate. Don't change unless you also change the pixel clock. |
| R1  | chars | `horiz_chars` | Horizontal displayed character count. |
| R2  | chars | adjust by `(base_R1 - R1) / 2` ish | Hsync position — shift to centre the displayed area within R0. Tweak by eye if image is off-centre. |
| R3  | chars (low nibble) + scanlines (high nibble) | leave | Sync widths. Default is `&28` in **HF** modes (8 chars hsync + 2 scanlines vsync) and `&24` in **LF** modes (4 chars hsync + 2 scanlines vsync). Match your starting mode. |
| R4  | char rows | leave (see below) | Vertical total — must give 312 scanlines for 50 Hz PAL. With R9=7 and R5=0, R4=38 gives `(38+1)*8 = 312`. Modes 3/6/7 use R4=30 with R5=2 and bigger R9 (9 in modes 3/6, 18 in mode 7) — still 312 scanlines, just larger character rows. |
| R5  | scanlines | leave (0, or 2 for modes 3/6/7) | Vertical fractional adjust. |
| R6  | char rows | `char_rows` | Vertical displayed character row count. |
| R7  | char rows | `R6 + ((R4 + 1 - R6) / 2)` ish | Vsync position — centre vertically. Tweak by eye. |
| R8  | bits | **0 for non-interlaced** (recommended for games/demos), or 1 for interlace-sync (the BBC default) | Interlace + display/cursor delays. See note below. |
| R9  | scanlines - 1 | leave (7 = 8 scanlines per row in graphics modes; 9 in modes 3/6 with R5=2; 18 in MODE 7) | Per-character-row height. Changing this changes the cell math in step 2. |
| R10, R11 | scanlines | leave | Cursor — only matters if cursor visible. |
| R12 | high 6 bits of addr/8 | `(screen_base / 8) >> 8` | Screen-start high byte. |
| R13 | low 8 bits of addr/8 | `(screen_base / 8) & 0xFF` | Screen-start low byte. |

R12/R13 are latched and apply at the next CRTC frame cycle — see [[hardware/crtc-6845#register-latching]].

Modes 3 and 6 are **graphics** modes (they have the same pixel layout as MODE 0 and MODE 4 respectively); they just trade vertical pixel count (192/200 vs 256) for inter-row padding that makes text readable. Treat them as "graphics with text spacing", not "text-only".

### Prefer non-interlaced for games and demos

The BBC's default for modes 0-6 is **interlace sync** (R8 bit 0 = 1) — the chip alternates between two slightly offset field positions per frame to match broadcast television. On a CRT this produces a faint vertical jitter at 25 Hz; on a modern display it can produce visible flicker or comb artefacts on horizontal edges.

For anything that doesn't need to match TV broadcast standards — games, demos, scrolling playfields, anything where image stability matters — **clear R8 bit 0 (R8 = 0)** to get non-interlaced sync. The image becomes rock-steady at the cost of slightly reduced vertical resolution (every scanline shown twice, effectively halving the visible vertical pixel count on modes that relied on interlace for full resolution).

In practice almost all BBC games and demos run non-interlaced. Leave interlace on only when matching the standard MODE-x look for text or compatibility reasons.

### MODE 7 is a special case

MODE 7 (teletext) uses the SAA5050 character generator instead of the Video ULA serialiser, has its own scrolling correction, its own R8 setting (3 = interlace sync + video — the only mode that uses interlace video), R9=18 (20 scanlines per character row), 1 KB screen RAM at `&7C00-&7FE7`, and a separate set of byte-level conventions (each byte is a teletext control code or character, not pixel data).

**MODE 7 customisation is out of scope for this page.** Building a custom teletext-style mode is genuinely different from custom graphics modes — covered separately in [[video/teletext-mode]] (planned). If you're after a 4-colour or 16-colour image, you're starting from a graphics mode (0-6), not 7.

### Worked example: community "MODE 8" 16-colour LF mode

For a concrete reference custom mode that combines MODE 2's 16-colour palette with MODE 5's LF clock (giving a 160×256 16-colour playfield instead of MODE 2's 160×256 8 KB cost in 20 KB), see [[synthesis/mode-8-16colour-lf]]. Worked CRTC and Video ULA register values; what the BBC community has historically called "MODE 8".

## Step 4: patch the Video ULA (only if base mode is wrong)

If the base mode already has the right colour depth and clock, you don't need to touch `&FE20` — leave it at the base mode's value (see [[hardware/video-ula]] per-mode table). For mid-frame mode-switching tricks, write `&FE20` (or via OSBYTE `&9A` for Tube safety) at the raster split point.

## Step 5: pick screen base & set the wrap addend

The 6845 hardware-wrap ([[hardware/system-via]]) adds a fixed value to fetch addresses ≥ `&8000`. The addend is set by addressable-latch lines **B4/B5** on the System VIA, and the four options match the standard mode sizes:

| Screen size | Standard start | Addend | B5 | B4 |
|---|---|---|---|---|
| 20 KB | `&3000` | 12 KB | 1 | 0 |
| 16 KB | `&4000` | 16 KB | 0 | 0 |
| 10 KB | `&5800` | 22 KB | 1 | 1 |
| 8 KB  | `&6000` | 24 KB | 0 | 1 |

Pick the addend whose window comfortably contains your `screen_bytes`. The unused remainder of the window is "wasted" RAM (won't display because R6 × R1 × 8 bounds the fetch, but you also can't reliably use it for code while displaying).

If you start from a base mode whose screen size already brackets yours (e.g. MODE 1's 20 KB for any image ≤ 20 KB), the addend is already correct after the mode select — no latch poke needed.

## Step 6: clear and use the screen

```asm
; Clear screen_bytes from screen_base
LDA #0
LDX #0
.clear_loop
    STA screen_base+0,X
    ...                     ; (one STA abs,X per page, or two-pointer loop)
```

Then write pixels directly per the bpp layout in [[video/modes]]. Don't expect `OSWRCH` to plot text correctly — it uses the OS's idea of geometry.

## MOS compatibility — what breaks

In MOS-bypass mode, accept that the following stop working:

- **`OSWRCH` / `OSNEWL` / `OSASCI`** plot text using page-3 workspace geometry (`&34F`, `&350/&351`, `&352/&353`, `&356`, `&360-&363`, `&36C`). Without patching these, characters land at the wrong pixel offsets and scrolling is wrong. **Workaround**: render text yourself (font lookup + direct STA to screen RAM).
- **Cursor** position tracking (`&31F`/`&320` = POS/VPOS) — same issue.
- **Hardware scroll via `VDU 23,12/13`** — the VDU driver computes from its stale geometry. Hardware-scroll directly via R12/R13 instead ([[video/hardware-scrolling]]).
- **Light pen** — NAUG's per-mode correction factor doesn't cover custom geometry.
- **`OSWORD &09`** (read pixel) and **`OSWORD &0A`** (read character) — also use page-3 workspace.
- **Palette via `VDU 19` / `OSBYTE &9B`** technically still works because the palette mechanics are mode-independent (only the colour-bit expansion rule depends on bpp). The OS shadow palette copy at `&380+` may go stale if you write `&FE21` directly.

**If you do want MOS to play nicely** (text output / OS hooks), patch the page-3 workspace bytes after your register pokes. The minimum set:

- `&34F` — bytes per character (8 in 1bpp modes, 16 in 2bpp, 32 in 4bpp). Determines cell stride.
- `&350/&351` — top-left screen address (NOT ÷ 8 — full address). Used by VDU drivers.
- `&352/&353` — bytes per cell-row (`R1 × 8`).
- `&354` — screen size in pages (`screen_bytes / 256`).
- `&356` — screen size code (0=20K, 1=16K, 2=10K, 3=8K, 4=1K — pick closest).
- `&360` — number of logical colours - 1.
- `&361` — pixels per byte - 1.
- `&362`, `&363` — leftmost/rightmost pixel bit masks (mode-specific).

Exact addresses are NAUG-documented but Acorn-internal; verify against MOS source disassembly for the target machine. [[memory/os-workspace]] has the source citations.

## Reset / BREAK survival

A hard reset reverts to MODE 7. A soft BREAK re-enters the current language which typically issues `VDU 22,1` (MODE 1). Either way, your custom mode is gone.

To survive BREAK: hook the BREAK intercept via `OSBYTE &F7/&F8/&F9` (a JMP + 16-bit address). The intercept code re-applies your CRTC/ULA writes. See [[os/osbyte]] `&F7-&F9`.

## Shadow / B+ / Master complications

The B+ and Master have shadow RAM at `&3000-&7FFF`. If shadow is selected (`*SHADOW`, MODE 128-135, or ACCCON forced), your direct writes to screen RAM may land in main while the 6845 reads shadow. Either:

- Force non-shadow: `OSBYTE &72` with X≠0 ([[memory/shadow-ram]]).
- Or use ACCCON `D`/`E`/`X` bits to drive write target and display source explicitly. Master's `OSBYTE &6C/&70/&71` are the safe path.

## Things to verify by experiment

Custom-mode geometry is hard to validate without a real screen:

- **Hsync centring**: image too far left → decrease R2; too far right → increase. Step by 2-4 chars at a time.
- **Vsync centring**: image too high → decrease R7; too low → increase. Step by 1 char-row (8 scan lines).
- **Aspect**: pixels may be non-square. A 288×192 image at 4:3 has 1.5× wider pixels than a 256×192 image. Account for this in art.
- **Border colour**: ULA outputs black during non-displayed time. To change the border, you'd need ULA bit-twiddling beyond what NAUG documents (Master has *FX 152 hooks; Model B doesn't easily).
- **Interlace flicker**: if you left R8 bit 0 set, you'll see 25 Hz shimmer especially on horizontal edges. Clear R8 bit 0 for the games/demos use case.

## Mid-frame mode changes (deferred)

Switching modes mid-frame (e.g. high-res top + low-colour bottom) requires raster-cycle-accurate writes to `&FE20` and possibly `&FE21`/`&FE00`/`&FE01`. The timing window is roughly 64 µs per scan line, with the visible-area boundary determined by R0/R1/R2. Detailed coverage deferred to [[hardware/crtc-6845-advanced]] and [[techniques/raster-splits]] (both planned).

## Worked example

A full worked example for 288×192 at 4 colours lives at [[synthesis/custom-mode-288x192]] (planned). The synthesis call covered: R1=72, R6=24, R2≈94, R7≈31, R8=0 (non-interlaced for game use), screen at `&4000-&73FF` (within a 16 KB addend window), Video ULA stays at MODE 1's `&D8`, palette via OSWORD `&0C`.

## See also

- [[hardware/crtc-6845]] — Register reference per chip.
- [[hardware/video-ula]] — Control register, palette mechanics, cursor width.
- [[hardware/system-via]] — Addressable latch (incl. wrap-addend lines B4/B5).
- [[video/modes]] — Pixel layouts for 1/2/4 bpp.
- [[video/hardware-scrolling]] — R12/R13 lever.
- [[memory/os-workspace]] — Page-3 VDU workspace.
- [[memory/shadow-ram]] — Shadow RAM and ACCCON on B+/Master.
