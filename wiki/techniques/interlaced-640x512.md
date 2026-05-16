---
title: 640×512 interlaced 2-colour mode (Master)
type: technique
tags: [interlace, shadow, master, custom-mode, 640x512, lynne]
sources: [master-arm]
machines: [Master 128]
updated: 2026-05-16
---

# 640×512 interlaced 2-colour mode (Master)

A high-resolution flicker-tolerant display mode the Master ARM ([[sources/master-arm]] Ch 6, "The VDU driver" section) documents as a worked recipe. It uses **CRTC interlace + LYNNE shadow RAM** to store two alternating half-frames, giving an effective 640×512 in two colours. Not strictly "640×512 progressive" — it's two interlaced 640×256 fields drawn on alternate vsync events.

## Recipe (from ARM Ch 6 page 51)

```
1. Select MODE 0
2. Re-program the CRTC for interlace SYNC AND VIDEO
   (R8 bits 0-1 = %11 — the MODE-7 setting, but in MODE 0)
3. Set EVNTV to point to your event handler
4. Enable the vertical-synchronisation event (event 4) via *FX 14,4
5. *FX 112,1  → first half-frame goes to main RAM
6. Draw the first half-frame
7. *FX 112,2  → second half-frame goes to LYNNE
8. Draw the second half-frame
9. *FX 113,1 / *FX 113,2 on alternate vsync events to switch
   the CRTC display source between main and LYNNE
```

The OS calls used:

- `OSBYTE &70` (`*FX 112`) — select VDU-write target (1 = main, 2 = LYNNE). See [[memory/shadow-ram]].
- `OSBYTE &71` (`*FX 113`) — select CRTC display source (1 = main, 2 = LYNNE).
- `EVNTV` event 4 — fires at every vsync. Your handler alternates `*FX 113,1` / `*FX 113,2` to swap which bank the CRTC pulls from.

## Why this works

The Master ACCCON bit **D** (CRTC display source) is what `*FX 113` toggles. When `D=0`, the CRTC scans main RAM at `&3000-&7FFF`; when `D=1`, it scans LYNNE. The CRTC is **already in interlace-sync-and-video mode** (R8 bits 0-1 = `%11`), so it emits *odd* lines on one field and *even* lines on the next. By having two different framebuffers (main has the odd field, LYNNE has the even field) and swapping the CRTC source per vsync, the TV sees alternating odd/even content from alternating buffers — visually combining to 512 vertical scan lines at 25 Hz field rate.

The CRTC clock is still MODE-0 HF (2 MHz), so horizontal resolution is the standard 640 pixels.

## Practical considerations

- **25 Hz field-pair rate** — visible flicker on bright content. Works best for fine-detail static images (CAD drawings, plotter previews, dense text).
- **Phase ambiguity** — the ARM recipe warns: "the program should provide the facility to reverse the display sequence as the hardware may present the two half-frames in the incorrect phase." On reset/MODE-set you don't know whether main or LYNNE will be the odd or even field. Provide a key to swap if the image looks wrong.
- **EVNTV-disabling software breaks it** — any code path that masks vsync events (or runs with IRQs disabled across multiple vsyncs) causes the swap to skip a beat, fusing the two half-frames on the same field and halving vertical resolution. Calling print or filing-system code during the display can do this.
- **`*FX 112` only sets the destination of MOS VDU writes** — your direct screen writes (e.g. `STA &3000+y_offset,X`) must target the correct bank yourself, via ACCCON `X` bit or `*FX 108` equivalents (or by running OS-flagged VDU writes through `OSWRCH`).
- **Not a "true" 640×512 mode** — `R6` (vertical displayed) is still 32 character rows × 8 scanlines = 256 scanlines per field. The interlace gives you 256 + 256 = 512 distinct scan rows per *frame-pair*, but each individual field is still 256.

## When to reach for this

- Static high-detail diagrams that benefit from the doubled vertical resolution and tolerate flicker.
- Two-colour scientific / engineering plots.
- "Pseudo-vector" line art where the eye averages the alternate fields anyway.

Not appropriate for animation, scrolling, or games — the per-field flicker becomes painful at any motion.

## Builds on / used by

- [[memory/shadow-ram]] — ACCCON D / X / E mechanics and `*FX 70` / `*FX 71` / `*FX 72`.
- [[hardware/crtc-6845]] — R8 bits 0-1 = `%11` for sync-and-video interlace.
- [[techniques/custom-modes]] — general recipe for re-programming CRTC + ULA.
- [[os/events]] — EVNTV / event 4 (vertical sync).
- [[techniques/fx-framework]] — alternative sync mechanism if you need finer than vsync precision.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
