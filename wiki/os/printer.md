---
title: Printer Driver
type: os
tags: [printer, uptv, osbyte]
sources: [naug-ch24-misc]
updated: 2026-05-13
---

# Printer Driver

MOS-level printer interface and how to hook a custom printer driver via **UPTV** (`&222`).

## Selecting the printer

`OSBYTE &05` chooses the destination:

| X | Destination |
|---|---|
| 0 | Sink (output ignored) |
| 1 | Parallel port (default on BBC) |
| 2 | RS423 (Acorn serial) |
| 3 | User printer routine (UPTV) |
| 4 | Net printer (via NETV) |
| 5-255 | User-defined |

`*FX 5,X` is the user form. The setting **survives soft BREAK**.

## Ignore character

`OSBYTE &06` / `OSBYTE &F6` set/read a character that's dropped from print output. Default `&0A` (LF) — many printers do their own LF after CR, so dropping it prevents double-spacing.

`OSBYTE &B6` (Master only) toggles whether the ignore is in effect at all.

## UPTV — user print vector (`&222`)

Hook this to implement a custom printer driver:

```asm
LDA &222 : STA old_uptv       ; save the chain
LDA &223 : STA old_uptv+1
LDA #my_uptv MOD 256 : STA &222
LDA #my_uptv DIV 256 : STA &223
```

MOS calls your hook via UPTV in several scenarios. **A = reason code**:

| A | When | Action |
|---|---|---|
| 0 | Every 10 ms while driver is active | Pull next byte from printer buffer (ID 3) via REMV; send to hardware. When buffer empty, declare dormant via `OSBYTE &7B`. |
| 1 | Buffer became non-empty while dormant | Activate. Return C=0 if you've activated; pull a byte and send. |
| 2 | `VDU 2` received | Printer-on signal (note: characters may still arrive without VDU 2 depending on `*FX 3`) |
| 3 | `VDU 3` received | Printer-off signal |
| 5 | New printer selected via `OSBYTE &5` | Update internal state |

X = printer buffer ID (always 3). Y = printer number (the `*FX 5` value) — **only respond if Y matches your printer number**.

Standard hook:

```asm
.my_uptv
    CPY #my_printer_num    ; my printer ID (e.g. 3, 7, etc.)
    BEQ handle
    JMP (old_uptv)         ; not for us, chain on

.handle
    PHA                    ; save reason code
    PHX : PHY
    ; ... process based on A reason code ...
    PLY : PLX
    PLA
    RTS
```

## Declare dormant — `OSBYTE &7B`

When your buffer is empty, tell MOS to stop polling you:

```asm
LDA #&7B : LDX #3 : JSR &FFF4    ; printer driver going dormant
```

MOS will resume calls (reason A=1) when the buffer gets a byte again.

## Pulling bytes — REMV (`&22C`)

Inside your A=0 / A=1 handler, use [[os/buffers]] REMV to pull bytes from the printer buffer (ID 3):

```asm
LDX #3                 ; buffer ID
CLV                    ; V=0 means remove (V=1 = examine only)
JSR remv_chain         ; or JMP (&22C) in chain handlers
; Y = byte; C=1 if buffer was empty
```

## Useful patterns

### Serial-attached printer

Already supported via `*FX 5,2` (RS423 output). No UPTV hook needed.

### Custom hardware printer (e.g. serial DAC for sound)

Use UPTV reason 0 to pull bytes from the printer buffer at 100 Hz and send them as needed. Effectively turns the printer buffer into a 64-byte queue serviced every 10 ms.

### Network printer (NETV path)

Already supported via `*FX 5,4`. NETV reason codes 0/1/2/3/5 mirror UPTV.

## Performance notes

- Printer buffer is **64 bytes by default**. Filled by OSWRCH when output goes to printer.
- The custom-buffer pattern (NAUG §9.4 worked example, [[os/buffers]]) extends the printer buffer to many KB by intercepting INSV/REMV/CNPV for buffer ID 3.
- For high-throughput output to a fast printer / serial-attached peripheral, use the OSBYTE / UPTV path rather than direct STA to the printer port — the buffered/IRQ-driven path lets the foreground task do other work.

## See also

- [[os/buffers]] — Printer buffer (ID 3); INSV/REMV/CNPV vectors.
- [[hardware/user-via]] — Parallel printer port (Port A + CA1/CA2).
- [[os/osbyte]] — `&05`, `&06`, `&7B`, `&F5`, `&F6` printer entries.
- [[sources/naug-ch24-misc]] — Full source page.
