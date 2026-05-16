---
title: Paged ROM Service Calls
type: os
tags: [paged-rom, service-call, mos]
sources: [naug-ch17-paged-roms]
updated: 2026-05-13
---

# Paged ROM Service Calls — Reference

Every paged ROM with a service entry receives these calls from MOS. See [[os/paged-roms]] for the dispatch mechanism (MOS scans ROMs in descending priority; first to set `A=0` claims).

Entry to service routine:
- `A` = reason code (table below)
- `X` = this ROM's slot number
- `Y` = call-specific (see each row)

Exit:
- Claimed: A=0, registers otherwise restored, RTS.
- Not claimed: A unchanged, X/Y restored, RTS.

| A | Name | Y (entry) | Notes |
|---|---|---|---|
| `&00` | No operation | — | Higher-priority ROM already claimed. Ignore. |
| `&01` | Absolute workspace claim | top of fixed area (starts `&0E`) | Reset only. Increment Y by pages claimed at `&E00+`. |
| `&02` | Relative private workspace | top of absolute area | Reset only. Store base at `&DF0+rom_id`. Increment Y by pages claimed. |
| `&03` | Auto-boot | 0=boot, ≠0=init only | Reset. Highest FS responds (if no key pressed or own key pressed). |
| `&04` | Unrecognised `*` command | offset to text in `&F2/&F3+Y` | **Main extension point.** Read command via `(&F2),Y`. |
| `&05` | Unknown interrupt | — | IRQ chain fallback. Service IRQ; RTS (not RTI). |
| `&06` | BRK occurred | — | `&FD/&FE` = error pointer, `&F0` = SP at BRK. |
| `&07` | Unknown OSBYTE | — | A/X/Y at OSBYTE saved in `&EF/&F0/&F1`. |
| `&08` | Unknown OSWORD | — | Same `&EF/&F0/&F1` save. OSWORDs `&E0-&FF` skip this and go to USERV. |
| `&09` | `*HELP` text query | offset to remainder of HELP cmd in `&F2/&F3+Y` | If Y points to space/CR, print ROM identification. |
| `&0A` | Claim absolute workspace | — | Issued by another ROM via `OSBYTE &8F`. Previous owner saves state, flags loss. |
| `&0B` | NMI released | filing-system ID of previous owner | Issued via `OSBYTE &8F`. |
| `&0C` | NMI claim | `&FF` | Current NMI owner returns its FS id in Y. |
| `&0D` | RFS initialise | 15 - next_rom_num | Only claim if `&F4 >= invert(Y)`. Store `&F5`, set `&F6/&F7` = data start. |
| `&0E` | RFS get byte | negative = OSRDRM available; positive = old OS | Return byte in Y. See [[sources/naug-ch17-paged-roms]] for OS-version split. |
| `&0F` | Vectors claimed | — | Notification — issued by a ROM after hooking a vector. |
| `&10` | Close `*SPOOL`/`*EXEC` | — | Issued by FS during init. |
| `&11` | Font implosion/explosion | new OSHWM | Electron/Model B only. Language ROMs should adjust HIMEM. |
| `&12` | Initialise filing system | FS id requested | Claim if your FS matches Y. |
| `&13` | Char in RS423 buffer | — | **Electron only.** |
| `&14` | Char in printer buffer | — | **Electron only.** |
| `&15` | **100 Hz poll** | semaphore value | **Master/Electron only.** Decrement Y by units serviced. |
| `&16` | BEL request | — | Electron only (external sound). |
| `&17` | SOUND buffer purged | — | Electron only. |
| `&18` | Interactive `*HELP` | — | Master only. Issued after `&09`. |
| `&21`-`&24` | Master HAZEL workspace claims | — | Master only. As `&01`/`&02` but in HAZEL (`&C000-&DBFF`). |
| `&25` | Return FS info | offset in `&F2/&F3+Y` | Master only. Write 11-byte FS info block. |
| `&26` | `*SHUT` issued | — | Master only. FS should select itself and close files. |
| `&27` | Reset call | — | Master only. After power-on / hard / soft reset. |
| `&28` | Unknown `*CONFIGURE` | offset in `&F2/&F3+Y` | Master / Master Compact. |
| `&29` | Unknown `*STATUS` | offset in `&F2/&F3+Y` | Master / Master Compact. |
| `&2A` | Language about to init | — | Master only. Activate language-support ROMs. |
| `&2B` | Report memory size | — | B+ only. DFS rewrites startup banner. |
| `&2C` | Compact joystick call | offset in `&200+Y` to param block | Master Compact only. |
| `&FE` | Post-init Tube call | `&FF`=Tube present, `&00`=absent | After OSHWM set. |
| `&FF` | Tube main init | — | Before message generation. Tube hardware detected. |

## Implementing a service entry

Typical pattern:

```asm
.service
    CMP #&04           ; unknown *command?
    BEQ handle_cmd
    CMP #&09           ; *HELP?
    BEQ handle_help
    CMP #&02           ; private workspace claim?
    BEQ handle_wkspace
    RTS                ; not us — pass on (A unchanged)

.handle_cmd
    ; parse command line at (&F2),Y
    ; if matches our command:
    ;   do the work
    ;   LDA #0 : RTS    ; claimed
    ; else:
    ;   LDA #&04 : RTS  ; restore A, pass on
```

**Always preserve A, X, Y across a non-claim path.** Use PHA/PHA before testing if you need scratch registers.

## Issuing a service call from user code

`OSBYTE &8F` is the user-facing entry to "tell every paged ROM something happened":

```asm
LDA #&8F
LDX #reason     ; service call reason
LDY #y_param
JSR &FFF4
; on exit: X=0 if any ROM claimed
```

Common uses:
- `X=&0A` — claim absolute workspace from current owner.
- `X=&0C, Y=&FF` — claim NMI.
- `X=&0F` — notify other ROMs that you've changed a vector.
- `X=&04` — invoke an unknown `*` command (less common; OSCLI is usually easier).

## Performance note

Service-call dispatch costs:
- Page in ROM: write `&FE30`.
- JSR ROM service entry.
- ROM tests A, decides, returns.
- MOS pages in next ROM, repeats.

A full scan of 16 ROMs is ~hundreds of cycles. For high-frequency events (e.g. character output), service calls are too slow — extended vectors are the right answer (one paging operation per call, no scan).

The 100 Hz polling call (`&15`) is OK for periodic background work (CMOS RTC updates, mouse polling, etc.) but **don't** do per-cycle work in it.

## See also

- [[os/paged-roms]] — ROM header format and dispatch mechanism.
- [[memory/paged-rom]] — Hardware paging register `&FE30`.
- [[os/calls]] — OS vector table.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
