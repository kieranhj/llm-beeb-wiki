---
title: NAUG Ch10 — Escape
type: source
parent: [[sources/naug]]
pages: 154-156
section: §10
tags: [escape, osbyte, brk]
updated: 2026-05-13
---

# NAUG Ch10 — Escape-related calls

Holmes & Dickens, *The New Advanced User Guide*, pp.154-156. Short chapter (3 pages) covering the **ESCAPE condition** — how it's triggered, suppressed, cleared, and what state it tears down.

## ESCAPE in a nutshell

- The ESCAPE key (by default ASCII `&1B`) raises a system-wide ESCAPE condition.
- Most OS routines check the condition between operations and abort if it's set, returning to the calling BASIC program with an "Escape" error.
- Event 6 ([[os/events]]) fires when ESCAPE is detected if event 6 is enabled.
- The condition stays set until explicitly cleared.

## OSBYTE calls

| OSBYTE | Function | Notes |
|---|---|---|
| `&7C` (124) | **Clear ESCAPE condition** (no side effects) | X=&FF returned if a condition existed and was cleared, X=0 if none. Tells Tube if active. |
| `&7D` (125) | **Set ESCAPE condition** (simulate key press) | No event generated. Useful from a service ROM to programmatically abort. |
| `&7E` (126) | **Acknowledge ESCAPE + effects** | Clears condition AND flushes buffers, closes *EXEC, resets VDU paging counter + queue, cancels soft-key expansion, stops any sound. X=&FF if cleared, X=0 if none. |
| `&C8` (200) | R/W escape disable + BREAK action | See bits below. |
| `&DC` (220) | R/W ESCAPE character | Default `&1B` (27). `*FX 220,65` makes 'A' the ESCAPE key. |
| `&E5` (229) | R/W ESCAPE key status | 0 = normal, ≠0 = treat ESCAPE as plain ASCII (no escape event). |
| `&E6` (230) | R/W ESCAPE effects flag | 0 = OSBYTE `&7E` does all the side effects above; ≠0 = `&7E` only clears the condition. |

### OSBYTE `&C8` (200) — escape disable + BREAK action

This OSBYTE packs two unrelated functions:

| Bits | Meaning |
|---|---|
| 0 | 0 = normal ESCAPE; 1 = ESCAPE disabled unless caused by `OSBYTE &7D` |
| 1-7 | 0 = normal BREAK action; non-zero = clear memory on BREAK |

Set with `OSBYTE &C8, X=value, Y=&00` (or via `*FX 200,value`):

- `*FX 200,0` — ESCAPE works, BREAK preserves memory (default).
- `*FX 200,1` — ESCAPE disabled, BREAK preserves memory.
- `*FX 200,2` — ESCAPE works, BREAK clears memory.
- `*FX 200,3` — ESCAPE disabled, BREAK clears memory.

## Practical patterns

### Game-style disable

For games that handle their own input and don't want ESCAPE to abort:

```asm
LDA #&C8 : LDX #1 : LDY #0 : JSR &FFF4    ; disable ESCAPE key
LDA #&E5 : LDX #&FF : LDY #0 : JSR &FFF4  ; treat ESCAPE as plain ASCII
```

Or, less destructively, leave ESCAPE active but trap event 6 ([[os/events]]).

### Custom ESCAPE key

```asm
LDA #&DC : LDX #ASC"Q" : LDY #0 : JSR &FFF4    ; ESCAPE key is now 'Q'
```

### Suppress effects of a programmatic ESCAPE

Sometimes you want ESCAPE to interrupt a long-running thing but not tear down the VDU queue / sound / soft keys:

```asm
LDA #&E6 : LDX #&FF : LDY #0 : JSR &FFF4   ; ESCAPE effects disabled
; ... later ...
LDA #&7E : JSR &FFF4                       ; acknowledge — only clears condition
```

## Side-effects of `OSBYTE &7E` when effects enabled

NAUG §10.7 p149 — when `OSBYTE &E6` flag = 0:

- Any open `*EXEC` file is closed.
- **All buffers purged** (including input buffer).
- VDU paging counter (lines since last halt) reset.
- VDU queue reset.
- Any current soft-key expansion is cleared.
- Any sound being produced is terminated.

When `&E6` flag ≠ 0, only the condition itself is cleared — none of the above.

## Filed into

- [[os/escape]] — Compact escape-handling reference (new page).
- Updates: [[os/osbyte]] entries `&7C/&7D/&7E/&C8/&DC/&E5/&E6` cross-linked.
- Updates: [[os/events]] — event 6 cross-link.

## Open follow-ups

- None — this is a thin chapter; everything captured.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
