"use client";

import { useState } from "react";

// One series (tickets per category): horizontal bars in a single hue, no legend box (the title
// names the series), value labels in text colour, a hover/focus readout in the header (it never
// covers a bar), and a table view.

export function CategoryChart({ counts }: { counts: Record<string, number> }) {
  const [showTable, setShowTable] = useState(false);
  const [hovered, setHovered] = useState<string | null>(null);
  const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...rows.map(([, n]) => n));
  const total = rows.reduce((sum, [, n]) => sum + n, 0);

  return (
    <figure className="rounded-lg bg-white p-5 ring-1 ring-slate-200">
      <div className="flex items-baseline justify-between">
        <figcaption className="text-sm font-medium text-slate-700">
          Tickets by category
          <span aria-live="polite" className="ml-2 font-normal text-slate-500">
            {hovered && `· ${hovered.replace("_", " ")}: ${counts[hovered]} ticket${counts[hovered] === 1 ? "" : "s"} (${Math.round((counts[hovered] / total) * 100)}%)`}
          </span>
        </figcaption>
        <button onClick={() => setShowTable(!showTable)} className="text-xs text-slate-500 underline hover:text-slate-900">
          {showTable ? "Show chart" : "Show table"}
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="mt-4 text-sm text-slate-400">No sorted tickets yet.</p>
      ) : showTable ? (
        <table className="mt-4 w-full text-sm">
          <thead className="text-left text-slate-500"><tr><th className="py-1 font-medium">Category</th><th className="py-1 text-right font-medium">Tickets</th></tr></thead>
          <tbody>{rows.map(([c, n]) => (
            <tr key={c} className="border-t border-slate-100"><td className="py-1">{c.replace("_", " ")}</td><td className="py-1 text-right tabular-nums">{n}</td></tr>
          ))}</tbody>
        </table>
      ) : (
        <ul className="mt-4 space-y-[2px]" aria-label="Tickets by category">
          {rows.map(([category, n]) => (
            <li key={category} className="grid grid-cols-[7.5rem_1fr_2.5rem] items-center gap-3 py-1">
              <span className="truncate text-sm text-slate-600">{category.replace("_", " ")}</span>
              {/* the hit target is the whole track, bigger than the bar itself */}
              <span tabIndex={0} className="relative h-5 rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                onMouseEnter={() => setHovered(category)} onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(category)} onBlur={() => setHovered(null)}
                aria-label={`${category}: ${n} tickets`}>
                <span className="absolute inset-y-0.5 left-0 rounded-r-[4px]"
                  style={{ width: `${(n / max) * 100}%`, background: "#2a78d6", opacity: hovered && hovered !== category ? 0.55 : 1 }} />
              </span>
              <span className="text-right text-sm tabular-nums text-slate-700">{n}</span>
            </li>
          ))}
        </ul>
      )}
    </figure>
  );
}
