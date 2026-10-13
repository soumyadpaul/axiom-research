# Put Axiom on GitHub and Cloudflare

This package is prepared for Cloudflare **Workers**, not Pages or Streamlit.
The app retains its React interface, live literature searches and D1-backed projects/library.
It uses Cloudflare Access for private, email-based sign-in. You can invite other researchers with Access policies; each verified user gets a separate workspace.

## 1. Install the prerequisites on your computer

Install Node.js 24 LTS and Git. Create accounts at https://github.com and https://dash.cloudflare.com if you do not already have them.
Extract this ZIP. Open Terminal inside the extracted `axiom-cloudflare` folder (the folder containing `package.json`).

```sh
npm ci
```

Do not upload the ZIP itself as your repository's application source.

## 2. Create the database

```sh
npx wrangler login
npx wrangler d1 create axiom-db
```

The second command prints a `database_id`. Open `wrangler.jsonc` and replace
`00000000-0000-4000-8000-000000000000` with that ID. Keep the binding named `DB` and the database name `axiom-db`.

Apply the included migration to this new database:

```sh
npm run db:migrate:remote
```

This records migrations and does not replay them on subsequent runs. Local testing uses a separate database.

## 3. Make your first deployment

```sh
npm run check
npm run deploy
```

Wrangler prints your `https://axiom-research.<your-subdomain>.workers.dev` URL.
Until you complete Access setup, the app deliberately displays a setup message (HTTP 503).
This prevents unconfigured authentication from exposing private workspaces.

## 4. Enable Cloudflare sign-in

1. In the Cloudflare dashboard, open **Workers & Pages → axiom-research → Settings → Domains & Routes**.
2. On its `workers.dev` URL, enable **Cloudflare Access**.
3. Complete the Cloudflare One/Zero Trust setup if prompted; choose a team domain.
4. Open the Access application created for that Worker. Configure an **Allow** policy for your email. Remove any policy permitting users you do not intend to invite. Use email one-time PIN or your preferred identity provider.
5. Copy the application's **Application Audience (AUD)** tag and your **team domain**.
6. In the Worker's **Settings → Variables & Secrets**, add these runtime text variables:

| Name | Value |
| --- | --- |
| `ACCESS_TEAM_DOMAIN` | `https://YOUR-TEAM.cloudflareaccess.com` |
| `ACCESS_AUD` | Application Audience (AUD) tag from that Access application |

7. Save/deploy the settings, then open the Worker URL in your browser and sign in.

Protect the whole `workers.dev` hostname, not only `/api/workspace`. Preview URLs are disabled in this configuration. If you add a custom hostname, protect that hostname with Access too and use the audience for the applicable application. The Worker verifies signature, issuer, audience and expiry; unsigned user headers are not accepted.

`keep_vars: true` preserves dashboard-managed runtime variables during normal Wrangler deployments. Do not add empty Access variables to the committed configuration.

## 5. Configure literature-provider settings

In the same runtime **Variables & Secrets** screen:

- Add `OPENALEX_API_KEY` as a **secret**, if required by your OpenAlex account/API access.
- Add `CROSSREF_MAILTO` as a text variable with your contact email for Crossref's polite pool.

Provider availability and limits depend on the providers. The app reports errors rather than inventing results. Never put API keys or Cloudflare tokens in your GitHub repository.

## 6. Upload the source to GitHub

Create an empty repository at https://github.com/new named `axiom-research`.
A private repository is a reasonable default. Do not initialize it with a README, license or `.gitignore`; these source files already contain a README and `.gitignore`.

In the same Terminal folder:

```sh
git init -b main
git add .
git commit -m "Prepare Axiom research app for Cloudflare"
git remote add origin https://github.com/YOUR-USERNAME/axiom-research.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Authenticate through Git's supported browser/credential flow or GitHub Desktop. Do not use your GitHub account password as a Git password, and do not paste access tokens into this app or chat.

If Git requests your commit identity, configure your own name and GitHub email locally and retry the commit:

```sh
git config user.name "Your Name"
git config user.email "your-github-email@example.com"
```

GitHub Desktop alternative: add this existing local folder, commit its files, then publish the repository to your account.

The repository root must contain `package.json`, `vite.config.ts`, `wrangler.jsonc`, `app/`, `components/`, `lib/`, `build/`, `scripts/`, `drizzle/`, `.github/`, and the lockfile. Git respects the included ignore rules for dependencies, build output, databases and credentials.

## 7. Connect GitHub for automatic deployment

In your existing Worker, open **Settings → Build** and connect the GitHub repository. Authorize Cloudflare to access that repository when prompted.

| Build setting | Value |
| --- | --- |
| Production branch | `main` |
| Root directory | Repository root (leave blank) |
| Build command | `npm run build` |
| Deploy command | `npm run deploy` |
| Node version | `24` (`.node-version` is included) |

If the service requests an explicit build variable for Node, use `NODE_VERSION=24`.
The database migration is deliberately separate from every deployment. For future schema changes, apply pending migrations to the correct database before deploying dependent code.

## 8. Check the live app

1. Sign in via Cloudflare Access.
2. Switch from the illustrative demo workspace to your personal workspace.
3. Create a project, then search live literature.
4. Save a real paper, add notes, and reload the browser. Confirm the project, saved paper and notes persist.
5. Sign out and confirm Access asks for sign-in again.
6. If you invite another researcher, confirm their personal workspace is separate.

## Local development

```sh
npm run db:migrate:local
npm run dev
```

Open http://127.0.0.1:5173. Loopback development uses a fixed local test identity; this identity is removed from production bundles. Do not expose the development server publicly.
For local provider credentials, copy `.dev.vars.example` to `.dev.vars` and fill it in.

`npm run preview` runs the production bundle locally, so it requires genuine Access configuration/tokens. It does not enable the development identity.

## Common issues

| Symptom | Check |
| --- | --- |
| "Create axiom-db..." during deploy | Replace the placeholder database ID in `wrangler.jsonc`. |
| HTTP 503 setup message | Set both runtime Access variables; build variables alone are insufficient. |
| HTTP 403 after Access login | Match the team issuer and application AUD exactly; confirm Access covers the correct hostname. |
| Workspace unavailable | Apply the remote migration; check that D1 binding `DB` points to your database. |
| OpenAlex credentials or limit warning | Configure its API key and check provider limits. |
| Cloudflare cannot find package.json | Set the build root to the folder containing `package.json`. |

## Validation and limits

The preparation checks are recorded in `VALIDATION.md`. Those local checks are not proof of a live deployment. Live Access login, live provider access, GitHub upload and production D1 persistence must be checked after configuring your accounts.
The framework is Vinext beta, inherited from the original app. Phase 2–5 tools remain roadmap items; this package does not implement numerical meta-analysis or an LLM engine.

Official references:
- https://developers.cloudflare.com/workers/ci-cd/builds/configuration/
- https://developers.cloudflare.com/d1/get-started/
- https://developers.cloudflare.com/d1/reference/migrations/
- https://developers.cloudflare.com/changelog/post/2025-10-03-one-click-access-for-workers/
- https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
