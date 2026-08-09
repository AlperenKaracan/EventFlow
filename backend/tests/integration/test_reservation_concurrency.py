from __future__ import annotations

import asyncio
from typing import cast
from uuid import UUID, uuid7

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.events.service as event_service
import app.reservations.service as reservation_service
from app.events.models import Event, EventStatus
from app.reservations.models import Reservation, ReservationStatus
from tests.integration.test_reservation_creation import create_event, register_actor


async def reserve(
    client: AsyncClient,
    *,
    event_id: UUID,
    headers: dict[str, str],
) -> Response:
    return await client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=headers | {"Idempotency-Key": f"race-{uuid7()}"},
    )


async def assert_event_invariant(
    app: FastAPI,
    *,
    event_id: UUID,
    expected_status: EventStatus,
    expected_active: int,
) -> None:
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        assert event is not None
        active_count = await session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(
                Reservation.event_id == event_id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
        )
        reserved_count = event.reserved_count
        event_status = event.status
    assert event_status is expected_status
    assert reserved_count == active_count == expected_active


@pytest.mark.parametrize("first_writer", ["create", "cancel"])
async def test_create_and_attendee_cancel_follow_event_first_order_without_deadlock(
    auth_client: AsyncClient,
    auth_app: object,
    monkeypatch: pytest.MonkeyPatch,
    first_writer: str,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event["id"]))
    initial = await reserve(auth_client, event_id=event_id, headers=attendee_headers)
    assert initial.status_code == 201
    reservation_id = UUID(initial.json()["id"])
    if first_writer == "create":
        cancelled = await auth_client.delete(
            f"/api/v1/reservations/{reservation_id}",
            headers=attendee_headers,
        )
        assert cancelled.status_code == 204

    original = reservation_service.get_event_for_update  # type: ignore[attr-defined]
    first_has_event_lock = asyncio.Event()
    release_first = asyncio.Event()
    calls = 0

    async def pause_first_after_event_lock(
        *, session: AsyncSession, event_id: UUID
    ) -> Event | None:
        nonlocal calls
        locked_event = await original(session=session, event_id=event_id)
        calls += 1
        if calls == 1:
            first_has_event_lock.set()
            await release_first.wait()
        return locked_event

    monkeypatch.setattr(
        reservation_service,
        "get_event_for_update",
        pause_first_after_event_lock,
    )
    if first_writer == "create":
        first_task = asyncio.create_task(
            reserve(auth_client, event_id=event_id, headers=attendee_headers)
        )
        await asyncio.wait_for(first_has_event_lock.wait(), timeout=2)
        second_task = asyncio.create_task(
            auth_client.delete(
                f"/api/v1/reservations/{reservation_id}",
                headers=attendee_headers,
            )
        )
        expected_active = 0
    else:
        first_task = asyncio.create_task(
            auth_client.delete(
                f"/api/v1/reservations/{reservation_id}",
                headers=attendee_headers,
            )
        )
        await asyncio.wait_for(first_has_event_lock.wait(), timeout=2)
        second_task = asyncio.create_task(
            reserve(auth_client, event_id=event_id, headers=attendee_headers)
        )
        expected_active = 1

    await asyncio.sleep(0.05)
    assert not second_task.done()
    release_first.set()
    first_response, second_response = await asyncio.wait_for(
        asyncio.gather(first_task, second_task),
        timeout=5,
    )
    assert {first_response.status_code, second_response.status_code} == {201, 204}
    await assert_event_invariant(
        app,
        event_id=event_id,
        expected_status=EventStatus.ACTIVE,
        expected_active=expected_active,
    )


