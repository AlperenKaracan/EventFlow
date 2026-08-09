from __future__ import annotations

import asyncio
from typing import cast
from uuid import UUID, uuid7

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import func, select

from app.audit.models import AuditLog
from app.auth.security import DUMMY_PASSWORD_HASH, create_access_token
from app.events.models import Event
from app.idempotency.keys import reservation_create_request_hash
from app.idempotency.models import IdempotencyRecord, IdempotencyState
from app.idempotency.repository import claim_idempotency_key
from app.reservations.models import Reservation, ReservationStatus
from app.seed import IDENTITY
from app.shared.config import Settings
from app.users.models import User, UserRole, UserStatus


async def register_actor(
    client: AsyncClient, *, role: str
) -> tuple[dict[str, object], dict[str, str]]:
    email = f"reservation-create-{uuid7()}@example.com"
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "fullName": "Reservation Actor",
            "password": "integration-password",
            "role": role,
        },
    )
    assert registration.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "integration-password"},
    )
    assert login.status_code == 200
    return registration.json(), {"Authorization": f"Bearer {login.json()['accessToken']}"}


async def create_event(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    capacity: int = 5,
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "categoryId": str(IDENTITY.technology_category_id),
            "title": f"Reservation Event {uuid7()}",
            "description": "Reservation integrity test",
            "location": "İstanbul",
            "startsAt": "2037-05-12T19:00:00+03:00",
            "timezone": "Europe/Istanbul",
            "capacity": capacity,
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


async def test_create_replay_and_reactivate_preserve_semantic_response_and_invariant(
    auth_client: AsyncClient,
    auth_app: object,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event["id"]))
    attendee_id = UUID(cast(str, attendee["id"]))
    owner_request_id = uuid7()
    replay_request_id = uuid7()
    key = f"create-{uuid7()}"

    owner = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=attendee_headers
        | {"Idempotency-Key": key, "X-Request-ID": str(owner_request_id)},
    )
    replay = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=attendee_headers
        | {"Idempotency-Key": key, "X-Request-ID": str(replay_request_id)},
    )

    assert owner.status_code == replay.status_code == 201
    assert owner.json() == replay.json()
    assert "Idempotent-Replayed" not in owner.headers
    assert replay.headers["Idempotent-Replayed"] == "true"
    assert replay.headers["Idempotency-Original-Request-ID"] == str(owner_request_id)
    assert replay.headers["X-Request-ID"] == str(replay_request_id)
    reservation_id = UUID(owner.json()["id"])

    cancellation = await auth_client.delete(
        f"/api/v1/reservations/{reservation_id}",
        headers=attendee_headers,
    )
    assert cancellation.status_code == 204
    reactivated = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=attendee_headers | {"Idempotency-Key": f"reactivate-{uuid7()}"},
    )
    assert reactivated.status_code == 201
    assert reactivated.json()["id"] == str(reservation_id)
    assert reactivated.json()["status"] == "ACTIVE"
    assert reactivated.json()["cancelledAt"] is None

    async with app.state.session_factory() as session:
        persisted_event = await session.get(Event, event_id)
        assert persisted_event is not None
        active_count = await session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(
                Reservation.event_id == event_id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
        )
        actions = list(
            await session.scalars(
                select(AuditLog.action)
                .where(
                    AuditLog.resource_type == "reservation",
                    AuditLog.resource_id == reservation_id,
                )
                .order_by(AuditLog.created_at)
            )
        )
        stored = await session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == attendee_id,
                IdempotencyRecord.key == key,
            )
        )
    assert persisted_event.reserved_count == active_count == 1
    assert actions == [
        "reservation.created",
        "reservation.cancelled_by_attendee",
        "reservation.reactivated",
    ]
    assert stored is not None
    assert stored.state is IdempotencyState.COMPLETED
    assert stored.original_request_id == owner_request_id
    assert stored.response_body is not None
    assert "requestId" not in str(stored.response_body)


