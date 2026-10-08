"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/Badge";
import { api, ApiError } from "@/lib/api";
import type { TicketDetail } from "@/lib/types";

const STEPS = ["sorter", "extractor", "drafter", "checker"];
const WORKING = ["new", "processing"];
const REVIEWABLE = ["ready_for_review", "needs_manual"];

export function TicketView() {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  // Only the reviewer's edits are state; null means "untouched, show the draft".
  const [edits, setEdits] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const t = await api<TicketDetail>(`/tickets/${id}`);
      setTicket(t);
      return t;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load the ticket");
    }
  }, [id]);

  // Load once; while the agents are working, check again every 1.5 seconds.
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      const t = await load();
      if (t && WORKING.includes(t.status)) timer = setTimeout(poll, 1500);
    };
    poll();
    return () => clearTimeout(timer);
  }, [load]);

  async function act(action: "approve" | "reject" | "rerun") {
    setBusy(true);
    setError(null);
    try {
      const body = action === "approve" ? JSON.stringify({ final_reply: reply }) : undefined;
      await api(`/tickets/${id}/${action}`, { method: "POST", body });
      setEdits(null); // after any decision, show what the server now holds
      const t = await load();
      if (action === "rerun" && t) {
        // follow the new run until it finishes
        const follow = async () => {
          const next = await load();
          if (next && WORKING.includes(next.status)) setTimeout(follow, 1500);
        };
        follow();
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  if (!ticket) return <p className="text-slate-500">{error ?? "Loading…"}</p>;

  const reply = edits ?? ticket.final_reply ?? ticket.draft_reply ?? "";
  const reviewable = REVIEWABLE.includes(ticket.status);
  const working = WORKING.includes(ticket.status);
  const edited = ticket.draft_reply !== null && reply.trim() !== ticket.draft_reply.trim();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link href="/" className="text-sm text-slate-500 hover:text-slate-900">← Inbox</Link>
        <h1 className="text-xl font-semibold">#{ticket.id} {ticket.subject}</h1>
        <Badge value={ticket.status} />
        <Badge value={ticket.category} />
        <Badge value={ticket.urgency} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: what the customer wrote */}
        <section className="rounded-lg bg-white p-5 ring-1 ring-slate-200">
          <h2 className="text-sm font-medium text-slate-500">Customer message</h2>
          <p className="mt-2 font-medium">{ticket.customer_name} <span className="font-normal text-slate-500">&lt;{ticket.customer_email}&gt;</span></p>
          <p className="text-sm text-slate-500">{new Date(ticket.created_at).toLocaleString()}</p>
          <p className="mt-4 whitespace-pre-wrap">{ticket.body}</p>
        </section>

        {/* Right: what the agents produced, and the human decision */}
        <section className="space-y-4 rounded-lg bg-white p-5 ring-1 ring-slate-200">
          {working && <p className="rounded bg-blue-50 p-3 text-sm text-blue-800">The agents are working on this message…</p>}
          {ticket.status === "needs_manual" && (
            <p className="rounded bg-orange-50 p-3 text-sm text-orange-800">
              An agent failed twice, so this needs a person. Write the reply yourself, or try Rerun.
            </p>
          )}

          <div>
            <h2 className="text-sm font-medium text-slate-500">Extracted details</h2>
            {ticket.extracted ? (
              <dl className="mt-2 grid grid-cols-[8rem_1fr] gap-y-1 text-sm">
                <dt className="text-slate-500">Name</dt><dd>{ticket.extracted.customer_name ?? <em className="text-slate-400">not in message</em>}</dd>
                <dt className="text-slate-500">Order ID</dt><dd>{ticket.extracted.order_id ?? <em className="text-slate-400">not in message</em>}</dd>
                <dt className="text-slate-500">Product</dt><dd>{ticket.extracted.product ?? <em className="text-slate-400">not in message</em>}</dd>
                <dt className="text-slate-500">Asking for</dt><dd>{ticket.extracted.request}</dd>
              </dl>
            ) : <p className="mt-2 text-sm text-slate-400">Not extracted yet.</p>}
          </div>

          {ticket.checker_problems && ticket.checker_problems.length > 0 && (
            <div role="alert" className="rounded border border-amber-300 bg-amber-50 p-3">
              <h2 className="text-sm font-medium text-amber-900">⚠ The Checker found problems in the draft</h2>
              <ul className="mt-1 list-disc pl-5 text-sm text-amber-900">
                {ticket.checker_problems.map((p) => <li key={p}>{p}</li>)}
              </ul>
            </div>
          )}
          {ticket.checker_ok && <p className="text-sm text-emerald-700">✓ The Checker found no problems.</p>}

          <div>
            <label htmlFor="reply" className="text-sm font-medium text-slate-500">
              {ticket.status === "approved" ? "Sent reply" : "Draft reply (you can edit it)"}
            </label>
            <textarea id="reply" value={reply} onChange={(e) => setEdits(e.target.value)} disabled={!reviewable}
              rows={10} className="mt-1 w-full rounded border border-slate-300 p-3 text-sm disabled:bg-slate-50" />
            {ticket.status === "approved" && (
              <p className="text-sm text-slate-500">Approved {ticket.edited ? "with edits" : "without edits"} · {ticket.reviewed_at && new Date(ticket.reviewed_at).toLocaleString()}</p>
            )}
          </div>

          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <div className="flex flex-wrap gap-2">
            <button onClick={() => act("approve")} disabled={!reviewable || busy || !reply.trim()}
              className="rounded bg-emerald-700 px-4 py-2 font-medium text-white hover:bg-emerald-800 disabled:opacity-40">
              {edited ? "Approve with edits" : "Approve"}
            </button>
            <button onClick={() => act("reject")} disabled={!reviewable || busy}
              className="rounded bg-white px-4 py-2 font-medium text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 disabled:opacity-40">
              Reject
            </button>
            <button onClick={() => act("rerun")} disabled={working || ticket.status === "approved" || busy}
              className="rounded bg-white px-4 py-2 font-medium text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 disabled:opacity-40">
              Rerun agents
            </button>
          </div>
        </section>
      </div>

      {/* Below: what each agent did, in order */}
      <section className="rounded-lg bg-white p-5 ring-1 ring-slate-200">
        <h2 className="text-sm font-medium text-slate-500">Agent timeline</h2>
        {ticket.agent_runs.length === 0 && <p className="mt-2 text-sm text-slate-400">No agent has run yet.</p>}
        <ol className="mt-3 space-y-2">
          {ticket.agent_runs.map((run) => (
            <li key={run.id}>
              <details className="rounded border border-slate-200">
                <summary className="flex cursor-pointer flex-wrap items-center gap-3 px-3 py-2 text-sm">
                  <span className="w-5 text-center" aria-hidden>{run.ok ? "✓" : "✗"}</span>
                  <span className="font-medium capitalize">{run.agent_name}</span>
                  <span className="text-slate-500">step {STEPS.indexOf(run.agent_name) + 1} of 4</span>
                  <span className={run.ok ? "text-emerald-700" : "text-red-700"}>{run.ok ? "ok" : "failed"}</span>
                  <span className="ml-auto tabular-nums text-slate-500">{(run.duration_ms / 1000).toFixed(1)} s</span>
                </summary>
                <div className="space-y-2 border-t border-slate-200 p-3 text-xs">
                  {run.error && <p className="text-red-700">Error: {run.error}</p>}
                  <p className="font-medium text-slate-500">Input</p>
                  <pre className="whitespace-pre-wrap rounded bg-slate-50 p-2">{run.input}</pre>
                  <p className="font-medium text-slate-500">Output</p>
                  <pre className="whitespace-pre-wrap rounded bg-slate-50 p-2">{run.output ?? "(no output)"}</pre>
                </div>
              </details>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
