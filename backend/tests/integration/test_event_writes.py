from __future__ import annotations

import asyncio
from typing import cast
from uuid import uuid7

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.audit.models import AuditLog
from app.events.models import Event
from app.seed import IDENTITY


async def register_writer(
    client: AsyncClient, *, role: str = "organizer"
) -> tuple[dict[str, str], dict[str, str]]:
    email = f"event-writer-{uuid7()}@example.com"
    registration = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "fullName": "Event Writer",
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


def event_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "categoryId": str(IDENTITY.technology_category_id),
        "title": "  Integration Event  ",
        "description": "Transaction-backed event",
        "location": "  İstanbul  ",
        "startsAt": "2036-05-12T19:00:00+03:00",
        "timezone": "Europe/Istanbul",
        "capacity": 5,
    }
    return payload | overrides


async def create_writer_event(
    client: AsyncClient, headers: dict[str, str], **overrides: object
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/events",
        json=event_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


async def install_event_audit_rejection(app: FastAPI) -> None:
    async with app.state.db_engine.begin() as connection:
        await connection.execute(
            text(
                """
                CREATE FUNCTION reject_test_event_audit_insert()
                RETURNS trigger
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    RAISE EXCEPTION 'forced event audit failure';
                END;
                $$
                """
            )
        )
        await connection.execute(
            text(
                """
                CREATE TRIGGER reject_test_event_audit_insert
                BEFORE INSERT ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION reject_test_event_audit_insert()
                """
            )
        )


async def remove_event_audit_rejection(app: FastAPI) -> None:
    async with app.state.db_engine.begin() as connection:
        await connection.execute(
            text("DROP TRIGGER IF EXISTS reject_test_event_audit_insert ON audit_logs")
        )
        await connection.execute(text("DROP FUNCTION IF EXISTS reject_test_event_audit_insert()"))


async def test_create_event_uses_auth_identity_and_same_transaction_audit(
    auth_client: AsyncClient, auth_app: object
) -> None:
    user, headers = await register_writer(auth_client)

    response = await auth_client.post(
        "/api/v1/events",
        json=event_payload(),
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Integration Event"
    assert body["location"] == "İstanbul"
    assert body["version"] == 1
    assert body["status"] == "ACTIVE"
    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        event = await session.get(Event, body["id"])
        audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.resource_id == event.id,
                AuditLog.action == "event.created",
            )
        )
    assert event is not None
    assert str(event.organizer_id) == user["id"]
    assert audit is not None
    assert audit.actor_id == event.organizer_id
    assert audit.changes["after"]["version"] == 1


async def test_create_rejects_capability_category_time_and_offset_attacks(
    auth_client: AsyncClient,
) -> None:
    _attendee, attendee_headers = await register_writer(auth_client, role="attendee")
    attendee = await auth_client.post(
        "/api/v1/events", json=event_payload(), headers=attendee_headers
    )
    assert attendee.status_code == 403

    _organizer, organizer_headers = await register_writer(auth_client)
    invalid_category = await auth_client.post(
        "/api/v1/events",
        json=event_payload(categoryId=str(uuid7())),
        headers=organizer_headers,
    )
    past = await auth_client.post(
        "/api/v1/events",
        json=event_payload(startsAt="2020-05-12T19:00:00+03:00"),
        headers=organizer_headers,
    )
    offset_attack = await auth_client.post(
        "/api/v1/events",
        json=event_payload(startsAt="2036-05-12T19:00:00+02:00"),
        headers=organizer_headers,
    )

    assert invalid_category.status_code == 422
    assert invalid_category.json()["error"]["code"] == "INVALID_CATEGORY"
    assert past.status_code == 422
    assert past.json()["error"]["code"] == "EVENT_START_NOT_FUTURE"
    assert offset_attack.status_code == 422
    assert offset_attack.json()["error"]["code"] == "TIMEZONE_OFFSET_MISMATCH"


