---
title: NAUG Ch7 — Events
type: source
parent: [[sources/naug]]
pages: 126-130
section: §7
tags: [events, evntv, oseven, irq]
updated: 2026-05-13
---

# NAUG Ch7 — Events

Holmes & Dickens, *The New Advanced User Guide*, pp.126-130. The **event** system is MOS's user-facing wrapper over a subset of IRQs — gets you a "callback when X happens" without writing a full IRQ handler.

## Key facts captured

- **EVNTV** at `&220/&221` — called by MOS's IRQ routine for each enabled event.
- 10 event types (0-9), enumerated below.
- `A` = event number on entry to EVNTV. `X`/`Y` = event-specific data.
- **Handler constraints**: don't enable IRQs, finish in <2 ms, preserve all registers, chain through old vector.
- `OSBYTE &0E` (`*FX 14,n`) — enable event `n`.
- `OSBYTE &0D` (`*FX 13,n`) — disable event `n`. Returns old enable state in X (0=disabled).
- `OSEVEN` (`&FFBF`) — generate a user event. Y = event number. Not available across Tube. C=0 on exit iff the event was enabled.
- Event enable flags stored at `&2BD-`onwards in page 2 ([[memory/os-workspace]]). Reading directly is faster than OSBYTE.

## Event table (NAUG §7.1 p119)

| # | Cause | Entry data |
|---|---|---|
| 0 | Output buffer empty | X = buffer number |
| 1 | Input buffer full | X = buffer number, Y = char value that couldn't be inserted |
| 2 | Character entering input buffer | Y = ASCII char (note: independent of input stream — fires for any incoming char) |
| 3 | ADC conversion complete | X = channel number |
| 4 | **Start of vsync** | — (50 Hz on UK BBC) |
| 5 | Interval timer crossed zero | — (timer set via OSWORD `&04`) |
| 6 | ESCAPE condition detected | — |
| 7 | RS423 error | X = 6850 status byte shifted right 1, Y = char received |
| 8 | Econet | — (or user use if no net hardware) |
| 9 | User event | Y = event number on call to OSEVEN |

## Event 4 — vsync

The cheapest "fire every frame" hook. Compared to hooking IRQ1V directly:

- **Event 4 path**: cheap to enable (`*FX 14,4`), runs inside MOS IRQ at ~50 Hz, your handler sits at EVNTV.
- **IRQ1V/IRQ2V path**: lower latency, you test System VIA CA1 bit yourself, can do raster-rate work. See [[os/interrupts]].

Event 4 is the lazy/safe option; IRQ hooking is the performance option. The handler-runtime constraint is the same either way (< 2 ms).

## Filed into

- [[os/events]] — Master events reference + handler patterns.
- Updates: [[os/interrupts]] cross-links to events as the "easier than IRQ hooking" alternative.

## Open follow-ups

- Exact `&2BD-`onwards layout for event enable flags (Master differs from Model B) — [[memory/os-workspace]] has the rough range; precise addresses would need MOS disassembly confirmation.
