from typing import cast

import pytest
from redis.asyncio import Redis

from app.auth.rate_limit import enforce_login_rate_limit
from app.shared.config import Settings
from app.shared.errors import AppError


class FakeRedis:
    def __init__(self, result: list[int]) -> None:
        self.result = result
        self.seen_key = ""

    async def eval(self, _script: str, _number_of_keys: int, key: str, _window: int) -> list[int]:
        self.seen_key = key
        return self.result


async def test_login_rate_limit_uses_anonymized_key(settings: Settings) -> None:
    fake = FakeRedis([1, 60])

    await enforce_login_rate_limit(
        redis=cast(Redis, fake),
        client_ip="203.0.113.10",
        normalized_email="person@example.com",
        settings=settings,
    )

    assert fake.seen_key.startswith("eventflow:rate-limit:login:")
    assert "person@example.com" not in fake.seen_key
    assert "203.0.113.10" not in fake.seen_key


async def test_login_rate_limit_returns_retry_after(settings: Settings) -> None:
    fake = FakeRedis([settings.LOGIN_RATE_LIMIT_PER_MINUTE + 1, 37])

    with pytest.raises(AppError) as error:
        await enforce_login_rate_limit(
            redis=cast(Redis, fake),
            client_ip="203.0.113.10",
            normalized_email="person@example.com",
            settings=settings,
        )

    assert error.value.status_code == 429
    assert error.value.code == "RATE_LIMIT_EXCEEDED"
    assert error.value.headers == {"Retry-After": "37"}