@pytest.mark.parametrize("first_writer", ["booking", "capacity_update"])
async def test_booking_and_capacity_update_serialize_without_oversell(
    auth_client: AsyncClient,
    auth_app: object,
    monkeypatch: pytest.MonkeyPatch,
    first_writer: str,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _first_attendee, first_headers = await register_actor(auth_client, role="attendee")
    _second_attendee, second_headers = await register_actor(auth_client, role="attendee")
    event_body = await create_event(auth_client, organizer_headers, capacity=2)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event_body["id"]))
    first_reservation = await reserve(
        auth_client,
        event_id=event_id,
        headers=first_headers,
    )
    assert first_reservation.status_code == 201
    first_has_event_lock = asyncio.Event()
    release_first = asyncio.Event()

    if first_writer == "booking":
        original = reservation_service.get_event_for_update  # type: ignore[attr-defined]

        async def pause_booking(*, session: AsyncSession, event_id: UUID) -> Event | None:
            locked_event = await original(session=session, event_id=event_id)
            first_has_event_lock.set()
            await release_first.wait()
            return locked_event

        monkeypatch.setattr(reservation_service, "get_event_for_update", pause_booking)
        first_task = asyncio.create_task(
            reserve(auth_client, event_id=event_id, headers=second_headers)
        )
        await asyncio.wait_for(first_has_event_lock.wait(), timeout=2)
        second_task = asyncio.create_task(
            auth_client.patch(
                f"/api/v1/events/{event_id}",
                headers=organizer_headers,
                json={"expectedVersion": 1, "capacity": 1},
            )
        )
        expected_capacity = 2
        expected_active = 2
        expected_codes = {201, 409}
    else:
        original_update = event_service.get_owned_event_for_update  # type: ignore[attr-defined]

        async def pause_update(
            *,
            session: AsyncSession,
            event_id: UUID,
            organizer_id: UUID,
            expected_version: int,
        ) -> Event | None:
            locked_event = await original_update(
                session=session,
                event_id=event_id,
                organizer_id=organizer_id,
                expected_version=expected_version,
            )
            first_has_event_lock.set()
            await release_first.wait()
            return locked_event

        monkeypatch.setattr(event_service, "get_owned_event_for_update", pause_update)
        first_task = asyncio.create_task(
            auth_client.patch(
                f"/api/v1/events/{event_id}",
                headers=organizer_headers,
                json={"expectedVersion": 1, "capacity": 1},
            )
        )
        await asyncio.wait_for(first_has_event_lock.wait(), timeout=2)
        second_task = asyncio.create_task(
            reserve(auth_client, event_id=event_id, headers=second_headers)
        )
        expected_capacity = 1
        expected_active = 1
        expected_codes = {200, 409}

    await asyncio.sleep(0.05)
    assert not second_task.done()
    release_first.set()
    first_response, second_response = await asyncio.wait_for(
        asyncio.gather(first_task, second_task),
        timeout=5,
    )
    assert {first_response.status_code, second_response.status_code} == expected_codes
    conflict = first_response if first_response.status_code == 409 else second_response
    assert conflict.json()["error"]["code"] in {
        "CAPACITY_BELOW_RESERVATIONS",
        "EVENT_FULL",
    }
    async with app.state.session_factory() as session:
        persisted_event = await session.get(Event, event_id)
        assert persisted_event is not None
        assert persisted_event.capacity == expected_capacity
    await assert_event_invariant(
        app,
        event_id=event_id,
        expected_status=EventStatus.ACTIVE,
        expected_active=expected_active,
    )


@pytest.mark.parametrize("first_writer", ["booking", "event_cancel"])
async def test_booking_and_event_cancel_serialize_without_orphaned_seats(
    auth_client: AsyncClient,
    auth_app: object,
    monkeypatch: pytest.MonkeyPatch,
    first_writer: str,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event_body = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event_body["id"]))
    first_has_event_lock = asyncio.Event()
    release_first = asyncio.Event()

    if first_writer == "booking":
        original = reservation_service.get_event_for_update  # type: ignore[attr-defined]

        async def pause_booking(*, session: AsyncSession, event_id: UUID) -> Event | None:
            locked_event = await original(session=session, event_id=event_id)
            first_has_event_lock.set()
            await release_first.wait()
            return locked_event

        monkeypatch.setattr(reservation_service, "get_event_for_update", pause_booking)
        first_task = asyncio.create_task(
            reserve(auth_client, event_id=event_id, headers=attendee_headers)
        )
        await asyncio.wait_for(first_has_event_lock.wait(), timeout=2)
        second_task = asyncio.create_task(
            auth_client.delete(
                f"/api/v1/events/{event_id}",
                params={"expectedVersion": 1},
                headers=organizer_headers,
            )
        )
        expected_codes = {201, 204}
    else:
        original_cancel = event_service.get_owned_event_for_update  # type: ignore[attr-defined]

        async def pause_cancel(
            *,
            session: AsyncSession,
            event_id: UUID,
            organizer_id: UUID,
            expected_version: int,
        ) -> Event | None:
            locked_event = await original_cancel(
                session=session,
                event_id=event_id,
                organizer_id=organizer_id,
                expected_version=expected_version,
            )
            first_has_event_lock.set()
            await release_first.wait()
            return locked_event

        monkeypatch.setattr(event_service, "get_owned_event_for_update", pause_cancel)
        first_task = asyncio.create_task(
            auth_client.delete(
                f"/api/v1/events/{event_id}",
                params={"expectedVersion": 1},
                headers=organizer_headers,
            )
        )
        await asyncio.wait_for(first_has_event_lock.wait(), timeout=2)
        second_task = asyncio.create_task(
            reserve(auth_client, event_id=event_id, headers=attendee_headers)
        )
        expected_codes = {204, 409}

    await asyncio.sleep(0.05)
    assert not second_task.done()
    release_first.set()
    first_response, second_response = await asyncio.wait_for(
        asyncio.gather(first_task, second_task),
        timeout=5,
    )
    assert {first_response.status_code, second_response.status_code} == expected_codes
    if first_writer == "event_cancel":
        conflict = first_response if first_response.status_code == 409 else second_response
        assert conflict.json()["error"]["code"] == "EVENT_NOT_ACTIVE"
    await assert_event_invariant(
        app,
        event_id=event_id,
        expected_status=EventStatus.CANCELLED,
        expected_active=0,
    )
