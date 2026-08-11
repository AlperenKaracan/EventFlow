from __future__ import annotations

import hashlib
import hmac
from typing import cast

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.observability.metrics import record_rate_limit_rejection
from app.shared.config import Settings
from app.shared.errors import AppError

LOGIN_WINDOW_SECONDS = 60

_CONSUME_FIXED_WINDOW = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


def _login_rate_limit_key(*, client_ip: str, email: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{client_ip}\0{email}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"eventflow:rate-limit:login:{digest}"


async def enforce_login_rate_limit(
    *,
    redis: Redis,
    client_ip: str,
    normalized_email: str,
    settings: Settings,
) -> None:
    key = _login_rate_limit_key(
        client_ip=client_ip,
        email=normalized_email,
        secret=settings.JWT_SECRET.get_secret_value(),
    )
    try:
        raw_result = await redis.eval(_CONSUME_FIXED_WINDOW, 1, key, LOGIN_WINDOW_SECONDS)
        count, ttl = cast(list[int], raw_result)
    except (RedisError, OSError, ValueError, TypeError) as exc:
        raise AppError(
            status_code=503,
            code="RATE_LIMIT_UNAVAILABLE",
            message="Giriş koruması geçici olarak kullanılamıyor.",
        ) from exc

    if count > settings.LOGIN_RATE_LIMIT_PER_MINUTE:
        retry_after = max(ttl, 1)
        record_rate_limit_rejection(endpoint="login")
        raise AppError(
            status_code=429,
            code="RATE_LIMIT_EXCEEDED",
            message="Çok fazla giriş denemesi yapıldı.",
            headers={"Retry-After": str(retry_after)},
        )
