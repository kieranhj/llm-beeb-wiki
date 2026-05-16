# BBC Micro Performance Wiki — Schema

A personal knowledge base for writing highly performant code on the BBC Micro series (Model B, B+, Master 128, Electron-adjacent topics). The wiki exists to compile hardware-specific knowledge — 6502 CPU timing, memory map quirks, ULA behaviour, video mode tradeoffs, MOS/OS calls, sideways RAM/ROM, 1MHz bus, Tube, etc. — into a structured, interlinked reference that supports fast lookup while writing assembly and demos.

You (Claude) own the wiki. The human curates sources and asks questions; you read, summarise, cross-reference, and maintain.

## Directory layout

```
llm-beeb-wiki/
├── CLAUDE.md              # this file (the schema)
├── MEMORY.md              # auto-memory index (separate system, do not confuse)
├── raw/                   # IMMUTABLE source documents — never edit
│   ├── articles/          # web clippings (.md from Obsidian Web Clipper)
│   ├── manuals/           # PDFs: Advanced User Guide, NAUG, Service Manual, etc.
│   ├── notes/             # human's personal project notes
│   ├── discord/           # exported Discord threads (.md or .txt)
│   └── assets/            # images, diagrams referenced by raw/ files
└── wiki/                  # LLM-owned markdown — you write everything here
    ├── index.md           # content catalog (see below)
    ├── log.md             # chronological action log (see below)
    ├── overview.md        # top-level synthesis / entry point
    ├── hardware/          # entity pages for chips, buses, ports
    │   ├── 6502.md
    │   ├── ula.md
    │   ├── crtc-6845.md
    │   ├── system-via.md
    │   ├── user-via.md
    │   └── ...
    ├── memory/            # memory map, paging, sideways RAM/ROM
    ├── video/             # MODE 0-7, palette, scrolling, raster effects
    ├── timing/            # cycle counts, 1MHz/2MHz stretching, vsync, rasters
    ├── os/                # MOS calls, vectors, OSWORD/OSBYTE, filing systems
    ├── techniques/        # performance techniques (self-mod code, unrolling, LUTs, …)
    ├── tools/             # assemblers, emulators, debuggers (BeebAsm, b-em, …)
    └── synthesis/         # filed-back query results: comparisons, deep analyses
```

`raw/` is immutable. Read from it; never write to it.

## Page conventions

Every wiki page starts with YAML frontmatter:

```yaml
---
title: 6502 CPU
type: hardware           # hardware | memory | video | timing | os | technique | tool | source | synthesis
tags: [cpu, 6502, timing]
sources: [advanced-user-guide-ch1, article-tobynelson-cycles]
updated: 2026-05-13
---
```

- `sources:` lists the slugs of source pages in `wiki/sources/` (or raw filenames) that back the claims on this page. Every non-trivial claim should be traceable to at least one source.
- Use `[[wikilink]]` syntax for cross-references (Obsidian-compatible). Link liberally — broken links are fine and act as TODOs for pages worth writing.
- For 6502 / hardware claims, **always cite cycle counts, addresses, and bit numbers with their source**. Hardware details get misremembered; do not invent or smooth over uncertainty. If two sources disagree, record both and flag the contradiction.
- Use code fences with `asm` for 6502 assembly. Prefer BeebAsm syntax unless the source uses something else (note dialect at top of block).
- Annotate cycle counts inline where useful: `LDA #&00   ; 2c`
- Memory addresses: hex with `&` prefix (BBC convention) — e.g. `&FE00`. In code blocks, match the dialect of the assembler being shown.

## Page types (with templates)

**Hardware entity** (`wiki/hardware/*.md`): what it is, where it lives (addresses/pins), how it's accessed, quirks, common pitfalls, links to techniques that exploit it.

**Memory region** (`wiki/memory/*.md`): address range, who owns it, timing characteristics (1MHz stretched? screen contention?), what lives there in each MODE.

**Video mode** (`wiki/video/*.md`): resolution, colours, bytes/row, memory footprint, scan timing, common tricks.

**Timing** (`wiki/timing/*.md`): cycle tables, 1MHz bus access penalties, raster timing, vsync/hsync, interrupt latency.

**OS call** (`wiki/os/*.md`): name, vector/entry, registers in/out, side effects, faster alternatives if any.

**Technique** (`wiki/techniques/*.md`): a performance pattern. Includes a minimal worked example, cycle/byte cost, when to use, when *not* to use, real-world references.

**Source** (`wiki/sources/<slug>.md`): one per ingested item. Holds the summary, key extracts, and a "filed into" list naming every wiki page touched by the ingest. This is the audit trail.

