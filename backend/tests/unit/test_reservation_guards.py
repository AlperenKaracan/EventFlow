from typing import cast
from uuid import UUID

import pytest
from redis.asyncio import Redis

from app.idempotency.keys import reservation_create_request_hash, validate_idempotency_key
from app.reservations.rate_limit import enforce_reservation_rate_limit
from app.shared.config import Settings
from app.shared.errors import AppError


class FakeRedis:
    def __init__(self, result: list[int]) -> None:
        self.result = result
        self.seen_key = ""

    async def eval(self, _script: str, _keys: int, key: str, _window: int) -> list[int]:
        self.seen_key = key
        return self.result


async def test_reservation_rate_limit_anonymizes_user_key(settings: Settings) -> None:
    user_id = UUID("10000000-0000-7000-8000-000000000002")
    fake = FakeRedis([1, 60])

    await enforce_reservation_rate_limit(
        redis=cast(Redis, fake),
        user_id=user_id,
        settings=settings,
    )

    assert fake.seen_key.startswith("eventflow:rate-limit:reservation:")
    assert str(user_id) not in fake.seen_key


async def test_reservation_rate_limit_returns_retry_after(settings: Settings) -> None:
    fake = FakeRedis([settings.RESERVATION_RATE_LIMIT_PER_MINUTE + 1, 23])

    with pytest.raises(AppError) as error:
        await enforce_reservation_rate_limit(
            redis=cast(Redis, fake),
            user_id=UUID("10000000-0000-7000-8000-000000000002"),
            settings=settings,
        )

    assert error.value.status_code == 429
    assert error.value.code == "RATE_LIMIT_EXCEEDED"
    assert error.value.headers == {"Retry-After": "23"}


@pytest.mark.parametrize(
    "key",
    ["", "contains space", "slash/not-allowed", "x" * 201, "türkçe"],
)
def test_idempotency_key_rejects_unsafe_values(key: str) -> None:
    with pytest.raises(AppError) as error:
        validate_idempotency_key(key)

    assert error.value.code == "INVALID_IDEMPOTENCY_KEY"


def test_reservation_request_hash_is_canonical_and_event_bound() -> None:
    first_event = UUID("30000000-0000-7000-8000-000000000001")
    second_event = UUID("30000000-0000-7000-8000-000000000002")

    first = reservation_create_request_hash(
        event_id=first_event,
        body={"z": 1, "nested": {"b": 2, "a": 1}},
    )
    reordered = reservation_create_request_hash(
        event_id=first_event,
        body={"nested": {"a": 1, "b": 2}, "z": 1},
    )
    another_event = reservation_create_request_hash(
        event_id=second_event,
        body={"z": 1, "nested": {"b": 2, "a": 1}},
    )

    assert validate_idempotency_key("018f.example:key-1") == "018f.example:key-1"
    assert first == reordered
    assert first != another_event
    assert len(first) == 64
