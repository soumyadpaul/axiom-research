import { createRemoteJWKSet, jwtVerify, type JWTVerifyGetKey } from "jose";

export interface AccessUser {
  userId: string;
  displayName: string;
  email: string;
  fullName: string | null;
}

export function accessIssuer(teamDomain: string): string {
  const url = new URL(teamDomain);
  if (url.protocol !== "https:" ||
      !/^[a-z0-9-]+\.cloudflareaccess\.com$/.test(url.hostname) ||
      url.username || url.password || url.port ||
      url.pathname !== "/" || url.search || url.hash) {
    throw new Error("Invalid Cloudflare Access team domain");
  }
  return url.origin;
}

export async function verifyAccessToken(
  token: string, issuer: string, audience: string, keys: JWTVerifyGetKey,
): Promise<AccessUser> {
  const { payload } = await jwtVerify(token, keys, {
    issuer, audience, algorithms: ["RS256"],
    requiredClaims: ["exp", "iat", "sub", "email"],
  });
  if (!payload.sub || typeof payload.email !== "string" || !payload.email.trim()) {
    throw new Error("Missing user identity");
  }
  const fullName = typeof payload.name === "string" ? payload.name : null;
  return { userId: payload.sub, email: payload.email,
    displayName: fullName || payload.email, fullName };
}

const keySets = new Map<string, JWTVerifyGetKey>();
export async function authenticateAccess(
  request: Request, settings: { ACCESS_TEAM_DOMAIN?: string; ACCESS_AUD?: string },
): Promise<AccessUser | null> {
  if (!settings.ACCESS_TEAM_DOMAIN || !settings.ACCESS_AUD) return null;
  const token = request.headers.get("Cf-Access-Jwt-Assertion");
  if (!token) return null;
  try {
    const issuer = accessIssuer(settings.ACCESS_TEAM_DOMAIN);
    let keys = keySets.get(issuer);
    if (!keys) {
      keys = createRemoteJWKSet(new URL(`${issuer}/cdn-cgi/access/certs`));
      keySets.set(issuer, keys);
    }
    return await verifyAccessToken(token, issuer, settings.ACCESS_AUD, keys);
  } catch {
    return null;
  }
}

// The Worker removes untrusted values, then writes only verified identity.
export function identityHeaders(input: Headers, user: AccessUser | null): Headers {
  const headers = new Headers(input);
  for (const name of [...headers.keys()]) {
    if (name.startsWith("axiom-user-") || name.startsWith("oai-authenticated-user-")) {
      headers.delete(name);
    }
  }
  if (user) {
    headers.set("axiom-user-id", user.userId);
    headers.set("axiom-user-email", user.email);
    headers.set("axiom-user-name", encodeURIComponent(user.displayName));
  }
  return headers;
}
