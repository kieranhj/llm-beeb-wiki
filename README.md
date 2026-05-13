# llm-beeb-wiki

A persistent, LLM-maintained knowledge base for writing high-performance code on the BBC Micro family (Model B, B+, Master 128, Master Compact, Electron). Built incrementally from technical sources — primarily *The New Advanced User Guide* by Holmes & Dickens — using the [LLM Wiki](https://github.com/karpathy/) pattern: the human curates sources, the LLM compiles and maintains a structured, interlinked wiki of markdown pages.

## What's here

- **`CLAUDE.md`** — the schema. Tells the LLM how the wiki is organised, what conventions to follow, and what workflows to use for ingest / query / lint. Also serves as the human-facing introduction to how this wiki works.
- **`wiki/`** — the wiki itself. Markdown files organised by domain (hardware, memory, video, timing, OS, techniques, synthesis, tools). All written by an LLM agent against the schema; the human reviews and corrects.
  - `index.md` — content catalog.
  - `log.md` — chronological log of every ingest / lint / synthesis pass.
  - `sources/` — one page per ingested source, with citations.
  - `hardware/`, `memory/`, `video/`, `timing/`, `os/` — entity / concept pages.
  - `techniques/`, `synthesis/`, `tools/` — derived / cross-cutting pages.
- **`tools/`** — small Python helpers for PDF text extraction (used during ingest).

## What's *not* here

- **`raw/`** — source PDFs, web clippings, personal notes. Not committed; the New Advanced User Guide is © Adder Publishing and not redistributable.
- **`.claude/`** — Claude Code's per-machine memory and session state.

## Browsing

The wiki is plain markdown with Obsidian-style `[[wikilinks]]`. Open in:

- **Obsidian** for the linked-graph view and backlinks.
- **VS Code** or any markdown viewer for plain reading.
- **GitHub** rendering — wikilinks won't resolve, but pages are still readable.

Start at `wiki/index.md`.

## Status

- 23 of 24 NAUG chapters ingested (Ch1 — beginner intro — intentionally skipped) plus both appendices.
- ~70 wiki pages across all categories.
- Most pages cite specific NAUG page numbers; cross-references between pages are dense.

## Adding to the wiki

Drop a source into `raw/`, then ask the LLM to ingest it. The schema in `CLAUDE.md` defines the workflow.

### Where to find source documents

[**bitshifters/bbc-documents**](https://github.com/bitshifters/bbc-documents) is the canonical online archive for BBC Micro reference material — Acorn manuals, application notes, chip datasheets, technical references. Most of the documents this wiki cites can be found there.

## Licence

Wiki content is © the contributors and licensed CC-BY-4.0. Schema and tooling are CC0 / public domain. The BBC Micro and related trademarks belong to their respective owners. Source PDFs are not redistributed here.
