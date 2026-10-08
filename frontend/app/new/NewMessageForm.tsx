"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Ticket } from "@/lib/types";

// Public: anyone trying the demo can write in as a customer of Pixel & Plug.
export function NewMessageForm() {
  const [form, setForm] = useState({ customer_name: "", customer_email: "", subject: "", body: "" });
  const [sent, setSent] = useState<Ticket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const field = (name: keyof typeof form) => ({
    value: form[name],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm({ ...form, [name]: e.target.value }),
  });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setSent(await api<Ticket>("/tickets", { method: "POST", body: JSON.stringify(form) }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server");
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <div className="mx-auto mt-8 max-w-xl space-y-3 rounded-lg bg-white p-6 ring-1 ring-slate-200">
        <h1 className="text-xl font-semibold">Message received</h1>
        <p>Your message is ticket <strong>#{sent.id}</strong>. The agents are sorting it and drafting a reply now; a person will review it before anything is sent.</p>
        <p>
          <Link href={`/tickets/${sent.id}`} className="font-medium text-blue-700 hover:underline">Watch it as support staff →</Link>
          <span className="text-sm text-slate-500"> (staff login needed)</span>
        </p>
        <button onClick={() => { setSent(null); setForm({ customer_name: "", customer_email: "", subject: "", body: "" }); }}
          className="text-sm text-slate-500 underline">Send another message</button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-8 max-w-xl space-y-4 rounded-lg bg-white p-6 ring-1 ring-slate-200">
      <div>
        <h1 className="text-xl font-semibold">Write to Pixel &amp; Plug support</h1>
        <p className="text-sm text-slate-500">Pixel &amp; Plug is a made-up electronics store. Try anything: a late order, a refund, an angry complaint.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block"><span className="text-sm text-slate-600">Your name</span>
          <input required maxLength={100} {...field("customer_name")} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" /></label>
        <label className="block"><span className="text-sm text-slate-600">Your email</span>
          <input required type="email" maxLength={254} {...field("customer_email")} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" /></label>
      </div>
      <label className="block"><span className="text-sm text-slate-600">Subject</span>
        <input required maxLength={200} {...field("subject")} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" /></label>
      <label className="block"><span className="text-sm text-slate-600">Message</span>
        <textarea required maxLength={5000} rows={6} {...field("body")} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" /></label>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button type="submit" disabled={busy} className="rounded bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50">
        {busy ? "Sending…" : "Send message"}
      </button>
    </form>
  );
}
