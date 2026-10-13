# Streamlit conversion validation

Validated on 14 October 2026 using Python 3.12, Streamlit 1.65.0 and Requests 2.34.2.

| Check | Result |
| --- | --- |
| Automated tests | 20 passed. |
| Live literature search | OpenAlex and Crossref both returned results for a mathematics query; 40 fetched records displayed, no provider warnings. |
| Provider normalization | Missing metadata remains unknown; abstracts, links and DOI metadata checked. |
| Ranking/deduplication | DOI variants merge; false OA values are preserved; relevant titles outrank irrelevant highly cited records. |
| Export/backup | CSV formula escaping and multiline cells, demo-free BibTeX, backup round trip and non-destructive merge checked. |
| Session separation | Independent SessionStore objects do not share workspaces. |
| Interface navigation | All six sections render with Streamlit AppTest. |
| Interface workflow | Project creation, search, saving a paper, notes/favorite editing and pagination pass AppTest. Search results in this test are explicitly synthetic interface-test records. |
| Authentication | Wrong password rejected, correct password opens app, incomplete durable configuration fails closed. |
| D1 adapter | Actual SQL CRUD and owner isolation tested with an in-memory SQLite database and mocked D1 API transport. No live account credentials were used. |
| Server startup | Streamlit health endpoint and HTTP application shell both return 200. |

The interface uses native Streamlit controls; it is not a pixel-identical React rendering. No live GitHub upload, Streamlit Community Cloud deployment or real D1 API connection is claimed. The durable database connection requires separate validation after the user configures their secrets.

Default storage is per-session and temporary; explicit workspace backup/restore is provided. Optional D1 storage is a single-owner/shared personal workspace, protected by APP_PASSWORD and recommended private platform access. It is not a multi-user account system.

Research phases beyond the original Phase 1 features remain roadmap items. No numerical meta-analysis engine or LLM/PDF reader was added.
