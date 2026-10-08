// The one place the front end talks to the API.

import { useSyncExternalStore } from "react";

// Baked in at build time (NEXT_PUBLIC_ variables are copied into the browser code).
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

const TOKEN_KEY = "replydesk_token";
const AUTH_EVENT = "replydesk-auth"; // fired in this tab when the token changes

// The login token lives in localStorage: simple, but readable by any script on the page.
// (An httpOnly cookie would be safer; see docs/DECISIONS.md.)
export const token = {
  get: () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY)),
  set: (value: string) => {
    localStorage.setItem(TOKEN_KEY, value);
    window.dispatchEvent(new Event(AUTH_EVENT));
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new Event(AUTH_EVENT));
  },
};

function subscribe(onChange: () => void) {
  window.addEventListener(AUTH_EVENT, onChange);
  window.addEventListener("storage", onChange); // login/logout in another tab
  return () => {
    window.removeEventListener(AUTH_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/** true / false in the browser; null while rendering on the server (we can't know there). */
export function useLoggedIn(): boolean | null {
  return useSyncExternalStore(subscribe, () => token.get() !== null, () => null);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** fetch() with the login token attached; throws ApiError with the API's message on failure. */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const t = token.get();
  if (t) headers.set("Authorization", `Bearer ${t}`);
  if (options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 401 && t) {
    token.clear(); // expired or invalid; RequireLogin sees this and shows the login page
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : response.statusText;
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<void> {
  // The API's login uses the standard OAuth2 form: "username" holds the email.
  const form = new URLSearchParams({ username: email, password });
  const result = await api<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: form,
  });
  token.set(result.access_token);
}
