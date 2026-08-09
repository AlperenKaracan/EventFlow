from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

from app.factory import create_app
from app.seed import seed_database
from app.shared.config import Settings

POSTGRES_IMAGE = "postgres:17.6-alpine"
REDIS_IMAGE = "redis:8.2-alpine"


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(
        POSTGRES_IMAGE,
        username="eventflow",
        password="eventflow_test_password",
        dbname="eventflow_test",
        driver="asyncpg",
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def migrated_postgres_url(postgres_url: str) -> str:
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", postgres_url)

    command.upgrade(config, "head")
    command.upgrade(config, "head")
    command.check(config)
    return postgres_url


@pytest.fixture(scope="session")
async def seeded_postgres_url(migrated_postgres_url: str) -> str:
    await seed_database(
        migrated_postgres_url,
        organizer_password="OrganizerDemo123!",
        attendee_password="AttendeeDemo123!",
    )
    return migrated_postgres_url


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    with RedisContainer(REDIS_IMAGE) as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


@pytest.fixture
def integration_settings(seeded_postgres_url: str, redis_url: str) -> Settings:
    return Settings(
        APP_ENV="test",
        DATABASE_URL=seeded_postgres_url,
        REDIS_URL=redis_url,
        JWT_SECRET="integration-test-secret-that-is-at-least-32-characters",
        JWT_ISSUER="eventflow-integration-api",
        JWT_AUDIENCE="eventflow-integration-web",
        ACCESS_TOKEN_TTL_MINUTES=15,
        REFRESH_TOKEN_TTL_DAYS=7,
        REFRESH_TOKEN_REVOKED_RETENTION_DAYS=7,
        CORS_ALLOWED_ORIGINS="http://localhost:5173",
        LOG_LEVEL="INFO",
        LOGIN_RATE_LIMIT_PER_MINUTE=5,
        RESERVATION_RATE_LIMIT_PER_MINUTE=10,
        DEPENDENCY_TIMEOUT_SECONDS=1,
        GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS=20,
        FRONTEND_PUBLIC_URL="http://localhost:5173",
        BACKEND_PUBLIC_URL="http://localhost:8000",
    )


@pytest.fixture
async def auth_app(integration_settings: Settings) -> AsyncIterator[object]:
    app = create_app(integration_settings)
    async with app.router.lifespan_context(app):
        await app.state.redis.flushdb()
        yield app


@pytest.fixture
async def auth_client(auth_app: object) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=auth_app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
