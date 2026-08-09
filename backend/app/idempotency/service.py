from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.idempotency.repository import delete_expired_idempotency_records


async def cleanup_expired_idempotency_records(
    *,
    session: AsyncSession,
    now: datetime | None = None,
) -> int:
    try:
        deleted_count = await delete_expired_idempotency_records(
            session=session,
            now=now,
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return deleted_count
