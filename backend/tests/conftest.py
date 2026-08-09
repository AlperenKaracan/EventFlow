from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.factory import create_app
from app.shared.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        APP_ENV="test",
        DATABASE_URL="postgresql+asyncpg://eventflow:eventflow@127.0.0.1:1/eventflow_test",
        REDIS_URL="redis://127.0.0.1:1/0",
        JWT_SECRET="test-only-secret-that-is-at-least-32-characters",
        JWT_ISSUER="eventflow-test-api",
        JWT_AUDIENCE="eventflow-test-web",
        ACCESS_TOKEN_TTL_MINUTES=15,
        REFRESH_TOKEN_TTL_DAYS=7,
        REFRESH_TOKEN_REVOKED_RETENTION_DAYS=7,
        CORS_ALLOWED_ORIGINS="http://localhost:5173",
        LOG_LEVEL="INFO",
        LOGIN_RATE_LIMIT_PER_MINUTE=5,
        RESERVATION_RATE_LIMIT_PER_MINUTE=10,
        DEPENDENCY_TIMEOUT_SECONDS=0.1,
        GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS=20,
        FRONTEND_PUBLIC_URL="http://localhost:5173",
        BACKEND_PUBLIC_URL="http://localhost:8000",
    )


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
            yield test_client
