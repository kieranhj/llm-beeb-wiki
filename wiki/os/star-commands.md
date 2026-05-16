---
title: MOS *commands (star commands)
type: os
tags: [mos, star-commands, cli, osCli, commands]
sources: [master-rm]
updated: 2026-05-16
---

# MOS *commands (star commands)

Any line starting with `*` (or `OSCLI` from assembly) is interpreted as a **command** by the MOS, not as input to the current language. MOS dispatches commands in this order:

1. **Resident MOS commands** (built into the MOS ROM — `*FX`, `*KEY`, `*CONFIGURE`, `*TV`, etc.)
2. **Currently-active filing system** commands (`*LOAD`, `*SAVE`, `*CAT`, etc.)
3. **All sideways ROMs in priority order** (highest slot first) — via Service Call 4 ("Offer Command")
4. **Final fallback**: try to `*RUN <filename>` via the current filing system

If nothing claims the command, MOS raises error 254 `Bad command` (see [[os/errors]]).

For programmatic invocation from assembly:

```asm
LDA #<command_str
LDY #>command_str
JSR &FFF7        ; OSCLI - same dispatch as user typing *cmd
; command_str must be terminated by &0D (CR)
```

For the filing-system-specific commands (`*LOAD`, `*SAVE`, `*INFO`, etc.) see [[os/filing-systems]] and the per-FS pages.

## Master MOS resident commands (per [[sources/master-rm]] Ch C)

| Command | Min abbrev | Executed by | Purpose |
|---|---|---|---|
| `*ADFS` | `*A.` | MOS | Make ADFS the current filing system |
| `*APPEND` | | FS | Append lines of input to a file |
| `*BUILD` | | FS | Create a file from lines of input |
| `*CAT` | | FS | Display disc/directory catalogue |
| `*CLOSE` | | FS | Close all sequential files |
| `*CODE` | | MOS | Run resident machine-code program via USERV with A=0 |
| `*CONFIGURE` | `*CO.` | MOS | Set CMOS RAM configuration |
| `*CREATE` | | FS | Create a file of given size |
| `*DELETE` | | FS | Delete a named file or files |
| `*DISC` | `*DI.` | MOS | Make DFS the current filing system |
| `*DUMP` | | FS | Display file in hex + ASCII |
| `*EX` | | FS | Display file information |
| `*EXEC` | | FS | Take subsequent input from a file |
| `*FX` | | MOS | OSBYTE call — see [[os/osbyte]] |
| `*GO` | | MOS | Execute machine-code program at given address |
| `*GOIO` | | MOS | Execute machine-code in I/O processor (host even if Tube active) |
| `*HELP` | `*H.` | MOS+ROMs | Per-ROM help text; `*HELP <subject>` to drill down |
| `*IGNORE` | `*IG.` | MOS | Equivalent to `*FX 6` |
| `*INSERT` | `*INS.` | MOS | Insert ROM number n into ROM map from reset |
| `*KEY` | `*K.` | MOS | Define soft key strings (red function keys, cursors, COPY) |
| `*LIBFS` | | MOS | Define filing system from which LIB is taken |
| `*LINE` | | MOS | Run resident machine-code program via USERV with A=1 |
| `*LOAD` | | FS | Load file into memory |
| `*MOTOR` | `*M.` | MOS | Cassette motor relay on/off |
| `*MOVE` | | FS | Move files between filing systems |
| `*OPT` | | FS | Set filing-system options |
| `*PRINT` | | FS | Display file as pure ASCII |
| `*ROM` | | MOS | Make ROM filing system current |
| `*ROMS` | | MOS | Display ROM contents (slot + name + version + ON/OFF state) |
| `*RUN` | | FS | Load + execute machine-code program |
| `*SAVE` | | FS | Save block of memory as a file |
| `*SHADOW` | `*SH.` | MOS | Define usage of shadow memory |
| `*SHOW` | | MOS | Display soft-key string allocation |
| `*SHUT` | | FS | Close all files on all filing systems |
| `*SPOOL` | | FS | Send all output to a file |
| `*SPOOLON` | | FS | Append all output to a file |
| `*SRDATA` | | MOS | Reserve sideways RAM for data use ([[memory/paged-rom]]) |
| `*SRREAD` | | MOS | Copy sideways RAM to main RAM |
| `*SRROM` | | MOS | Reserve sideways RAM for ROM-style addressing |
| `*SRWRITE` | | MOS | Copy main RAM to sideways RAM |
| `*STATUS` | `*ST.` | MOS | Display CMOS RAM configuration |
| `*TAPE` | `*T.` | MOS | Make CFS the current filing system |
| `*TIME` | `*TI.` | MOS | Display date and time from CMOS RTC |
| `*TV` | | MOS | Adjust vertical screen alignment + interlace |
| `*TYPE` | | FS | Display file in GSREAD format without line numbers |
| `*UNPLUG` | `*UNP.` | MOS | Direct MOS to ignore specified ROM |
| `*X` | | MOS | Enable more than one external second processor |

## Filing-system commands

The "Executed by FS" entries above dispatch to whichever filing system is currently selected — DFS / ADFS / CFS / NFS / RFS each implement their own versions. Additional FS-specific commands include:

