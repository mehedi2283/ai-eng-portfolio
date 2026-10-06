from dataclasses import dataclass, field
from typing import Literal

Category = Literal["lead", "support", "spam", "other"]
Urgency = Literal["low", "medium", "high"]


@dataclass
class Email:
    sender: str
    subject: str
    body: str
    tags: list[str] = field(default_factory=list)


@dataclass
class TriageResult:
    category: Category
    urgency: Urgency
    summary: str
    needs_reply: bool