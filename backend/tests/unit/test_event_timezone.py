from datetime import UTC, datetime

import pytest

from app.events.timezone import validate_event_datetime
from app.shared.errors import AppError


@pytest.mark.parametrize(
    ("starts_at", "timezone_name", "expected_utc"),
    [
        (
            datetime.fromisoformat("2035-05-12T19:00:00+03:00"),
            "Europe/Istanbul",
            datetime(2035, 5, 12, 16, 0, tzinfo=UTC),
        ),
        (
            datetime.fromisoformat("2035-10-28T02:30:00+02:00"),
            "Europe/Berlin",
            datetime(2035, 10, 28, 0, 30, tzinfo=UTC),
        ),
        (
            datetime.fromisoformat("2035-10-28T02:30:00+01:00"),
            "Europe/Berlin",
            datetime(2035, 10, 28, 1, 30, tzinfo=UTC),
        ),
    ],
)
def test_timezone_accepts_normal_and_both_ambiguous_offsets(
    starts_at: datetime, timezone_name: str, expected_utc: datetime
) -> None:
    assert validate_event_datetime(starts_at=starts_at, timezone_name=timezone_name) == expected_utc


def test_timezone_rejects_dst_gap_and_offset_mismatch() -> None:
    with pytest.raises(AppError) as captured:
        validate_event_datetime(
            starts_at=datetime.fromisoformat("2035-03-25T02:30:00+01:00"),
            timezone_name="Europe/Berlin",
        )

    assert captured.value.status_code == 422
    assert captured.value.code == "TIMEZONE_OFFSET_MISMATCH"


def test_timezone_rejects_unknown_iana_name() -> None:
    with pytest.raises(AppError) as captured:
        validate_event_datetime(
            starts_at=datetime.fromisoformat("2035-05-12T19:00:00+03:00"),
            timezone_name="Invalid/EventFlow",
        )

    assert captured.value.code == "INVALID_TIMEZONE"


def test_timezone_rejects_naive_datetime() -> None:
    with pytest.raises(AppError) as captured:
        validate_event_datetime(
            starts_at=datetime(2035, 5, 12, 19, 0),
            timezone_name="Europe/Istanbul",
        )

    assert captured.value.code == "DATETIME_OFFSET_REQUIRED"
