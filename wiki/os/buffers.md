---
title: Buffers
type: os
tags: [buffers, fifo, insv, remv, cnpv]
sources: [naug-ch09-buffers]
updated: 2026-05-13
---

# Buffers

MOS maintains nine FIFO buffers servicing slow peripherals — keyboard scan, RS423, printer, sound channels, speech. Producer and consumer run at different rates; the buffer decouples them so the foreground task doesn't block.

| ID | Name | Default size | Producer | Consumer |
|---|---|---|---|---|
| 0 | Keyboard input | 32 bytes | keyboard IRQ (CA2 on System VIA) | OSRDCH |
| 1 | RS423 input | 32 bytes | 6850 receive IRQ | OSRDCH (when input source = RS423) |
| 2 | RS423 output | 32 bytes | OSWRCH (when output → RS423) | 6850 transmit IRQ |
| 3 | Printer | 64 bytes | OSWRCH (when printer enabled) | printer driver (User VIA CA1) |
| 4-7 | Sound channels 0-3 | 16 bytes each | `OSWORD &07` (SOUND) | 100 Hz timer IRQ |
| 8 | Speech | — | speech driver | speech chip (Model B/B+ only) |

Buffer storage spans `&800-&9FF` ([[memory/os-workspace]]): sound + envelope + (optional) printer in `&800-&8FF`, CFS/RS423/speech output in `&900-&9BF`, speech/CFS input in `&9C0-&9FF`. Per-buffer base addresses, removal pointers, insertion pointers, and busy flags live in OS workspace bytes around `&2C3-&2DD` on Model B and similar regions on Master.

## Vectors

| Vector | Address | Purpose |
|---|---|---|
| INSV | `&22A/&22B` | Insert byte |
| REMV | `&22C/&22D` | Remove or examine next byte |
| CNPV | `&22E/&22F` | Count free / used space, or purge |

The default routines validate nothing — passing an out-of-range buffer ID is undefined. Hooks must check `X` themselves.

**Not available across Tube.** Buffer hooks must reside on the I/O processor — ideally in a service ROM ([[os/paged-roms]]).

## INSV — insert

```asm
LDA #value
LDX #buffer_id
JSR (insv_via_macro)  ; or JMP (&22A) from your own handler
; on exit: A, X preserved; Y undefined
; C=1 if buffer was full (insertion failed), C=0 if inserted
```

## REMV — remove or examine

V flag selects mode: **V=1 examine**, V=0 remove.

```asm
LDX #buffer_id
CLV               ; remove (or BIT $XX where XX has bit 6 set, for examine)
JSR remv_chain    ; or JMP (&22C)
; remove: Y = byte just removed, A undefined, X preserved
; examine: A = byte without removing, Y undefined, X preserved
; C=1 if buffer was empty
```

## CNPV — count or purge

V=1 → purge (clear buffer).
V=0 → count. C=1 → return *free space*. C=0 → return *content length*.

```asm
LDX #buffer_id
JSR cnp_chain     ; X+Y = 16-bit count (low+high) for count modes
                  ; X, Y preserved for purge
```

## OSBYTE wrappers (no vector access needed)

| OSBYTE | Function | X / Y |
|---|---|---|
| `&0F` (15) | Flush class | X=0 → all buffers; X≠0 → input buffers only |
| `&15` (21) | Flush specific buffer | X = buffer ID (0-8) |
| `&80` (128) | Read buffer status | X = `&FF - id` (so &FF=kbd, &FC=printer, &FB=sound 0). Returns count in X. **Collides with ADC read** when X < 4. |
| `&8A` (138) | Insert | X = buffer, Y = byte. C=1 if full. |
| `&91` (145) | Get byte | X = buffer. Y = byte. C=1 if empty. |
| `&98` (152) | Examine next | X = buffer. **OS 1.20 / Model B**: Y = pointer offset from `&FA/&FB`; **later OS**: Y = byte itself. |
| `&99` (153) | Insert into input | X = 0 (kbd) or 1 (RS423). Generates event 2 ([[os/events]]). Honours ESCAPE-character (`OSBYTE &DC`) by generating event 6 if matched. |

The OSBYTE `&80` ID-inversion is unique to this call. Other buffer OSBYTEs use the direct ID (0-8).

## Hooking the vectors

Common reason: replace the **printer buffer** (default 64 bytes is tiny) with a 4-KB or larger user buffer. Pattern:

1. SEI.
2. Save current `&22A-&22F` to your handler's chain locations.
3. Install your INSV/REMV/CNPV addresses.
4. CLI.

Inside each handler:

```asm
.my_insv
    CPX #my_buffer_id
    BNE chain_to_os
    ; ... handle insert into your buffer ...
    RTS
.chain_to_os
    JMP (old_insv)
```

NAUG §9.4 p137-138 has a complete worked example installing a user-defined printer buffer (`*FX 21,3` first to flush the old one, then hook). It uses zero-page `&80-&83` for the input/output pointer pair — note the conflict with BASIC's user zp.

## Buffer events

The buffer system feeds events ([[os/events]]):

- **Event 0** (output buffer empty) — fires just after REMV takes the last byte. X = buffer.
- **Event 1** (input buffer full) — fires when INSV would fail. X = buffer, Y = byte that couldn't fit.
- **Event 2** (char entering input buffer) — fires from `OSBYTE &99` and the keyboard IRQ. Y = ASCII char.

## Performance notes

- Buffer ops are **IRQ-driven** for hardware-fed buffers (keyboard, 6850, printer ACK, sound timer). Foreground reads/writes via OSWRCH/OSRDCH and OSBYTE wrappers walk the buffers without polling the hardware.
- For **maximum throughput** to the printer or RS423, bypass MOS entirely: hook the relevant device IRQ yourself, and drive the chip register-by-register. Buffers add per-byte overhead (vector dispatch + ptr math + IRQ wakeup). The trade-off is reimplementing flow control / ACK handshake.
- The **sound channel buffers** are the one place you can't really bypass and still use MOS sound — if you want fully custom sound, drive the SN76489 directly ([[hardware/sn76489]]) and ignore the buffers.

## See also

- [[memory/os-workspace]] — Buffer RAM at `&800-&9BF`, pointer table around `&2C3-&2DD`.
- [[os/events]] — Buffer events 0/1/2.
- [[hardware/system-via]] — Keyboard CA2, ADC CB1 (consumers).
- [[hardware/user-via]] — Printer CA1 (printer-buffer consumer).
- [[hardware/sn76489]] — Sound chip (sound-buffer consumer).

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
