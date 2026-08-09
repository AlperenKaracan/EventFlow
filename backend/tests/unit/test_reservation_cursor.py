from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.reservations.cursor import (
    ReservationCursorKind,
    decode_reservation_cursor,
    encode_reservation_cursor,
    reservation_filter_fingerprint,
)
from app.shared.config import Settings
from app.shared.errors import AppError


def test_reservation_cursor_round_trip_preserves_sort_tuple(settings: Settings) -> None:
    timestamp = datetime(2035, 5, 12, 16, 0, tzinfo=UTC)
    reservation_id = UUID("40000000-0000-7000-8000-000000000001")
    fingerprint = reservation_filter_fingerprint({"attendeeId": "attendee-a"})

    raw_cursor = encode_reservation_cursor(
        kind=ReservationCursorKind.ATTENDEE_HISTORY,
        timestamp=timestamp,
        reservation_id=reservation_id,
        filter_hash=fingerprint,
        settings=settings,
    )
    decoded = decode_reservation_cursor(
        raw_cursor,
        expected_kind=ReservationCursorKind.ATTENDEE_HISTORY,
        expected_filter_hash=fingerprint,
        settings=settings,
    )

    assert decoded.timestamp == timestamp
    assert decoded.reservation_id == reservation_id


def test_reservation_cursor_rejects_tampering(settings: Settings) -> None:
    raw_cursor = encode_reservation_cursor(
        kind=ReservationCursorKind.EVENT_ATTENDEES,
        timestamp=datetime(2035, 5, 12, 16, 0, tzinfo=UTC),
        reservation_id=UUID("40000000-0000-7000-8000-000000000001"),
        filter_hash=reservation_filter_fingerprint({"eventId": "event-a"}),
        settings=settings,
    )
    payload, signature = raw_cursor.split(".")

    with pytest.raises(AppError) as error:
        decode_reservation_cursor(
            f"{payload}A.{signature}",
            expected_kind=ReservationCursorKind.EVENT_ATTENDEES,
            expected_filter_hash=reservation_filter_fingerprint({"eventId": "event-a"}),
            settings=settings,
        )

    assert error.value.code == "INVALID_CURSOR"


def test_reservation_cursor_is_bound_to_kind_and_filter(settings: Settings) -> None:
    raw_cursor = encode_reservation_cursor(
        kind=ReservationCursorKind.ATTENDEE_HISTORY,
        timestamp=datetime(2035, 5, 12, 16, 0, tzinfo=UTC),
        reservation_id=UUID("40000000-0000-7000-8000-000000000001"),
        filter_hash=reservation_filter_fingerprint({"attendeeId": "attendee-a"}),
        settings=settings,
    )

    with pytest.raises(AppError) as error:
        decode_reservation_cursor(
            raw_cursor,
            expected_kind=ReservationCursorKind.EVENT_ATTENDEES,
            expected_filter_hash=reservation_filter_fingerprint({"eventId": "event-a"}),
            settings=settings,
        )

    assert error.value.code == "INVALID_CURSOR"
