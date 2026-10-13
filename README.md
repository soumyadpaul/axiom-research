# Axiom — Streamlit research workspace

Python/Streamlit conversion of the Axiom research app. **Read [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md)** for GitHub upload and deployment steps.

## Launch on Streamlit Community Cloud

Repository: `soumyadpaul/axiom-research` · Branch: `main` · Entry point: **`streamlit_app.py`** · Python: **3.12**.

No Cloudflare Workers or Zero Trust setup is required to launch this edition.

## Implemented

- OpenAlex and Crossref live literature searches with provider selection, year/type/access filters and pagination.
- DOI deduplication, transparent lexical ranking, original provider abstracts and source links.
- Research projects with PICO/PICOS/PECO/SPIDER/Custom frameworks.
- Saved library, collections, notes, favorites, reading status and library search.
- CSV, BibTeX and JSON exports; complete workspace backup and non-destructive restore.
- Fictional demo mode, kept separate from real research.
- Optional personal-workspace password and durable storage in an existing D1 database through its API.

## Storage

**Default: temporary, per-browser-session workspace. Download backups before ending/reloading a session.**
Optional D1 configuration provides automatic persistence across visits. It requires a D1 API token, a strong app password and private app access; it does not require Cloudflare Zero Trust. It is a shared single-owner workspace, not individual accounts for multiple researchers.

## Local use

```sh
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Verification

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

See [VALIDATION.md](VALIDATION.md) for observed checks and remaining live verification.

This release does not implement systematic review screening/PRISMA, numerical meta-analysis, LLM/PDF synthesis or knowledge graphs. Those remain roadmap items. Metadata relevance scores do not measure scientific quality; verify evidence against original publications.