async def test_same_key_parallel_requests_replay_one_domain_write(
    auth_client: AsyncClient,
    auth_app: object,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event["id"]))
    attendee_id = UUID(cast(str, attendee["id"]))
    key = f"parallel-same-{uuid7()}"

    responses = await asyncio.gather(
        *[
            auth_client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=attendee_headers
                | {"Idempotency-Key": key, "X-Request-ID": str(uuid7())},
            )
            for _ in range(5)
        ]
    )

    assert [response.status_code for response in responses] == [201] * 5
    assert all(response.json() == responses[0].json() for response in responses)
    assert sum(response.headers.get("Idempotent-Replayed") == "true" for response in responses) == 4
    reservation_id = UUID(responses[0].json()["id"])
    async with app.state.session_factory() as session:
        reservation_count = await session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(
                Reservation.event_id == event_id,
                Reservation.attendee_id == attendee_id,
            )
        )
        audit_count = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.resource_id == reservation_id,
                AuditLog.action == "reservation.created",
            )
        )
    assert reservation_count == audit_count == 1


async def test_different_keys_parallel_requests_return_one_created_and_conflicts(
    auth_client: AsyncClient,
    auth_app: object,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event["id"]))

    responses = await asyncio.gather(
        *[
            auth_client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=attendee_headers | {"Idempotency-Key": f"different-{uuid7()}"},
            )
            for _ in range(5)
        ]
    )

    assert sorted(response.status_code for response in responses) == [201, 409, 409, 409, 409]
    assert {
        response.json()["error"]["code"]
        for response in responses
        if response.status_code == 409
    } == {"ALREADY_RESERVED"}
    async with app.state.session_factory() as session:
        persisted_event = await session.get(Event, event_id)
        assert persisted_event is not None
        active_count = await session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(
                Reservation.event_id == event_id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
        )
    assert persisted_event.reserved_count == active_count == 1


async def test_key_reuse_rate_limit_and_role_guards(
    auth_client: AsyncClient,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    first_event = await create_event(auth_client, organizer_headers)
    second_event = await create_event(auth_client, organizer_headers)
    first_event_id = UUID(cast(str, first_event["id"]))
    second_event_id = UUID(cast(str, second_event["id"]))
    key = f"reuse-{uuid7()}"

    created = await auth_client.post(
        f"/api/v1/events/{first_event_id}/reservations",
        headers=attendee_headers | {"Idempotency-Key": key},
    )
    reused = await auth_client.post(
        f"/api/v1/events/{second_event_id}/reservations",
        headers=attendee_headers | {"Idempotency-Key": key},
    )
    organizer_denied = await auth_client.post(
        f"/api/v1/events/{second_event_id}/reservations",
        headers=organizer_headers | {"Idempotency-Key": f"organizer-{uuid7()}"},
    )
    missing_key = await auth_client.post(
        f"/api/v1/events/{second_event_id}/reservations",
        headers=attendee_headers,
    )

    assert created.status_code == 201
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert organizer_denied.status_code == 403
    assert missing_key.status_code == 422

    limited_responses = [
        await auth_client.post(
            f"/api/v1/events/{second_event_id}/reservations",
            headers=attendee_headers | {"Idempotency-Key": f"limit-{uuid7()}"},
        )
        for _ in range(9)
    ]
    assert limited_responses[-1].status_code == 429
    assert limited_responses[-1].json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert int(limited_responses[-1].headers["Retry-After"]) >= 1


async def test_deterministic_full_error_replay_injects_current_request_id(
    auth_client: AsyncClient,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _first_attendee, first_headers = await register_actor(auth_client, role="attendee")
    _second_attendee, second_headers = await register_actor(auth_client, role="attendee")
    event = await create_event(auth_client, organizer_headers, capacity=1)
    event_id = UUID(cast(str, event["id"]))
    filled = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=first_headers | {"Idempotency-Key": f"fill-{uuid7()}"},
    )
    assert filled.status_code == 201
    key = f"full-{uuid7()}"
    owner_request_id = uuid7()
    replay_request_id = uuid7()

    owner = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=second_headers
        | {"Idempotency-Key": key, "X-Request-ID": str(owner_request_id)},
    )
    replay = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=second_headers
        | {"Idempotency-Key": key, "X-Request-ID": str(replay_request_id)},
    )

    assert owner.status_code == replay.status_code == 409
    assert owner.json()["error"] | {"requestId": None} == replay.json()["error"] | {
        "requestId": None
    }
    assert owner.json()["error"]["code"] == "EVENT_FULL"
    assert owner.json()["error"]["requestId"] == str(owner_request_id)
    assert replay.json()["error"]["requestId"] == str(replay_request_id)
    assert replay.headers["X-Request-ID"] == str(replay_request_id)
    assert replay.headers["Idempotency-Original-Request-ID"] == str(owner_request_id)


