---
title: User/Printer VIA
type: hardware
tags: [via, user-via, printer, user-port, gpio]
sources: [naug-ch22-vias]
sheila: ["&FE60", "&FE6F"]
machines: [BBC Model B, BBC B+, Master 128, Master Compact]
updated: 2026-05-13
---

# User/Printer VIA

6522 VIA at SHEILA `&FE60-&FE6F`. Port A drives the **parallel printer port**; Port B + CB1/CB2 form the **user port**. Unlike the System VIA, the MOS leaves this alone unless you're using `*PRINT` — so it's free for user GPIO.

See [[hardware/via-6522]] for register layout. Standard VIA register block.

## Port A — Printer (output only, buffered)

- PA0-PA7 buffered, drive the printer connector D0-D7 lines.
- CA1 = printer ACK input (4K7 pull-up to +5V).
- CA2 = printer STROBE output.

To send a byte: write to ORA `&FE61` (or non-handshake at `&FE6F`); MOS handles the STROBE pulse via PCR mode 101 (pulse output).

Because Port A is buffered for output, you cannot read meaningful values from PA0-PA7 — read accesses to ORA give back whatever was last *written* (or zeros after power-up). Don't try to use Port A as input.

### Printer connector (26-way IDC on B/B+/Master 128)

Pin assignments (NAUG §22.2.1 p381):

```
 1: STROBE        (CA2)
 2: D0            (PA0)
 3-9: D1-D7       (PA1-PA7)
11: ACKNOWLEDGE   (CA1)
13+15+17+19+21+23+25: 0V
```

Master Compact uses a 24-way variant with the same signals.

## Port B — User port (general-purpose I/O)

PB0-PB7 are bidirectional. CB1 and CB2 are control lines exposed on the user port connector. **Sourcing limit: 100 µA on CB1/CB2; 1 mA at 1.5 V on PB outputs** (NAUG §22.1.2 p381).

PB7 can be toggled by T1 (ACR bit 7) — useful for output square waves without CPU involvement.

PB6 can be a pulse-counter input via T2 (ACR bit 5).

### User port connector (20-way IDC)

```
 1: +5V                11: 0V
 2: +5V                12: 0V
 3: CB1                13: 0V
 4: CB2                14: 0V
 5: PB0                15: 0V
 6: PB1                16: 0V
 7: PB2                17: 0V
 8: PB3                18: 0V
 9: PB4                19: 0V
10: PB5                20: PB7  (wait — see note)
```

(NAUG §22.2.2 p382 — diagram is small and OCR-prone; verify against connector pinout before soldering. The actual pinout has PB6, PB7 in there; reread §22.2.2 for the exact 20-pin map.)

Master Compact has a different combined joystick/user-port connector (9-pin variant) with LPSTB also routed.

## Common uses

- **General-purpose I/O**: any 8-bit peripheral attached via the user port. Light pens, sound digitisers, mouse interfaces, joystick adapters (Voltmace etc.), Centronics-to-something adapters.
- **PB7 as audio**: ACR bit 7 + T1 free-run gives a square wave on PB7 with no CPU involvement — output through the user port for one extra audio channel beyond the SN76489.
- **PB6 pulse counting**: T2 in pulse-count mode counts negative-going pulses on PB6 — useful for tachometers, custom mouse interfaces, photogate timing.
- **Mouse**: the AMX Mouse uses CB1/CB2 + PB0-PB3 for quadrature inputs, with one VIA interrupt per mouse-step.

## IRQ uses

The User VIA's IRQ asserts the 6502's IRQ line just like the System VIA — both feed into the shared IRQ line. MOS dispatches via **IRQ1V**: if IFR bit 7 at `&FE4D` (System VIA) is set, MOS handles that source; otherwise the IRQ must be from the User VIA at `&FE6D` (or another chip).

User-handled IRQ pattern:
1. Hook IRQ2V (`&206/&207`) — fires after MOS has cleared its own VIA flags but before RTI.
2. Read `&FE6D` (User VIA IFR). Test bits for your source (CA1, CB1, T1, T2, etc.).
3. Service and clear the relevant flag.

See [[sources/naug-ch08-interrupts]] once ingested for the full IRQ dispatch chain.
