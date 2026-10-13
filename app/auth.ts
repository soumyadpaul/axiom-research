import { headers } from "next/headers";
import type { AccessUser } from "@/lib/access-auth";

export async function getUser(): Promise<AccessUser | null> {
  const h = await headers();
  const userId = h.get("axiom-user-id");
  const email = h.get("axiom-user-email");
  if (!userId || !email) return null;
  let displayName = email;
  try { displayName = decodeURIComponent(h.get("axiom-user-name") || email); } catch {}
  return { userId, email, displayName, fullName: null };
}