async def test_visible_processing_record_returns_retryable_conflict(
    auth_client: AsyncClient,
    auth_app: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event["id"]))
    attendee_id = UUID(cast(str, attendee["id"]))
    key = f"processing-{uuid7()}"
    async with app.state.session_factory() as session:
        record = await claim_idempotency_key(
            session=session,
            user_id=attendee_id,
            operation="reservation.create",
            key=key,
            request_hash=reservation_create_request_hash(event_id=event_id, body={}),
        )
        assert record is not None
        await session.commit()

    response = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=attendee_headers | {"Idempotency-Key": key},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert response.headers["Retry-After"] == "1"
    assert any(
        getattr(record, "event", None) == "idempotency.processing_visible"
        for record in caplog.records
    )


async def test_capacity_one_allows_exactly_one_of_two_hundred_parallel_attendees(
    auth_client: AsyncClient,
    auth_app: object,
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    event = await create_event(auth_client, organizer_headers, capacity=1)
    app = cast(FastAPI, auth_app)
    settings = cast(Settings, app.state.settings)
    event_id = UUID(cast(str, event["id"]))
    attendee_ids = [uuid7() for _ in range(200)]
    async with app.state.session_factory() as session:
        session.add_all(
            [
                User(
                    id=attendee_id,
                    email=f"capacity-{attendee_id}@example.com",
                    full_name=f"Capacity Attendee {index:03d}",
                    password_hash=DUMMY_PASSWORD_HASH,
                    role=UserRole.ATTENDEE,
                    status=UserStatus.ACTIVE,
                )
                for index, attendee_id in enumerate(attendee_ids)
            ]
        )
        await session.commit()
    headers = [
        {
            "Authorization": "Bearer "
            + create_access_token(
                user_id=attendee_id,
                role=UserRole.ATTENDEE,
                settings=settings,
            ).raw,
            "Idempotency-Key": f"capacity-{uuid7()}",
        }
        for attendee_id in attendee_ids
    ]

    responses = await asyncio.gather(
        *[
            auth_client.post(
                f"/api/v1/events/{event_id}/reservations",
                headers=request_headers,
            )
            for request_headers in headers
        ]
    )

    assert sum(response.status_code == 201 for response in responses) == 1
    assert sum(response.status_code == 409 for response in responses) == 199
    assert {
        response.json()["error"]["code"]
        for response in responses
        if response.status_code == 409
    } == {"EVENT_FULL"}
    assert all(
        response.json()["error"]["requestId"] == response.headers["X-Request-ID"]
        for response in responses
        if response.status_code == 409
    )
    async with app.state.session_factory() as session:
        persisted_event = await session.get(Event, event_id)
        assert persisted_event is not None
        active_count = await session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(
                Reservation.event_id == event_id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
        )
        audit_count = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action == "reservation.created",
                AuditLog.resource_id.in_(
                    select(Reservation.id).where(Reservation.event_id == event_id)
                ),
            )
        )
        completed_keys = await session.scalar(
            select(func.count())
            .select_from(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id.in_(attendee_ids),
                IdempotencyRecord.state == IdempotencyState.COMPLETED,
            )
        )
    assert persisted_event.reserved_count == active_count == 1
    assert audit_count == 1
    assert completed_keys == 200
