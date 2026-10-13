import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
const config = JSON.parse(readFileSync("wrangler.jsonc", "utf8"));
const id = config.d1_databases?.find(x => x.binding === "DB")?.database_id;
if (!id || id === "00000000-0000-4000-8000-000000000000") {
  console.error("Create axiom-db and put its database ID in wrangler.jsonc. See DEPLOY.md.");
  process.exit(1);
}
let built;
try { built = JSON.parse(readFileSync("dist/server/wrangler.json", "utf8")); }
catch { console.error("Run npm run build before deploying."); process.exit(1); }
if (built.d1_databases?.find(x => x.binding === "DB")?.database_id !== id || built.name !== config.name) {
  console.error("Deployment settings changed. Run npm run build again before deploying.");
  process.exit(1);
}
const result = spawnSync(process.execPath,
  ["node_modules/wrangler/bin/wrangler.js", "deploy"], { stdio: "inherit" });
if (result.error) throw result.error;
process.exit(result.status ?? 1);
