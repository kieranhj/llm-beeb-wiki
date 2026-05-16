---
title: NAUG Ch22 — User/Printer & System VIAs
type: source
parent: [[sources/naug]]
pages: 387-408
section: §22
tags: [via, 6522, system-via, user-via, timers, ifr, ier]
updated: 2026-05-13
---

# NAUG Ch22 — User/Printer & System VIAs

Holmes & Dickens, *The New Advanced User Guide*, pp.387-408. Two Rockwell 6522 VIAs (Versatile Interface Adapters):

- **System VIA** @ SHEILA `&FE40-&FE4F` — owned by MOS. Drives keyboard, sound, speech, CMOS (Master), joystick fire, ADC EOC, light pen strobe, vsync IRQ, hardware-scroll wrap latch, CAPS/SHIFT LEDs.
- **User/Printer VIA** @ SHEILA `&FE60-&FE6F` — Port A = parallel printer (output-only, buffered), Port B + CB1/CB2 = user port (general-purpose I/O).

Both chips have the same 16-register map (§22.4 p387 — see [[hardware/via-6522]]). Both have two 16-bit 1 MHz timers (T1, T2) and a shift register.

## Key facts captured

- Register block repeats every 16 bytes at the base address. Register numbers are 0-15 (see [[hardware/via-6522]] for the canonical table).
- **Timers decrement at 1 MHz**, not the 2 MHz CPU clock (§22.4.3 p391). T1 timeout = `(N+2) × 1 µs` where `N` is the loaded value.
- **Slow peripheral bus** (System VIA Port A): CPU writes only via System VIA with all interrupts disabled — MOS uses this constantly for keyboard scan etc. (§22.3.1 p384). Direct access strongly discouraged.
- **System VIA addressable latch** (PB0-PB3 of System VIA) is the gateway to 8 different peripheral functions, including the **hardware-scroll wrap addend** (B4, B5) referenced by [[video/hardware-scrolling]]. Full assignment in [[hardware/system-via]].
- **Vsync interrupt** = System VIA CA1 (PCR programmed for negative edge by MOS). IFR bit 1. Fires every 20 ms.
- **Keyboard interrupt** = System VIA CA2. IFR bit 0.
- **Light pen strobe** = System VIA CB2. IFR bit 3.
- **ADC end-of-conversion** = System VIA CB1. IFR bit 4.
- **PB4, PB5** = joystick fire buttons (active low).
- **PB6, PB7** = speech I/F on Model B / B+; CMOS RAM chip enable / address strobe on Master.

## IFR / IER bit map (both VIAs)

| Bit | Source | Cleared by |
|---|---|---|
| 0 | CA2 active edge | R/W reg 1 (ORA) — except in independent-interrupt mode, then only by writing 1 into IFR |
| 1 | CA1 active edge | R/W reg 1 (ORA) |
| 2 | Shift register 8 bits shifted | R/W shift register |
| 3 | CB2 active edge | R/W reg 0 (ORB) — same caveat as CA2 |
| 4 | CB1 active edge | R/W reg 0 (ORB) |
| 5 | T2 timeout | Read T2-L or write T2-H |
| 6 | T1 timeout | Read T1-L or read T1-H |
| 7 | Any enabled interrupt | Clear all flags (not directly) |

IER write protocol (§22.4.11 p401):
- `bit 7 = 0`: each `1` in bits 0-6 *clears* that enable
- `bit 7 = 1`: each `1` in bits 0-6 *sets* that enable

So `STA &FE4E` with `&xx` where bit 7 is the set/clear selector, bits 0-6 are the bits to act on. This is unusual — don't confuse with normal bit-set semantics.

## Filed into

- [[hardware/via-6522]] — Generic 6522 entity: register map, port semantics, PCR/ACR/IFR/IER bit layout.
- [[hardware/system-via]] — System VIA specifics: line assignments, addressable latch table, IRQ uses.
- [[hardware/user-via]] — User/Printer VIA: printer pinout, user port pinout, handshake usage.
- [[timing/via-timers]] — T1 (one-shot/free-run/PB7 toggle) and T2 (interval/pulse-count) modes. Use cases for raster timing, audio, etc.

## Open follow-ups

- Joystick read protocol via System VIA — referenced as `OSBYTE &80` (§22.3.1 p385) but full call form not in this chapter. Capture when Ch20 ADC is ingested.
- Shift register modes 0-7 (§22.4.10 p397-400) summarised — full timing diagrams need re-reading if anyone needs serial-style use.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
