---
title: Escape
type: os
tags: [escape, osbyte, event-6]
sources: [naug-ch10-escape]
updated: 2026-05-13
---

# Escape

Pressing the ESCAPE key sets a system-wide **ESCAPE condition**. Most OS routines check between operations and bail back to BASIC if it's set, producing the "Escape" error. Held in MOS workspace until explicitly cleared.

## OSBYTE summary

| OSBYTE | Function | Common use |
|---|---|---|
| `&7C` (124) | Clear condition (no effects) | Manually clear after handling an escape |
| `&7D` (125) | Set condition (programmatic ESCAPE) | Service ROM aborts something |
| `&7E` (126) | Acknowledge + clear effects | Standard "what BASIC does on ESCAPE" |
| `&C8` (200) | R/W escape-disable + BREAK behaviour | Games (disable both) |
| `&DC` (220) | R/W ESCAPE character (default `&1B`) | Remap ESCAPE to another key |
| `&E5` (229) | R/W ESCAPE key status | Treat ESCAPE as plain ASCII |
| `&E6` (230) | R/W ESCAPE effects flag | Lighter `&7E` that only clears the flag |

## OSBYTE `&C8` — disable / BREAK control

Packs two unrelated things:

```
bit 0: 0 = ESCAPE works,  1 = ESCAPE disabled (only OSBYTE &7D can set it)
bit 1-7: 0 = preserve memory on BREAK,  non-zero = clear memory on BREAK
```

| `*FX 200,n` | Effect |
|---|---|
| `n=0` | Normal (default) |
| `n=1` | ESCAPE disabled, memory preserved |
| `n=2` | ESCAPE works, memory cleared on BREAK |
| `n=3` | ESCAPE disabled, memory cleared on BREAK |

`*FX 200,1` is the canonical "game launcher" setting — survives soft BREAK with memory intact, ESCAPE doesn't kill your game.

## What `OSBYTE &7E` tears down

When `OSBYTE &E6` flag = 0 (default), acknowledging ESCAPE (`OSBYTE &7E`) also:

- Closes any open `*EXEC` file.
- **Purges all buffers** (input + output, sound, printer, RS423).
- Resets VDU paging counter (lines since last halt).
- Clears the VDU queue (`&323`).
- Cancels any current soft-key expansion.
- Stops any sound currently playing.

That's a lot. Set `OSBYTE &E6, X=&FF` to make `&7E` only clear the condition without touching anything else.

## Patterns

### Game — disable ESCAPE completely

```asm
LDA #&C8 : LDX #1 : LDY #0 : JSR &FFF4    ; ESCAPE disabled
```

Or treat ESCAPE as plain ASCII (so it enters the buffer but doesn't abort):

```asm
LDA #&E5 : LDX #&FF : LDY #0 : JSR &FFF4
```

The user can still press it; it just doesn't cause an abort. Read it from the key buffer like any other key.

### Game — handle ESCAPE manually

Hook **event 6** ([[os/events]]):

```asm
LDA #&0E : LDX #6 : JSR &FFF4         ; enable event 6
LDA #handler MOD 256 : STA &220       ; install EVNTV
LDA #handler DIV 256 : STA &221
```

In the handler: set a flag, return. The main loop checks the flag and does what you want (pause, quit-to-menu, etc.). Then call `OSBYTE &7E` to acknowledge cleanly.

### Remap ESCAPE to a different key

```asm
LDA #&DC : LDX #ASC"Q" : LDY #0 : JSR &FFF4    ; ESCAPE is now 'Q'
```

Or to make TAB the ESCAPE key:

```asm
LDA #&DC : LDX #9 : LDY #0 : JSR &FFF4         ; ESCAPE is now TAB (ASCII 9)
```

### Light acknowledge (preserve sound/buffers)

```asm
LDA #&E6 : LDX #&FF : LDY #0 : JSR &FFF4   ; disable side effects of &7E
LDA #&7E : JSR &FFF4                       ; clear condition only
LDA #&E6 : LDX #0 : LDY #0 : JSR &FFF4     ; restore default for next time
```

## See also

- [[os/osbyte]] — All ESCAPE-related entries (`&7C-&7E`, `&C8`, `&DC`, `&E5`, `&E6`).
- [[os/events]] — Event 6 = ESCAPE detected.
- [[os/brk]] — BREAK is a different thing (direct reset line).
- [[os/keyboard]] — TAB / ESCAPE character defaults.
- [[os/errors]] — error 17 (`Escape`) is what BRKV sees when the MOS auto-converts an ESCAPE flag to a BRK.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