**Synthesis** (`wiki/synthesis/*.md`): filed-back query answers — comparisons, deep dives, design analyses produced during querying.

## Operations

### Ingest

Triggered by: "ingest <path>" or dropping a file into `raw/` and asking to process it.

1. Read the source in full (for PDFs, identify which chapters are relevant first).
2. Briefly discuss key takeaways with the human before writing. Flag anything that contradicts existing wiki content.
3. Create `wiki/sources/<slug>.md` with: bibliographic info, 1-paragraph summary, bullet list of key technical claims (each with page/timestamp citation where possible), list of wiki pages this ingest will touch.
4. Update or create the affected entity/concept/technique pages. Add inline `[[source-slug]]` citations next to new claims.
5. Update `wiki/index.md`.
6. Append an entry to `wiki/log.md`.
7. Report back: what was added, what was changed, what contradictions surfaced, suggested follow-up questions.

Default mode: one source at a time, with the human in the loop. Batch ingest only on explicit request.

### Query

Triggered by: any technical question.

1. Read `wiki/index.md` first to locate relevant pages.
2. Read those pages, then drill into cited sources only if needed.
3. Answer with citations to wiki pages (and through them to raw sources).
4. If the answer is non-trivial (a comparison, derivation, worked example, new connection), **offer to file it back** as a page under `wiki/synthesis/` or as updates to existing pages. Don't auto-file without asking — the human decides what's worth keeping.
5. If the wiki lacks the data to answer, say so explicitly and suggest what source could fill the gap.

### Lint

Triggered by: "lint the wiki".

Check for:
- Contradictions between pages (especially cycle counts, addresses, bit assignments).
- Stale claims newer sources have superseded (compare `updated:` dates against `sources:`).
- Orphan pages (no inbound `[[links]]`).
- Important hardware/technique concepts referenced but lacking their own page.
- Code blocks missing dialect annotation.
- Claims missing source citations.
- Suggest new questions to investigate and sources to seek out.

Produce a report; do not auto-fix without confirmation.

## index.md format

Content-oriented catalog, grouped by section. Updated on every ingest. Example entry:

```
### Hardware
- [[hardware/6502]] — CPU core; addressing modes, cycle table, IRQ/NMI behaviour. (12 sources)
- [[hardware/ula]] — Video ULA; MODE register, palette, cursor. (4 sources)
```

Keep entries to one line. Use this file as a routing table when answering queries.

## log.md format

Append-only. Every entry starts with a consistent prefix so it's greppable:

```
## [2026-05-13] ingest | Advanced User Guide, Chapter 24 (Video ULA)
- Created: wiki/hardware/ula.md, wiki/sources/advanced-user-guide-ch24.md
- Updated: wiki/video/mode-7.md, wiki/timing/raster.md, wiki/index.md
- Flagged: cycle count for palette write disagrees with [[sources/article-tobynelson-cycles]]

## [2026-05-13] query | "fastest way to plot a pixel in MODE 1"
- Read: wiki/video/mode-1, wiki/techniques/pixel-plot, wiki/timing/screen-contention
- Filed back: wiki/synthesis/mode-1-pixel-plot-comparison.md
```

`grep "^## \[" wiki/log.md | tail -10` gives the recent timeline.

## Style rules for written content

- Be precise. "Roughly 2 cycles" is worthless on a 6502 — say `2c` or `2c (+1 if page crossed)`.
- Prefer tables for cycle counts, register layouts, memory maps.
- When something is uncertain or sourced from a Discord chat rather than an authoritative manual, mark it: `(unverified — [[sources/discord-2026-04-tube-timing]])`.
- Acorn / community terminology over generic terms: "MOS" not "OS firmware", "sideways ROM" not "bank-switched ROM", "1MHz bus" not "slow bus", etc.
- BBC hex convention (`&FE00`) in prose; match assembler dialect in code blocks.

## Page footer (every wiki page)

Every `.md` file under `wiki/` ends with an LLM-disclaimer footer. When creating a new page, append exactly:

```
---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
```

The `<!-- llm-wiki-footer -->` marker is the idempotency check — a footer-application script greps for this and skips files that already have it.

## Out of scope (for now)

- Embedding-based search / RAG infrastructure — `index.md` is enough at the expected scale.
- Auto-ingest pipelines — every ingest is interactive.
- Slide decks / charts — add if and when a use case appears.

## Bootstrap

When this schema is first applied (no `wiki/` directory yet), create the skeleton: empty `index.md`, empty `log.md`, and the section subdirectories listed above with a `.gitkeep` in each. Then wait for the first source.
