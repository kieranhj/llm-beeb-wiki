---
title: System VIA
type: hardware
tags: [via, system-via, keyboard, sound, vsync, latch]
sources: [naug-ch22-vias, master-arm, master-rm]
sheila: ["&FE40", "&FE4F"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-05-13
---

# System VIA

6522 VIA at SHEILA `&FE40-&FE4F`. **Owned by the MOS.** The CPU does **not** directly access keyboard/sound/speech/CMOS — it talks to a "slow peripheral bus" routed through System VIA Port A, with destinations selected by an 8-bit addressable latch driven from Port B.

**Hands off** unless you really know what you're doing — MOS IRQ handlers fight you for the chip. Direct manipulation requires SEI / careful state restore.

See [[hardware/via-6522]] for the generic 6522 register layout (T1/T2/SR/ACR/PCR/IFR/IER are identical across both VIAs).

## Line assignments

### Port A (PA0-PA7) — slow peripheral data bus

8-bit bidirectional. Carries data to/from sound chip, speech, keyboard, and (Master only) CMOS RAM. **Direction is set per-transaction** via DDRA at `&FE43`.

- Set DDRA = `&FF` (all output) before a write.
- Set DDRA = `&00` (all input) before a read.
- Write/read happens at ORA `&FE41`.

The peripheral being addressed is selected by the addressable latch — see below.

### Port B (PB0-PB7) — control / status

| Pin | Direction | Function |
|---|---|---|
| PB0 | output | Latch address bit 0 |
| PB1 | output | Latch address bit 1 |
| PB2 | output | Latch address bit 2 |
| PB3 | output | Latch data bit (the value to store at the selected latch line) |
| PB4 | input  | Joystick 1 fire (active low) |
| PB5 | input  | Joystick 2 fire (active low) |
| PB6 | input  | Speech "interrupt" (B / B+) or CMOS chip enable (Master, output) |
| PB7 | input  | Speech "ready" (B / B+) or CMOS address strobe (Master, output) |

### Control lines

| Line | Function | IFR bit |
|---|---|---|
| CA1 | **Vsync** input from 6845 — IRQ every 20 ms (50 Hz) | 1 |
| CA2 | **Keyboard** key-press interrupt | 0 |
| CB1 | **ADC end-of-conversion** from µPD7002 | 4 |
| CB2 | **Light pen strobe** (LPSTB) from analogue port | 3 |

## The addressable latch (8-line write-only)

Driven from PB0-PB3:
- PB0-PB2 = latch line index (0-7).
- PB3 = value to store at that line.

To "set line 3 to 1": clock PB0-PB3 = `0,1,1,1` → addressable latch line 3 becomes high. The chip latches the value on each PB write.

### Line assignments

| Line | Function |
|---|---|
| 0 | Sound chip `/WE` (write enable, active low) |
| 1 | Speech READ (B / B+); CMOS R/W direction (Master) |
| 2 | Speech WRITE (B / B+); CMOS DS (Master) |
| 3 | Keyboard `/WE` |
| 4 | Screen-size addend bit 0 — hardware-scroll wrap |
| 5 | Screen-size addend bit 1 — hardware-scroll wrap |
| 6 | CAPS LOCK LED |
| 7 | SHIFT LOCK LED |

## Hardware-scroll wrap addend

[[video/hardware-scrolling]] mentions hardware wrap-around. Lines 4-5 of this latch select **which value gets added to the 6845's fetch address when it goes above `&7FFF`**, so the screen image wraps cleanly through screen RAM:

| Mode | Screen size | Start | Addend | B5 (line 5) | B4 (line 4) |
|---|---|---|---|---|---|
| 0, 1, 2 | 20 KB | `&3000` | 12 KB | 1 | 0 |
| 3       | 16 KB | `&4000` | 16 KB | 0 | 0 |
| 4, 5    | 10 KB | `&5800` | 22 KB | 1 | 1 |
| 6       |  8 KB | `&6000` | 24 KB | 0 | 1 |

(MODE 7's small screen wraps via different MOS logic — not via this addend.) Source: NAUG §22.3.2 p386.

The MOS sets these correctly at mode-set time; you only need to know about them if you build a custom mode.

## Writing to the addressable latch

```asm
; Set line N to value V (V ∈ {0, 1})
; Pseudocode — must guard with SEI/CLI as System VIA is busy
SEI
LDA &FE40       ; current ORB (read-back of last write)
AND #&F0        ; clear PB0-3
ORA #(N | (V<<3))
STA &FE40       ; write back
CLI
```

In MOS terms there's an OSBYTE for some of these (e.g. `OSBYTE &78`/`&79` for keyboard suppression), but for sound chip / hardware scroll, direct PB write is the norm.

## IRQ sources from this chip

MOS hooks IRQ1V (`&204/&205`) and reads `IFR` at `&FE4D` to dispatch:

| IFR bit | Source | What MOS does |
|---|---|---|
| 0 | CA2 (keyboard) | Read keyboard column on slow bus, push to key buffer |
| 1 | CA1 (vsync) | Update flashing colours, run 100 Hz semaphores, kick paged-ROM 100 Hz call |
| 2 | SR | (typically unused on this VIA) |
| 3 | CB2 (light pen) | Read R16/R17 of 6845; only if user enabled |
| 4 | CB1 (ADC EOC) | Read conversion result |
| 5 | T2 timeout | Currently unused by MOS on most machines |
| 6 | T1 timeout | Used by sound chip envelope timing (MOS) |

## Performance use cases

- **Vsync IRQ hook**: hook IRQ1V, in your handler check `&FE4D` bit 1, if set then run frame-start work and clear the flag by *reading* ORA (`&FE41`). Use **`BIT &FE41`** rather than `LDA &FE41` — same 4 cycles, same bus read (so the chip still clears the IFR bit), but `BIT` doesn't clobber the accumulator. That matters in an IRQ handler, where A is already stashed at `&FC` by MOS and reloading it costs cycles. See [[techniques/fast-animation]].
- **Free-running T1**: if MOS isn't using T1 for sound (test by reading IER bit 6), repurpose T1 to fire raster splits at a specific scan line within a frame. Set ACR for free-run + PB7 toggle, load latches with `lines_per_split × 64`.
- **Manual sound-chip writes** are tricky — between writing the sound data byte to PA and pulsing line 0 of the latch you need to ensure MOS doesn't preempt and overwrite. Many demos disable IRQs across the whole sequence.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
