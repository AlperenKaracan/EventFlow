from __future__ import annotations

import asyncio
from typing import cast
from uuid import uuid7

from fastapi import FastAPI

from app.idempotency.models import IdempotencyState
from app.idempotency.repository import (
    claim_idempotency_key,
    complete_idempotency_record,
    lock_idempotency_key,
)
from app.seed import IDENTITY


async def test_committed_owner_makes_waiter_observe_completed_record(
    auth_app: object,
) -> None:
    app = cast(FastAPI, auth_app)
    key = f"commit-{uuid7()}"
    owner_inserted = asyncio.Event()
    release_owner = asyncio.Event()

    async def owner() -> None:
        async with app.state.session_factory() as session:
            record = await claim_idempotency_key(
                session=session,
                user_id=IDENTITY.attendee_id,
                operation="reservation.create",
                key=key,
                request_hash="a" * 64,
            )
            assert record is not None
            owner_inserted.set()
            await release_owner.wait()
            complete_idempotency_record(
                record,
                status_code=409,
                response_body={"error": {"code": "EVENT_FULL"}},
                original_request_id=uuid7(),
            )
            await session.commit()

    async def waiter() -> tuple[bool, IdempotencyState, int | None]:
        await owner_inserted.wait()
        async with app.state.session_factory() as session:
            claim = await claim_idempotency_key(
                session=session,
                user_id=IDENTITY.attendee_id,
                operation="reservation.create",
                key=key,
                request_hash="a" * 64,
            )
            record = claim or await lock_idempotency_key(
                session=session,
                user_id=IDENTITY.attendee_id,
                operation="reservation.create",
                key=key,
            )
            assert record is not None
            return claim is not None, record.state, record.response_status

    owner_task = asyncio.create_task(owner())
    await owner_inserted.wait()
    waiter_task = asyncio.create_task(waiter())
    await asyncio.sleep(0.05)
    assert not waiter_task.done()
    release_owner.set()

    await owner_task
    claimed, state, response_status = await asyncio.wait_for(waiter_task, timeout=2)
    assert claimed is False
    assert state is IdempotencyState.COMPLETED
    assert response_status == 409


async def test_rolled_back_owner_allows_waiter_to_take_ownership(
    auth_app: object,
) -> None:
    app = cast(FastAPI, auth_app)
    key = f"rollback-{uuid7()}"
    owner_inserted = asyncio.Event()
    release_owner = asyncio.Event()

    async def owner() -> None:
        async with app.state.session_factory() as session:
            record = await claim_idempotency_key(
                session=session,
                user_id=IDENTITY.attendee_id,
                operation="reservation.create",
                key=key,
                request_hash="b" * 64,
            )
            assert record is not None
            owner_inserted.set()
            await release_owner.wait()
            await session.rollback()

    async def waiter() -> bool:
        await owner_inserted.wait()
        async with app.state.session_factory() as session:
            record = await claim_idempotency_key(
                session=session,
                user_id=IDENTITY.attendee_id,
                operation="reservation.create",
                key=key,
                request_hash="b" * 64,
            )
            assert record is not None
            await session.commit()
            return record.state is IdempotencyState.PROCESSING

    owner_task = asyncio.create_task(owner())
    await owner_inserted.wait()
    waiter_task = asyncio.create_task(waiter())
    await asyncio.sleep(0.05)
    assert not waiter_task.done()
    release_owner.set()

    await owner_task
    assert await asyncio.wait_for(waiter_task, timeout=2)
