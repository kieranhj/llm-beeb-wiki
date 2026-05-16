---
title: Filing Systems
type: os
tags: [filing-system, osfile, osargs, osbget, osbput, osgbpb, osfind, fscv, dfs, adfs, cfs, rfs]
sources: [naug-ch16-filing]
updated: 2026-05-13
---

# Filing Systems — MOS API

Eight (well, nine) filing systems on the BBC family, all sharing a common API. For chip-level direct disc access (bypassing the FS), see [[hardware/wd1770]].

## Filing systems available

| # | Name | BREAK key | `*` cmd | Workspace pages (abs + priv) |
|---|---|---|---|---|
| 0 | none | — | — | — |
| 1 | CFS 1200 baud | SPACE | `*TAPE` | 0 + 0 |
| 2 | CFS 300 baud | — | `*TAPE 3` | 0 + 0 |
| 3 | RFS | SHIFT-SPACE | `*ROM` | 0 + 0 |
| 4 | DFS | D | `*DISC` / `*DISK` | 9 + 2 |
| 5 | NFS | N | `*NET` | 2 + 2 |
| 6 | Telesoft | T | `*TELESOFT` | 12 + 8 |
| 7 | IEEE | — | `*IEEE` | 2 + 1 |
| 8 | ADFS | A or F | `*ADFS` / `*FADFS` | 14 + 1 |
| 9 | HFS | — | (host) | — |
| 10 | Videodisc | Q or L | `*VFS` / `*LVFS` | — |

`OSARGS A=0 Y=0` returns the active FS number.

## The standard API

Six entry points + one vector. All Tube-aware.

| Call | Address | Vector | Function |
|---|---|---|---|
| OSFILE | `&FFDD` | `&212` FILEV | Whole-file load/save + attribute R/W |
| OSARGS | `&FFDA` | `&214` ARGSV | File pointer / length / flush, FS-id query |
| OSBGET | `&FFD7` | `&216` BGETV | Read 1 byte from open file |
| OSBPUT | `&FFD4` | `&218` BPUTV | Write 1 byte to open file |
| OSGBPB | `&FFD1` | `&21A` GBPBV | Multi-byte transfer, directory list |
| OSFIND | `&FFCE` | `&21C` FINDV | Open/close file |
| — | — | `&21E` FSCV | OS-internal dispatch (FSCV-only) |

## OSFILE — whole-file operations

```asm
LDA #action      ; see table
LDX #pb MOD 256
LDY #pb DIV 256
JSR &FFDD
```

Parameter block (18 bytes):

```
+0..1   filename ptr (terminated by CR)
+2..5   load address (4 bytes, LSB first)
+6..9   exec address
+10..13 start address / length (depending on action)
+14..17 end address / file attributes
```

Actions:

| A | Function |
|---|---|
| 0 | **Save** memory block. Set +10/+14 to start/end. Returns length + attrs. |
| 1 | Write catalogue info (load, exec, attrs all at once) |
| 2 | Write load address |
| 3 | Write exec address |
| 4 | Write attributes |
| 5 | Read catalogue info. **Exit A**: 0=not found, 1=file, 2=directory, &FF=E-attr (ADFS). |
| 6 | Delete file (returns catalogue info first) |
| 7 | **Create empty file** (Master only). Length in +10..+13. |
| 255 | **Load** named file. If +6 = 0, use specified load address; otherwise use file's stored address. |

### File attributes (byte at +14)

