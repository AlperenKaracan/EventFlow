import pytest
from pydantic import ValidationError

from app.events.schemas import EventUpdateRequest


def test_event_update_requires_at_least_one_non_null_change() -> None:
    with pytest.raises(ValidationError, match="at least one event field"):
        EventUpdateRequest.model_validate({"expectedVersion": 1})

    with pytest.raises(ValidationError, match="must not be null"):
        EventUpdateRequest.model_validate({"expectedVersion": 1, "title": None})


def test_event_update_requires_start_and_timezone_as_pair() -> None:
    with pytest.raises(ValidationError, match="must be changed together"):
        EventUpdateRequest.model_validate(
            {
                "expectedVersion": 1,
                "startsAt": "2036-05-12T19:00:00+03:00",
            }
        )
