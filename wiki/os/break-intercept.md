---
title: BREAK Intercept & Reset Handling
type: os
tags: [break, reset, intercept, osbyte, startup]
sources: [naug-ch24-misc, bbc-service-manual, beeb-port-kit-hardware-facts, beeb-port-kit-hardware-facts-2026-11]
updated: 2026-11-18
---

# BREAK Intercept & Reset Handling

How to survive — or take over — the BREAK / reset sequence.

## Reset types

| Type | Trigger | `OSBYTE &FD` returns |
|---|---|---|
| Soft BREAK | BREAK key alone | 0 |
| Power-on reset | Power-up; or software-triggered by masking System VIA IRQs (`STA &FE4E` with `&7F`) then forcing reset | 1 |
| Hard BREAK | CTRL + BREAK | 2 |

A **hard BREAK** clears memory and reinitialises everything from scratch (MOS reads the keyboard PCB links / `*FX 255` byte). A **soft BREAK** preserves user memory (`&E00`+) and just re-enters the current language. A **power-on reset** does the most aggressive init.

After any reset, `OSBYTE &FD` returns the type — useful for "skip init the second time" logic.

### How MOS distinguishes cold-start from BREAK at the hardware level

Per [[sources/bbc-service-manual]] §3.1, the BBC's reset circuitry has two paths:

- A **555 timer** (IC16 on a Model B) drives the general `RESET` line, asserted both at power-on and on BREAK.
- A separate **RC network** (C10 + R20 + D1) feeds the System VIA's `RESET A` input on power-up *only* — the time constant is long enough that the BREAK key's reset pulse doesn't trigger it.

Power-on therefore latches an extra interrupt source in the System VIA IFR that BREAK does not. MOS's startup code polls the IFR to set the cold-start / warm-start flag that `OSBYTE &FD` later surfaces. Master 128 / Compact use different reset circuitry (not covered by this manual) but the `OSBYTE &FD` API is preserved across all BBC machines.

You cannot easily "fake" a cold-start from software — the only reliable software path to value `1` is via the documented "mask all System VIA IRQs then jump to `&FFFC` indirect" sequence, which is a brittle hack. Just use `OSBYTE &FD` to read the type and branch.

## OSBYTE `&F7-&F9` — install a BREAK intercept

These three bytes hold a **JMP instruction** that MOS calls during every reset. By default they're `00 00 00` (no JMP, no intercept). They live at **`&0287-&0289`** in page 2 (the OSBYTE-variable formula on [[memory/os-workspace]]; the kit's 1942 and phX entries name the address — [[sources/beeb-port-kit-hardware-facts-2026-11]] §6), so anything a program keeps or copies into page 2 must lay itself around them. Install:

```asm
; Install a JMP to my_handler at &F7-&F9
LDA #&F7 : LDX #&4C : LDY #0 : JSR &FFF4              ; JMP opcode (&4C)
LDA #&F8 : LDX #my_handler MOD 256 : LDY #0 : JSR &FFF4   ; lo byte
LDA #&F9 : LDX #my_handler DIV 256 : LDY #0 : JSR &FFF4   ; hi byte
```

MOS calls your JMP **twice per BREAK**:

1. **First call: C=0** — before the OS startup message, before Tube init.
2. **Second call: C=1** — after the startup message and Tube init.

Handler skeleton:

```asm
.my_break_handler
    BCC .first_call

; ----- second call (C=1) -----
    ; OS message printed, Tube init done.
    ; Re-install your IRQ vectors, custom mode, palette, etc.
    LDA #ivec_lo : STA &204                ; IRQ1V or whatever
    LDA #ivec_hi : STA &205
    ; ... etc ...
    RTS                                    ; or JMP to your reset entry

.first_call
    ; Pre-message work.
    ; Clear pending IRQs, restore default state.
    RTS
```

## Why intercept BREAK

