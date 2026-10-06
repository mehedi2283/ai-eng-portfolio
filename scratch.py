from pydantic import ValidationError

from triage.models import TriageResult

import json

print(json.dumps(TriageResult.model_json_schema(), indent=2))

try:
    TriageResult(
        category="lead",
        urgency="high",
        summary="x",
        needs_reply=True,
        confidence=.5,
    )
except ValidationError as e:
    for err in e.errors():
        print(err["loc"], "->", err["msg"])