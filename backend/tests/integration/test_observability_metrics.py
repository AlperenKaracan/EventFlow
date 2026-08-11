from typing import cast
from uuid import UUID, uuid7

from httpx import AsyncClient

from tests.integration.test_reservation_creation import create_event, register_actor


async def test_domain_metrics_cover_reservation_idempotency_cancellation_and_rate_limit(
    auth_client: AsyncClient,
) -> None:
    organizer, organizer_headers = await register_actor(auth_client, role="organizer")
    _attendee, attendee_headers = await register_actor(auth_client, role="attendee")
    _second_attendee, second_attendee_headers = await register_actor(
        auth_client,
        role="attendee",
    )
    event = await create_event(auth_client, organizer_headers, capacity=1)
    event_id = UUID(cast(str, event["id"]))
    idempotency_key = f"metrics-{uuid7()}"

    created = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=attendee_headers | {"Idempotency-Key": idempotency_key},
    )
    replayed = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=attendee_headers | {"Idempotency-Key": idempotency_key},
    )
    full = await auth_client.post(
        f"/api/v1/events/{event_id}/reservations",
        headers=second_attendee_headers | {"Idempotency-Key": f"metrics-full-{uuid7()}"},
    )
    cancelled = await auth_client.delete(
        f"/api/v1/events/{event_id}",
        headers=organizer_headers,
        params={"expectedVersion": 1},
    )

    login_response = None
    for _ in range(5):
        login_response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": organizer["email"], "password": "incorrect-password"},
        )

    assert created.status_code == replayed.status_code == 201
    assert replayed.headers["Idempotent-Replayed"] == "true"
    assert full.status_code == 409
    assert cancelled.status_code == 204
    assert login_response is not None and login_response.status_code == 429

    metrics = await auth_client.get("/metrics")

    assert metrics.status_code == 200
    body = metrics.text
    assert 'eventflow_reservation_attempts_total{outcome="created"} 1.0' in body
    assert 'eventflow_reservation_attempts_total{outcome="replayed"} 1.0' in body
    assert 'eventflow_reservation_attempts_total{outcome="full"} 1.0' in body
    assert 'eventflow_idempotency_requests_total{outcome="owner"} 2.0' in body
    assert 'eventflow_idempotency_requests_total{outcome="replay"} 1.0' in body
    assert 'eventflow_reservation_lock_wait_seconds_count{operation="create"} 2.0' in body
    assert "eventflow_event_cancellations_total 1.0" in body
    assert 'eventflow_rate_limit_rejections_total{endpoint="login"} 1.0' in body
    assert str(event_id) not in body
