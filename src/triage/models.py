from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["lead", "support", "spam", "other"]
Urgency = Literal["low", "medium", "high"]


class Email(BaseModel):
    sender: str
    subject: str
    body: str
    tags: list[str] = []


class TriageResult(BaseModel):
    category: Category = Field(
        description=(
            "lead: a potential customer asking for a quote, pricing, or partnership. "
            "support: an existing user needing help with a problem. "
            "spam: unsolicited promotions or scams. "
            "other: invoices, receipts, notifications, anything else."
        )
    )
    urgency: Urgency = Field(
        description="high: deadline or blocking problem; medium: needs reply this week; low: no time pressure."
    )
    summary: str = Field(max_length=200, description="One sentence summary of the email.")
    needs_reply: bool = Field(description="True only if a human reply is expected.")
    confidence: float = Field(ge=0, le=1, description="Your confidence in the category, 0 to 1.")