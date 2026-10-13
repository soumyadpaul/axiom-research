import handler from "vinext/server/fetch-handler";
import { authenticateAccess, identityHeaders, type AccessUser } from "../lib/access-auth";

export default {
  async fetch(request: Request, env: Cloudflare.Env, ctx: ExecutionContext) {
    const url = new URL(request.url);
    let user: AccessUser | null = null;
    // This branch is removed from production bundles. Local development only.
    if (import.meta.env.DEV && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) {
      user = { userId: "local-researcher", email: "researcher@localhost",
        displayName: "Local researcher", fullName: null };
    } else {
      if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) {
        return new Response("Axiom needs Cloudflare Access setup. See DEPLOY.md.", {
          status: 503, headers: { "Cache-Control": "no-store" },
        });
      }
      user = await authenticateAccess(request, env);
      if (!user) return new Response("Sign in through Cloudflare Access to use Axiom.", {
        status: 403, headers: { "Cache-Control": "no-store" },
      });
    }
    if (url.pathname === "/auth/logout") {
      return Response.redirect(new URL("/cdn-cgi/access/logout", url.origin).href, 302);
    }
    if (url.pathname === "/auth/login") {
      return Response.redirect(new URL("/", url.origin).href, 302);
    }
    const authenticated = new Request(request, { headers: identityHeaders(request.headers, user) });
    return handler.fetch(authenticated, env, ctx);
  },
};