- **Game / demo persistence**: if a user accidentally presses BREAK during your game, re-set up the custom mode + load resume state instead of dropping to BASIC.
- **Protected environments**: a service ROM can re-claim NMI/IRQ vectors that BASIC would otherwise reset.
- **Custom startup**: silent boot directly into your application (set `OSBYTE &D7` bit 7 to suppress the BBC startup message, then your BREAK handler runs into your app entry).

## OSBYTE summary

| OSBYTE | Function |
|---|---|
| `&C8` (200) | R/W escape-disable + BREAK-clears-memory flags |
| `&D7` (215) | R/W startup message + boot-error suppression |
| `&F7` (247) | R/W BREAK intercept byte 0 (JMP opcode = `&4C`) |
| `&F8` (248) | R/W BREAK intercept byte 1 (handler low byte) |
| `&F9` (249) | R/W BREAK intercept byte 2 (handler high byte) |
| `&FD` (253) | Read last-BREAK type (0/1/2) |
| `&FF` (255) | R/W start-up options byte |

### `OSBYTE &C8` — ESCAPE + BREAK behaviour

```
bit 0:   0 = normal ESCAPE,  1 = ESCAPE disabled
bits 1-7: 0 = preserve memory on BREAK,  non-zero = clear memory on BREAK
```

`*FX 200,1` = "ESCAPE disabled, memory preserved on soft BREAK" — the canonical game-launcher setting.

