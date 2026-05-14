# Quartz setup plan — publishing the wiki to GitHub Pages

Plan for serving `wiki/` as a browsable site via [Quartz v4](https://quartz.jzhao.xyz/) on GitHub Pages. Build once, push, and the wiki becomes readable in any browser with working wikilinks, backlinks, search, and graph view.

## Pre-flight decisions

Before starting, decide:

| Decision | Default | Alternative |
|---|---|---|
| **Quartz location** | Same repo, `quartz/` subdir | Separate repo that pulls `wiki/` as a git submodule |
| **Content layout** | Symlink `wiki/` → `quartz/content/` at build time | Move `wiki/` → `content/` (more conventional but breaks current paths) |
| **Branch strategy** | Quartz GH Action builds + deploys to `gh-pages` branch automatically | Manual `npx quartz build` + push |
| **Site URL** | `https://kieranhj.github.io/llm-beeb-wiki/` | Custom domain via CNAME (later) |
| **Theme** | Quartz default (clean, dark/light toggle) | Custom CSS / custom layout |
| **Public vs unlisted** | Public (already a public repo) | Add `noindex` meta if you want to keep it from search engines |

Recommended defaults in **bold** below.

## Step-by-step

### 1. Install prerequisites

- Node.js ≥ 22 (`node --version`). Install from nodejs.org or via winget/nvm if missing.
- Git already configured (done).

### 2. Bootstrap Quartz in a subdirectory

```powershell
cd C:\Users\khcon\OneDrive\BEEB\Projects\llm-beeb-wiki
git checkout -b quartz-setup
npx quartz create
```

Quartz's interactive setup will ask:

- **Where is your content?** → `../wiki` (or wherever you've placed `wiki/`)
  - Or **Symlink**: keep `wiki/` at repo root, create `quartz/content` → `../wiki` symlink (Windows: `mklink /D` or copy on build).
- **Treat links as Obsidian-style?** → **Yes**.
- **Sync changes via GitHub?** → **Yes** (it'll add a workflow file).

The bootstrap creates a `quartz/` directory containing `quartz.config.ts`, `quartz.layout.ts`, content/, public/, etc.

### 3. Configure for this wiki

Edit `quartz/quartz.config.ts`:

```ts
const config: QuartzConfig = {
  configuration: {
    pageTitle: "llm-beeb-wiki",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,                    // or { provider: "plausible" } etc.
    locale: "en-GB",
    baseUrl: "kieranhj.github.io/llm-beeb-wiki",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Schibsted Grotesk",
        body: "Source Sans Pro",
        code: "IBM Plex Mono",
      },
      colors: { /* keep defaults or tweak */ },
    },
  },
  // ... plugins below
}
```

Key plugin settings (in the same file, under `plugins.transformers`):

- Ensure `Plugin.ObsidianFlavoredMarkdown({ enableWikilinks: true })` is enabled — that's what resolves `[[wikilinks]]`.
- Keep `Plugin.SyntaxHighlighting()` for asm code blocks.
- `Plugin.Latex({ renderEngine: "katex" })` if any math appears (probably not).

### 4. Handle the wiki's quirks

The wiki has a few non-standard bits worth checking:

- **Hex addresses in frontmatter** (`sheila: ["&FE00", "&FE01"]`). Quartz's YAML parser should handle quoted strings fine — verify after first build.
- **Anchor links** (`[[hardware/6502-isa#summary]]`). Should resolve to heading anchors automatically.
- **Stub wikilinks** (`[[techniques/raster-splits]]`) — Quartz renders these as "ghost" links with a different style. Fine; signals to readers what's planned.
- **Page-3 workspace tables** with leading `&` and pipe-separated values — render correctly as markdown tables.
- **Inline assembly code blocks** (` ```asm `) — Quartz syntax-highlights via Prism/Shiki. Should look right out of the box.

### 5. Customise the layout

Edit `quartz/quartz.layout.ts` to:

- Show backlinks on every page (default).
- Show graph view on right sidebar (default).
- Enable explorer/file tree on left (default).
- Possibly disable the "right sidebar" on mobile to save space.
- Add a custom header link to the GitHub repo.

### 6. Local preview

```powershell
cd quartz
npx quartz build --serve
```

Opens `http://localhost:8080`. Check:

- Index page renders.
- Wikilinks click through.
- Backlinks panel shows on entity pages.
- Graph view at root shows the page network.
- Search (`Cmd+K` / `Ctrl+K`) works.
- Code blocks colourised.
- Hex addresses in frontmatter don't break rendering.

### 7. GitHub Pages deployment

Quartz's bootstrap should have created `.github/workflows/deploy.yml`. Verify it's there. If not, copy the template from [Quartz docs hosting page](https://quartz.jzhao.xyz/hosting).

Then in GitHub:

1. Repo → Settings → Pages.
2. **Source**: GitHub Actions (not "deploy from branch").
3. The first push of the `quartz-setup` branch should trigger the build.
4. Once it succeeds, merge to `main`. Subsequent pushes to `main` auto-redeploy.

### 8. Verify the live site

After ~2 minutes (first build can take longer), visit:

```
https://kieranhj.github.io/llm-beeb-wiki/
```

Check the same things as local preview, plus:

- Page URLs use clean paths (`/hardware/6502/` not `/hardware/6502.md`).
- No mixed-content warnings.
- Open Graph tags render correctly on link previews (Twitter, Slack).

### 9. README update

Add a "Browse online" section at the top of `README.md`:

```markdown
## Browse online

[**kieranhj.github.io/llm-beeb-wiki**](https://kieranhj.github.io/llm-beeb-wiki/) — full wiki with search, backlinks, and graph view.
```

## Maintenance

- **Adding pages**: just write markdown in `wiki/` and push. The Action rebuilds on every push to `main`.
- **Theme tweaks**: edit `quartz/quartz.config.ts` or `quartz/styles/custom.scss`.
- **Quartz upgrades**: `cd quartz; npx quartz update` (Quartz pulls the latest version into your tree as merged commits).
- **Broken builds**: most often caused by malformed frontmatter. The Action log shows which file fails. Quartz is strict-by-default but configurable.

## What's NOT being addressed

This plan deliberately doesn't cover:

- **Custom domain** — easy later: add a `CNAME` file to `quartz/static/`, configure DNS, enable HTTPS in repo Pages settings.
- **Search indexing controls** — Quartz indexes the whole site by default. If you want to exclude work-in-progress pages, add them to `ignorePatterns` or set `draft: true` in frontmatter.
- **RSS feed** — Quartz can generate one; add `Plugin.ContentIndex({ enableRSS: true })`.
- **Analytics** — opt-in via the config. Plausible / Umami are privacy-respecting choices.
- **Per-page CSS variations** — possible but adds complexity. Skip until needed.

## Time estimate

- Bootstrap + first local preview: **20-30 minutes**.
- Config tuning to taste: **another 20-30 minutes**.
- First successful GH Pages deploy: **5-10 minutes** once config works locally.
- Total: **~1 hour** end to end for someone with Node/git already set up.

## Decision points to revisit when starting

1. **Repo structure** — same repo or separate? Same-repo is simpler; separate is cleaner if Quartz config evolves a lot.
2. **`wiki/` path** — keep as-is or rename to `content/`? Keeping `wiki/` is friendlier for non-Quartz users (Obsidian, plain markdown viewers).
3. **What to publish** — entire wiki, or filter out draft / synthesis / template-ish pages? Default: publish everything.

## See also

- [Quartz documentation](https://quartz.jzhao.xyz/)
- [Quartz GitHub](https://github.com/jackyzha0/quartz)
- [Andy Matuschak's notes](https://notes.andymatuschak.org/) — an early popular example of Obsidian-vault-as-website (predates Quartz but same spirit).
- [Schema reference: CLAUDE.md](CLAUDE.md) — the wiki's structural conventions, useful context when configuring Quartz plugins.
