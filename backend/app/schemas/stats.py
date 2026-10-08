from pydantic import BaseModel


class Stats(BaseModel):
    total_tickets: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    approved: int
    approved_without_edits: int
    # approved_without_edits / approved drafts; None until something has been approved
    share_approved_without_edits: float | None
    checked_drafts: int
    # share of drafts the Checker passed; None until something has been checked
    checker_pass_rate: float | None
    # average milliseconds per successful agent call, e.g. {"sorter": 2310.5, ...}
    avg_ms_per_step: dict[str, float]
