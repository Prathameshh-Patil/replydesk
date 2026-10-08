"""The exact JSON shape each agent must return. Anything else counts as a failed call."""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["billing", "order_status", "technical", "refund", "complaint", "other"]
Urgency = Literal["low", "medium", "high"]


class SorterOutput(BaseModel):
    category: Category
    urgency: Urgency
    reason: str = Field(min_length=1, max_length=300)
