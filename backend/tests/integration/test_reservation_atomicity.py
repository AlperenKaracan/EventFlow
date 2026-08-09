from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid7

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.reservations.service as reservation_service
from app.audit.models import AuditLog
from app.events.models import Event
from app.idempotency.models import IdempotencyRecord
from app.idempotency.repository import complete_idempotency_record
from app.reservations.models import Reservation
from tests.integration.test_reservation_creation import create_event, register_actor


async def assert_create_fully_rolled_back(
    app: FastAPI,
    *,
    event_id: UUID,
    idempotency_key: str,
) -> None:
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        assert event is not None
        reservation_count = await session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(Reservation.event_id == event_id)
        )
        audit_count = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.resource_type == "reservation",
                AuditLog.action == "reservation.created",
                AuditLog.changes["after"]["eventId"].as_string() == str(event_id),
            )
        )
        key_count = await session.scalar(
            select(func.count())
            .select_from(IdempotencyRecord)
            .where(IdempotencyRecord.key == idempotency_key)
        )
        reserved_count = event.reserved_count
    assert reserved_count == 0
    assert reservation_count == 0
    assert audit_count == 0
    assert key_count == 0


async def test_audit_commit_failure_rolls_back_reservation_counter_and_key(
    auth_client: AsyncClient,
    auth_app: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event_body = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event_body["id"]))
    key = f"audit-failure-{uuid7()}"
    original_commit = AsyncSession.commit

    async def fail_when_reservation_audit_is_pending(session: AsyncSession) -> None:
        if any(
            isinstance(instance, AuditLog) and instance.action == "reservation.created"
            for instance in session.new
        ):
            raise RuntimeError("injected reservation audit persistence failure")
        await original_commit(session)

    monkeypatch.setattr(AsyncSession, "commit", fail_when_reservation_audit_is_pending)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as failure_client:
        response = await failure_client.post(
            f"/api/v1/events/{event_id}/reservations",
            headers=attendee_headers | {"Idempotency-Key": key},
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    await assert_create_fully_rolled_back(
        app,
        event_id=event_id,
        idempotency_key=key,
    )


async def test_idempotency_finalize_failure_rolls_back_domain_and_audit(
    auth_client: AsyncClient,
    auth_app: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event_body = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event_body["id"]))
    key = f"finalize-failure-{uuid7()}"

    def fail_finalize(
        record: IdempotencyRecord,
        *,
        status_code: int,
        response_body: dict[str, Any],
        original_request_id: UUID,
    ) -> None:
        del record, status_code, response_body, original_request_id
        raise RuntimeError("injected idempotency finalize failure")

    assert reservation_service.complete_idempotency_record is complete_idempotency_record  # type: ignore[attr-defined]
    monkeypatch.setattr(
        reservation_service,
        "complete_idempotency_record",
        fail_finalize,
    )
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as failure_client:
        response = await failure_client.post(
            f"/api/v1/events/{event_id}/reservations",
            headers=attendee_headers | {"Idempotency-Key": key},
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    await assert_create_fully_rolled_back(
        app,
        event_id=event_id,
        idempotency_key=key,
    )
