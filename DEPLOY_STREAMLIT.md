# Deploy Axiom on Streamlit

This is the Python conversion. You can deploy and search literature without Cloudflare Workers, Access, Zero Trust, or a payment-details setup. The existing Cloudflare database is optional.

## 1. Put these files into your existing GitHub repository

Use https://github.com/soumyadpaul/axiom-research. Add the extracted **contents** of this ZIP at the repository root. This adds `streamlit_app.py`, `requirements.txt`, the Python `axiom/` package, and supporting files. Keep the directory structure.

This edition has fewer than 100 files, so you can upload its contents through GitHub's **Add file → Upload files** screen in one batch. On Mac, show hidden files with Command + Shift + period and include `.streamlit`, `.github` and `.gitignore`.

If you prefer the ZIP/Codespaces method:

1. Upload `axiom-streamlit-ready.zip` to your repository and commit it.
2. Open **Code → Codespaces → Create codespace on main**, or resume your existing Codespace.
3. Open **Terminal → New Terminal** and run:

```sh
cd "$(git rev-parse --show-toplevel)"
axiom_extract_dir=$(mktemp -d)
unzip axiom-streamlit-ready.zip -d "$axiom_extract_dir"
cp -a "$axiom_extract_dir/axiom-streamlit/." .
git add .
git commit -m "Add Streamlit edition of Axiom"
git push
```

If resuming an existing Codespace that does not yet contain the uploaded ZIP, run `git pull --ff-only` before extracting. Resolve uncommitted local work before pulling rather than discarding it.

The ZIP preserves ignores for existing Node dependencies and secrets. It adds a separate Python check workflow; it does not remove the React source or its workflow. Deploying Streamlit does not delete or stop your existing Cloudflare Worker. Your README will describe the new Streamlit edition; the previous Cloudflare instructions remain in `DEPLOY.md` if you keep that file.

## 2. Deploy from Streamlit Community Cloud

1. Open https://share.streamlit.io and sign in with GitHub.
2. Authorize access to `soumyadpaul/axiom-research`, including private repositories if applicable.
3. Click **Create app**, then choose the option to deploy from GitHub.
4. Enter:

| Setting | Value |
| --- | --- |
| Repository | `soumyadpaul/axiom-research` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |
| Python version in Advanced settings | `3.12` |

5. Choose an available app URL and click **Deploy**.
6. Streamlit installs `requirements.txt` and launches the app. There is no npm build command.

You can launch immediately with no app secrets. Provider availability/limits may vary. For personal research, keep the app private: **App settings → Sharing → Only specific people can view this app**. Community Cloud currently permits one private app per account. If your existing app is already private, check this limit before changing either app's visibility.

## 3. Understand workspace storage before saving research

The default workspace belongs to the current browser session. It is isolated from other visitor sessions but is **temporary**. Closing/reloading the page, reconnecting into a new session, or a server restart can lose it. Local files on Community Cloud are not a durable database.

Use **Backup & settings → Download full workspace backup** before ending a session. Next time, upload that JSON and click **Merge backup into my workspace**. A backup preserves projects, papers, notes, favorites and reading status. CSV and BibTeX preserve paper metadata only. Imports add missing records and keep current values for existing IDs.

For automatic persistence, use the optional D1 connection below. This reuses the database you already created and does not use Zero Trust.

## 4. Optional: keep your workspace automatically in existing D1

This mode is for one personal/shared owner workspace, not separate user accounts. Keep the Streamlit app private and require the included workspace password. Other authorized people who know that password can access the same research workspace.

1. In Cloudflare, open `axiom-db` and copy its **Database ID** and **Account ID**.
2. Open **My Profile → API Tokens → Create Token → Custom token**.
3. Add the account permission **D1 → Edit** (D1 Write), restricted to your Cloudflare account. Create the token. Store it privately; never paste it into GitHub or a chat.
4. In Streamlit app settings, open **Secrets** and enter these values as TOML:

```toml
APP_PASSWORD = "YOUR-OWN-LONG-PASSWORD-AT-LEAST-16-CHARACTERS"
CF_ACCOUNT_ID = "YOUR-32-CHARACTER-ACCOUNT-ID"
CF_DATABASE_ID = "YOUR-EXISTING-DATABASE-UUID"
CF_API_TOKEN = "YOUR-D1-API-TOKEN"
AXIOM_OWNER_ID = "axiom-streamlit-owner"
```

5. Save the secrets and let the app restart. Sign in with your chosen password.
6. The sidebar should say **Persistent personal workspace · D1**.
7. Create a project, save a paper and notes, then reload and sign in again. Confirm the data remains.

The app uses your existing `projects` and `saved_papers` tables and makes owner-scoped queries through the D1 API. Do not change `AXIOM_OWNER_ID` between visits unless intentionally selecting a different owner workspace. The original Worker may have used different identity values, so its saved records will not automatically appear under this new owner.

The app will not silently fall back to an empty session when a configured D1 connection fails. Fix the connection before continuing. Bulk backup import into D1 is non-destructive, can partially complete if a network call fails, and can safely be retried. Current records keep their values.

If you already created both tables during this conversation, do not run `schema.sql` again. It is included only for a fresh database. This mode reads/writes existing tables and does not run schema migrations.

## Optional provider settings

Add only the settings you need to Streamlit Secrets:

```toml
OPENALEX_API_KEY = "YOUR-OPENALEX-KEY"
CROSSREF_MAILTO = "your-contact-email@example.com"
```

A password can also be enabled without D1 by setting only `APP_PASSWORD`.
Do not commit `.streamlit/secrets.toml`, actual tokens, or real workspace backups to GitHub.

## Local use and tests

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Windows, activate with `.venv\Scripts\activate`.

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

## What has changed

The interface uses Streamlit's native sidebar, forms, cards and settings, rather than a pixel-identical React interface. Live search, ranking, deduplication, projects, reading notes, collections, favorites, filtering and exports are implemented. The fictional demo remains separate. Systematic review, PRISMA, numerical meta-analysis, AI/PDF reading and knowledge graphs remain roadmap items.

No live GitHub upload or Streamlit deployment is claimed by this ZIP. Validation results and limits are in `VALIDATION.md`.

Official references:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- https://docs.streamlit.io/develop/concepts/connections/connecting-to-data
- https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/
