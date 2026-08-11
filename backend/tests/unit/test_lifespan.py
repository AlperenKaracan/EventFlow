from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app import factory
from app.shared.config import Settings


class FakeEngine:
    def __init__(self) -> None:
        self.dispose = AsyncMock()


class FakeRedis:
    def __init__(self) -> None:
        self.aclose = AsyncMock()


async def test_lifespan_closes_redis_and_database_pools(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = FakeEngine()
    redis = FakeRedis()
    monkeypatch.setattr("app.factory.create_async_engine", lambda *_args, **_kwargs: engine)
    monkeypatch.setattr("app.factory.Redis.from_url", lambda *_args, **_kwargs: redis)
    app = factory.create_app(settings)

    async with app.router.lifespan_context(app):
        assert app.state.db_engine is engine
        assert app.state.redis is redis

    engine.dispose.assert_awaited_once()
    redis.aclose.assert_awaited_once()
