// Small coloured labels. Colour is never the only signal: the text always says the value.

const STYLES: Record<string, string> = {
  // urgency
  high: "bg-red-100 text-red-800 ring-red-200",
  medium: "bg-amber-100 text-amber-800 ring-amber-200",
  low: "bg-slate-100 text-slate-700 ring-slate-200",
  // status
  new: "bg-slate-100 text-slate-700 ring-slate-200",
  processing: "bg-blue-100 text-blue-800 ring-blue-200",
  ready_for_review: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  needs_manual: "bg-orange-100 text-orange-800 ring-orange-200",
  approved: "bg-emerald-600 text-white ring-emerald-600",
  rejected: "bg-slate-600 text-white ring-slate-600",
};

export function Badge({ value }: { value: string | null }) {
  if (!value) return <span className="text-slate-400">–</span>;
  const style = STYLES[value] ?? "bg-indigo-50 text-indigo-800 ring-indigo-200"; // categories
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}