async def test_update_increments_version_audits_and_rejects_stale_edit(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _user, headers = await register_writer(auth_client)
    created = await create_writer_event(auth_client, headers)
    event_id = created["id"]

    updated = await auth_client.patch(
        f"/api/v1/events/{event_id}",
        json={
            "expectedVersion": 1,
            "title": "Updated Event",
            "capacity": 8,
        },
        headers=headers,
    )
    stale = await auth_client.patch(
        f"/api/v1/events/{event_id}",
        json={"expectedVersion": 1, "title": "Lost Update"},
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert updated.json()["title"] == "Updated Event"
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "EVENT_VERSION_CONFLICT"
    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        audits = (
            await session.scalars(
                select(AuditLog)
                .where(AuditLog.resource_id == event_id)
                .order_by(AuditLog.created_at)
            )
        ).all()
    assert [audit.action for audit in audits] == ["event.created", "event.updated"]
    assert audits[-1].changes["before"]["version"] == 1
    assert audits[-1].changes["after"]["version"] == 2


@pytest.mark.parametrize("attempt", range(5))
async def test_concurrent_updates_accept_exactly_one_expected_version(
    auth_client: AsyncClient, auth_app: object, attempt: int
) -> None:
    _user, headers = await register_writer(auth_client)
    created = await create_writer_event(auth_client, headers)
    event_id = created["id"]

    first, second = await asyncio.gather(
        auth_client.patch(
            f"/api/v1/events/{event_id}",
            json={"expectedVersion": 1, "title": f"Concurrent Alpha {attempt}"},
            headers=headers,
        ),
        auth_client.patch(
            f"/api/v1/events/{event_id}",
            json={"expectedVersion": 1, "title": f"Concurrent Beta {attempt}"},
            headers=headers,
        ),
    )

    assert sorted((first.status_code, second.status_code)) == [200, 409]
    conflict = first if first.status_code == 409 else second
    assert conflict.json()["error"]["code"] == "EVENT_VERSION_CONFLICT"

    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        update_audits = (
            await session.scalars(
                select(AuditLog).where(
                    AuditLog.resource_id == event_id,
                    AuditLog.action == "event.updated",
                )
            )
        ).all()
    assert event is not None
    assert event.version == 2
    assert event.title in {f"Concurrent Alpha {attempt}", f"Concurrent Beta {attempt}"}
    assert len(update_audits) == 1


@pytest.mark.parametrize("attempt", range(5))
async def test_concurrent_update_and_cancel_commit_exactly_one_mutation(
    auth_client: AsyncClient, auth_app: object, attempt: int
) -> None:
    _user, headers = await register_writer(auth_client)
    created = await create_writer_event(auth_client, headers)
    event_id = created["id"]

    updated, cancelled = await asyncio.gather(
        auth_client.patch(
            f"/api/v1/events/{event_id}",
            json={"expectedVersion": 1, "title": f"Race Update Winner {attempt}"},
            headers=headers,
        ),
        auth_client.delete(
            f"/api/v1/events/{event_id}",
            params={"expectedVersion": 1},
            headers=headers,
        ),
    )

    statuses = {updated.status_code, cancelled.status_code}
    assert 409 in statuses
    assert statuses & {200, 204}
    conflict = updated if updated.status_code == 409 else cancelled
    assert conflict.json()["error"]["code"] == "EVENT_VERSION_CONFLICT"

    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        mutation_audits = (
            await session.scalars(
                select(AuditLog).where(
                    AuditLog.resource_id == event_id,
                    AuditLog.action.in_(("event.updated", "event.cancelled")),
                )
            )
        ).all()
    assert event is not None
    assert event.version == 2
    assert len(mutation_audits) == 1
    assert mutation_audits[0].action == (
        "event.updated" if updated.status_code == 200 else "event.cancelled"
    )


async def test_update_hides_other_owner_and_blocks_capacity_and_started_event(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _owner, owner_headers = await register_writer(auth_client)
    created = await create_writer_event(auth_client, owner_headers)
    event_id = created["id"]
    _other, other_headers = await register_writer(auth_client)
    inaccessible = await auth_client.patch(
        f"/api/v1/events/{event_id}",
        json={"expectedVersion": 1, "title": "Attack"},
        headers=other_headers,
    )
    assert inaccessible.status_code == 404

    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        event = await session.get(Event, event_id)
        assert event is not None
        event.reserved_count = 2
        await session.commit()
    capacity = await auth_client.patch(
        f"/api/v1/events/{event_id}",
        json={"expectedVersion": 1, "capacity": 1},
        headers=owner_headers,
    )
    assert capacity.status_code == 409
    assert capacity.json()["error"]["code"] == "CAPACITY_BELOW_RESERVATIONS"

    seed_headers_response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "organizer@eventflow.local",
            "password": "OrganizerDemo123!",
        },
    )
    seed_headers = {"Authorization": f"Bearer {seed_headers_response.json()['accessToken']}"}
    started = await auth_client.patch(
        f"/api/v1/events/{IDENTITY.past_event_id}",
        json={"expectedVersion": 1, "title": "Too Late"},
        headers=seed_headers,
    )
    assert started.status_code == 409
    assert started.json()["error"]["code"] == "EVENT_STARTED"


async def test_cancel_is_soft_versioned_audited_and_publicly_hidden(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _user, headers = await register_writer(auth_client)
    created = await create_writer_event(auth_client, headers)
    event_id = created["id"]

    cancelled = await auth_client.delete(
        f"/api/v1/events/{event_id}",
        params={"expectedVersion": 1},
        headers=headers,
    )
    stale = await auth_client.delete(
        f"/api/v1/events/{event_id}",
        params={"expectedVersion": 1},
        headers=headers,
    )
    inactive = await auth_client.patch(
        f"/api/v1/events/{event_id}",
        json={"expectedVersion": 2, "title": "Cannot Revive"},
        headers=headers,
    )
    owner_detail = await auth_client.get(f"/api/v1/me/events/{event_id}", headers=headers)
    public_detail = await auth_client.get(f"/api/v1/events/{event_id}")

    assert cancelled.status_code == 204
    assert cancelled.content == b""
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "EVENT_VERSION_CONFLICT"
    assert inactive.status_code == 409
    assert inactive.json()["error"]["code"] == "EVENT_NOT_ACTIVE"
    assert owner_detail.status_code == 200
    assert owner_detail.json()["status"] == "CANCELLED"
    assert owner_detail.json()["version"] == 2
    assert owner_detail.json()["cancelledAt"] is not None
    assert public_detail.status_code == 404
    app = cast(FastAPI, auth_app)
    async with app.state.session_factory() as session:
        audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.resource_id == event_id,
                AuditLog.action == "event.cancelled",
            )
        )
    assert audit is not None
    assert audit.changes["after"]["status"] == "CANCELLED"


