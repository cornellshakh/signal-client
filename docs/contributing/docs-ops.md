---
title: Docs ops runbook
description: How we build, preview, and publish the MkDocs site.
---

# Docs ops runbook

## Versions and plugins
- MkDocs: **1.6.1** (strict mode on).
- Material: **9.7.x** (maintenance channel; minimal overrides for easy theme swap).
- Versioning: `mike` with `latest` alias; tags promote versioned docs.
- Core plugins: awesome-pages, section-index, mkdocstrings[python], mike, i18n (default en), redirects, git-revision-date-localized, minify, mermaid2, glightbox, Material blog/feed.
- Governance: propose new plugins via PR, include maintenance status and perf impact; pin versions in `pyproject.toml`.

## Commands
- Local preview: `poetry run mkdocs serve`
- Strict build: `poetry run mkdocs build`
- Versioned publish (dry run): `poetry run mike deploy --update-aliases 0.1.0 latest --push --remote origin --dry-run`
- Promote tag: `poetry run mike deploy --update-aliases $VERSION latest --push --remote origin`
- Set default: `poetry run mike set-default latest --push --remote origin`

## Quality gates (CI)
- Broken references: `mkdocs build --strict`
- Links: `lycheeverse/lychee-action` on built `site/`
- Markdown style: `pymarkdown scan`
- Spell check: `codespell` with project dictionary

## Previews and deploys
- PRs: build docs, run quality checks, upload `site` as artifact, and (when permitted) publish a GitHub Pages preview.
- Default branch: build + mike deploy `latest` to `gh-pages`.
- Tags: promote tag version with `mike` and keep `latest` alias in sync.
- Rollback: redeploy previous artifact/commit via workflow input `rollback_ref`.

## Maintenance
- Refresh dependencies quarterly or when security advisories land.
- If Material support degrades, evaluate Zensical or vanilla MkDocs theme with existing palette and icons; keep custom CSS minimal to ease the swap.
- Periodically audit redirects and remove stale mappings.