**Caveat, measured (Edge Grinder, Master 128, jsbeeb, 2026-09-04 — [[sources/beeb-port-kit-hardware-facts]] §4):** `*FX 200,1` is the right default *unless the program has taken HAZEL* (`&C000-&DFFF`, ACCCON Y — the filing system's workspace on the Master). Then BREAK must clear memory: a soft BREAK out of a game that had loaded its music into HAZEL gave `Acorn MOS` with no DFS banner and `*CAT` returned nothing. `OSBYTE 200, X=3` (ESCAPE disabled **and** memory cleared, making BREAK a power-on reset) at the top of the program fixed it — afterwards BREAK gave a clean `Acorn 1770 DFS` and SHIFT+BREAK reloaded the game ([Edge layer-7-music.md](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-7-music.md)). See [[memory/shadow-ram]]. **Later measurements narrow this:** on MOS 3.20 the memory-clear setting is honoured only when the System VIA's IER is 0 or `&0258` still holds it, so a game running with VIA interrupts enabled needs the BREAK intercept — next section.

### BREAK that clears RAM on a Master: `*FX 200,2` is not enough (MOS 3.20, measured 2026)

From [[sources/beeb-port-kit-hardware-facts-2026-11]] §6 "BREAK that clears RAM", 1942 and phX (both Master 128):

- **MOS 3.20's reset clears `&0000-&DFFF`, HAZEL and shadow only if the System VIA's IER reads 0 or `&0258` is 2 or 3** (read off `&8046`: IER = 0 or `(&0258 >> 1) = 1`). **In play the IER is not 0** (`&C2` in 1942), and a game that reuses `&0258` (the MOS's low RAM is fair game once the IRQ is yours) loses the setting too. So a game that runs with VIA interrupts enabled cannot rely on `*FX 200,2`; a tune or title that runs with IER 0 clears anyway (1942, jsbeeb Master 2026-10-18/19 — a soft BREAK in `tools/measure_break.mjs` became a hard one — **and KC's real Master**, rc4). Re-measured by the kit 2026-10-25, jsbeeb 2.10.2 Master, IER `&53` (`lib/break.6502`, `lib/test/break_test.mjs`): no `*FX 200` keeps RAM; `*FX 200,2` clears it; `*FX 200,2` then `&0258` = 0 keeps it; the intercept below then `&0258` = 0 clears it again. The `&8046` reading was not re-disassembled; the rule is confirmed by behaviour.
- **The intercept is the reliable form for a program that owns the IRQs and low RAM.** 1942's: `*FX 247` arms a `JMP` at `&0287-&0289` pointing at seven bytes that store 2 at `&0258` and `JMP (&FFFC)`, so the second reset pass clears. phX's (its decision 59) drops `*FX 200,2` altogether: `*FX 247-249` point the intercept at 8 bytes at `&0D20` that clear the System VIA's IER and restart the reset, so the MOS takes every BREAK for a power-on. (Without it a soft BREAK needed the MOS's HAZEL workspace `&DE00-&DFFF`, the DFS's, page `&0D` and `&0258` back — measured in jsbeeb by restoring regions from a cold machine.)
- **The clear zeroes `&0287`**, so the intercept must be re-armed by the next boot (kit, 2026-10-25).
- **Keep `&0287-&0289` free.** 1942 put two variables at `&0288` and the intercept read `JMP &005D` in play (1942 BUGS #92, found on real hardware at rc4). phX lost it the same way: one of its overlays, copied into page 2, overwrote the `JMP` 196 fields in, so every later BREAK was soft, and **on KC's Master the DFS could not be selected afterwards** (2026-11-15/16, `phX/docs/decisions.md` 59, `phX/docs/hwtest.md` "B7").
- **Test a PLAIN BREAK, at many points of the run.** phX's SHIFT+BREAK check passed throughout, because SHIFT+BREAK reboots the disc either way. Its `tools/verify_break_plain.mjs` presses BREAK at eight points and requires the banner and a working `*CAT` after each.
- **A real Master's RAM powers up with junk, and the junk survives BREAK** — "nothing may read RAM it did not write"; phX's harnesses take `JUNK=seed` (every RAM junk, a soft BREAK, then the boot). See [[tools/emulators]].
- **A `*RUN` boot (disc option 2) is entered with interrupts OFF**, before any language starts: P = `&35` (I set) at the release `!BOOT` stub on `B-DFS1.2` and `Master` alike (kit template, jsbeeb, 2026-09-11). On the Model B the BREAK beep then never ends (channel 0 still at 523 Hz, attenuation 2, after 400 frames) — write attenuation 15 to all four channels yourself; OSBYTE 126 does nothing here (no ESCAPE is pending). A boot program that waits for a key in OSRDCH waits for ever until it does `CLI` (phX hardware-test menu, jsbeeb Master). See [[os/sound]].

### `OSBYTE &D7` — message suppression

```
bit 7: 0 = suppress startup message, 1 = print message (default)
bit 0: 0 = boot-file errors cause lock-up if !BOOT in *ROM,
       1 = boot-file errors continue if !BOOT in *ROM but lock-up on disc
```

Set bit 7 = 0 for a silent boot.

### `OSBYTE &FF` — start-up options byte

On Model B, set by 8 keyboard PCB links read at hard BREAK. On Electron / Master, programmable via `*FX 255,n`:

| Bits | Function |
|---|---|
| 0-2 | Initial MODE after reset |
| 3 | If clear, SHIFT+BREAK swapped (auto-boot vs no-boot) |
| 4-5 | Disc-drive timings (depends on FDC) |
| 6 | Reserved |
| 7 | 0 = boot to NFS, 1 = boot to DFS |

## Triggering a reset programmatically

```asm
LDA #&7F : STA &FE4E         ; mask System VIA IRQs
JMP (&FFFC)                  ; vector via reset → power-on reset path
```

The IRQ-mask + reset combo causes MOS to detect a power-on reset (return `OSBYTE &FD` = 1) rather than soft BREAK. Useful when you want full re-initialisation rather than language re-entry.

## See also

- [[os/escape]] — ESCAPE handling (separate from BREAK).
- [[os/osbyte]] — All BREAK-related OSBYTE entries.
- [[os/calls]] — BRKV (`&202`) vs the `&F7-&F9` intercept (different mechanisms).
- [[os/paged-roms]] — Service ROMs use their own service-call &27 reset notification (Master) in addition to the BREAK intercept.
- [[sources/naug-ch24-misc]] — Full source page with worked examples.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
