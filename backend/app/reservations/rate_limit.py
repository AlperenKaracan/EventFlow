from __future__ import annotations

import hashlib
import hmac
from typing import cast
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.observability.metrics import record_rate_limit_rejection
from app.shared.config import Settings
from app.shared.errors import AppError

RESERVATION_WINDOW_SECONDS = 60

_CONSUME_FIXED_WINDOW = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


def _reservation_rate_limit_key(*, user_id: UUID, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        str(user_id).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"eventflow:rate-limit:reservation:{digest}"


async def enforce_reservation_rate_limit(
    *,
    redis: Redis,
    user_id: UUID,
    settings: Settings,
) -> None:
    key = _reservation_rate_limit_key(
        user_id=user_id,
        secret=settings.JWT_SECRET.get_secret_value(),
    )
    try:
        raw_result = await redis.eval(
            _CONSUME_FIXED_WINDOW,
            1,
            key,
            RESERVATION_WINDOW_SECONDS,
        )
        count, ttl = cast(list[int], raw_result)
    except (RedisError, OSError, ValueError, TypeError) as exc:
        raise AppError(
            status_code=503,
            code="RATE_LIMIT_UNAVAILABLE",
            message="Rezervasyon koruması geçici olarak kullanılamıyor.",
        ) from exc

    if count > settings.RESERVATION_RATE_LIMIT_PER_MINUTE:
        record_rate_limit_rejection(endpoint="reservation_create")
        raise AppError(
            status_code=429,
            code="RATE_LIMIT_EXCEEDED",
            message="Çok fazla rezervasyon denemesi yapıldı.",
            headers={"Retry-After": str(max(ttl, 1))},
        )
