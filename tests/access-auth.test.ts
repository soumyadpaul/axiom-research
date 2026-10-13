import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPair, SignJWT } from "jose";
import { accessIssuer, verifyAccessToken, identityHeaders, authenticateAccess } from "../lib/access-auth";

const issuer = "https://axiom-test.cloudflareaccess.com";
const audience = "test-application-audience";
const keyPair = generateKeyPair("RS256");
async function signed(options: { issuer?: string; audience?: string; expired?: boolean; email?: string; sub?: string } = {}) {
  const { privateKey } = await keyPair;
  return new SignJWT({ email: options.email ?? "researcher@example.test", name: "Researcher" })
    .setProtectedHeader({ alg: "RS256" })
    .setIssuer(options.issuer ?? issuer).setAudience(options.audience ?? audience)
    .setSubject(options.sub ?? "user-one").setIssuedAt()
    .setExpirationTime(options.expired ? Math.floor(Date.now()/1000)-60 : "1h")
    .sign(privateKey);
}
async function verify(token: string) {
  const { publicKey } = await keyPair;
  return verifyAccessToken(token, issuer, audience, async () => publicKey);
}
test("signed Access token resolves stable user identity", async () => {
  const user = await verify(await signed());
  assert.equal(user.userId, "user-one");
  assert.equal(user.email, "researcher@example.test");
});
test("wrong audience is rejected", async () => {
  await assert.rejects(verify(await signed({ audience: "other-app" })));
});
test("wrong issuer is rejected", async () => {
  await assert.rejects(verify(await signed({ issuer: "https://other.cloudflareaccess.com" })));
});
test("expired token is rejected", async () => {
  await assert.rejects(verify(await signed({ expired: true })));
});
test("token signed with attacker key is rejected", async () => {
  const attacker = await generateKeyPair("RS256");
  const token = await new SignJWT({ email: "attacker@example.test" })
    .setProtectedHeader({ alg: "RS256" }).setIssuer(issuer).setAudience(audience)
    .setSubject("user-one").setIssuedAt().setExpirationTime("1h").sign(attacker.privateKey);
  await assert.rejects(verify(token));
});
test("missing personal identity is rejected", async () => {
  await assert.rejects(verify(await signed({ email: "" })));
  await assert.rejects(verify(await signed({ sub: "" })));
});
test("team domain is constrained to Cloudflare Access HTTPS hosts", () => {
  assert.equal(accessIssuer(issuer + "/"), issuer);
  for (const domain of ["http://axiom-test.cloudflareaccess.com", "https://evil.test", issuer+"/path", issuer+"?query=1"]) {
    assert.throws(() => accessIssuer(domain));
  }
});
test("unverified identity headers cannot select another user's workspace", async () => {
  const input = new Headers({ "axiom-user-id": "victim", "oai-authenticated-user-id": "victim", "accept": "application/json" });
  assert.equal(identityHeaders(input, null).has("axiom-user-id"), false);
  const headers = identityHeaders(input, await verify(await signed()));
  assert.equal(headers.get("axiom-user-id"), "user-one");
  assert.equal(headers.has("oai-authenticated-user-id"), false);
  assert.equal(headers.get("accept"), "application/json");
});
test("absent configuration and tokens fail closed", async () => {
  const request = new Request("https://axiom.example.test", { headers: { "axiom-user-id": "victim" } });
  assert.equal(await authenticateAccess(request, {}), null);
  assert.equal(await authenticateAccess(request, { ACCESS_TEAM_DOMAIN: issuer, ACCESS_AUD: audience }), null);
});
