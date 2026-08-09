from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.idempotency.service import cleanup_expired_idempotency_records
from app.observability.logging import configure_logging
from app.shared.config import load_settings


async def main() -> None:
    settings = load_settings()
    logger = configure_logging(level=settings.LOG_LEVEL, environment=settings.APP_ENV)
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with session_factory() as session:
            deleted_count = await cleanup_expired_idempotency_records(session=session)
        logger.info(
            "Expired idempotency records cleaned",
            extra={
                "event": "idempotency.records.cleaned",
                "deletedCount": deleted_count,
            },
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
