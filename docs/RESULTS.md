# Results

Every number here is produced by `eval/run_eval.py` from the per-message rows in `eval/runs/<run>.csv`. Labels: `eval/emails.csv` (rules in `docs/BRIEF.md`). Product counts as correct when one name contains the other; the free-text `request` field is not scored. "Invented" uses the extractor's raw answer, before the code's order-ID safety net.

## Run `baseline`: 2026-10-08

Model `openai/gpt-oss-120b` · 60 messages · agent prompts at commit `b6ce503` · reproduce: `backend/.venv/bin/python eval/run_eval.py --run baseline`

**What changed:** First run. Agent prompts as written in Phases 4–5.

| Measure | Result |
|---|---|
| Category accuracy | 90% |
| Urgency accuracy | 82% |
| `customer_name` correct | 98% |
| `order_id` correct | 98% |
| `product` correct | 93% |
| `customer_name` invented (of messages with none) | 0 of 47 |
| `order_id` invented (of messages with none) | 0 of 21 |
| `product` invented (of messages with none) | 0 of 22 |
| Checker passed the draft | 86% |
| Ended in `needs_manual` | 1 |
| Injection messages handled safely (keyword check, drafts read by hand) | 3 of 3 |
| Average time per message (4 agents) | 18.8 s |
| Tokens per message | 4,467 |
| Cost | $0 (Groq free tier); $0.0492 at list price |

Category or urgency misses (got → expected):

- E06: other/low → billing/low
- E10: billing/medium → billing/low
- E14: order_status/medium → order_status/high
- E15: order_status/medium → order_status/low
- E16: order_status/low → order_status/medium
- E17: order_status/medium → order_status/low
- E20: order_status/medium → order_status/high
- E24: technical/medium → technical/low
- E32: technical/medium → technical/low
- E37: other/low → refund/low
- E38: refund/high → refund/medium
- E41: refund/medium → refund/low
- E42: billing/high → refund/medium
- E46: refund/medium → complaint/medium
- E50: order_status/medium → complaint/medium
- E52: order_status/medium → complaint/medium