- **DFS**: `*ENABLE`, `*BACKUP`, `*COPY`, `*ACCESS`, `*FREE`, `*COMPACT`, `*RENAME`, `*WIPE`, `*DESTROY`, `*VERIFY`, `*FORMAT` (Master DFS only — Issue 1 DFS used external utilities).
- **ADFS**: `*MOUNT`, `*DISMOUNT`, `*DIR`, `*BACK`, `*BYE`, `*COMPACT`, `*COPY`, `*BACKUP`, `*VERIFY`, `*FORMAT`, `*ACCESS`, `*FREE`, `*INFO`, `*MAP`, `*RENAME`, `*TITLE`, `*WIPE`.
- **NFS / ANFS**: `*I AM`, `*BYE`, `*PASS`, `*NOTIFY`, `*REMOTE`, `*FS`, `*FLIP`, `*LCAT`, `*LEX`, `*WIPE`, `*PROT`, `*UNPROT`, `*PS`, `*POLLPS`.

See [[os/filing-systems]] for the API + per-FS detail.

## Sideways-ROM commands

Any sideways ROM can claim a command via paged-ROM service-call 4 ("Offer Command") at boot or dynamically. The ROM gets to inspect the `*command` text and either claim or pass through. See [[os/paged-roms]] and [[os/service-calls]].

Common ROM-provided commands include:
- **BASIC** ROM: `*BASIC` (to enter the language)
- **EDIT** ROM: `*EDIT`, `*FORMAT` (text formatter)
- **VIEW** ROM: `*VIEW`, `*VFORM`
- **TERMINAL** ROM: `*TERMINAL`

## Notable Master MOS commands in detail

### `*GO` / `*GOIO`

```
*GO <addr>             — execute at <addr> in current language processor
*GOIO <addr>           — execute at <addr> in I/O processor (host)
```

`*GOIO` is critical when a Tube co-processor is active and you need code that touches host-side I/O to run on the host. Without it, code at `<addr>` runs on the parasite where it has no I/O access.

### `*CODE` / `*LINE` (USERV dispatch)

`*CODE` and `*LINE` invoke a user-installed handler at the address stored in `USERV` (`&0200/&0201`), with A=0 (CODE) or A=1 (LINE). The handler can implement custom commands, languages, or extensions. See [[os/calls]] USERV section.

### `*CONFIGURE` / `*STATUS`

Reads/writes the Master's CMOS RAM configuration store ([[hardware/cmos-rtc]]) — keyboard speed, default mode, filing system, network station, tube selection, etc. Settings persist across power-off via the battery-backed CMOS chip.

```
*CONFIGURE FILE 4        — default FS = ROM 4 (typically ADFS)
*CONFIGURE LANG 12       — default language = ROM 12 (typically BASIC)
*CONFIGURE MODE 135      — default mode = shadow MODE 7
*CONFIGURE TV 0,1        — *TV 0,1 at every boot (no vertical offset, interlace)
*CONFIGURE NOBOOT        — disable auto-boot
*STATUS                  — list all current settings
```

CMOS layout in [[hardware/cmos-rtc]] section "Master CMOS layout".

### `*FX` (= OSBYTE shortcut)

```
*FX <a> [, <x> [, <y>]]
```

Equivalent to `OSBYTE A=<a>, X=<x>, Y=<y>`. The single most-used MOS command — every documented OSBYTE has an `*FX` form. See [[os/osbyte]] for the directory.

### `*KEY`

```
*KEY <key number> <string>
```

Defines what string is generated when the user presses a function key (or COPY / cursor keys). Strings can include MOS-format pipe escapes: `|M` = CR, `|J` = LF, `|"` = literal `"`, `|<` = pipe itself, `|@` = NUL, `|!byte` = top-bit-set byte, etc.

Soft keys live in the soft-key buffer — at `&0B00-&0BFF` on Model B (256 bytes), or `&8000-&83FF` on Master (1 KB; see [[memory/os-workspace]]).

### `*HELP`

The Master extends `*HELP` to an interactive query system. `*HELP <subject>` queries each ROM in priority order via service call `&18` ("Interactive Help"); each ROM can offer additional information about subjects it knows. With no parameter, `*HELP` lists every ROM by slot, name and version.

## Dispatch internals

When you type a `*command` (or call `OSCLI`):

1. MOS calls **CLIV** (`&0208`) which jumps to the MOS internal CLI handler.
2. The handler strips the leading `*` and any leading spaces.
3. It matches the first word against the **MOS resident commands** above (longest match; abbreviations like `*A.` resolve to `*ADFS` if unambiguous).
4. If no resident-MOS match, it issues service call `&04` ("Offer Command") to all sideways ROMs in priority order. Each ROM can claim or pass.
5. If still no claim, it issues service call `&27` to the active filing system as `*RUN <text>`.
6. If still no claim, error 254 `Bad command`.

You can intercept the entire process by hooking **CLIV** — but be careful, as MOS uses CLIV internally for things like `*RUN`. Better to claim service call `&04` from a service ROM.

## See also

- [[os/calls]] — OSCLI entry point + dispatch.
- [[os/osbyte]] — `*FX` directory.
- [[os/filing-systems]] — filing-system command details.
- [[os/paged-roms]] — service-call 4 dispatch.
- [[os/service-calls]] — full service-call reference.
- [[memory/os-workspace]] — soft-key buffer location per model.
- [[hardware/cmos-rtc]] — `*CONFIGURE` / `*STATUS` backing store.
- [[sources/master-rm]] Ch C — primary source.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
