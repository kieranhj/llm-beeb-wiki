---
title: Keyboard
type: os
tags: [keyboard, ascii, inkey, ikn, soft-keys, scan]
sources: [naug-ch14-keyboard, master-arm, bbc-user-guide]
updated: 2026-05-16
---

# Keyboard

Reference for keyboard scan, key numbering, and MOS keyboard calls. For the hardware path (System VIA CA2 IRQ + slow bus matrix scan), see [[hardware/system-via]].

## Three key numbering schemes

Every key has three numbers, used by different APIs:

| Scheme | Range | Used by | What it represents |
|---|---|---|---|
| **ASCII** | 0-255 | OSRDCH, character input | Translated value (after SHIFT/CTRL/CAPS apply) |
| **INKEY** (negative) | -1 to -128 | BASIC `INKEY(-n)`, `OSBYTE &81` scan-key mode | Raw key identity |
| **Internal Key Number (IKN)** | 0-127 | `OSBYTE &78/&79/&7A` | Lowest level matrix code |

Conversion: `INKEY_value = IKN EOR &FF`.

So `INKEY(-1)` (= `&FF`) tests **IKN 0** (SHIFT). `INKEY(-2)` (= `&FE`) tests **IKN 1** (CTRL).

## Common keys — quick reference

| Key | ASCII | INKEY | IKN |
|---|---|---|---|
| SHIFT | — | -1 | 0 |
| CTRL | — | -2 | 1 |
| Caps Lock | — | -65 | 64 |
| Shift Lock | — | -81 | 80 |
| Return | 13 | -74 | 73 |
| Escape | 27 | -113 | 112 |
| Tab | 9 | -97 | 96 |
| Delete | 127 | -90 | 89 |
| Copy | 135 | -106 | 105 |
| Cursor Up | 139 | -58 | 57 |
| Cursor Down | 138 | -42 | 41 |
| Cursor Left | 136 | -26 | 25 |
| Cursor Right | 137 | -122 | 121 |
| Space | 32 | -99 | 98 |
| 0 | 48 | -40 | 39 |
| 1-9 | 49-57 | varies | varies |
| A-Z | 65-90 | varies | varies |
| f0 | — | -33 (`&DF`) | 32 |
| f1 | — | -114 (`&8E`) | 113 |
| f2 | — | -115 (`&8D`) | 114 |
| f3 | — | -116 (`&8C`) | 115 |
| f4 | — | **-21 (`&EB`)** | **234** — out of sequence (matrix wiring) |
| f5 | — | -117 (`&8B`) | 116 |
| f6 | — | -118 (`&8A`) | 117 |
| f7 | — | **-23 (`&E9`)** | **232** — out of sequence (matrix wiring) |
| f8 | — | -119 (`&89`) | 118 |
| f9 | — | -120 (`&88`) | 119 |

Full table in NAUG §14.1 p219-220. The IKN ordering doesn't follow ASCII — it's matrix-determined.

## Read a character (blocking) — OSRDCH

```asm
JSR &FFE0          ; A = ASCII char read from input stream
BCS error          ; C=1 = read error (e.g. ESCAPE)
```

Blocks until a char arrives. Honours the currently-selected input stream (keyboard or RS423).

## Read a character with timeout — OSBYTE `&81`

```asm
LDA #&81
LDX #time_lo       ; centiseconds, low byte
LDY #time_hi       ; centiseconds, high byte (max &7FFF total ≈ 5.5 min)
JSR &FFF4
; on exit:
;   C=0, X = ASCII char, Y = 0       → got a char
;   C=1, Y = &FF                     → timeout
;   C=1, Y = &1B (27)                → ESCAPE
```

## Test if a specific key is pressed — OSBYTE `&81` scan mode

```asm
LDA #&81
LDX #INKEY_value   ; e.g. &FF for SHIFT (= -1 negated to unsigned)
LDY #&FF
JSR &FFF4
; on exit:
;   X = &FF, Y = &FF   → key pressed
;   X = 0,   Y = 0     → not pressed
```

For polling multiple keys in a tight loop, this is the fastest MOS-blessed path.

## Test if any key is pressed — OSBYTE `&79`/`&7A`

```asm
LDA #&7A           ; scan from IKN &10 upwards
LDX #0
LDY #0
JSR &FFF4
; X = IKN of first pressed key, or 0 if none
```

**Model B caveat**: `OSBYTE &79` scans in a strange order (`&10, &20, &30, …, &70, &11, &21, …`). Master / Compact / Electron scan ascending.

## Direct matrix scan — bypassing MOS

For maximum control (e.g. detect chord presses, scan all keys per frame in a game), drive the System VIA matrix directly. NAUG doesn't give this code explicitly, but the protocol:

1. SEI (MOS owns the slow bus).
2. Set System VIA Port A DDRA = `&FF` low nibble, `&00` high nibble (or all-output for column select).
3. Disable keyboard IRQ (set keyboard line of addressable latch high — line 3).
4. Output column number on PA0-PA3, read row on PA4-PA7.
5. Iterate over all 16 columns × 8 rows.
6. Re-enable keyboard IRQ (line 3 low) and CLI.

Detailed matrix layout differs between Model B, Master, Master Compact (NAUG §14 opening note). Capture per-machine matrix if/when needed.

## Auto-repeat

