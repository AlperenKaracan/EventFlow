from __future__ import annotations

from uuid import uuid7

from httpx import AsyncClient

from app.seed import IDENTITY


async def login_seed_user(client: AsyncClient, *, email: str, password: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


async def register_organizer(client: AsyncClient) -> dict[str, str]:
    email = f"event-owner-{uuid7()}@example.com"
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "fullName": "Other Organizer",
            "password": "integration-password",
            "role": "organizer",
        },
    )
    assert registered.status_code == 201
    return await login_seed_user(
        client,
        email=email,
        password="integration-password",
    )


async def test_categories_and_public_events_use_stable_projections(
    auth_client: AsyncClient,
) -> None:
    categories = await auth_client.get("/api/v1/categories")
    assert categories.status_code == 200
    assert len(categories.json()) == 6
    assert [row["name"] for row in categories.json()] == sorted(
        row["name"] for row in categories.json()
    )

    first_page = await auth_client.get("/api/v1/events", params={"limit": 2})
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert len(first_body["items"]) == 2
    assert first_body["hasMore"] is True
    assert first_body["nextCursor"]

    second_page = await auth_client.get(
        "/api/v1/events",
        params={"limit": 2, "cursor": first_body["nextCursor"]},
    )
    assert second_page.status_code == 200
    second_body = second_page.json()
    assert len(second_body["items"]) == 2
    assert second_body["hasMore"] is False
    assert second_body["nextCursor"] is None
    first_ids = {item["id"] for item in first_body["items"]}
    second_ids = {item["id"] for item in second_body["items"]}
    assert first_ids.isdisjoint(second_ids)
    all_items = first_body["items"] + second_body["items"]
    assert [item["startsAt"] for item in all_items] == sorted(
        item["startsAt"] for item in all_items
    )
    assert all(item["availableCapacity"] >= 0 for item in all_items)


async def test_public_detail_hides_cancelled_event_and_invalid_cursor(
    auth_client: AsyncClient,
) -> None:
    active = await auth_client.get(f"/api/v1/events/{IDENTITY.istanbul_event_id}")
    cancelled = await auth_client.get(f"/api/v1/events/{IDENTITY.cancelled_event_id}")
    invalid_cursor = await auth_client.get(
        "/api/v1/events", params={"cursor": "attacker-controlled"}
    )

    assert active.status_code == 200
    assert active.json()["id"] == str(IDENTITY.istanbul_event_id)
    assert cancelled.status_code == 404
    assert cancelled.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert invalid_cursor.status_code == 400
    assert invalid_cursor.json()["error"]["code"] == "INVALID_CURSOR"


async def test_owner_list_and_detail_include_cancelled_and_past_events(
    auth_client: AsyncClient,
) -> None:
    headers = await login_seed_user(
        auth_client,
        email="organizer@eventflow.local",
        password="OrganizerDemo123!",
    )
    first = await auth_client.get("/api/v1/me/events", params={"limit": 3}, headers=headers)
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 3
    assert first_body["hasMore"] is True

    second = await auth_client.get(
        "/api/v1/me/events",
        params={"limit": 3, "cursor": first_body["nextCursor"]},
        headers=headers,
    )
    assert second.status_code == 200
    all_items = first_body["items"] + second.json()["items"]
    assert len(all_items) == 6
    assert {item["status"] for item in all_items} == {"ACTIVE", "CANCELLED"}
    assert any(item["id"] == str(IDENTITY.past_event_id) for item in all_items)

    detail = await auth_client.get(
        f"/api/v1/me/events/{IDENTITY.cancelled_event_id}", headers=headers
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "CANCELLED"
    assert detail.json()["version"] == 1


async def test_owner_resource_is_hidden_and_cursor_is_bound_to_owner(
    auth_client: AsyncClient,
) -> None:
    seed_owner_headers = await login_seed_user(
        auth_client,
        email="organizer@eventflow.local",
        password="OrganizerDemo123!",
    )
    seed_page = await auth_client.get(
        "/api/v1/me/events", params={"limit": 1}, headers=seed_owner_headers
    )
    cursor = seed_page.json()["nextCursor"]
    other_owner_headers = await register_organizer(auth_client)

    inaccessible = await auth_client.get(
        f"/api/v1/me/events/{IDENTITY.istanbul_event_id}",
        headers=other_owner_headers,
    )
    unknown = await auth_client.get(
        f"/api/v1/me/events/{uuid7()}",
        headers=other_owner_headers,
    )
    copied_cursor = await auth_client.get(
        "/api/v1/me/events",
        params={"cursor": cursor},
        headers=other_owner_headers,
    )

    assert inaccessible.status_code == unknown.status_code == 404
    assert inaccessible.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert unknown.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert copied_cursor.status_code == 400
    assert copied_cursor.json()["error"]["code"] == "INVALID_CURSOR"


async def test_attendee_gets_403_for_owner_list_but_404_for_owner_uuid(
    auth_client: AsyncClient,
) -> None:
    headers = await login_seed_user(
        auth_client,
        email="attendee@eventflow.local",
        password="AttendeeDemo123!",
    )

    owner_list = await auth_client.get("/api/v1/me/events", headers=headers)
    owner_detail = await auth_client.get(
        f"/api/v1/me/events/{IDENTITY.istanbul_event_id}", headers=headers
    )

    assert owner_list.status_code == 403
    assert owner_list.json()["error"]["code"] == "FORBIDDEN"
    assert owner_detail.status_code == 404
    assert owner_detail.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
