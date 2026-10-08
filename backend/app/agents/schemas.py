"""The exact JSON shape each agent must return. Anything else counts as a failed call."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

Category = Literal["billing", "order_status", "technical", "refund", "complaint", "other"]
Urgency = Literal["low", "medium", "high"]


class SorterOutput(BaseModel):
    category: Category
    urgency: Urgency
    reason: str = Field(min_length=1, max_length=300)


class ExtractorOutput(BaseModel):
    # null (None) means "not in the message"; the agent must never fill a gap with a guess.
    customer_name: str | None = Field(max_length=100)
    order_id: str | None = Field(max_length=50)
    product: str | None = Field(max_length=100)
    request: str = Field(min_length=1, max_length=300)


class DrafterOutput(BaseModel):
    reply: str = Field(min_length=1, max_length=2000)


class CheckerOutput(BaseModel):
    ok: bool
    problems: list[str] = Field(max_length=10)

    @model_validator(mode="after")
    def ok_means_no_problems(self) -> Self:
        if self.ok != (len(self.problems) == 0):
            raise ValueError('"ok" must be true exactly when "problems" is empty')
        return self