| Bit | Set means |
|---|---|
| 0 | R — owner can read |
| 1 | W — owner can write |
| 2 | E — owner can execute |
| 3 | L — locked (can't delete) |
| 4 | r — others can read |
| 5 | w — others can write |
| 6 | e — others can execute |

DFS only honours bit 3 (L=locked).

NFS uses +15..+17 for **date** (day, month, year-1981 packed into 12 bits).

## OSFIND — open / close

```asm
LDA #action      ; 0/64/128/192
LDX #fname MOD 256   ; for open
LDY #fname DIV 256
JSR &FFCE
```

| A | Action | Returns |
|---|---|---|
| 0 | Close. Y=0 closes all, Y=handle closes one. | — |
| 64 | Open for input. | A = handle, 0 if failed |
| 128 | Open for output (creates if absent). | A = handle |
| 192 | Open for random access. | A = handle |

Default file size on creation: 16 KB (DFS), 64 KB (ADFS).

## OSARGS — file pointer / attributes / FS query

```asm
LDA #action
LDX #zp_4byte_buffer    ; zp address for transfer
LDY #file_handle        ; or 0 for non-file queries
JSR &FFDA
```

| A | Y | Action |
|---|---|---|
| 0 | 0 | A returns FS number |
| 0 | handle | Read sequential pointer into 4-byte zp buffer |
| 1 | 0 | Return remaining command-line address in zp |
| 1 | handle | Write sequential pointer from zp |
| 2 | handle | Return file length in zp (4 bytes) |
| 255 | 0 | Flush all open files to disc |
| 255 | handle | Flush one file |

## OSBGET / OSBPUT — single byte

```asm
LDY #handle
JSR &FFD7          ; OSBGET: returns A=byte, C=1 if EOF
                   ; advances sequential pointer
```

```asm
LDA #byte
LDY #handle
JSR &FFD4          ; OSBPUT: writes byte, advances pointer
```

**Fast Tube OSBPUT**: from a 6502 second processor, `OSBYTE &9D` (X=byte, Y=handle) is faster than going through OSBPUT — bypasses one level of vector dispatch ([[sources/naug-ch18-tube]]).

## OSGBPB — bulk transfer

```asm
LDA #action      ; 1-8
LDX #pb MOD 256
LDY #pb DIV 256
JSR &FFD1
```

Parameter block:

```
+0    file handle (or disc cycle number for A=8)
+1..4 memory address (LSB first)
+5..8 byte count (or filename count for A=8)
+9..12 sequential pointer
```

| A | Action |
|---|---|
| 1 | Write bytes at the specified sequential position |
| 2 | Append bytes at current position |
| 3 | Read bytes from specified position |
| 4 | Read bytes from current position |
| 5 | Read disc title, boot option, drive number |
| 6 | Read current directory + drive name |
| 7 | Read current library + drive |
| 8 | Read filenames from current directory |

Exit C=1 if transfer couldn't complete (partial); +5..+8 holds remaining byte count.

## FSCV — internal dispatch (don't call from user code)

The OS calls FSCV (`&21E`) for filing-system housekeeping. User code shouldn't call FSCV directly, but service ROMs may intercept FSCV to add custom filing-system commands.

Reason codes: see [[sources/naug-ch16-filing]] §16.1.7.

## Filing-system OSBYTEs

| OSBYTE | Function |
|---|---|
| `&77` (119) | Close all `*SPOOL`/`*EXEC` files |
| `&7F` (127) | EOF check (X = handle, returns X ≠ 0 if EOF) |
| `&82` (130) | Read 32-bit machine high-order address (Tube prefix) |
| `&87` (135) | (also char at cursor — [[sources/naug-ch13-video]]) |
| `&89` (137) | Cassette motor (X=0/1) |
| `&8B` (139) | Perform `*OPT` (X = option, Y = value) |
| `&8C` (140) | Select CFS (X=0 default, X=3 = 300 baud, X=12 = 1200) |
| `&8D` (141) | Select RFS |
| `&9D` (157) | Fast Tube OSBPUT |
| `&B7` (183) | R/W CFS/RFS switch flag |
| `&C6` (198) | R/W *EXEC handle |
| `&C7` (199) | R/W *SPOOL handle |
| `&6D` (109) | Make temporary FS permanent (Master) |

## OSWORD calls used by filing systems

| OSWORD | FS | Function |
|---|---|---|
| `&7A` | Telesoft | Issue Telesoftware command |
| `&7D` | DFS | Read disc cycle number |
| `&7E` | DFS | Read disc / directory size |
| **`&7F`** | DFS | **Issue raw 1770 FDC command** |
| `&80` | IEEE | Issue IEEE-488 command |

OSWORD `&7F` is the direct-FDC path — bypasses DFS's high-level routines and lets you issue Type I/II/III commands directly via the parameter block. Useful for custom disc formats, IBM/CP/M disc reads, and disc repair tools. Parameter block layout in [[sources/naug-ch16-filing]].

## Per-filing-system variation summary

| FS | OSFILE | OSARGS | OSGBPB | OSFIND | OSWORDs added |
|---|---|---|---|---|---|
| CFS | load/save only | FS-id only | (limited Master) | input + output (max 2) | none |
| RFS | load only | FS-id only | (A=4 Master) | input only (1 file) | none |
| DFS | full | full | full | full | `&7D`, `&7E`, `&7F` |
| ADFS | full | full | full | full | DFS set + extensions |
| NFS | full + dates | full | full | full | many (see Econet AUG) |
| Telesoft | load only | FS-id only | none | input only | `&7A` |
| IEEE | not supported | FS-id only | none | input + output (16 ch) | `&80` |

## Master FS handler — multiple FS simultaneously

On Master, the FS handler in HAZEL (`&DF00-&DFFF`, see [[memory/shadow-ram]]) lets you run with **current**, **library**, and **temporary** filing systems all known simultaneously. Use the prefix syntax:

```
*LOAD -DISC-prog          rem use DFS for this command only
*ADFS                      rem switch persistently
*LIB :0.$                  rem set the library FS path
```

HAZEL's state:

| Addr | Use |
|---|---|
| `&DF00` | Current FS # |
| `&DF01` | Active FS # |
| `&DF02` | Library FS # |
| `&DF03` | Current FS ROM # |
| `&DF05`, `&DF06` | Min, max file handle |
| `&DF06-&DFC1` | Up to 17 × 11-byte FS info blocks |
| `&DFD4`-`&DFDD` | `*MOVE` workspace |
| `&DFDA`-`&DFDB` | Copy of FSCV for active FS |

## Bypass-MOS strategies for fast disc I/O

1. **OSWORD `&7F`** (DFS direct FDC command) — lets you issue Type II read/write sector commands with custom parameter blocks. Still goes through DFS workspace but skips file-level dispatch.
2. **Direct `&FE28`/`&FE29`/`&FE2A`/`&FE2B`** writes ([[hardware/wd1770]]) — fully bypass DFS. Must install NMI handler yourself.
3. **Stay with OSGBPB** for sequential reads — already the fastest MOS-blessed bulk transfer.

The trade-offs:

| Path | Cost per sector | Risk |
|---|---|---|
| OSFIND + OSBGET 256× | very high (per-byte vector dispatch) | low |
| OSFIND + OSGBPB 256 bytes | moderate (one OSGBPB call) | low |
| OSWORD `&7F` | low (one OSWORD + sector-level transfer) | low |
| Direct 1770 + own NMI | minimum | high — your NMI handler can crash |

For game / demo loaders: OSGBPB with a custom NMI handler captured from DFS is the usual sweet spot. For disc utilities (sector editor, copier): direct 1770 access is mandatory.

## See also

- [[hardware/wd1770]] — FDC chip reference.
- [[sources/naug-ch16-filing]] — Detailed catalogue formats (DFS, ADFS), per-FS specifics.
- [[os/calls]] — All MOS entry points including filing-system vectors.
- [[os/paged-roms]] — Filing systems implement themselves as service ROMs; service-call dispatch.
- [[memory/shadow-ram]] — Master HAZEL FS-handler workspace.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
