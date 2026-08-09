from __future__ import annotations

from typing import cast
from uuid import uuid7

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text

from app.seed import IDENTITY


async def login_user(client: AsyncClient, *, email: str, password: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


async def register_user(client: AsyncClient, *, role: str) -> dict[str, str]:
    email = f"reservation-read-{uuid7()}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "fullName": "Reservation Reader",
            "password": "integration-password",
            "role": role,
        },
    )
    assert response.status_code == 201
    return await login_user(client, email=email, password="integration-password")


async def test_attendee_history_is_stable_and_includes_cancelled_reservations(
    auth_client: AsyncClient,
) -> None:
    headers = await login_user(
        auth_client,
        email="attendee@eventflow.local",
        password="AttendeeDemo123!",
    )

    first = await auth_client.get(
        "/api/v1/me/reservations",
        headers=headers,
        params={"limit": 1},
    )
    assert first.status_code == 200
    assert first.json()["hasMore"] is True
    assert first.json()["nextCursor"]
    second = await auth_client.get(
        "/api/v1/me/reservations",
        headers=headers,
        params={"limit": 1, "cursor": first.json()["nextCursor"]},
    )

    assert second.status_code == 200
    items = first.json()["items"] + second.json()["items"]
    assert len(items) == 2
    assert {item["status"] for item in items} == {"ACTIVE", "CANCELLED_BY_EVENT"}
    assert {item["event"]["id"] for item in items} == {
        str(IDENTITY.full_event_id),
        str(IDENTITY.cancelled_event_id),
    }
    assert second.json()["nextCursor"] is None


async def test_history_rejects_invalid_or_other_attendee_cursor_and_organizer_role(
    auth_client: AsyncClient,
) -> None:
    attendee_headers = await login_user(
        auth_client,
        email="attendee@eventflow.local",
        password="AttendeeDemo123!",
    )
    first = await auth_client.get(
        "/api/v1/me/reservations",
        headers=attendee_headers,
        params={"limit": 1},
    )
    other_attendee_headers = await register_user(auth_client, role="attendee")
    copied = await auth_client.get(
        "/api/v1/me/reservations",
        headers=other_attendee_headers,
        params={"cursor": first.json()["nextCursor"]},
    )
    invalid = await auth_client.get(
        "/api/v1/me/reservations",
        headers=attendee_headers,
        params={"cursor": "attacker-controlled"},
    )
    organizer_headers = await login_user(
        auth_client,
        email="organizer@eventflow.local",
        password="OrganizerDemo123!",
    )
    organizer = await auth_client.get(
        "/api/v1/me/reservations",
        headers=organizer_headers,
    )

    assert copied.status_code == invalid.status_code == 400
    assert copied.json()["error"]["code"] == "INVALID_CURSOR"
    assert invalid.json()["error"]["code"] == "INVALID_CURSOR"
    assert organizer.status_code == 403
    assert organizer.json()["error"]["code"] == "FORBIDDEN"


async def test_event_attendee_list_is_active_minimal_and_owner_scoped(
    auth_client: AsyncClient,
) -> None:
    owner_headers = await login_user(
        auth_client,
        email="organizer@eventflow.local",
        password="OrganizerDemo123!",
    )
    active = await auth_client.get(
        f"/api/v1/events/{IDENTITY.full_event_id}/attendees",
        headers=owner_headers,
    )
    cancelled = await auth_client.get(
        f"/api/v1/events/{IDENTITY.cancelled_event_id}/attendees",
        headers=owner_headers,
    )

    assert active.status_code == 200
    assert len(active.json()["items"]) == 1
    attendee = active.json()["items"][0]
    assert set(attendee) == {
        "reservationId",
        "attendeeId",
        "fullName",
        "email",
        "reservedAt",
    }
    assert attendee["attendeeId"] == str(IDENTITY.attendee_id)
    assert cancelled.status_code == 200
    assert cancelled.json()["items"] == []


async def test_event_attendee_list_hides_event_from_other_roles_and_owners(
    auth_client: AsyncClient,
) -> None:
    attendee_headers = await login_user(
        auth_client,
        email="attendee@eventflow.local",
        password="AttendeeDemo123!",
    )
    other_owner_headers = await register_user(auth_client, role="organizer")

    attendee = await auth_client.get(
        f"/api/v1/events/{IDENTITY.full_event_id}/attendees",
        headers=attendee_headers,
    )
    other_owner = await auth_client.get(
        f"/api/v1/events/{IDENTITY.full_event_id}/attendees",
        headers=other_owner_headers,
    )
    unknown = await auth_client.get(
        f"/api/v1/events/{uuid7()}/attendees",
        headers=other_owner_headers,
    )

    assert attendee.status_code == other_owner.status_code == unknown.status_code == 404
    assert attendee.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert other_owner.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert unknown.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


async def test_reservation_read_openapi_contract(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    history = paths["/api/v1/me/reservations"]["get"]
    attendees = paths["/api/v1/events/{event_id}/attendees"]["get"]
    assert history["operationId"] == "listMyReservations"
    assert attendees["operationId"] == "listEventAttendees"
    assert (
        history["responses"]["403"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorEnvelope"
    )
    assert (
        attendees["responses"]["404"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorEnvelope"
    )


async def test_reservation_list_queries_use_composite_cursor_indexes(
    auth_app: object,
) -> None:
    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        await session.execute(text("SET LOCAL enable_seqscan = off"))
        attendee_plan = (
            await session.execute(
                text(
                    """
                    EXPLAIN (FORMAT TEXT, COSTS OFF)
                    SELECT reservations.id
                    FROM reservations
                    WHERE reservations.attendee_id = :attendee_id
                    ORDER BY reservations.created_at DESC, reservations.id DESC
                    LIMIT 20
                    """
                ),
                {"attendee_id": IDENTITY.attendee_id},
            )
        ).scalars().all()
        event_plan = (
            await session.execute(
                text(
                    """
                    EXPLAIN (FORMAT TEXT, COSTS OFF)
                    SELECT reservations.id
                    FROM reservations
                    WHERE reservations.event_id = :event_id
                      AND reservations.status = 'ACTIVE'
                    ORDER BY reservations.created_at ASC, reservations.id ASC
                    LIMIT 20
                    """
                ),
                {"event_id": IDENTITY.istanbul_event_id},
            )
        ).scalars().all()

    assert "ix_reservations_attendee_id_created_at_id" in "\n".join(attendee_plan)
    assert "ix_reservations_event_id_status_created_at" in "\n".join(event_plan)
