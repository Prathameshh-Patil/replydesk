"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Badge } from "@/components/Badge";
import { api } from "@/lib/api";
import type { Ticket } from "@/lib/types";

const TABS = [
  { status: "ready_for_review", label: "To review" },
  { status: "needs_manual", label: "Needs manual" },
  { status: "", label: "All" },
  { status: "approved", label: "Approved" },
  { status: "rejected", label: "Rejected" },
];
const CATEGORIES = ["billing", "order_status", "technical", "refund", "complaint", "other"];
const URGENCIES = ["high", "medium", "low"];

export function Inbox() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  // Filters live in the URL, so a filtered view can be bookmarked or shared.
  const status = params.get("status") ?? "ready_for_review";
  const category = params.get("category") ?? "";
  const urgency = params.get("urgency") ?? "";
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const query = new URLSearchParams({ limit: "200" });
    if (status) query.set("status", status);
    if (category) query.set("category", category);
    if (urgency) query.set("urgency", urgency);
    const load = () =>
      api<Ticket[]>(`/tickets?${query}`).then(setTickets, (e) => setError(e.message));
    load();
    const timer = setInterval(load, 5000); // new messages show up without a reload
    return () => clearInterval(timer);
  }, [status, category, urgency]);

  function setFilter(name: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name === "status" && !value) next.set("status", ""); // "All" is an explicit choice
    router.replace(`${pathname}?${next}`);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {TABS.map((tab) => (
          <button key={tab.label} onClick={() => setFilter("status", tab.status)}
            className={`rounded-full px-3 py-1 text-sm ${status === tab.status
              ? "bg-slate-900 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100"}`}>
            {tab.label}
          </button>
        ))}
        <span className="ml-auto flex gap-2">
          <select aria-label="Category" value={category} onChange={(e) => setFilter("category", e.target.value)}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-sm">
            <option value="">All categories</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
          </select>
          <select aria-label="Urgency" value={urgency} onChange={(e) => setFilter("urgency", e.target.value)}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-sm">
            <option value="">All urgencies</option>
            {URGENCIES.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </span>
      </div>

      {error && <p role="alert" className="text-red-700">{error}</p>}
      {tickets === null ? (
        <p className="text-slate-500">Loading…</p>
      ) : tickets.length === 0 ? (
        <p className="rounded-lg bg-white p-8 text-center text-slate-500 ring-1 ring-slate-200">No tickets here.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg bg-white ring-1 ring-slate-200">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">#</th>
                <th className="px-4 py-2 font-medium">Customer</th>
                <th className="px-4 py-2 font-medium">Subject</th>
                <th className="px-4 py-2 font-medium">Category</th>
                <th className="px-4 py-2 font-medium">Urgency</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Received</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-2 text-slate-500">{t.id}</td>
                  <td className="px-4 py-2">{t.customer_name}</td>
                  <td className="px-4 py-2">
                    <Link href={`/tickets/${t.id}`} className="font-medium text-slate-900 hover:underline">{t.subject}</Link>
                  </td>
                  <td className="px-4 py-2"><Badge value={t.category} /></td>
                  <td className="px-4 py-2"><Badge value={t.urgency} /></td>
                  <td className="px-4 py-2"><Badge value={t.status} /></td>
                  <td className="whitespace-nowrap px-4 py-2 text-slate-500">{new Date(t.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
