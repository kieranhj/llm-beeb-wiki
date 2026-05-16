---
title: Events
type: os
tags: [events, evntv, oseven, vsync]
sources: [naug-ch07-events]
updated: 2026-05-13
---

# Events — MOS Callback Layer

Events are a thin MOS wrapper over the IRQ chain ([[os/interrupts]]). Enable an event with `OSBYTE &0E,n`; MOS calls your handler at **EVNTV** (`&220`) whenever event `n` fires, with the event number in A. Disable with `OSBYTE &0D,n`.

Compared to hooking IRQ1V/IRQ2V directly:

| | Events | IRQ vectors |
|---|---|---|
| Setup | one OSBYTE | save + replace vector, manage chain |
| Latency | ~50-200 cycles MOS dispatch + your code | ~30-50 cycles from CPU IRQ |
| Per-event filtering | MOS dispatches `A`-based | you test IFR bits yourself |
| Cycle budget | <2 ms (NAUG §7.1) | <2 ms |
| Tube-safe | yes | yes |

Use events for "callback when X happens" plumbing. Use IRQ hooks for cycle-tight raster work.

## Event table

| # | Cause | Entry data |
|---|---|---|
| 0 | Output buffer empty | X = buffer ID |
| 1 | Input buffer full | X = buffer ID, Y = char that couldn't fit |
| 2 | Character entering input buffer | Y = ASCII char |
| 3 | ADC conversion complete | X = channel |
| 4 | Vertical sync (50 Hz) | — |
| 5 | Interval timer crossed zero | — |
| 6 | ESCAPE condition | — |
| 7 | RS423 error | X = 6850 status >> 1, Y = received char |
| 8 | Econet event | — |
| 9 | User event | Y = number passed to OSEVEN |

## Handler conventions

1. **Don't enable interrupts.** MOS is already inside its IRQ — CLI would let a nested interrupt corrupt zp `&FC` and the vector chain.
2. **<2 ms total.** The 100 Hz timer ([[os/interrupts]]) needs to run on schedule.
3. **Preserve all registers** (PHP/PHA/TXA/PHA/TYA/PHA on entry; reverse on exit).
4. **Chain through old EVNTV** if you want lower-priority handlers to also run. Save the previous `&220/&221` before installing your own; the last `RTS` should be a `JMP (old_evntv)` if chaining.

Standard handler skeleton:

```asm
.my_event
    PHP : PHA           ; save state
    TXA : PHA
    TYA : PHA
    ; A = event number; X/Y = event-specific
    CMP #4              ; vsync only?
    BNE chain
    JSR do_vsync_work
.chain
    PLA : TAY
    PLA : TAX
    PLA : PLP
    JMP (old_evntv)     ; or RTS if you're the only handler
```

## Installing

```asm
SEI
LDA &220 : STA old_evntv      ; save chain target
LDA &221 : STA old_evntv+1
LDA #my_event MOD 256 : STA &220
LDA #my_event DIV 256 : STA &221
CLI
LDA #&0E : LDX #event_num : JSR &FFF4   ; enable
```

To uninstall: disable the event (`OSBYTE &0D`), then SEI / restore `&220-&221` / CLI.

## OSEVEN — generate a user event

`JSR &FFBF` with Y = event number. Generally used with event 9 (user event) but can synthetically fire any event. C=0 on return iff that event was enabled (and thus dispatched). Not available across the Tube.

## Event 4 vs IRQ-hook vsync

For frame-synced work where 50 Hz latency is fine:

- **Event 4** is one OSBYTE to enable and one EVNTV install. MOS's IRQ has already cleared the CA1 flag for you. Your handler just runs.
- **IRQ1V/IRQ2V** + System VIA CA1 ([[hardware/system-via]]): a few cycles faster to start, and you can preempt MOS's flash-colour swap if you want to. You must clear the IFR yourself (`BIT &FE41`).

For raster-rate work *within* a frame (timing splits to a specific scan line), neither — use the User VIA T1 timer ([[timing/via-timers]]).

## Event enable flags in memory

The enable mask is stored in OS workspace around `&2BD-&2BE` on Model B ([[memory/os-workspace]]). Reading the byte directly is faster than `OSBYTE &0E`/`&0D`. **Don't write directly** — the OSBYTE also re-evaluates VIA IRQ enables for some events (e.g. ADC, light pen).

## See also

- [[os/interrupts]] — IRQ chain (events ride on top).
- [[os/buffers]] — buffer events (0, 1, 2) require buffer activity.
- [[hardware/system-via]] — CA1 vsync, CB1 ADC, the source of events 3 and 4.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
