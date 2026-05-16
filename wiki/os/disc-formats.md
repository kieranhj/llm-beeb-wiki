---
title: DFS and ADFS disc formats
type: os
tags: [dfs, adfs, filing-system, catalogue, fsm, sectors, disc-format]
sources: [master-rm, naug-ch16-filing]
updated: 2026-05-16
---

# DFS and ADFS disc formats — sector-level layout

Sector-level format of BBC discs as seen from low-level filing-system code or direct WD1770/1772 access. See [[hardware/wd1770]] for the controller chip itself, [[os/filing-systems]] for the user-level filing-system API, and [[hardware/wd1770]] for the disc-controller programming sequence.

## DFS — 40/80-track, single-sided, 10×256-byte sectors

A DFS disc surface has either 40 or 80 tracks. Each track holds **10 sectors of 256 bytes**. Total: 400 sectors (100 KB) for 40-track, 800 sectors (200 KB) for 80-track. Per [[sources/master-rm]] Ch J.5.

**Absolute sector number** = `10 × track + sector_on_track`. Used throughout DFS internals.

Files are **contiguous byte streams** starting at a sector boundary. The last sector may be partially used. The catalogue holds the file length so the filing system knows where to stop reading.

⚠ Track 0 is the **outermost** track on both 40- and 80-track discs. The catalogue lives there, so reads of the catalogue work in either drive type — but files extending beyond sector 9 (= beyond track 0) will read garbage if a 40-track image is loaded in an 80-track drive without stepping translation.

### DFS catalogue layout (sectors 0 + 1)

#### Sector 0

| Bytes | Content |
|---|---|
| 0-7 | First 8 bytes of disc title |
| 8-14 | First file name (7 chars) |
| 15 | Directory letter of first file (bit 7 = lock attribute) |
| 16-22 | Second file name |
| 23 | Directory letter of second file (bit 7 = lock) |
| ... | (repeat for up to **31 files**) |

#### Sector 1

| Bytes | Content |
|---|---|
| 0-3 | Final 4 bytes of disc title (total title length = 12) |
| 4 | Master sequence number (BCD-counted catalogue-access cycle) |
| 5 | (number of catalogue entries) × 8 — used as pointer to next free entry |
| 6 | bits 0-1: high 2 bits of (sectors on disc, 10-bit total); bits 4-5: boot option (`*OPT 4`) |
| 7 | low 8 bits of (sectors on disc) |
| 8 | File 1 load address LSB |
| 9 | File 1 load address middle byte |
| 10 | File 1 exec address LSB |
| 11 | File 1 exec address middle byte |
| 12 | File 1 length LSB |
| 13 | File 1 length middle byte |
| 14 | bits 0-1: high 2 bits of start sector; bits 2-3: load addr high; bits 4-5: length high; bits 6-7: exec addr high |
| 15 | low 8 bits of file 1 start sector |
| ... | (repeat for up to 31 files) |

### File attributes

DFS supports only the **L (locked)** attribute, encoded as bit 7 of the directory-letter byte in sector 0.

### Master sequence number

Cyclic BCD counter incremented on every catalogue modification (file create/delete). Used by the filing system to detect "disc changed" between operations — if the cached MSN doesn't match what's on disc when a file operation is retried, the operation is aborted. Set to 0 on `*FORMAT`.

## ADFS — multi-format, hierarchical, 16×256-byte sectors

ADFS supports three disc geometries (per [[sources/master-rm]] Ch J.10):

| Geometry | Tracks | Sides | Sectors/track | Total |
|---|---|---|---|---|
| Single-sided 40-track | 40 | 1 | 16 | 640 sectors (160 KB) |
| Single-sided 80-track | 80 | 1 | 16 | 1280 sectors (320 KB) |
| Double-sided 80-track | 80 × 2 = 160 | 2 (treated as single entity) | 16 | 2560 sectors (640 KB) |

**Absolute sector number** = `16 × track + sector_on_track`.

