---
title: NAUG Ch9 — Buffers
type: source
parent: [[sources/naug]]
pages: 143-153
section: §9
tags: [buffers, insv, remv, cnpv, fifo, keyboard, printer, sound]
updated: 2026-05-13
---

# NAUG Ch9 — Buffers

Holmes & Dickens, *The New Advanced User Guide*, pp.143-153. The **buffer** layer is FIFO queues between producers (keyboard scan, OSWRCH, SOUND command) and consumers (input reader, printer driver, sound chip). All operate at the IRQ layer so the foreground task doesn't block waiting for slow peripherals.

## Buffer IDs

| ID | Buffer | Default size |
|---|---|---|
| 0 | Keyboard input | typically 32 bytes |
| 1 | RS423 input | typically 32 bytes |
| 2 | RS423 output | typically 32 bytes |
| 3 | Printer | typically 64 bytes (`&40`) |
| 4 | SOUND channel 0 | typically 16 bytes |
| 5 | SOUND channel 1 | typically 16 bytes |
| 6 | SOUND channel 2 | typically 16 bytes |
| 7 | SOUND channel 3 | typically 16 bytes |
| 8 | Speech | (only used if speech hardware fitted) |

Memory for **all** buffers is reserved on every machine, even where the hardware isn't present. Buffer storage lives at `&800-&9BF` and around (`[[memory/os-workspace]]`).

## Vectors

| Vector | Address | Purpose |
|---|---|---|
| INSV | `&22A/&22B` | Insert byte into buffer |
| REMV | `&22C/&22D` | Remove (or examine) next byte |
| CNPV | `&22E/&22F` | Count free / used space, or purge |

**No ID validation** — passing an out-of-range buffer ID has undefined behaviour. **Not available across Tube** — vector hooks must reside on the I/O processor (ideally in a service ROM).

## INSV — insert into buffer

Entry: A = value, X = buffer ID.
Exit: A, X preserved. Y undefined. **C=1 if buffer full**, C=0 if inserted.

## REMV — remove or examine

Entry: X = buffer ID. V flag selects mode: **V=1 examine** (don't remove), V=0 remove.

Exit:
- Remove (V=0): Y = byte just removed, A undefined, X preserved.
- Examine (V=1): A = next byte without removing, Y undefined, X preserved.
- C=1 if buffer was empty.

## CNPV — count or purge

Entry: X = buffer ID. V=1 purge / V=0 count. For count: C=1 means "return free space", C=0 means "return content length".

Exit: X (low) + Y (high) form the 16-bit count. (For a purge, X/Y are preserved.)

## OSBYTE wrappers

| OSBYTE | Function | Notes |
|---|---|---|
| `&0F` (15) | Flush buffer class | X=0 all, X≠0 input buffers only |
| `&15` (21) | Flush specific buffer | X = buffer number (0-8) |
| `&80` (128) | **Read buffer status** | X = 0xFF-id (e.g. `&FF` for keyboard, `&FC` for printer). Returns count in X. |
| `&8A` (138) | Insert byte | X = buffer, Y = value. C=1 if full. |
| `&91` (145) | Get byte | X = buffer. Y = byte. C=1 if empty. |
| `&98` (152) | Examine next byte | Same as REMV examine. **OS 1.20 and earlier**: Y is a *pointer* indexed off `&FA/&FB` zp; later OS: Y is the byte itself. |
| `&99` (153) | Insert into input buffer | X = 0 (keyboard) or 1 (RS423); Y = char. Generates input event 2. |

`OSBYTE &80` uses the *inverted* buffer ID (`&FF` = id 0, `&FE` = id 1, etc.) — collision with ADC channel read, where X has the channel number. `[[os/osbyte]]` has the mapping.

## Notes for buffer-vector hooking

Several caveats from NAUG §9.4 p137-139:

- No ID validation in the OS routines — your custom INSV/REMV/CNPV handler should check `X` before claiming.
- Hooks must live in the I/O processor (Tube limitation).
- The right place for hooks is a **service ROM** — sideways RAM or EPROM. Otherwise BASIC will trample the handler code (the NAUG example explicitly warns about this).
- OS calls that touch buffers (OSBYTE, OSWRCH, OSWORD &00, etc.) implicitly go through these vectors — your hook applies everywhere.

## Filed into

- `[[os/buffers]]` — Buffer reference + vector hook patterns.
- Updates: `[[os/osbyte]]` entries `&0F`/`&15`/`&80`/`&8A`/`&91`/`&98`/`&99` now point here.
- Updates: `[[memory/os-workspace]]` cross-links — buffer RAM at `&800-&9BF`.

## Open follow-ups

- **Sound buffer mechanics**: how the SOUND OSWORD enqueues into channel 0-3 buffers and how the 100 Hz IRQ services them — covered in Ch21 ingest.
- Exact per-buffer base addresses and lengths — NAUG p114 has the page-1 sound layout; full table would need to dump zp `&E2-&E6`-ish for CFS state and the OS workspace buffer pointers at `&2C3-&2D4` (Master) / `&2CC-&2DD` (Model B).
