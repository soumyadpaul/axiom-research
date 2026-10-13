# Preparation checks — 13 October 2026

Validated locally using Node.js 24.19.0, the included dependency lockfile and Cloudflare's local Workers runtime.

| Check | Observed result |
| --- | --- |
| Dependency installation | npm ci succeeded; jose installed and recorded in lockfile. |
| Lockfile consistency | Dependency and devDependency maps match package.json. |
| Lint | Passed after final source changes. |
| TypeScript | Passed after final source changes. |
| Unit tests | 19 passed: 10 original research/export tests plus 9 authentication tests. |
| Production build | Passed after final configuration changes. |
| Wrangler deploy dry run | Passed; Worker includes DB and ASSETS bindings; no remote deployment occurred. |
| Local database migration | Applied successfully using Wrangler migrations. |
| Homepage | Rendered successfully through local development server. |
| Workspace identity | Spoofed identity headers overwritten by local development identity. |
| Project and paper saving | Create project, save paper, update notes/status/favorite, and remove paper succeeded. |
| Persistence | Saved notes and favorite state persisted after stopping and restarting the server. |
| Cross-origin writes | Rejected with HTTP 403. |
| Invalid search input | Rejected with HTTP 400. |
| Production gate | Homepage, workspace API and favicon return HTTP 503 when Access configuration is absent, including requests with forged identity headers. |
| Development bypass | Local test identity is absent from the generated production Worker bundle. |
| Deployment guard | Refuses deployment while the D1 database ID is a placeholder. |

The build emits nonfatal framework warnings about modules imported both statically and dynamically. The pinned Workers runtime supports the selected compatibility date, 2026-05-15.

## Still needs live account configuration and verification

- GitHub repository creation/upload and GitHub Actions execution.
- Cloudflare database provisioning, remote migration and live deployment.
- Real Cloudflare Access login/logout and user isolation across two authenticated accounts.
- Provider searches from the deployed environment with the user's provider settings.
- Live production save/reload persistence.

No GitHub upload or live Cloudflare deployment is claimed by these preparation checks. Test database contents, credentials, dependencies, build output and caches are excluded from the deliverable.
