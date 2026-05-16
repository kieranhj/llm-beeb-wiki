---
title: NAUG Ch24 — Miscellaneous
type: source
parent: [[sources/naug]]
pages: 426-438
section: §24
tags: [break, reset, printer, code, line, netv, keyv, machine-id]
updated: 2026-05-13
---

# NAUG Ch24 — Miscellaneous

Holmes & Dickens, *The New Advanced User Guide*, pp.426-438. Catch-all chapter — BREAK / reset handling, printer driver vector, `*CODE` / `*LINE`, OS / machine identification, NETV, KEYV.

## Key topics captured

### BREAK / reset

Three reset types:

| Type | Trigger | OSBYTE `&FD` returns |
|---|---|---|
| Soft BREAK | BREAK key alone | 0 |
| Power-on reset | Power-up; or programmatically by masking System VIA IRQs (write `&7F` to `&FE4E`) then forcing reset | 1 |
| Hard BREAK | CTRL + BREAK | 2 |

### BREAK intercept — `OSBYTE &F7/&F8/&F9`

The single most useful pattern in this chapter: install a **JMP instruction** at a 3-byte intercept slot that MOS calls during every reset.

The slot is normally `00 00 00` (no intercept). The user installs:

```
&F7  : opcode &4C (JMP)
&F8  : low byte of handler
&F9  : high byte of handler
```

MOS calls the JMP **twice per BREAK**:

1. First call: **C=0**, before the reset message is printed and before Tube initialisation.
2. Second call: **C=1**, after the message + Tube init.

The first call lets you reset the OS's idea of state (your custom mode, hooked vectors, etc.) before the user sees the boot banner. The second is for fixup after MOS has finished its own reset sequence.

To install, use `OSBYTE &F7/&F8/&F9` (each writes one byte of the JMP, plus reads the next byte via the standard `<NEW>=(<OLD> AND Y) EOR X` pattern):

```asm
LDA #&F7 : LDX #&4C        : LDY #0 : JSR &FFF4    ; JMP opcode
LDA #&F8 : LDX #handler MOD 256 : LDY #0 : JSR &FFF4
LDA #&F9 : LDX #handler DIV 256 : LDY #0 : JSR &FFF4
```

Handler skeleton:

```asm
.my_break_handler
    BCC first_call          ; C=0 = pre-message/Tube
    ; C=1 = post-message: re-install hooks etc.
    ; ... your re-init code ...
.first_call
    ; ... pre-MOS-reset work ...
    JMP (saved_break_vector)   ; chain to whatever was here before
```

### Other reset OSBYTEs

| OSBYTE | Function |
|---|---|
| `&C8` (200) | ESCAPE-disable + BREAK-clears-memory flags (see [[os/escape]]) |
| `&D7` (215) | R/W startup message suppression flag (bit 7) + boot-error behaviour (bit 0) |
| `&FD` (253) | R/W last-BREAK type (0/1/2) |
| `&FF` (255) | R/W start-up options byte — Model B keyboard links, or any machine via `*FX` |

#### `OSBYTE &FF` startup byte

On Model B set by 8 PCB links; on Electron / Master programmable via `*FX 255,n`:

| Bits | Function |
|---|---|
| 0-2 | Screen mode at reset |
| 3 | If clear, reverse SHIFT+BREAK action |
| 4-5 | Disc drive timings (per FDC type) |
| 6 | Reserved |
| 7 | 0 = NFS at boot, 1 = DFS at boot |

### Printer driver

`*FX 5,X` selects the printer:

| X | Destination |
|---|---|
| 0 | Sink (output ignored) |
| 1 | Parallel port (default on BBC) |
| 2 | RS423 (acts as sink if RS423 is also output) |
| 3 | User printer routine (via UPTV `&222`) |
| 4 | Net printer |
| 5-255 | User-defined printer routines |

`*FX 5` is **not reset by soft BREAK** — survives unless explicitly changed.

### UPTV — user print vector (`&222`)

Custom printer drivers hook this. MOS calls UPTV every 10 ms (when active) plus on `VDU 2`/`VDU 3`/`*FX 5` events:

| A | Reason |
|---|---|
| 0 | 10 ms tick — pull byte from printer buffer via REMV ([[os/buffers]]); declare dormant via `OSBYTE &7B` when buffer empty |
| 1 | Printer buffer non-empty — driver should activate; return C=0 if activated |
| 2 | `VDU 2` received |
| 3 | `VDU 3` received |
| 5 | New printer selected via `OSBYTE &5` |

On entry: X = printer buffer ID (3), Y = printer number from `*FX 5`.

