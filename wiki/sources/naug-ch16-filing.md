---
title: NAUG Ch16 — Filing Systems
type: source
parent: [[sources/naug]]
pages: 257-289
section: §16
tags: [filing-systems, osfile, osargs, osbget, osbput, osgbpb, osfind, dfs, adfs, cfs, rfs, nfs, wd1770]
updated: 2026-05-13
---

# NAUG Ch16 — Filing System Implementations

Holmes & Dickens, *The New Advanced User Guide*, pp.257-289. Defines the **filing-system API** (OSFILE/OSARGS/OSBGET/OSBPUT/OSGBPB/OSFIND + FSCV), the per-filing-system variations (CFS/RFS/DFS/ADFS/NFS/Telesoft/IEEE), the Master filing-system handler, and direct WD1770 FDC programming.

## Key facts captured

### The standard filing-system API

| Call | Entry | Vector | Purpose |
|---|---|---|---|
| OSFILE | `&FFDD` | `&212` FILEV | Whole-file load/save + attribute R/W |
| OSARGS | `&FFDA` | `&214` ARGSV | File attribute R/W + FS identification |
| OSBGET | `&FFD7` | `&216` BGETV | Read 1 byte from open file |
| OSBPUT | `&FFD4` | `&218` BPUTV | Write 1 byte to open file |
| OSGBPB | `&FFD1` | `&21A` GBPBV | Multi-byte transfer + directory listing |
| OSFIND | `&FFCE` | `&21C` FINDV | Open / close files |
| (FSC)  | — | `&21E` FSCV | Misc FS dispatch (called by OS) |

Most calls take **A = reason code** and a parameter block in X+Y.

### OSFILE actions

| A | Action |
|---|---|
| 0 | Save block of memory; returns length + attributes |
| 1 | Write catalogue info |
| 2 | Write load address |
| 3 | Write exec address |
| 4 | Write attributes |
| 5 | Read catalogue info |
| 6 | Delete file (returns its catalogue info) |
| 7 | Create empty file (Master only) |
| 255 | **Load named file** (most common) |

Parameter block at X+Y:

```
+0..1   filename ptr (+ CR terminator)
+2..5   load address
+6..9   exec address
+10..13 start address / length
+14..17 end address / file attributes
```

Exit A: 0 = not found, 1 = file, 2 = directory, &FF = E-attribute set (ADFS only).

### File attribute byte (bits in `+14`)

