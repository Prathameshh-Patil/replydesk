// The shapes the API returns (mirrors backend/app/schemas).

export type Status =
  | "new"
  | "processing"
  | "ready_for_review"
  | "needs_manual"
  | "approved"
  | "rejected";

export interface AgentRun {
  id: number;
  agent_name: string;
  input: string;
  output: string | null;
  ok: boolean;
  error: string | null;
  duration_ms: number;
  created_at: string;
}

export interface Ticket {
  id: number;
  customer_name: string;
  customer_email: string;
  subject: string;
  body: string;
  status: Status;
  category: string | null;
  urgency: string | null;
  extracted: {
    customer_name: string | null;
    order_id: string | null;
    product: string | null;
    request: string;
  } | null;
  draft_reply: string | null;
  checker_ok: boolean | null;
  checker_problems: string[] | null;
  final_reply: string | null;
  edited: boolean | null;
  reviewed_by: number | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface TicketDetail extends Ticket {
  agent_runs: AgentRun[];
}

export interface Stats {
  total_tickets: number;
  by_status: Record<Status, number>;
  by_category: Record<string, number>;
  approved: number;
  approved_without_edits: number;
  share_approved_without_edits: number | null;
  checked_drafts: number;
  checker_pass_rate: number | null;
  avg_ms_per_step: Record<string, number>;
}
