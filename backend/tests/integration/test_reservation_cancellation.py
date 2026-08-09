from __future__ import annotations

from typing import cast
from uuid import UUID, uuid7

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import func, select

from app.audit.models import AuditLog
from app.events.models import Event, EventStatus
from app.reservations.models import Reservation, ReservationStatus
from app.seed import IDENTITY


async def register_actor(
    client: AsyncClient, *, role: str
) -> tuple[dict[str, object], dict[str, str]]:
    email = f"reservation-cancel-{uuid7()}@example.com"
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "fullName": "Cancellation Actor",
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


async def create_event(client: AsyncClient, headers: dict[str, str]) -> dict[str, object]:
    response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "categoryId": str(IDENTITY.technology_category_id),
            "title": f"Cancellation Event {uuid7()}",
            "description": "Event-first cancellation test",
            "location": "İstanbul",
            "startsAt": "2037-05-12T19:00:00+03:00",
            "timezone": "Europe/Istanbul",
            "capacity": 5,
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


async def add_active_reservation(app: FastAPI, *, event_id: UUID, attendee_id: UUID) -> UUID:
    reservation_id = uuid7()
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        assert event is not None
        event.reserved_count += 1
        session.add(
            Reservation(
                id=reservation_id,
                event_id=event_id,
                attendee_id=attendee_id,
                status=ReservationStatus.ACTIVE,
            )
        )
        await session.commit()
    return reservation_id


async def test_attendee_cancellation_is_idempotent_and_preserves_counter_audit(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    event_body = await create_event(auth_client, organizer_headers)
    app = cast(FastAPI, auth_app)
    event_id = UUID(cast(str, event_body["id"]))
    attendee_id = UUID(cast(str, attendee["id"]))
    reservation_id = await add_active_reservation(
        app,
        event_id=event_id,
        attendee_id=attendee_id,
    )

    first = await auth_client.delete(
        f"/api/v1/reservations/{reservation_id}", headers=attendee_headers
    )
    second = await auth_client.delete(
        f"/api/v1/reservations/{reservation_id}", headers=attendee_headers
    )

    assert first.status_code == second.status_code == 204
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        reservation = await session.get(Reservation, reservation_id)
        audit_count = await session.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.resource_id == reservation_id,
                AuditLog.action == "reservation.cancelled_by_attendee",
            )
        )
    assert event is not None and event.reserved_count == 0
    assert reservation is not None
    assert reservation.status is ReservationStatus.CANCELLED_BY_ATTENDEE
    assert reservation.cancelled_at is not None
    assert audit_count == 1


async def test_cancellation_hides_reservation_and_rejects_started_event(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _owner, owner_headers = await register_actor(auth_client, role="organizer")
    attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    _other, other_headers = await register_actor(auth_client, role="attendee")
    app = cast(FastAPI, auth_app)
    attendee_id = UUID(cast(str, attendee["id"]))
    reservation_id = await add_active_reservation(
        app,
        event_id=IDENTITY.past_event_id,
        attendee_id=attendee_id,
    )

    other = await auth_client.delete(
        f"/api/v1/reservations/{reservation_id}", headers=other_headers
    )
    organizer = await auth_client.delete(
        f"/api/v1/reservations/{reservation_id}", headers=owner_headers
    )
    unknown = await auth_client.delete(f"/api/v1/reservations/{uuid7()}", headers=attendee_headers)
    started = await auth_client.delete(
        f"/api/v1/reservations/{reservation_id}", headers=attendee_headers
    )

    assert other.status_code == organizer.status_code == unknown.status_code == 404
    assert other.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert organizer.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert started.status_code == 409
    assert started.json()["error"]["code"] == "EVENT_STARTED"
    async with app.state.session_factory() as session:
        event = await session.get(Event, IDENTITY.past_event_id)
        reservation = await session.get(Reservation, reservation_id)
    assert event is not None and event.reserved_count == 1
    assert reservation is not None and reservation.status is ReservationStatus.ACTIVE


async def test_event_cancellation_bulk_transitions_reservations_and_audits(
    auth_client: AsyncClient, auth_app: object
) -> None:
    organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    first_attendee, _first_headers = await register_actor(auth_client, role="attendee")
    second_attendee, _second_headers = await register_actor(auth_client, role="attendee")
    event_body = await create_event(auth_client, organizer_headers)
    event_id = UUID(cast(str, event_body["id"]))
    app = cast(FastAPI, auth_app)
    reservation_ids = [
        await add_active_reservation(
            app,
            event_id=event_id,
            attendee_id=UUID(cast(str, attendee["id"])),
        )
        for attendee in (first_attendee, second_attendee)
    ]

    response = await auth_client.delete(
        f"/api/v1/events/{event_id}",
        headers=organizer_headers,
        params={"expectedVersion": 1},
    )

    assert response.status_code == 204
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        reservations = [
            await session.get(Reservation, reservation_id) for reservation_id in reservation_ids
        ]
        reservation_audits = (
            await session.scalars(
                select(AuditLog).where(
                    AuditLog.resource_id.in_(reservation_ids),
                    AuditLog.action == "reservation.cancelled_by_event",
                )
            )
        ).all()
        event_audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.resource_id == event_id,
                AuditLog.action == "event.cancelled",
            )
        )
    assert event is not None
    assert event.status is EventStatus.CANCELLED
    assert event.reserved_count == 0
    assert all(
        reservation is not None
        and reservation.status is ReservationStatus.CANCELLED_BY_EVENT
        and reservation.cancelled_at is not None
        for reservation in reservations
    )
    assert len(reservation_audits) == 2
    assert all(audit.actor_id == UUID(cast(str, organizer["id"])) for audit in reservation_audits)
    assert event_audit is not None


async def test_reservation_cancel_openapi_contract(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/v1/reservations/{reservation_id}"]["delete"]
    assert operation["operationId"] == "cancelReservation"
    assert (
        operation["responses"]["404"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorEnvelope"
    )
