---
title: CMOS RTC (146818 — Master only)
type: hardware
tags: [cmos, rtc, 146818, master-specific, battery-backed]
sources: [naug-ch19-clocks-cmos]
machines: [Master 128]
updated: 2026-05-13
---

# Motorola 146818 CMOS RTC (Master 128)

Battery-backed real-time clock + 50 bytes of CMOS RAM. **Master 128 only** — replaces the speech processor's socket from the Model B / B+.

- Master Compact: no RTC chip; has an EEPROM (128 or 256 bytes) for config but no time-keeping.
- Model B, B+, Electron: no RTC at all.

The chip is **not directly memory-mapped** — it sits on the System VIA's slow peripheral bus ([[hardware/system-via]]), accessed via Port A + addressable-latch lines (PB6 = chip enable, PB7 = address strobe).

## Address space (64 bytes)

| Addr | Function |
|---|---|
| 0 | Seconds |
| 1 | Seconds alarm |
| 2 | Minutes |
| 3 | Minutes alarm |
| 4 | Hours |
| 5 | Hours alarm |
| 6 | Day of week (1-7, Sunday=1) |
| 7 | Day of month |
| 8 | Month |
| 9 | Year |
| 10 | Register A (UIP, divider, periodic IRQ rate) |
| 11 | Register B (SET, PIE, AIE, UIE, SQWE, DM, 24/12, DSE) |
| 12 | Register C (IRQF, PF, AF, UF — read-only, **clear on read**) |
| 13 | Register D (VRT) |
| 14-63 | **50 bytes of user CMOS RAM** |

Time fields are **BCD or binary** depending on the `DM` bit (Register B). MOS uses BCD by default (so `21` is stored as `&21`, not `&15`).

## MOS access (recommended)

| OSBYTE | Function | Notes |
|---|---|---|
| `&A1` (161) | Read CMOS byte | X = address (0-49 of the 50 user bytes) |
| `&A2` (162) | Write CMOS byte | X = address, Y = value |

These OSBYTEs handle the slow-bus dance for you. The 50 RAM bytes are mapped to OSBYTE addresses 0-49 (MOS hides the time registers from this path — use OSWORD `&0E`/`&0F` for time).

OSWORDs `&0E` / `&0F` handle the time/date read/write end:

| OSWORD | Function |
|---|---|
| `&0E` | Read RTC (string, BCD, or BCD→string conversion modes) |
| `&0F` | Write RTC (time only, date only, or both) |

See [[os/clocks]] for full parameter blocks.

## Master CMOS layout (50 user bytes)

These are configuration storage — the MOS reads them at boot to set up defaults. Don't trample without thinking:

| Addr | Function |
|---|---|
| 0-4 | Econet station numbers (own, FS, PFS) |
| 5 | Default FS + language ROM numbers (4 bits each) |
| 6, 7 | ROM-installed bitmaps (slot 0-7 in byte 6, 8-15 in byte 7) |
| 8 | EDIT ROM workspace |
| 9 | Telecom reserved |
| 10 | Default MODE + shadow + interlace + *TV |
| 11 | FDRIVE + CAPS-lock behaviour + dir-load + default-drive |
| 12-13 | Keyboard auto-repeat delay + rate |
| 14 | Printer ignore character |
| 15 | Tube + baud rate + *FX5 |
| 16 | BEEP loudness + Tube int/ext + scrolling + boot + serial format |
| 17 | ANFS settings |
| 18 | Compact joystick settings |
| 19 | Reserved |
| 20-29 | Reserved (Acorn future) |
| 30-45 | Per-ROM private (16 ROMs × 1 byte) |
| **46-49** | **User applications** — safe for arbitrary storage |

Use `*CONFIGURE` and `*STATUS` to manipulate these from the command line — they're the supported abstraction. Direct OSBYTE writes to addresses 0-45 should track what they break.

## Register A — control (`&0A`)

| Bit | Field |
|---|---|
| 7 | UIP — update in progress (read-only, ≠0 means time data unstable for ~244 µs) |
| 6-4 | Divider control (DV2 DV1 DV0). Must be `0 1 0`. |
| 3-0 | RS3 RS2 RS1 RS0 — periodic IRQ rate select |

Periodic IRQ rates (when PIE = 1 in Register B):

| RS3-0 | Rate |
|---|---|
| `0000` | Off |
| `0001` | 3.906 ms |
| `0010` | 7.8125 ms |
| `0011` | 122.07 µs |
| ... | ... |
| `1111` | 500 ms |

Full table in [[sources/naug-ch19-clocks-cmos]] §19.6 p361.

