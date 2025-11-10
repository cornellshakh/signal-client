# Documentation Master Plan

## Goals
- Give bot authors a guided journey from concept to deployment using signal-client.
- Reuse MkDocs plugins/macros to keep facts, diagrams, and examples consistent.
- Keep content modular so contributors can update one area without breaking others.

## Information Architecture

### 1. Home
- `docs/index.md`
- Value proposition, hero cards linking into the major sections, latest release note snippet.
- Use `shadcn.extensions.iconify` for icon cards and `glightbox` for diagram previews.

### 2. Discover
- `docs/discover/overview.md`, `.../use-cases.md`, `.../feature-tour.md`
- Audience: decision makers.
- Embed Mermaid diagrams for messaging flows and `table-reader` tables for capability matrices.

### 3. Building Bots
- Landing page `docs/bots/index.md` plus:
  - `overview.md`: architecture high-level, dependencies, DI containers.
  - `quickstart.md`: pip vs Poetry instructions (tabs), runnable snippet via `codexec`.
  - `architecture.md`: deep dive per module (`bot`, `command`, `context`, `infrastructure`) with cross-links from `autorefs`.
  - `configuration.md`: settings hierarchy, `.env` examples, macros for env var names.
  - `observability.md`, `operations.md`, `diagnostics.md`, `troubleshooting.md`.
  - Guides subfolder `guides/recipes.md`, `guides/writing-async-commands.md`.
- Use `pymdownx.tabbed`, admonitions, and `glightbox` for sequence diagrams exported from Excalidraw.

### 4. Reference
- `docs/reference/api.md`: mkdocstrings auto API by module.
- `docs/reference/commands.md`: CLI entry points, generated via macros and `table-reader`.
- `docs/reference/schema.md`: link to `https://bbernhard.github.io/signal-cli-rest-api/src/docs/swagger.json` plus compatibility checker instructions.

### 5. Runbook
- `docs/run/operations.md`, `run/observability.md`, `run/performance.md`.
- Include `pymdownx.tasklist` for operational checklists, `progressbar` for SLO tracking.

### 6. Standards & Contribution
- `docs/contribute/coding_standards.md`, `docs/contribute/production_secrets.md`, `docs/contribute/test_plan.md`.
- Embed macros to insert lint/type/test command lists so they stay in sync with AGENTS.

### 7. Appendix
- `docs/appendix/resources.md`, `.../changelog.md`, `.../tee_privacy_architecture.md`.
- Use `table-reader` for roadmap CSV and `glightbox` for privacy diagrams.

## Plugin Usage Checklist
- **macros**: centralize install commands, supported Python version, required test suite list.
- **mermaid2**: default for architecture + flow diagrams.
- **table-reader**: feature maps, compatibility matrices.
- **glightbox**: gallery of Excalidraw exports and screenshot walk-throughs.
- **codexec**: runnable Python snippets for handlers and CLI commands.
- **pymdownx.tabbed**: multi-flavor instructions (pip vs Poetry, dev vs prod configs).
- **mkdocstrings**: API reference that pulls docstrings from `src/signal_client`.

## Implementation Phases
1. Update `mkdocs.yml` nav/groups to match IA, create directories/files above.
2. Seed each page with concise narrative + TODO blocks; wire macros and plugin showcases.
3. Expand macros to expose install/test commands, shared badges, and snippet helpers.
4. Iterate on content depth, add diagrams/data tables, and enforce docs QA checklist in PR template.

## Outstanding Questions
- Do we want localized quickstarts (multiple languages) or just Python? (defaults to Python only)
- Should changelog mirror GitHub releases or act as high-level highlights? (lean highlights)
- Any blocked plugins (analytics) we should add later?

Answering these secures the docs backlog and keeps scope clear as we start writing.
