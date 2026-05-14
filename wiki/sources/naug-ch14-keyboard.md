---
title: NAUG Ch14 — Keyboard
type: source
parent: [[sources/naug]]
pages: 225-239
section: §14
tags: [keyboard, ascii, inkey, internal-key-number, soft-keys]
updated: 2026-05-13
---

# NAUG Ch14 — Keyboard

Holmes & Dickens, *The New Advanced User Guide*, pp.225-239. Keyboard scan mechanics, three different key-numbering schemes, auto-repeat, soft keys, LEDs, status byte.

## Three key numbering schemes

For every key, NAUG documents three different numbers:

1. **ASCII** — the value returned by OSRDCH after MOS has translated SHIFT/CTRL/etc. State-dependent (a key produces different ASCII codes depending on modifier state).
2. **INKEY negative value** — used by BASIC's `INKEY(-n)` to test if a specific key is pressed. INKEY = `IK_no EOR &FF` (negated form).
3. **Internal Key Number (IKN)** — the lowest level. Direct from the keyboard matrix. Used by `OSBYTE &78/&79/&7A`.

Conversion: `INKEY = IK_no EOR &FF`. So `INKEY = -1` (`&FF`) = IK 0 (SHIFT), `INKEY = -2` (`&FE`) = IK 1 (CTRL), etc.

## Hardware scan path

System VIA owns the keyboard:

1. **System VIA** constantly scans columns. When any key is pressed, **CA2** generates an IRQ ([[hardware/system-via]], [[os/interrupts]]).
2. MOS reads the column counter, scans rows to identify the key, stores the IKN in zero-page "current keys pressed" state, sets a flag.
3. **100 Hz background poll** (System VIA T1) translates IKN → ASCII (applying SHIFT/CTRL/CAPS LOCK/etc.) and inserts the byte into the keyboard buffer (ID 0, see [[os/buffers]]).

Two-key rollover: zero page holds the *current* and *previous* keypress IKNs so a second press is recognised before the first releases.

BREAK is **wired directly to the 6502 reset line** — it's not part of the matrix and can't be intercepted at this level (only via OSBYTE `&F7-&F9` BREAK intercept).

## Reading keys

| OSBYTE | Function |
|---|---|
| `&78` (120) | Write "current keys pressed" — only for filing systems handling key+BREAK boot |
| `&79` (121) | Keyboard scan from given IKN (X = IKN, or X = `IKN EOR &80` to test single key). Returns `&FF` if no key. |
| `&7A` (122) | Keyboard scan from IKN `&10` (equivalent to `&79` with X=`&10`) |
| `&81` (129) | **INKEY** — read key with time limit (X+Y = centiseconds, max `&7FFF`); or scan-key (Y=`&FF`, X = negative INKEY value); or read OS type (special X/Y combo) |

`OSBYTE &79` on Model B scans in a **non-ascending** order (`&10, &20, ..., &70, &11, &21, ..., &19, &29, ..., &79`); other machines scan ascending. `OSBYTE &7A` always returns 0-79 IKN range.

## Auto-repeat

| OSBYTE | Function | Default |
|---|---|---|
| `&0B` / `&C4` (11/196) | Initial repeat delay (centiseconds, 0 = disable) | 50 |
| `&0C` / `&C5` (12/197) | Repeat period (centiseconds, 0 = reset both to defaults) | 8 |

`*FX 11,0` disables auto-repeat entirely — useful for games where holding a key shouldn't generate repeat events.

## Soft keys (function keys + others)

Function keys f0-f9 expand into user-defined strings (`*KEY 1 "LIST|M"` etc.). Stored at page B (`&B00-&BFF`, see [[memory/os-workspace]]).

| OSBYTE | Function |
|---|---|
| `&E1` (225) | R/W function-key status (`&80-&8F`): 0=ignore, 1=expand soft key, ≥2=ASCII offset |
| `&E2`/`&E3`/`&E4` | Same for SHIFT/CTRL/SHIFT+CTRL + function key |
| `&DD-&E0` | R/W character-status for `&C0-&FF` (treat as soft key, ASCII, or ignore) |
| `&D8` (216) | R/W remaining soft-key buffer length |
| `&F4` (244) | R/W soft-key consistency flag |
| `&12` (18) | Reset all soft-key definitions |

Default: function keys alone = expand. SHIFT+fn = generate ASCII `&80+n`. CTRL+fn = `&90+n`. SHIFT+CTRL+fn = ignored.

## Cursor editing

`OSBYTE &04`:
- X=0: cursor keys edit (default).
- X=1: cursor keys generate ASCII 135-139.
- X=2: cursor keys act as soft keys 11-15.
- X=3: Master Compact only — joystick emulation.

## Keyboard status byte (OSBYTE `&CA`)

Model B:

| Bit | Meaning |
|---|---|
| 3 | SHIFT pressed |
| 4 | CAPS LOCK engaged (**0 = engaged**) |
| 5 | SHIFT LOCK engaged (**0 = engaged**) |
| 6 | CTRL pressed |
| 7 | SHIFT enable — if any lock is engaged, SHIFT reverses it |

Electron uses different layout (SHIFT/CTRL/CAPS/FUNC bits, mostly transient).

## Disable / suppress

| OSBYTE | Function |
|---|---|
| `&76` (118) | Update CAPS/SHIFT LOCK LEDs to reflect status byte |
| `&B2` (178) | R/W keyboard semaphore — 0 = ignore keyboard IRQs, `&FF` = enabled |
| `&C9` (201) | R/W keyboard disable — non-zero = ignore all keys except BREAK (Econet-only flag) |
| `&FE` (254) | R/W shift-key effect (Master numeric keypad) |
| `&EE` (238) | R/W numeric-keypad base (Master) |

## TAB / ESCAPE characters

| OSBYTE | Function | Default |
|---|---|---|
| `&DB` (219) | R/W TAB character | 9 (cursor forward) |
| `&DC` (220) | R/W ESCAPE character | `&1B` (27) |

Set TAB to `&80+n` to make TAB act as soft key n.

## Filed into

- [[os/keyboard]] — Keyboard reference: scan model, all three numbering schemes (with full table), OSBYTE summary, auto-repeat, soft keys.

## Open follow-ups

- Full ASCII / INKEY / IKN table is ~100 rows. Captured in [[os/keyboard]] as a structured table.
- Master numeric keypad layout — covered briefly; defer detailed per-key table unless needed.
- Electron firm keys (`OSBYTE &CC`/`&CD`) cross-reference [[os/paged-roms]] Electron language-ROM section.
