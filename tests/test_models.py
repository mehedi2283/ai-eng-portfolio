import pytest
from pydantic import ValidationError

from triage.models import TriageResult


def make(**overrides):
    data = dict(
        category="lead",
        urgency="high",
        summary="x",
        needs_reply=True,
        confidence=0.5,
    )
    return TriageResult(**{**data, **overrides})


def test_valid_parse():
    r = make()
    assert r.category == "lead"


def test_invalid_category_rejected():
    with pytest.raises(ValidationError):
        make(category="banana")


@pytest.mark.parametrize("bad", [1.5, -0.1])
def test_confidence_out_of_range_rejected(bad):
    with pytest.raises(ValidationError):
        make(confidence=bad)