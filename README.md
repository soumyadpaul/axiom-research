# Axiom — Research Intelligence Workspace

This archive contains the Phase 1 application source, its dependency lockfile, database migrations, and tests.

## Implemented in this source

- Responsive research dashboard and collapsible navigation
- Guided/advanced presentation, light/dark themes, and onboarding
- Live server-side OpenAlex and Crossref searches, provider toggles, filters, pagination, metadata ranking, and exact DOI deduplication
- Paper detail views with original abstracts and source links
- Personal projects and a database-backed library with collections, notes, favorites, and reading status
- CSV, JSON, and BibTeX export
- Explicitly labeled fictional demo workspace
- Command palette and search across the saved workspace

## Requirements

Node.js 22.13 or newer, npm, and an internet connection for dependency installation and scholarly searches.

## Run locally

Open a terminal in the extracted `axiom` directory:

```sh
npm ci
npm run build
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_lovely_meteorite.sql
npm run dev -- --hostname 127.0.0.1
```

The migration command initializes a fresh local database. Run it once per fresh database. Open the URL printed by the development server (normally http://127.0.0.1:5173).

To test saved projects and papers, use the application's sign-in link. The portable development server provides a local test identity through `/signin-with-chatgpt?return_to=/`. This is development-only authentication, not a production identity system.

## Environment variables

The `.env.example` file lists optional `OPENALEX_API_KEY` and `CROSSREF_MAILTO` settings. Copy it to `.env` and supply values if needed. Do not use `NEXT_PUBLIC_` prefixes for private API keys. Provider availability and request limits can vary.

No private environment files, installed dependencies, local database contents, credentials, or caches are included in this archive. The original hosting project identity has been removed from the packaged manifest.

## Checks

```sh
npm run lint
npm run typecheck
npm test
npm run build
```

Ten source-level tests cover normalization, missing metadata, DOI deduplication, ranking, link safety, validation, and exports. Lint, type checking, and those tests passed during development. A build passed before the last UI changes. Live search returned results from both scholarly providers. Full project/save/reload browser verification was interrupted, and the latest complete source has not received a final production build or deployment verification. Treat this as the current development source, not a validated production release.

## Architecture

- `app/`: Next.js-style App Router pages and server API routes
- `components/`: modular workspace, search, project, library, and dialog views
- `lib/providers/`: normalized OpenAlex/Crossref provider adapters
- `lib/papers/`: transparent ranking and deduplication
- `lib/projects/`: user-scoped database repository
- `lib/models.ts`: core models and future evidence/analysis interfaces
- `lib/validation.ts`: server input validation
- `db/` and `drizzle/`: schema and migration files
- `tests/`: deterministic source-level tests
- `build/` and `scripts/`: required runtime/build support (these are source, not generated output)

Stack: TypeScript, React, Next.js-compatible routing via Vinext/Vite, Tailwind CSS, Radix/shadcn primitives, Lucide icons, Cloudflare Workers and local D1/SQLite via Miniflare. This is not a plain `next start` deployment; the included build pipeline targets Workers.

## Planned, not implemented

Phase 2: systematic-review protocols, screening, PRISMA, and extraction.
Phase 3: validated deterministic meta-analysis and statistical charts.
Phase 4: grounded PDF/AI reading, synthesis, gaps, and hypotheses.
Phase 5: citation networks, authors, knowledge graphs, and timelines.

The sidebar links for those phases show a roadmap. There is no active LLM integration or numerical meta-analysis engine in Phase 1. Missing evidence is not invented. Ranking is lexical metadata ranking, not semantic AI analysis. Some filters apply only to the current fetched page.

Production hosting requires provisioning the database and configuring trusted platform authentication. The original Sites runtime notes are preserved in `RUNTIME.md`.
