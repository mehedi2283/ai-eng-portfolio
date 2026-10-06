import json
from pathlib import Path

from triage.models import Email


def load_emails(path: str) -> list[Email]:
    text = Path(path).read_text()
    data = json.loads(text)
    return [Email.model_validate(item) for item in data]