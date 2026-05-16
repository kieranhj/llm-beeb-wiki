---
title: NAUG Ch8 — Interrupts
type: source
parent: [[sources/naug]]
pages: 131-142
section: §8
tags: [interrupts, irq, nmi, brk, irq1v, irq2v]
updated: 2026-05-13
---

# NAUG Ch8 — Interrupts

Holmes & Dickens, *The New Advanced User Guide*, pp.131-142. Defines the MOS IRQ handling chain, the dispatch order, IRQ bit masks, the BRK protocol, and user-side handler conventions.

## Key facts captured

- **Vectors** (at the top of 6502 address space):
  - NMI: `&FFFA/&FFFB` → routes via `&D00` (NMI RAM) → optionally paged ROM (Econet/DFS).
  - IRQ/BRK: `&FFFE/&FFFF` → MOS IRQ entry. First test: BRK flag in pushed P; if set, divert to BRKV.
- **User intercepts**:
  - `BRKV` at `&202/&203` — invoked for BRK only.
  - `IRQ1V` at `&204/&205` — **high priority**, called before MOS dispatch. Avoid unless absolutely necessary.
  - `IRQ2V` at `&206/&207` — **low priority**, called by MOS after its own dispatch fails to identify the source. **Preferred** for user IRQ work.
- **MOS IRQ poll order** (§8.3 p125-126):
  1. 6850 ACIA (RS423 / cassette) — status @ `&FE08`, bit 7 = "I caused this IRQ".
  2. System VIA (`&FE40`) — IFR @ `&FE4D`, bits 0-6 = sources, bit 7 = any active.
  3. User VIA (`&FE60`) — IFR @ `&FE6D`, same layout.
- **System VIA IRQ sources** (§8.5 p127), matching `&FE4D`:
  | Bit | Source |
  |---|---|
  | 0 | Keyboard (CA2) |
  | 1 | Vsync (CA1) |
  | 2 | Shift register |
  | 3 | Light pen strobe (CB2) — only off-screen pen |
  | 4 | ADC conversion complete (CB1) |
  | 5 | T2 timeout (speech system) |
  | 6 | T1 timeout — **100 Hz centi-second interrupt** |
- **The 100 Hz interrupt** (System VIA T1) drives: TIME update (dual-clock), interval timer (event 5 when expired), INKEY countdown, sound envelope (one centi-second's worth), key-buffer processing, missed-interrupt rescue (speech / 6850 / ADC).
- **Vsync (CA1) does NOT drive TIME** — common misconception. CA1 drives:
  - Flashing colour change (timed against blanking).
  - RS423/cassette 6850 takeover timeout (~0.5 s).
  - Event 4 (V-sync).
- **User VIA**: only CA1 (printer ACK) is MOS-handled. Everything else goes to IRQ2V.

## User handler entry state (§8.7 p130)

When IRQ1V or IRQ2V is jumped to (via the MOS handler):

- Status reg, return address on stack — RTI returns to caller.
- **X and Y are unchanged** from the interrupted code.
- **A is in zero page `&FC`** (MOS has stashed it there before vectoring).
- D flag undefined on NMOS — clear with `CLD` if you use ADC/SBC. (65C12 auto-clears.)

To pass through to the next handler (chain):
```asm
LDA &FC      ; restore A from MOS save
RTI          ; or JMP (saved_vector) to chain
```

Or to chain via a saved IRQ2V:
```asm
LDA &FC
TAX          ; if you need A elsewhere
JMP (old_irq2v)
```

## Re-entrancy rules (§8.7 p130, point (e))

If your handler is long enough that re-enabling IRQs is desirable (e.g. you want to allow keyboard during a long sound update):

1. Push X, Y, and the saved A (`&FC` contents) onto the stack.
2. CLI.
3. Do work.
4. SEI.
5. Pull A back, restore X/Y from stack, restore `&FC`.

Also: **don't use fixed memory locations** for variables; reuse via the stack so the same handler can run inside itself.

## Don't call OS routines from a handler (§8.7 point (d))

OS routines re-enable IRQs and reuse workspace at `&FC` etc. — calling them from within an IRQ handler corrupts the outer call's state. The only safe MOS calls from an IRQ handler are documented as "interrupt-safe" in Ch6 (mostly OSWORDs that explicitly say so — e.g. `OSWORD &0C` palette write).

## IRQ bit masks (the OS shadow copies)

MOS keeps software copies of each chip's enabled-bits mask. Setting a bit in the mask makes MOS *ignore* that source — the IRQ falls through to IRQ2V where user code can handle it. The OSBYTEs use the standard `<NEW>=(<OLD> AND Y) EOR X` protocol:

| OSBYTE | Chip | Default |
|---|---|---|
| `&E7` (231) | User VIA | `&FF` (all unmasked, MOS handles only CA1) |
| `&E8` (232) | 6850 ACIA | `&FF` |
| `&E9` (233) | System VIA | `&FF` |
| `&CB` (203) | Electron ULA | `&0C` |

Note: "ignored by MOS" doesn't mean the IRQ doesn't fire — the chip still raises IRQ, MOS just hands it down the chain. You must clear the source flag in IRQ2V or the CPU will re-enter immediately.

## BRK protocol (§8.13 p132-134)

When BRK is executed:
- A, X, Y unchanged from before BRK.
- Address of the **byte after BRK** is in `&FD/&FE` (zero page pointer).
- MOS issues paged-ROM service call `&06` (BRK offered to ROMs).
- MOS records active ROM number for `OSBYTE &BA`.
- MOS selects the current language ROM.
- Then JMPs via BRKV.

Acorn convention: BRK is followed by:
1. One byte error number.
2. ASCII error message.
3. Zero terminator.

RTI from a BRK handler returns to the **second byte** after BRK (i.e. it jumps over the error number). Most BRK handlers reset SP via TXS and JMP into language reset — they don't return.

Service ROMs generating their own errors: copy a BRK + message into RAM (commonly low page 1) and JMP to it — otherwise the language ROM is paged in for BRK handling and your error message vanishes.

## Critical performance constraint

> "Disabling interrupts for longer than about 2 ms will prevent these background tasks being performed and will have undefined effects." (§8.5 p129)

200 cycles per ms × 2 ms = 400 6502 cycles maximum SEI window before the 100 Hz handler misses a tick. Practical raster effects and sprite drawing should keep SEI windows under ~100 µs (200 cycles); only crash-on-error or unrecoverable critical sections justify longer.

## Filed into

- [[os/interrupts]] — IRQ dispatch chain, user handler conventions, IRQ mask OSBYTEs.
- [[os/brk]] — BRK protocol, error message convention.
- Updates: [[hardware/system-via]], [[hardware/6502]], [[hardware/via-6522]] cross-link to these for handler context.

## Open follow-ups

- NMI handler protocol — referenced (§8.1 + §17.4.1) but Ch17 ingest needed for full picture.
- Event numbering (event 3 ADC, event 4 vsync, event 5 timer, event 7 RS423 error) — Ch7 ingest needed for the event system.
- OS workspace at `&FC` is part of a larger zero-page IRQ-save area (`&FC`-`&FF` and beyond) — pin down on Ch6 ingest.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
