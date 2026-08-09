from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid7

from fastapi import FastAPI
from sqlalchemy import select

from app.idempotency.models import IdempotencyRecord, IdempotencyState
from app.idempotency.service import cleanup_expired_idempotency_records
from app.seed import IDENTITY


async def test_cleanup_removes_only_expired_records_and_is_repeatable(
    auth_app: object,
) -> None:
    app = cast(FastAPI, auth_app)
    now = datetime(2035, 1, 1, tzinfo=UTC)
    expired_completed_key = f"expired-completed-{uuid7()}"
    expired_processing_key = f"expired-processing-{uuid7()}"
    future_key = f"future-{uuid7()}"
    async with app.state.session_factory() as session:
        session.add_all(
            [
                IdempotencyRecord(
                    user_id=IDENTITY.attendee_id,
                    operation="reservation.create",
                    key=expired_completed_key,
                    request_hash="a" * 64,
                    state=IdempotencyState.COMPLETED,
                    response_status=409,
                    response_body={"error": {"code": "EVENT_FULL"}},
                    original_request_id=uuid7(),
                    expires_at=now - timedelta(seconds=1),
                ),
                IdempotencyRecord(
                    user_id=IDENTITY.attendee_id,
                    operation="reservation.create",
                    key=expired_processing_key,
                    request_hash="b" * 64,
                    state=IdempotencyState.PROCESSING,
                    expires_at=now,
                ),
                IdempotencyRecord(
                    user_id=IDENTITY.attendee_id,
                    operation="reservation.create",
                    key=future_key,
                    request_hash="c" * 64,
                    state=IdempotencyState.PROCESSING,
                    expires_at=now + timedelta(seconds=1),
                ),
            ]
        )
        await session.commit()

    async with app.state.session_factory() as session:
        first_deleted = await cleanup_expired_idempotency_records(
            session=session,
            now=now,
        )
        second_deleted = await cleanup_expired_idempotency_records(
            session=session,
            now=now,
        )
        remaining_keys = set(
            await session.scalars(
                select(IdempotencyRecord.key).where(
                    IdempotencyRecord.key.in_(
                        (expired_completed_key, expired_processing_key, future_key)
                    )
                )
            )
        )

    assert first_deleted == 2
    assert second_deleted == 0
    assert remaining_keys == {future_key}
