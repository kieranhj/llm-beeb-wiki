---
title: BeebAsm — gotchas from two ports
type: tool
tags: [beebasm, assembler, build, toolchain, ssd]
sources: [beeb-port-kit-hardware-facts, naug-ch02-basic-assembler]
updated: 2026-09-06
---

# BeebAsm — gotchas from two ports

[BeebAsm](https://github.com/stardot/beebasm) (Rich Talbot-Watkins, 2004 onwards) is the community-standard cross-assembler; its syntax is a near-superset of the BBC BASIC inline assembler documented on [[tools/basic-assembler]]. This page is not a syntax reference — it is the list of things that **cost a build** during two C64-to-BBC ports by Kieran Connell, [Paradroid](https://github.com/kieranhj/paradroid-beeb) and [Edge Grinder](https://github.com/kieranhj/edge-beeb), both on **beebasm 1.11**. Source: [[sources/beeb-port-kit-hardware-facts]] §10 (and §6 for the disc-order item).

## Conditional assembly and command-line symbols

- **There is no `IFDEF`, and a symbol defined twice is an error.** So a source file cannot carry a default for a command-line symbol: every invocation must pass `-D RELEASE=0` (and every other such flag) or assembly stops with *Symbol not defined*. A build with one optional flag therefore needs every bare invocation to pass it — which is why Paradroid's `!BOOT` wiring became a post-processor patch instead of a `-D`. (Paradroid, 2026-08-26 and 2026-08-29, [`CLAUDE.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/CLAUDE.md), [`docs/intro.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/intro.md).) Edge Grinder passes four such symbols on every build and stamps every one that changes the disc's contents into `!BOOT`, so a build cannot lie about itself.
- **Constant assignments resolve in file order**, so shared constants go in the top file before the `INCLUDE`s that need them.
- **beebasm will not `INCLUDE` inside a braced `{}` block.** A generated table that a braced routine needs must be INCLUDEd outside the braces. ([Edge `CLAUDE.md`](https://github.com/kieranhj/edge-beeb/blob/master/CLAUDE.md).)

## Labels

- **A local label inside `{}` shadows a global of the same name, silently.** `sta comp_flag` next to a local `.comp_flag` would have stored into code. Assembles cleanly, fails quietly. Do not name a local label after anything it is used next to. (Edge, `wave_manager`.)
- **An undefined symbol is assembled as an absolute address in pass 1**, then errors on the size change in pass 2 when it turns out to be zero page. Declare zero-page slots before the code that uses them. (Edge, 2026-09-04, [`docs/layer-9-loader.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-9-loader.md).) The same trap in the BASIC assembler is on [[tools/basic-assembler]] — there it shifts every later label by a byte.

## Output, `SAVE` and disc images

- **beebasm writes progress and success messages to stderr.** In PowerShell under `$ErrorActionPreference = 'Stop'`, redirecting that stream (`2>&1`) raises `NativeCommandError` on a *successful* build. Redirect stdout alone and check the exit code. From bash, `2>&1` is fine. (Both ports' `CLAUDE.md`.)
- **`SAVE` writes a loose host file whenever there is no disc image to put it in**, so a run without a working `-do` drops every SAVEd file in the working directory, and a `-do` path that cannot be written leaves a build that looks like it worked. (Paradroid `CLAUDE.md`.)
- **beebasm lays files on the disc in `SAVE` order.** That put `!BOOT` and the main executable physically last; every boot read the end of the disc and seeked back to track 0. Reordering into boot-access order was the whole of a 6.01M → 4.33M cycle saving on the first boot phase. (Paradroid, 2026-08-21, [`docs/loader-compression.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/loader-compression.md).) Both ports post-process the SSD with a Python tool that rewrites the catalogue in access order; see [[techniques/zx0-loading]].
- **beebasm's own image need not be bootable.** Edge Grinder's `EDGE-RAW.SSD` is beebasm's output and every data file on the shipped disc is ZX0-compressed by a second pass; hand the second image to the emulator. And jsbeeb **does** boot an unpadded SSD — see [[tools/emulators]].
- **`INCLUDE` and `INCBIN` resolve from the working directory**, so the build must run from the project root (or from inside a vendored directory whose paths are relative to itself). (Edge [`docs/layer-0-toolchain.md`](https://github.com/kieranhj/edge-beeb/blob/master/docs/layer-0-toolchain.md); Paradroid `CLAUDE.md`.)
- **The assembler works in one 64K image**: a file assembled at an address after another file's `SAVE` lands on the earlier file's bytes, so the order of the two is load-bearing. (Paradroid [`docs/layer-13-compatibility.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-13-compatibility.md).) Edge Grinder assembles `!BOOT` at `&2600` — inside a region that only exists at run time — for exactly this reason.

## `GUARD`, `CLEAR`, `SKIP`, `ALIGN`

- **`CLEAR` releases beebasm's overwrite check; `GUARD` is what catches an overrun.** `CLEAR A, B` over the range an over-long image spills into means the overrun assembles silently and corrupts whatever loads there at run time. Keep a `GUARD` at the top of every image. (Paradroid `CLAUDE.md`.) Edge adds `ASSERT code_end <= SPR_SAVE` for a ceiling that is lower than the image's `GUARD` because the region above it is rewritten at run time.
- **`SKIP` emits nothing, so a listing-based gap finder cannot tell reserved storage from padding.** A "739 bytes of alignment holes" claim was four `SKIP`ped tables; the genuine `ALIGN` padding was 111 bytes, and removing it freed nothing because the next `ALIGN` padded by the same amount. (Paradroid RAM pass, 2026-08-25, [`docs/layer-13-ram-pass.md`](https://github.com/kieranhj/paradroid-beeb/blob/main/docs/layer-13-ram-pass.md).)
- **Spending one byte past an `ALIGN` pad costs 256 at a stroke**; anything assembled before the pad rides in it for nothing. Quote a bank's pad and tail as a pair.

## Useful tricks

- **`TIME$` stamps the assembly time** — put it in `!BOOT` so any disc image can be dated. (Edge.)
- **The symbol dump** — `beebasm -i src/main.asm -do build/symbols.ssd -D RELEASE=0 -d | tr ',' '\n' | grep "'name'"` prints every global label as `'name':decimal`, the quick way to find a variable's address for an emulator poke. `-do` is there only to stop the loose files. (Paradroid `CLAUDE.md`.)
- **A mechanical change can be proved mechanical** by reducing both `-v` listings to a stream of (mnemonic, addressing class) and comparing, or by extracting the files from both SSD catalogues and comparing bytes. Edge Grinder has no automated tests; this is its regression check. (Edge `docs/layer-0-toolchain.md`.)
- **Boot-only code can live where run-time data will be.** Both ports put their loader and depacker above the code ceiling, in memory that a sprite blitter or a screen overwrites once the game is running — the assembler does not care, and it is the tightest region in the build. Just `ASSERT` that nothing read in play is there (Edge's `BUGS.md` #13 is a table that drifted over the line).

## See also

- [[tools/basic-assembler]] — the syntax this dialect comes from, and porting notes.
- [[tools/emulators]] — what to hand the result to, and how to measure it.
- [[techniques/zx0-loading]] — the second build pass both ports use.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
