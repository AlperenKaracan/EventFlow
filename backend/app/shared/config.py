from __future__ import annotations

from functools import cached_property
from typing import Literal, Self

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Fail-fast runtime configuration loaded only from environment variables."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=True,
        extra="ignore",
        frozen=True,
    )

    APP_ENV: Literal["development", "test", "production"]
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: SecretStr = Field(min_length=32)
    JWT_ISSUER: str = Field(min_length=1, max_length=200)
    JWT_AUDIENCE: str = Field(min_length=1, max_length=200)
    ACCESS_TOKEN_TTL_MINUTES: int = Field(gt=0, le=60)
    REFRESH_TOKEN_TTL_DAYS: int = Field(gt=0, le=30)
    REFRESH_TOKEN_REVOKED_RETENTION_DAYS: int = Field(ge=1, le=90)
    CORS_ALLOWED_ORIGINS: str
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    LOGIN_RATE_LIMIT_PER_MINUTE: int = Field(gt=0)
    RESERVATION_RATE_LIMIT_PER_MINUTE: int = Field(gt=0)
    DEPENDENCY_TIMEOUT_SECONDS: float = Field(gt=0, le=30)
    GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS: int = Field(gt=0, le=120)
    FRONTEND_PUBLIC_URL: AnyHttpUrl
    BACKEND_PUBLIC_URL: AnyHttpUrl

    @model_validator(mode="after")
    def validate_security_configuration(self) -> Self:
        origins = self.cors_origins
        if not origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must contain at least one origin")
        if "*" in origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must not contain a wildcard")

        raw_secret = self.JWT_SECRET.get_secret_value()
        if self.APP_ENV == "production" and raw_secret.lower() in {
            "change-me-change-me-change-me-change-me",
            "development-only-secret-change-me",
        }:
            raise ValueError("JWT_SECRET must not use a demo value in production")
        if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")
        if not self.REDIS_URL.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must use redis or rediss")
        return self

    @cached_property
    def cors_origins(self) -> tuple[str, ...]:
        return tuple(
            origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
        )


def load_settings() -> Settings:
    return Settings()