async def test_event_create_rolls_back_when_audit_insert_fails(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _user, headers = await register_writer(auth_client)
    app = cast(FastAPI, auth_app)
    title = f"Rollback Event {uuid7()}"
    await install_event_audit_rejection(app)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/events",
                json=event_payload(title=title),
                headers=headers,
            )
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    finally:
        await remove_event_audit_rejection(app)

    async with app.state.session_factory() as session:
        event_count = await session.scalar(select(Event).where(Event.title == title).limit(1))
    assert event_count is None


async def test_event_update_and_cancel_roll_back_when_audit_insert_fails(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _user, headers = await register_writer(auth_client)
    update_target = await create_writer_event(auth_client, headers, title="Rollback Update")
    cancel_target = await create_writer_event(auth_client, headers, title="Rollback Cancel")
    app = cast(FastAPI, auth_app)
    await install_event_audit_rejection(app)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            update_response = await client.patch(
                f"/api/v1/events/{update_target['id']}",
                json={"expectedVersion": 1, "title": "Must Roll Back"},
                headers=headers,
            )
            cancel_response = await client.delete(
                f"/api/v1/events/{cancel_target['id']}",
                params={"expectedVersion": 1},
                headers=headers,
            )
        assert update_response.status_code == 500
        assert cancel_response.status_code == 500
    finally:
        await remove_event_audit_rejection(app)

    async with app.state.session_factory() as session:
        updated_event = await session.get(Event, update_target["id"])
        cancelled_event = await session.get(Event, cancel_target["id"])
        failed_audits = (
            await session.scalars(
                select(AuditLog).where(
                    AuditLog.resource_id.in_((update_target["id"], cancel_target["id"])),
                    AuditLog.action.in_(("event.updated", "event.cancelled")),
                )
            )
        ).all()
    assert updated_event is not None
    assert updated_event.title == "Rollback Update"
    assert updated_event.version == 1
    assert cancelled_event is not None
    assert cancelled_event.status.value == "ACTIVE"
    assert cancelled_event.cancelled_at is None
    assert cancelled_event.version == 1
    assert failed_audits == []
