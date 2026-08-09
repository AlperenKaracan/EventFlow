from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.idempotency.models import IdempotencyRecord, IdempotencyState

IDEMPOTENCY_RETENTION = timedelta(hours=24)


async def claim_idempotency_key(
    *,
    session: AsyncSession,
    user_id: UUID,
    operation: str,
    key: str,
    request_hash: str,
) -> IdempotencyRecord | None:
    statement = (
        insert(IdempotencyRecord)
        .values(
            user_id=user_id,
            operation=operation,
            key=key,
            request_hash=request_hash,
            state=IdempotencyState.PROCESSING,
            created_at=func.now(),
            expires_at=func.now() + IDEMPOTENCY_RETENTION,
        )
        .on_conflict_do_nothing(
            constraint="uq_idempotency_records_user_operation_key"
        )
        .returning(IdempotencyRecord)
    )
    return cast(IdempotencyRecord | None, await session.scalar(statement))


async def lock_idempotency_key(
    *,
    session: AsyncSession,
    user_id: UUID,
    operation: str,
    key: str,
) -> IdempotencyRecord | None:
    return cast(
        IdempotencyRecord | None,
        await session.scalar(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.key == key,
            )
            .with_for_update()
        ),
    )


def complete_idempotency_record(
    record: IdempotencyRecord,
    *,
    status_code: int,
    response_body: dict[str, Any],
    original_request_id: UUID,
) -> None:
    record.state = IdempotencyState.COMPLETED
    record.response_status = status_code
    record.response_body = response_body
    record.original_request_id = original_request_id


async def delete_expired_idempotency_records(
    *,
    session: AsyncSession,
    now: datetime | None = None,
) -> int:
    cutoff = now if now is not None else func.now()
    result = await session.execute(
        delete(IdempotencyRecord).where(IdempotencyRecord.expires_at <= cutoff)
    )
    return int(getattr(result, "rowcount", 0))
