import pytest
from pydantic import ValidationError

from app.shared.config import Settings


def valid_config() -> dict[str, object]:
    return {
        "APP_ENV": "test",
        "DATABASE_URL": "postgresql+asyncpg://eventflow:eventflow@localhost/eventflow",
        "REDIS_URL": "redis://localhost:6379/0",
        "JWT_SECRET": "test-only-secret-that-is-at-least-32-characters",
        "JWT_ISSUER": "eventflow-test-api",
        "JWT_AUDIENCE": "eventflow-test-web",
        "ACCESS_TOKEN_TTL_MINUTES": 15,
        "REFRESH_TOKEN_TTL_DAYS": 7,
        "REFRESH_TOKEN_REVOKED_RETENTION_DAYS": 7,
        "CORS_ALLOWED_ORIGINS": "http://localhost:5173",
        "LOG_LEVEL": "INFO",
        "LOGIN_RATE_LIMIT_PER_MINUTE": 5,
        "RESERVATION_RATE_LIMIT_PER_MINUTE": 10,
        "DEPENDENCY_TIMEOUT_SECONDS": 1,
        "GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS": 20,
        "FRONTEND_PUBLIC_URL": "http://localhost:5173",
        "BACKEND_PUBLIC_URL": "http://localhost:8000",
    }


def test_settings_reject_wildcard_cors() -> None:
    values = valid_config() | {"CORS_ALLOWED_ORIGINS": "*"}

    with pytest.raises(ValidationError, match="must not contain a wildcard"):
        Settings(**values)  # type: ignore[arg-type]


def test_settings_reject_non_async_postgres_url() -> None:
    values = valid_config() | {"DATABASE_URL": "postgresql://localhost/eventflow"}

    with pytest.raises(ValidationError, match=r"must use postgresql\+asyncpg"):
        Settings(**values)  # type: ignore[arg-type]


def test_settings_normalize_exact_cors_allowlist() -> None:
    values = valid_config() | {
        "CORS_ALLOWED_ORIGINS": "http://localhost:5173, https://eventflow.example"
    }

    settings = Settings(**values)  # type: ignore[arg-type]

    assert settings.cors_origins == (
        "http://localhost:5173",
        "https://eventflow.example",
    )
