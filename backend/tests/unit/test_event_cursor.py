from datetime import UTC, datetime
from uuid import uuid7

import pytest

from app.events.cursor import (
    CursorKind,
    decode_event_cursor,
    encode_event_cursor,
    filter_fingerprint,
)
from app.shared.config import Settings
from app.shared.errors import AppError


def test_cursor_round_trip_preserves_sort_tuple(settings: Settings) -> None:
    event_id = uuid7()
    timestamp = datetime(2035, 5, 12, 16, 0, 12, 345678, tzinfo=UTC)
    fingerprint = filter_fingerprint({})

    raw_cursor = encode_event_cursor(
        kind=CursorKind.PUBLIC_START,
        timestamp=timestamp,
        event_id=event_id,
        filter_hash=fingerprint,
        settings=settings,
    )
    decoded = decode_event_cursor(
        raw_cursor,
        expected_kind=CursorKind.PUBLIC_START,
        expected_filter_hash=fingerprint,
        settings=settings,
    )

    assert decoded.timestamp == timestamp
    assert decoded.event_id == event_id
    assert decoded.kind is CursorKind.PUBLIC_START


@pytest.mark.parametrize("mutation", ["signature", "payload"])
def test_cursor_rejects_tampering(settings: Settings, mutation: str) -> None:
    raw_cursor = encode_event_cursor(
        kind=CursorKind.PUBLIC_START,
        timestamp=datetime(2035, 5, 12, tzinfo=UTC),
        event_id=uuid7(),
        filter_hash=filter_fingerprint({}),
        settings=settings,
    )
    payload, signature = raw_cursor.split(".")
    tampered = (
        f"{payload}.A{signature[1:]}" if mutation == "signature" else f"A{payload[1:]}.{signature}"
    )

    with pytest.raises(AppError) as captured:
        decode_event_cursor(
            tampered,
            expected_kind=CursorKind.PUBLIC_START,
            expected_filter_hash=filter_fingerprint({}),
            settings=settings,
        )

    assert captured.value.status_code == 400
    assert captured.value.code == "INVALID_CURSOR"


def test_cursor_cannot_be_reused_for_another_list_context(settings: Settings) -> None:
    raw_cursor = encode_event_cursor(
        kind=CursorKind.PUBLIC_START,
        timestamp=datetime(2035, 5, 12, tzinfo=UTC),
        event_id=uuid7(),
        filter_hash=filter_fingerprint({}),
        settings=settings,
    )

    with pytest.raises(AppError):
        decode_event_cursor(
            raw_cursor,
            expected_kind=CursorKind.OWNER_CREATED,
            expected_filter_hash=filter_fingerprint({"owner": "current"}),
            settings=settings,
        )
