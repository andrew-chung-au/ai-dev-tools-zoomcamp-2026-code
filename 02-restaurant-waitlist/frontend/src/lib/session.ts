import type { StaffSession } from "@/services";

/** In-memory only (no localStorage). Resets on reload, which is fine for the prototype. */
let currentSession: StaffSession | null = null;

export function setSession(session: StaffSession | null) {
  currentSession = session;
}

export function getSession(): StaffSession | null {
  return currentSession;
}
