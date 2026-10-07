---
title: ZX0 compressed loading — in-place unpacking rules
type: technique
tags: [zx0, compression, loader, dfs, boot, staging]
sources: [beeb-port-kit-hardware-facts]
updated: 2026-09-06
---

# ZX0 compressed loading

Shipping every data file ZX0-compressed and running a depacker over it at boot, as both of Kieran Connell's ports do ([Paradroid](https://github.com/kieranhj/paradroid-beeb) on a Model B, [Edge Grinder](https://github.com/kieranhj/edge-beeb) on a Master 128). [ZX0](https://github.com/einar-saukas/ZX0) is Einar Saukas's LZ-family format with a tiny 6502 depacker. The rules below are the ones that were **measured**; source [[sources/beeb-port-kit-hardware-facts]] §9, with §6 for the disc facts.

## The in-place rule

**ZX0 unpacks forwards; a stream may share memory with its output only while the reader stays ahead of the writer.** The rule of thumb "the stream must end where the output ends" is *not enough*: the required gap is a property of THIS stream, because a literal run copies 1:1 plus flag bits and the writer can gain on the reader locally.

- Walk the decode offline and track `max(write_index − bytes_consumed)`. For Paradroid's font that was 1,566 bytes, with the worst point at the very end (ZX0's closing matches consume almost no input). Check it every build — the tool that builds the disc should refuse an image where any stream overlaps its own output by less than its measured delta. (Paradroid, 2026-08-29, `make_disc.py`'s `in_place_delta()`, verified by booting in jsbeeb; [`docs/loader-compression.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/loader-compression.md).)
- **A full 20K screen cannot be unpacked in place from inside the screen**: the stream's tail would run past `&8000`. Stage it below the screen, and split it if the staging area is small — Edge Grinder's loading picture is two files staged in the sprite-save area at `&2400`. (Edge 2026-09-04, [`docs/layer-9-loader.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-9-loader.md); Paradroid intro 2026-08-30.)
- **On a Master, the shadow screen is 20K nobody is looking at** while main RAM is displayed, so with ACCCON `D = 0`, `X = 1` it is a free staging area for every bank and music stream. See [[memory/shadow-ram]].

## Where a stream may NOT be staged

- **Not at `&0800-&08FF` while the MOS still owns IRQ1V.** The MOS's 100 Hz sound driver writes there, and one changed byte sends the depacker off a wrong offset: 542 wrong bytes across a credits screen, found by diffing the depacked output, not by looking at it. `&1100` (the DFS random-access buffers, untouched by `*LOAD`/OSFILE) is the safe staging address on a Model B. (Paradroid, 2026-08-30, [`docs/intro.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/intro.md).) See [[memory/os-workspace]].
- **Not at `&8000`** — the DFS ROM is paged in there during a filing-system call, so a sideways bank cannot be loaded direct even uncompressed. Stage below and unpack into the paged-in slot. See [[memory/paged-rom]].
- **Not into HAZEL or ANDY** via OSFILE on a Master — HAZEL is the filing system's own workspace and ANDY cannot be written while the filing system runs. Stage, then unpack up with the region paged in. Load HAZEL's contents **last**. See [[memory/shadow-ram]].

## What compression actually buys

- **Already-compressed data does not compress again.** A bank whose deck maps and character bitmaps were already ZX0 streams packed to 63.9%; four compiled sprite shifts of the same data packed to 18.5%. (Paradroid, 2026-08-21.)
- **A size-optimised depacker costs about 40k cycles per 1K** on deck maps, rising on less compressible data. (Paradroid, 2026-08-21.)
- **On a Master with a 1770 DFS, compression roughly pays for a loading picture and no more**: reading 37,632 bytes instead of 91,904 saved about 9 s of disc, and unpacking 74,752 bytes plus drawing a 20K picture cost almost all of it back (11.1 s → 10.9 s, `*RUN` to the IRQ install). (Edge, 2026-09-04, jsbeeb.) The win is the picture on screen while the banks load, not the clock.
- **DFS throughput is about 0.07 s a sector, plus about 0.7 s once per path for the first access after the drive has been idle** (motor spin-up). The same 368-byte file cost 0.181 s or 0.902 s depending on nothing but context; every non-first load sat in 0.046-0.091 s/sector with no measurable per-file overhead, so **merging files buys nothing**. Effective raw rate ~5.6 KB/s, ~14 sectors/s. **This is jsbeeb's disc model**; a faster reader's gain is only real if the model is faithful. (Paradroid, 2026-08-29, breakpoints on the `JSR &FFF7` sites.)
- **Lay the files out in boot access order.** beebasm writes them in `SAVE` order, which put `!BOOT` last; reordering was the whole of a 6.01M → 4.33M cycle saving on the first boot phase. See [[tools/beebasm]].

## Loader discipline that came out of it

- **Every `*LOAD`/OSFILE happens before IRQ1V is taken**; after that the MOS is not servicing the filing system. See [[os/interrupts]].
- **The MOS's disc code needs VSync**: with R7 parked where VSync never fires the second `*LOAD` hung in DFS's 8271 status poll at `&ACAE`. Do not park the CRTC before the last load. See [[os/filing-systems]].
- **OSFILE writes the file's catalogue addresses back into its parameter block**, so reset load/exec before every call or the second file lands where the first said. See [[os/filing-systems]].
- **`VDU 22` clears `&3000-&7FFF`**, so anything staged above `&3000` is wiped by a later mode change — change mode first. See [[os/vdu]].
- **Blank with R8 (`&30`) and hide the cursor with R10 (`&20`)** while the screen is being filled; `R6 = 0` leaks a row and shows the stream. See [[hardware/crtc-6845-advanced]].

## See also

- [[tools/beebasm]] — why a second pass builds the disc.
- [[memory/os-workspace]] — what low RAM is reclaimable for staging.
- [[os/filing-systems]] — OSFILE behaviour and DFS traps.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