The driver should respond only to its own printer number.

### Ignore character

`OSBYTE &06` / `&F6` (R/W) sets a character to drop from print output. Default `&0A` (LF) — many printers do their own LF on CR. `OSBYTE &B6` (Master) enables/disables the ignore (bit 7).

### `*CODE` and `*LINE`

Both run user-supplied machine code via **USERV** (`&200`):

| Command | Entry to USERV |
|---|---|
| `*CODE x,y` | A=0, X=x, Y=y |
| `*LINE <text>` | A=1, X=low byte of text address, Y=high byte |

`*CODE` is two single-byte arguments; `*LINE` is a string. Both are tagged with `A` so a single USERV handler can serve both. Default USERV produces "Bad Command". Replace by writing to `&200/&201`:

```asm
LDA #my_handler MOD 256 : STA &200
LDA #my_handler DIV 256 : STA &201
```

### Machine / OS identification

| OSBYTE | Returns | Notes |
|---|---|---|
| `&00` (0) | OS version (X=0 → BRK with text, X≠0 → X = version code 0-5) | 0=OS 1.0, 1=OS 1.2/US, 2=OS 2.0 (B+), 3=OS 3.2/3.5 (Master), 4=Master Econet Term, 5=OS 5.0 (Compact) |
| `&81` (129) | Machine type (X=0, Y=&FF) | Many variants, see table below |
| `&F0` (240) | Country code | 0=UK, 1=US |

`OSBYTE &81` machine codes:

| X | Machine |
|---|---|
| 0 | BBC OS 0.10 |
| 1 | Electron OS 1.0 |
| `&FF` | BBC OS 1.00 / 1.20 |
| `&FE` | BBC OS A1.0 (USA) |
| `&FD` | Master 128 OS 3.20 / 3.50 |
| `&FC` | BBC OS 1.20 West Germany |
| `&FB` | B+ OS 2.00 |
| `&FA` | Acorn Business Computer OS 1.00 / 2.00 |
| `&F7` | Master Econet Terminal OS 4.00 |
| `&F5` | Master Compact OS 5.10 |

### NETV — Econet vector (`&224`)

Used for net printer control (A=0,1,2,3,5) **and** for vetoing OS calls on networked machines:

| A | When called | Effect on exit |
|---|---|---|
| 4 | OSWRCH attempted (if OSBYTE `&D0` enabled) | C set = block character |
| 6 | OSRDCH attempted (if OSBYTE `&CF` enabled) | A on exit = character read |
| 7 | OSBYTE attempted (if `&CE` enabled). A/X/Y at `&EF/&F0/&F1` | V set = block call |
| 8 | OSWORD attempted (if `&CE` enabled). A/X/Y at `&EF/&F0/&F1` | V set = block call |
| 13 | Line entered (OSWORD 0 complete) | NFS can take over input now |

For non-networked use, NETV can act as a generic "veto every OS call" hook — useful for protected/sandboxed environments.

### KEYV — keyboard control vector (`&228`)

Called whenever the keyboard is accessed:

| C | V | Function |
|---|---|---|
| 0 | 0 | Test SHIFT + CTRL — N flag set if CTRL pressed, V flag set if SHIFT pressed |
| 1 | 0 | Full keyboard scan (= `OSBYTE &79`) — A = X on exit |
| 0 | 1 | Key-press IRQ entry — System VIA CA2 |
| 1 | 1 | Timer IRQ entry — 100 Hz auto-repeat + two-key rollover |

Hooking KEYV lets you intercept all keyboard activity at a low level — useful for keyboard-rebinding ROMs or chord-key handlers.

### Misc user flag

| OSBYTE | Function |
|---|---|
| `&01` (1) | Set user flag (X = new value) |
| `&F1` (241) | R/W user flag |

One byte of OS workspace reserved for user code's own use. Default 0.

## Filed into

- [[os/break-intercept]] — BREAK / reset detection + the `&F7-&F9` intercept pattern (closes the stub referenced from many other pages).
- [[os/printer]] — UPTV + printer destination + ignore character (new).
- Updates: [[os/osbyte]] — many entries linked.
- Updates: [[os/calls]] — NETV, KEYV cross-links.

## Open follow-ups

- **Disc drive timings** in `OSBYTE &FF` bits 4-5 — covered briefly per-FDC; if writing copy-protection or non-standard formats, the per-1770/8271/1772 settling/step times matter.
- **Master Compact joystick byte 18** — referenced but not enumerated; pull from Master Compact reference manual if anyone targets that platform.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