| Bit | Meaning when set |
|---|---|
| 0 | R — can be read |
| 1 | W — can be written |
| 2 | E — can be executed |
| 3 | L — locked (can't delete) |
| 4 | r — readable by others |
| 5 | w — writable by others |
| 6 | e — executable by others |

DFS uses only bit 3 (L = locked).

### OSARGS actions

| A | Y | Action |
|---|---|---|
| 0 | 0 | Return filing-system number in A |
| 0 | handle | Read sequential file pointer (into zp at ptr-in-X) |
| 1 | 0 | Return remaining command-line address (zp ptr-in-X) |
| 1 | handle | Write sequential pointer (from zp ptr-in-X) |
| 2 | handle | Return file length (zp ptr-in-X) |
| 255 | 0 | Flush all open files |
| 255 | handle | Flush specific file |

### Filing-system numbers

| FS # | System |
|---|---|
| 0 | none selected |
| 1 | 1200 baud CFS |
| 2 | 300 baud CFS |
| 3 | RFS (ROM filing system) |
| 4 | DFS |
| 5 | NFS (Econet) |
| 6 | Telesoft |
| 7 | IEEE |
| 8 | ADFS |
| 9 | HFS (host) |
| 10 | VFS (videodisc) |

### OSFIND modes (A on entry)

| A | Action | Returns |
|---|---|---|
| 0 | Close (Y=0 = all, Y=handle = one) | — |
| 64 | Open for input | A = handle (or 0 = fail) |
| 128 | Open for output (creates if absent) | A = handle |
| 192 | Open for random access | A = handle |

Default file size on creation: 16 KB DFS, 64 KB ADFS.

### FSCV actions (A on entry)

| A | Function |
|---|---|
| 0 | `*OPT` command |
| 1 | EOF check (X = handle, returns X=&FF if EOF) |
| 2 | `*/` command |
| 3 | Unrecognised `*` command |
| 4 | `*RUN` command |
| 5 | `*CAT` command |
| 6 | New filing system start |
| 7 | Return file handle range (X = min, Y = max) |
| 8 | OS received a `*` command |
| 9 | `*EX` |
| 10 | `*INFO` |
| 11 | `*RUN` for library |
| 12 | `*RENAME` |

### Per-filing-system variation summary

| FS | OSFILE | OSARGS | OSGBPB | OSFIND | Handle range |
|---|---|---|---|---|---|
| CFS | load/save only | FS-id only | (limited on Master) | input + output | 1 in, 2 out |
| RFS | load only | FS-id only | (A=4 on Master) | input only | 3 |
| DFS | full | full | full | full | typically 1-5 |
| ADFS | full | full | full | full | wider range |
| NFS | full + dates | full | full | full | — |
| Telesoft | load only | FS-id only | none | input only | &14, &15 |
| IEEE | not supported | FS-id only | none | input + output (16 ch) | `&F0-&FF` |

### Filing-system OSBYTEs

| OSBYTE | Function |
|---|---|
| `&77` (119) | Close *SPOOL/*EXEC files |
| `&7F` (127) | EOF check on a handle |
| `&82` (130) | Read machine high-order address (Tube 32-bit prefix) |
| `&89` (137) | Cassette motor relay (X=0 off, X=1 on) |
| `&8B` (139) | Perform *OPT (X = option, Y = value) |
| `&8C` (140) | Select CFS (X = baud rate code) |
| `&8D` (141) | Select RFS |
| `&9D` (157) | Fast Tube OSBPUT |
| `&B7` (183) | R/W CFS/RFS switch flag |
| `&C6` (198) | R/W *EXEC file handle |
| `&C7` (199) | R/W *SPOOL file handle |

### OSWORD `&7F` — direct FDC command (DFS only)

Issue raw 1770 commands via the DFS — bypasses the high-level OSFILE etc. Used for raw sector access (custom disc formats, copying, repair).

## WD1770 FDC chip (§16.4 p270-278)

**Replaces 8271 on B+ / Master / Compact**. Two-chip family: 1770 and 1772 (1772 has 2-3 ms stepping rates available for fast drives).

### Register addresses

| Reg | B+ | Master | Function (read) | Function (write) |
|---|---|---|---|---|
| Status / Command | `&FE84` | `&FE28` | Status | Command |
| Track | `&FE85` | `&FE29` | Track | Track |
| Sector | `&FE86` | `&FE2A` | Sector | Sector |
| Data | `&FE87` | `&FE2B` | Data | Data |
| Drive control | `&FE80` | `&FE24` | — | Drive ctrl |

### Drive control register

Master `&FE24` (similar but different bit order on B+ `&FE80`):

| Bit | Field |
|---|---|
| 5 | DDEN: 0 = double-density (MFM), 1 = single-density (FM) |
| 4 | SEL: side select (0/1) |
| 2 | DS2: select drive 2 |
| 1 | DS1: select drive 1 |
| 0 | DS0: select drive 0 |
| 3 | RES: pulse low ≥ 50 µs to reset 1770 |

### Command types

| Type | Commands |
|---|---|
| I | Restore, Seek, Step, Step-in, Step-out (head positioning) |
| II | Read sector, Write sector (single or multiple via `m` bit) |
| III | Read address, Read track, Write track |
| IV | Force interrupt |

Each command byte: `[type-encoded high bits] [flags]`. Key flag bits:

- **h**: motor-on (0 = enable spin-up, 1 = disable spin-up if already running)
- **v**: verify destination track (Type I only)
- **r1,r0**: stepping rate (Type I)
- **m**: multi-sector (Type II)
- **e**: 15 ms head-settle delay (Type II/III)

### NMI per byte

Every byte read/write generates an **NMI** to the 6502. The handler must service within 32 µs (double-density) or 64 µs (single-density) or the byte is lost. NMI handler lives at `&0D00` (1 page).

Status bit `LD` (lost data) sets if the handler is too slow.

### Status register bits

(`&FE28` on Master, `&FE84` on B+):

| Bit | Type I meaning | Type II/III meaning |
|---|---|---|
| 7 | MON (motor on) | MON |
| 6 | WRP (write-protect) | WRP |
| 5 | RT/SU (spin-up complete) | Record type (0=data, 1=deleted) |
| 4 | RNF (record not found) | RNF |
| 3 | CRC (CRC error) | CRC |
| 2 | LD (lost data) | LD |
| 1 | DRQ/ID (index hole) | DRQ (data ready) |
| 0 | BUSY | BUSY |

**Don't poll status to check completion** — that resets a pending NMI. Use the NMI to signal completion instead.

### Example: direct sector read

NAUG §16.4.4 p278-281 provides a complete IBM-disc-dump example using the 1770 directly. Pattern:

1. Set drive-control register (drive, side, density).
2. Issue Restore (`&09` cmd) to seek track 0.
3. Wait for BUSY clear (or NMI).
4. Write target track to data register, issue Seek (`&19` cmd).
5. Write target sector to sector register.
6. Issue Read Sector (`&84` cmd, h=1 since motor running, m=0 single sector).
7. Each NMI: read data register, store, increment dest pointer.
8. On final NMI: check status for RNF / CRC / LD errors.

NMI handler skeleton (NAUG §16.4.4):

```asm
                ; lives at &D00
                PHA
                LDA &FE28       ; or &FE84 on B+
                AND #&1F        ; mask
                CMP #&03        ; DRQ + BUSY both set?
                BNE exit
                LDA &FE2B       ; or &FE87 — read data
.save           STA &2000       ; (self-modifying address)
                INC save+1
                BNE exit
                INC save+2
.exit           PLA
                RTI
```

## Master filing-system handler (§16.2 p259-260)

Master has **multiple filing systems active simultaneously**. The FS handler intercepts FSC calls (in HAZEL at `&DFxx`) and dispatches to the right per-FS handler based on:

- **Current FS** (default).
- **Library FS** (fallback for unrecognised disc commands).
- **Temporary FS** — prefixed call like `*LOAD -DISC-prog` uses DISC just for this call.

`OSBYTE &6D` makes a temporary FS permanent.

HAZEL allocations (`&DF00-&DFFF`):

| Range | Use |
|---|---|
| `&DF00` | Current FS number |
| `&DF01` | Active FS number |
| `&DF02` | Library FS number |
| `&DF03` | Current FS ROM number |
| `&DF05-&DF06` | Min/max file handle |
| `&DF06-&DFC1` | Up to 17× 11-byte FS info blocks |
| `&DFC2` | FS flags (bit 7 = APPEND/BUILD, bit 6 = ASCII-only print) |
| `&DFC6` | Temporary FS flag |
| `&DFC7-&DFDD` | `*MOVE` workspace |
| `&DFDA-&DFDB` | Copy of FSCV for active FS |

## DFS catalogue format (§16.3.3 p266)

Two sectors at start of each disc surface:

**Sector 0**: 12-byte title (first 8 bytes), then 31× 8-byte filename slots. Each slot: 7 bytes filename + 1 byte (directory char + bit 7 access flag).

**Sector 1**: 4 more bytes of title, cycle number (BCD), file count × 8, boot option + sector info, total sectors LSB, then 31× 8-byte file metadata (load, exec, length, start sector, with high-bit packing for 10-bit addresses).

10-bit address packing: low 16 bits per field, top 2 bits packed into a shared byte:

```
top byte bits 1-0: total sectors high 2 bits
       bits 3-2: file 1 start sector top bits  (sectors > 1023)
       bits 5-4: file 1 load address top bits  (> 65535)
       bits 7-6: file 1 exec address top bits
```

## ADFS format (§16.3.4 p267)

16 sectors/track × 256 bytes. Total sector counts: 640 (40-track SS), 1280 (80-track SS), 2560 (DS 80).

- Sectors 0-1: free-space list (82 free-space entries, max).
- Sectors 2-6: root directory (47 entries, each 26 bytes).
- Sub-directories anywhere.

## Filed into

- [[os/filing-systems]] — Standard FS API (OSFILE/OSARGS/etc), FS numbering, per-FS variation summary.
- [[hardware/wd1770]] — FDC chip register reference + commands + NMI protocol + direct-sector example.
- Updates: [[os/osbyte]] — filing-system entries linked.
- Updates: [[os/calls]] — FILEV/ARGSV/BGETV/BPUTV/GBPBV/FINDV/FSCV cross-links.

## Open follow-ups

- **OSWORD `&7F` parameter block format** (direct 1770 command) — captured at hint level only; if writing a disc-image utility, refer back to DFS source disassembly for the exact block layout.
- **Acorn CP/M disc format** (Z80 2P, NAUG §18.10.4) — covered in [[sources/naug-ch18-tube]] already.
- **NFS protocol detail** — Acorn defers to Econet Advanced User Guide; out of scope here.
- **Per-FS detailed OSBYTE/OSWORD additions** — captured at headline level; specifics belong in per-FS pages if needed.
