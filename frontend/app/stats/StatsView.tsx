"use client";

import { useEffect, useState } from "react";
import { CategoryChart } from "@/components/CategoryChart";
import { api } from "@/lib/api";
import type { Stats } from "@/lib/types";

const STEPS = ["sorter", "extractor", "drafter", "checker"];
const percent = (x: number | null) => (x === null ? "–" : `${Math.round(x * 100)}%`);

function Tile({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="rounded-lg bg-white p-5 ring-1 ring-slate-200">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold tabular-nums">{value}</p>
      {note && <p className="mt-1 text-xs text-slate-500">{note}</p>}
    </div>
  );
}

export function StatsView() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    api<Stats>("/stats").then(setStats);
  }, []);

  if (!stats) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Stats</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile label="Approved without edits" value={percent(stats.share_approved_without_edits)}
          note={`${stats.approved_without_edits} of ${stats.approved} approved drafts`} />
        <Tile label="Checker pass rate" value={percent(stats.checker_pass_rate)} note={`${stats.checked_drafts} drafts checked`} />
        <Tile label="Waiting for review" value={stats.by_status.ready_for_review} />
        <Tile label="Needs manual handling" value={stats.by_status.needs_manual} />
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <CategoryChart counts={stats.by_category} />
        <div className="rounded-lg bg-white p-5 ring-1 ring-slate-200">
          <p className="text-sm font-medium text-slate-700">Average time per step</p>
          <table className="mt-4 w-full text-sm">
            <tbody>
              {STEPS.map((step) => (
                <tr key={step} className="border-t border-slate-100 first:border-0">
                  <td className="py-1.5 capitalize text-slate-600">{step}</td>
                  <td className="py-1.5 text-right tabular-nums">
                    {step in stats.avg_ms_per_step ? `${(stats.avg_ms_per_step[step] / 1000).toFixed(1)} s` : "–"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-sm font-medium text-slate-700">Tickets by status</p>
          <table className="mt-2 w-full text-sm">
            <tbody>
              {Object.entries(stats.by_status).map(([s, n]) => (
                <tr key={s} className="border-t border-slate-100 first:border-0">
                  <td className="py-1.5 text-slate-600">{s.replaceAll("_", " ")}</td>
                  <td className="py-1.5 text-right tabular-nums">{n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
