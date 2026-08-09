from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.router import router as auth_router
from app.observability.logging import configure_logging
from app.observability.middleware import RequestContextMiddleware
from app.observability.router import router as observability_router
from app.shared.config import Settings, load_settings
from app.shared.errors import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or load_settings()
    logger = configure_logging(
        level=active_settings.LOG_LEVEL,
        environment=active_settings.APP_ENV,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db_engine = create_async_engine(
            active_settings.DATABASE_URL,
            pool_pre_ping=True,
        )
        redis_client = Redis.from_url(
            active_settings.REDIS_URL,
            decode_responses=True,
        )
        app.state.db_engine = db_engine
        app.state.session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        app.state.redis = redis_client
        try:
            yield
        finally:
            await redis_client.aclose()
            await db_engine.dispose()

    app = FastAPI(
        title="EventFlow API",
        version="0.1.0",
        docs_url="/docs" if active_settings.APP_ENV != "production" else None,
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.state.logger = logger
    app.add_middleware(RequestContextMiddleware, logger=logger)
    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(observability_router)
    return app
