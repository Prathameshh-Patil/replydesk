"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, login } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-12 max-w-sm space-y-4 rounded-lg bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h1 className="text-xl font-semibold">Staff login</h1>
      <label className="block">
        <span className="text-sm text-slate-600">Email</span>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2" autoComplete="username" />
      </label>
      <label className="block">
        <span className="text-sm text-slate-600">Password</span>
        <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2" autoComplete="current-password" />
      </label>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button type="submit" disabled={busy}
        className="w-full rounded bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50">
        {busy ? "Logging in…" : "Log in"}
      </button>
    </form>
  );
}