Unlike DFS, ADFS keeps **free-space tracking in a dedicated map** (sectors 0+1) and supports **hierarchical directories** (root + sub-directories). Addresses are **32-bit** (vs DFS's 18-bit).

### ADFS Free Space Map (sectors 0 + 1)

#### Sector 0

| Bytes | Content |
|---|---|
| 0-2 | Start sector of 1st free space (3 bytes — 24 bits) |
| 3-5 | Start sector of 2nd free space |
| ... | (up to 82 entries) |
| 246-250 | Reserved |
| 251 | Reserved |
| 252-254 | Total number of sectors on disc (LSB-first) |
| 255 | Checksum on FSM sector 0 |

#### Sector 1

| Bytes | Content |
|---|---|
| 0-2 | Length (sectors) of 1st free space |
| 3-5 | Length of 2nd free space |
| ... | (up to 82 entries, paired with sector-0 starts) |
| 246-250 | Reserved |
| 251-252 | Disc identifier |
| 253 | Boot option number (`*OPT 4`) |
| 254 | Pointer to end of free space list |
| 255 | Checksum on FSM sector 1 |

The two FSM sectors are kept in lock-step: entry N's start sector is at `sector_0[3N..3N+2]`, and its length is at `sector_1[3N..3N+2]`.

### ADFS Root Directory (sectors 2-6)

The **root directory** always lives at sectors 2-6 inclusive (5 sectors = 1280 bytes). Sub-directories are 5-sector regions allocated elsewhere on disc — start sector recorded in the parent directory's entry for that sub-directory.

A directory holds up to **47 entries** (file or sub-directory). Format (per directory):

| Bytes | Content |
|---|---|
| 0 | Directory Master Sequence Number (BCD) |
| 1-4 | Fixed identifier string (`"Hugo"` in ADFS / `"Nick"` on some variants — marks "valid directory start") |
| 5-14 | Entry 1 name (10 bytes) + access string in top bits |
| 15-18 | Entry 1 load address (32-bit) |
| 19-22 | Entry 1 exec address (32-bit) |
| 23-26 | Entry 1 length (32-bit) |
| 27-29 | Entry 1 start sector (24-bit) |
| 30 | Entry 1 sequence number |
| 31-56 | Entry 2 (same layout as entry 1) |
| ... | (up to 47 entries) |
| 1227 | `0` (terminator) |
| 1228-1237 | Directory name / access string |
| 1238-1240 | Start sector of parent directory |
| 1241-1259 | Directory title |
| 1260-1273 | Reserved |
| 1274 | Directory Master Sequence Number (repeated for consistency check) |
| 1275-1279 | (final tail bytes) |

Entries are kept in **alphabetical order**. The "end of directory" is marked by the next entry having a name string starting with `&00`.

### ADFS file/directory attributes

Encoded in the top bit of the first 4 bytes of the name/access string:

| Byte | Bit 7 set | Bit 7 clear |
|---|---|---|
| Name byte 1 | R (read) attribute set | Not set |
| Name byte 2 | W (write) attribute set | Not set |
| Name byte 3 | L (locked) attribute set | Not set |
| Name byte 4 | E (executable / sub-directory marker on directories) | Not set |

The bottom 7 bits of those name bytes still hold the actual character — top bit is overlaid for attribute storage.

## DFS vs ADFS addressing scale

| Aspect | DFS | ADFS |
|---|---|---|
| Address width | 18-bit (load/exec/length fit in 3 bytes) | 32-bit (4 bytes each) |
| Sectors/track | 10 | 16 |
| Catalogue location | sector 0+1 (combined) | FSM sectors 0+1 + root dir sectors 2-6 |
| Max entries/dir | 31 | 47 |
| Sub-directories | No | Yes (hierarchical) |
| Attributes | L only | R, W, L, E |
| Free space tracking | Implicit (derived from catalogue) | Explicit (FSM) |
| Sector skew | Issue 1 DFS: 9; Master DFS: 9; Master Compact 1772 ADFS: 4 (faster) | n/a |

## Direct disc access from assembly

For Tube-safe disc operations, use `OSWORD &7F` (DFS) / `OSWORD &72` (ADFS multi-sector). See [[hardware/wd1770]] for the chip-level NMI-per-byte protocol if you need to bypass the filing system entirely.

DFS catalogue read (Master DFS pattern):

```asm
; Read catalogue (sectors 0 and 1) into a 512-byte buffer
LDX #<param_block
LDY #>param_block
LDA #&7F          ; OSWORD &7F — DFS disc access
JSR &FFF1
```

Parameter block format depends on FS — see filing-system-specific docs.

## See also

- [[os/filing-systems]] — user-level filing-system API (OSFILE, OSGBPB, OSARGS, etc.)
- [[hardware/wd1770]] — WD1770/1772 controller programming
- [[sources/master-rm]] Ch J.5 (DFS technical) + J.10 (ADFS technical) — primary source
- [[sources/naug-ch16-filing]] — secondary source

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
