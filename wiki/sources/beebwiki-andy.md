---
title: "BeebWiki: ANDY"
type: source
tags: [memory, andy, shadow-ram, paged-rom, master, b-plus]
url: https://beebwiki.mdfs.net/ANDY
updated: 2026-05-14
---

# BeebWiki — ANDY

**URL:** https://beebwiki.mdfs.net/ANDY

## Summary

Short page describing the ANDY paged-RAM area on the B+ and Master. Most of the content is already covered in `[[memory/paged-rom]]` and `[[memory/memory-map]]`; the new material worth adding is OSWORD-based access (`&05`/`&06` with `&FFFExxxx` addresses), the B+ `&A000-&AFFF` shadow-display-manipulation trick, and the MOS-won't-scan-it-for-languages rule.

## Key technical claims

### Per-machine size and location

| Machine | Size | Location | Notes |
|---|---|---|---|
| B+ | 12 KB | `&8000-&AFFF` (top of shadow RAM, above the 20 KB shadow screen) | Paged in by setting top bit of `&FE30` ROMSEL |
| Master 128 | 4 KB | `&8000-&8FFF` | Reserved for MOS system variables (see AllMem `&8000-&8FFF` workspace breakdown) |

Master also exposes a separate 8 KB area as **HAZEL** at `&C000-&DFFF` (controlled by ACCCON `Y` — see `[[memory/shadow-ram]]`).

### Access methods

1. **Paged-ROM space**: write `&FE30` with the top bit set (in addition to the bank number). Then `&8000-` reads/writes hit ANDY rather than the selected sideways bank.
2. **OSWORD `&05`** — read byte using addresses formatted as `&FFFExxxx`.
3. **OSWORD `&06`** — write byte using same address format.

The `&FFFExxxx` form is the I/O-processor "extended" addressing convention; the high `&FFFE` selects ANDY, low 16 bits select the offset.

### B+ shadow-display trick

On the B+, code at `&A000-&AFFF` can directly manipulate shadow RAM display memory. The shadow display physically occupies the bottom 20 KB of the same RAM that ANDY pages into; mapping ANDY makes a 4 KB window into the top of shadow RAM addressable as normal memory.

Behaviour when shadow display is disabled is undocumented.

### MOS behaviour

> The MOS will not search for languages or service ROM images in this space.

Both B+ and Master. Implication: if you put code at `&8000` in ANDY, you cannot enter it via `*command` dispatch — you must JSR directly with the right ROMSEL value already set.

### Caveat

Original B+ documentation warned ANDY "may not be available in 'other Acorn products'". On the Master the address range and size differ (4 KB vs 12 KB) and the use is reserved for MOS — write-access from user code risks corrupting MOS state.

## Cross-check against existing wiki

| Claim | Wiki state | Resolution |
|---|---|---|
| ANDY on B+ = 12 KB at `&8000-&AFFF` | covered in `[[memory/paged-rom]]` and `[[memory/memory-map]]` | no change |
| ANDY on Master = 4 KB at `&8000-&8FFF` | covered | no change |
| OSWORD `&05`/`&06` extended addressing | not documented | **add to `[[memory/paged-rom]]`** |
| B+ `&A000-&AFFF` window onto shadow display | not documented | **add to `[[memory/paged-rom]]`** + cross-link `[[memory/shadow-ram]]` |
| MOS won't scan ANDY for languages | not stated | **add a one-liner to `[[memory/paged-rom]]`** |

## Filed into

- Updated: `[[memory/paged-rom]]` (OSWORD `&05`/`&06` access; B+ `&A000-&AFFF` shadow trick; MOS scan rule).