| OSBYTE | Function | Default |
|---|---|---|
| `&0B` (11) | Initial delay (centiseconds, 0 = disable repeat) | 50 |
| `&0C` (12) | Repeat period | 8 |
| `&C4` (196) | R/W initial delay | — |
| `&C5` (197) | R/W period | — |

For games / responsive UI: `*FX 11,0` disables repeat. Keys still scan on press/release.

## Soft keys (function keys + others)

Function keys f0-f9 expand into user-defined strings stored at `&B00-&BFF` ([[memory/os-workspace]]).

| OSBYTE | Function |
|---|---|
| `&12` (18) | Reset all soft-key definitions |
| `&E1`-`&E4` (225-228) | R/W function-key status: alone / SHIFT / CTRL / SHIFT+CTRL. 0=ignore, 1=expand, ≥2=ASCII offset |
| `&DD`-`&E0` (221-224) | R/W character-status for `&C0-&FF` (treat as soft key / ASCII / ignore) |
| `&D8` (216) | R/W remaining soft-key buffer length |
| `&F4` (244) | R/W consistency flag |

Defaults: fn alone = expand. SHIFT+fn = ASCII `&80+n`. CTRL+fn = `&90+n`. SHIFT+CTRL+fn = ignored.

## Cursor-key behaviour

`OSBYTE &04`:
- X=0: cursor keys = edit (default).
- X=1: ASCII 135-139.
- X=2: act as soft keys 11-15.
- X=3: Master Compact joystick emulation.

## Status byte (modifier keys) — OSBYTE `&CA`

Read the current modifier state:

```asm
LDA #&CA : LDX #0 : LDY #&FF : JSR &FFF4
; X = status byte
```

Model B layout:

| Bit | Set when |
|---|---|
| 3 | SHIFT pressed |
| 4 | **0 = CAPS LOCK engaged** (inverted) |
| 5 | **0 = SHIFT LOCK engaged** (inverted) |
| 6 | CTRL pressed |
| 7 | SHIFT enable (locks reverse on SHIFT) |

Electron: bits 4 (CAPS), 5 (FUNC), 6 (SHIFT), 7 (CTRL).

After writing the status byte directly, call `OSBYTE &76` to update the keyboard LEDs accordingly.

## Disable / suppress

| OSBYTE | Function |
|---|---|
| `&B2` (178) | Keyboard semaphore — 0 = ignore IRQs, `&FF` = normal |
| `&C9` (201) | Keyboard disable — non-zero = ignore all except BREAK (Econet use only) |
| `&76` (118) | Refresh CAPS/SHIFT LOCK LEDs |

## Special character mappings

| OSBYTE | Function | Default |
|---|---|---|
| `&DB` (219) | TAB character — set to `&80+n` to make TAB a soft key | 9 |
| `&DC` (220) | ESCAPE character | `&1B` (27) |

## Performance / bypass

- **MOS scan via `OSBYTE &81` or `&7A`** costs several hundred cycles per call.
- **Direct matrix scan** (custom System VIA driver) can poll all 80-something keys in ~200 cycles total — useful for games needing per-frame full-keyboard read.
- **Disabling auto-repeat** (`*FX 11,0`) is mandatory for any game that distinguishes "key down" from "auto-repeated".
- The keyboard buffer (ID 0) carries the type-ahead — purge with `OSBYTE &15, X=0` if you want a clean slate ([[os/buffers]]).

## KBDENC scan modes (hardware)

The Master's keyboard encoder (`KBDENC` IC, a custom Acorn ULA — same role on Model B / B+ via different parts) operates in three modes per [[sources/master-arm]] Ch 5:

1. **Free-run** (idle, no key pressed): a 4-bit counter clocked at 1 MHz drives a 4-to-15 decoder, rippling a logic-low signal through columns C0-C14. If any key is pressed, the NAND output goes high and triggers CA2 → System VIA → IRQ. The CPU does nothing during free-run.
2. **Column detection** (after IRQ, MOS scan): MOS asserts `nKBEN` (latch line 3 low) to stop free-run, then writes a column number to PA0-PA3 and reads PA7. The selected column output drives low; if a key on that column is pressed, PA7 reads low. MOS scans columns 0-14 to find the active one.
3. **Row detection**: with the column held, MOS writes a row number to PA4-PA6 and reads PA7. The row decoder gates one row's input onto PA7 in inverted form, so PA7 high means "key at this (col,row) is pressed".

After identifying all pressed keys, MOS returns to free-run by clearing nKBEN. MOS rescans every 10 ms (via the 100 Hz interval timer) while any key remains held, until the matrix is clear.

**For a direct-matrix scan from user code** (`SEI` + drive PA + read PA7), you take over the slow bus — which competes with sound-chip writes and CMOS access. Pattern: own the bus, drive nKBEN low (latch line 3 = 0), iterate through column/row pairs of interest, then restore. ~3 µs per key tested; ~200-300 cycles to scan all interesting keys.

The Model B / B+ keyboard hardware is functionally identical at the slow-bus interface, so this section applies to all BBC machines — just the silicon implementing the matrix scanner differs.

## See also

- [[hardware/system-via]] — CA2 IRQ source, slow-bus matrix scan via addressable latch line 3.
- [[os/buffers]] — keyboard buffer (ID 0).
- [[os/events]] — events 2 (char entering input) and 6 (ESCAPE).
- [[memory/os-workspace]] — soft-key string storage at `&B00-&BFF`.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
