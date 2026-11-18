---
title: System VIA
type: hardware
tags: [via, system-via, keyboard, sound, vsync, latch]
sources: [naug-ch22-vias, master-arm, master-rm, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
sheila: ["&FE40", "&FE4F"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-11-18
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

To "set line 3 to 1", write the nibble `PB3..PB0 = %1011` (= `&0B`) to ORB — i.e. PB3 = 1 (the value), PB2/PB1/PB0 = 0/1/1 (index 3) → addressable latch line 3 becomes high. The chip latches the value on each PB write.

Written as a general formula: `ORB low nibble = (V << 3) | N`, where `N` is the line index 0-7 and `V` the value. Beware pin-order confusion: `%1011` is MSB-first (PB3 first); listed PB0-first the same write is `1,1,0,1`.

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

**Measured in practice (Edge Grinder, Master 128, jsbeeb, 2026-09-04; the 10K case independently in Paradroid's Layer 3 — [[sources/beeb-port-kit-hardware-facts]] §3):** the table agrees with the measurement bit for bit. Stated as what is added back when the display address passes `&8000`: line 4/line 5 = 0/0 → `&4000` (16K), 1/0 → `&6000` (8K), 0/1 → `&3000` (20K), 1/1 → `&5800` (10K). Written as `LDA #4` / `LDA #12` to `&FE40` for line 4 clear/set, `#5` / `#13` for line 5. Two wiki pages had these the wrong way round in their comments — see the flags on [[techniques/vertical-rupture]] and [[techniques/smooth-vertical-scroll]].

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

## Measured in practice — two C64 → BBC ports (2026)

Source: [[sources/beeb-port-kit-hardware-facts]] — facts measured during Kieran Connell's two C64 → BBC ports, [Paradroid](https://github.com/kieranhj/paradroid-beeb) (BBC Model B, August 2026) and [Edge Grinder](https://github.com/kieranhj/edge-beeb) (BBC Master 128, September 2026). Instrument is jsbeeb driven through an MCP unless the entry says otherwise; b-em and b2 were the cross-checks. Each entry gives the date (or the port's layer where the write-up carries no date), the emulator or hardware, and the port's own write-up. Both ports own IRQ1V outright and drive a rupture from this chip's T1; both read the keyboard directly through Port A.

### Timers

- **T1 in continuous mode, not T2, for raster timing.** T2 is one-shot only, so the interval starts when the handler writes `T2C-H` and every interrupt's service latency feeds into the next interval. T1 auto-reloads from its latch at underflow, so the period is exact however late the service; restart it at VSync and the fires stay phase-locked. A latch write takes effect one reload later, so intervals are set one fire ahead (Paradroid Layer 3, jsbeeb, after T2 was tried first).
- **T1 ticks at 1 MHz; a scanline is 64 ticks (`SL = 64`)** (Edge, 2026-09-02, jsbeeb). The two ports' T1 constants are on [[timing/field-timing]].
- **A `&FE44` read at a fixed point in a VSync-locked loop is NOT random.** Under the MOS, System VIA T1 runs the 100 Hz tick: 20,000 cycles, exactly half a frame, so the sampled byte is near-constant and drifts only with interrupt jitter. It cost Paradroid's loading intro its lightning randomness; use a stepped PRNG with the timer as seed only (2026-08-26, jsbeeb; [intro.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/intro.md)).
- **A T1 difference used as a stopwatch is only modular while the counter does not pass zero between the reads**; when it does, the sample gains ~65,536 ticks, and because the reload point drifts slowly the bad readings come in consecutive runs. Paradroid's `DEBUG_TIME` reported 2,903 cycles for code measured at 1,009 by breakpoints (2026-08-26).
- **T2's two bytes are read one after the other and the counter can roll between them**, so an elapsed reading can come out 256 µs smaller than the mark before it; reject a sample whose subtraction borrows. A frame longer than 65.5 ms wraps the counter outright (Edge, 2026-09-04, jsbeeb; three readings of three were junk before the fix).

### VSync

- **The VSync CA1 interrupt is serviced about 4 scanlines after the VSync edge.** The timer chain itself is exact — breakpoint bisection put Paradroid's fire 1 at 78.3-79.3 scanlines after handler entry against a design figure of 78 — so the whole error is in where VSync itself sits. The scanline component cannot be read from screenshots better than ±2; it was KC spotting two wrong lines on b-em that pinned it (Paradroid Layer 3).
- **Polling `&FE4D` bit 1 for VSync races the MOS**, whose own handler clears the flag when it services VSync; chain on IRQ1V instead while the MOS is alive (stated as the design reason; not separately measured). **With interrupts down, polling the flag directly works** — Edge Grinder's memorial fade does exactly that before its IRQ install (Layer 9d, 2026-09-05, jsbeeb).
- **Taking IRQ1V outright**: disable every interrupt source on both VIAs except System VIA CA1 and T1, or anything unserviced holds the IRQ line asserted forever. The MOS saves the interrupted A in `&FC` but not X or Y (Paradroid Layer 3). See [[os/interrupts]].
- **Chaining to the MOS loses VSyncs** unless the MOS's System VIA mask (`&0279`, OSBYTE `&E9`) has bit 1 cleared while the game owns VSync: a VSync landing in the ~30 cycles before the MOS dispatcher reads the IFR is acknowledged by the MOS first. Stryker's Run's original lost 12 fields of 1,000; 0 after the fix (2026-10-16, jsbeeb 2.5.0, Master; [BUGS #3](https://github.com/kieranhj/strykers-run/blob/main/BUGS.md) — [[sources/beeb-port-kit-hardware-facts-2026-11]] §3). See [[os/interrupts]].
- **The MOS reset reads this chip's IER**: MOS 3.20 clears memory on BREAK only if the IER reads 0 (or `&0258` says so), so a game running with VIA interrupts enabled (IER `&C2` in 1942) keeps RAM through a BREAK despite `*FX 200,2`; phX's BREAK intercept clears the IER and restarts the reset. See [[os/break-intercept]].
- **System VIA T1's state matters to a filing-system call on a Master**: with a chaining IRQ1V handler, a changed T1 latch or T1's interrupt disabled (IER `&40`) hung a 1770 DFS `*LOAD` in jsbeeb (1942, 2026-09-13). A rupture's own T1 cadence cannot run across a filing-system call. See [[os/interrupts]].

Later T1 measurements (chain the latch rather than re-arm from a constant; one T1 chain for a whole demo; a 304-line field) are on [[timing/via-timers]].

### Port A: keyboard and sound chip together

- **Reading one named key direct costs 69 cycles against 243 through `OSBYTE &81`**, `JSR` to `RTS` inclusive (Paradroid, 2026-08-26, jsbeeb, breakpoint pair differencing `elapsed_cycles`; the OSBYTE figure taken twice by different routes, 238 and 237). The routine is on [[os/keyboard]]. The 26 masked cycles round the sequence, twelve times a pass, cost a T1-driven rupture nothing: 25.0 Hz before and after, panel boundary clean while scrolling.
- **Port A is shared with the SN76489 write path, safely.** A sound write from the IRQ that saves and restores DDRA and ORA around its strobe does not disturb a foreground keyboard poll: key up, 0 of 8,192 polls read down with 225 IRQ writes interleaved; key held, 8,192 of 8,192 with 192 interleaved. The sound strobe touches only latch bit 0, never the keyboard-enable bit (Paradroid, 2026-08-21, jsbeeb, `tools/sndtest.asm`; [layer-11e-sound.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-11e-sound.md)). See [[hardware/sn76489]].
- **Phantom keys.** The matrix has no diodes, so five keys held at once can phantom a sixth, and asking about one key at a time does not save you: Z, X, K, M and L together triggered a debug key on C. Reported by KC on **real hardware**, not instrumented; addressed by gating every debug key on CTRL ([human-notes-status.md](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/human-notes-status.md)).

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
