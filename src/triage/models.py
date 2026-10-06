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
    category: Category
    urgency: Urgency
    summary: str = Field(max_length=200)
    needs_reply: bool
    confidence: float = Field(ge=0, le=1)