## Register B — IRQ enables (`&0B`)

| Bit | Field |
|---|---|
| 7 | SET — 1 = freeze clock for writing |
| 6 | PIE — periodic IRQ enable |
| 5 | AIE — alarm IRQ enable |
| 4 | UIE — update-ended IRQ enable |
| 3 | SQWE — square-wave output (not used in Master) |
| 2 | DM — 0 = BCD, 1 = binary |
| 1 | 24/12 — 0 = 12-hour mode, 1 = 24-hour |
| 0 | DSE — daylight saving enable |

## Register C — IRQ flags (`&0C`, read-only, clear-on-read)

| Bit | Field |
|---|---|
| 7 | IRQF — any of PF/AF/UF AND their enable is set |
| 6 | PF — periodic fired |
| 5 | AF — alarm fired |
| 4 | UF — update-ended fired |

**Critical**: reading Register C **clears all four flags**. The IRQ handler must:

1. Read `&0C`.
2. Test the bit it cares about (e.g. AND with `&20` for AF).
3. Branch accordingly.

If you read C twice without acting, the second read sees 0 — the IRQ source is lost.

## Three interrupt sources

The 146818 can fire IRQs on:

- **Alarm match** (AIE): seconds/minutes/hours alarm registers equal current time. Each alarm byte can be set to `&FF` for "don't care" — `&FF`/`&FF`/X = "fire every hour at minute=any, second=any" (i.e. every second).
- **Periodic** (PIE): fires at a rate from 122 µs to 500 ms (rate bits in Register A).
- **Update-ended** (UIE): fires after each ~1.984 ms time update.

## Master link LK4 — IRQ enable

By default, **the RTC's IRQ output is not connected** to the 65C12. To get any RTC interrupt, you must close **link LK4** on the Master mainboard. Out-of-the-box Master machines have it open; users opening the case to install an upgrade often do this.

Without LK4, AIE/PIE/UIE can be set all you want but nothing reaches the CPU.

## Direct chip access pattern

For features MOS doesn't expose (alarm IRQ setup, periodic IRQ), you must drive the slow-bus dance directly. Pattern (from §19.6 p362-364):

```asm
; Read CMOS register X (carry=1) or write (carry=0, Y=value)
.cmosaccess
    PHP
    SEI                      ; own the slow bus
    BCC .write
.read
    JSR .address
    LDA #&49 : STA &FE40     ; latch line for "read" mode
    STZ &FE43                ; DDRA = input
    LDA #&4A : STA &FE40     ; DS active
    LDY &FE4F                ; slow-bus = Y
    BRA .finish
.write
    JSR .address
    LDA #&41 : STA &FE40     ; latch line for "write" mode
    LDA #&4A : STA &FE40     ; DS active
    STY &FE4F                ; output Y onto slow-bus
.finish
    LDA #&42 : STA &FE40     ; deactivate DS
    LDA #&02 : STA &FE40     ; deactivate CE
    PLP
    RTS

.address
    LDA #&02   : STA &FE40   ; CE + DS inactive
    LDA #&82   : STA &FE40   ; AS active
    LDA #&FF   : STA &FE43   ; DDRA = output
    STX &FE4F                ; address on slow-bus
    LDA #&C2   : STA &FE40   ; CE active
    LDA #&42   : STA &FE40   ; strobe AS low
    RTS
```

Combined with hooking IRQ2V (because CMOS RTC IRQs come through the normal IRQ path), you can use the RTC's alarm/periodic IRQ for any task — wake at a specific time of day, periodic 122 µs ticks for audio, etc. Full worked example in NAUG §19.6 p363.

## Performance considerations

- MOS OSBYTE access (`&A1`/`&A2`) is ~hundreds of cycles per byte (slow-bus dance through OSBYTE dispatch).
- Direct chip access (above) is faster but you take over the slow bus — incompatible with MOS sound, keyboard scan, etc. for the duration.
- For high-frequency periodic IRQ work (e.g. >100 Hz timer), the System VIA T1 ([[timing/via-timers]]) is cheaper and doesn't require the slow bus.
- For day-of-week / date-aware applications, the RTC is unique — System VIA timers don't track wall-clock time across power-off.

## See also

- [[os/clocks]] — OS-level time interface (OSWORDs `&0E`, `&0F`).
- [[hardware/system-via]] — Slow peripheral bus protocol.
- [[memory/shadow-ram]] — Master ACCCON for related architecture.
- [[os/interrupts]] — IRQ dispatch (RTC IRQs come in via System VIA when LK4 is closed).
- [[sources/naug-ch19-clocks-cmos]] — Full worked alarm-IRQ example.
