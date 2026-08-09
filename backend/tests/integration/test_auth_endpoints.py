from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid7

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth.models import RefreshToken
from app.auth.router import REFRESH_COOKIE_NAME
from app.auth.security import hash_refresh_token
from app.auth.service import cleanup_inactive_refresh_tokens
from app.shared.config import Settings

ALLOWED_ORIGIN = "http://localhost:5173"


def registration_payload(*, email: str | None = None) -> dict[str, str]:
    return {
        "email": email or f"person-{uuid7()}@example.com",
        "fullName": "Integration Person",
        "password": "integration-password",
        "role": "attendee",
    }


async def register_and_login(client: AsyncClient) -> tuple[dict[str, str], str, str]:
    payload = registration_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    refresh_token = client.cookies.get(REFRESH_COOKIE_NAME)
    assert refresh_token is not None
    return payload, login_response.json(), refresh_token


async def test_register_login_and_me_contract(auth_client: AsyncClient) -> None:
    payload = registration_payload(email=f"NORMALIZED-{uuid7()}@Example.COM")

    registered = await auth_client.post("/api/v1/auth/register", json=payload)

    assert registered.status_code == 201
    assert registered.json()["email"] == payload["email"].lower()
    assert registered.json()["fullName"] == "Integration Person"
    duplicate = await auth_client.post("/api/v1/auth/register", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    login = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    assert login.json()["tokenType"] == "Bearer"
    assert login.json()["expiresIn"] == 900
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "SameSite=lax" in login.headers["set-cookie"]
    assert "Path=/api/v1/auth" in login.headers["set-cookie"]

    me = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['accessToken']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == registered.json()["id"]


async def test_invalid_credentials_share_one_safe_response(auth_client: AsyncClient) -> None:
    payload = registration_payload()
    await auth_client.post("/api/v1/auth/register", json=payload)

    wrong_password = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "wrong-password"},
    )
    unknown_user = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": f"unknown-{uuid7()}@example.com", "password": "wrong-password"},
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert unknown_user.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong_password.json()["error"]["message"] == unknown_user.json()["error"]["message"]


async def test_login_rate_limit_is_enforced(auth_client: AsyncClient) -> None:
    email = f"limited-{uuid7()}@example.com"
    responses = [
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429
    assert int(responses[5].headers["Retry-After"]) >= 1


async def test_refresh_rotation_replay_revokes_entire_family(auth_client: AsyncClient) -> None:
    _payload, _login, original_token = await register_and_login(auth_client)

    rotated = await auth_client.post("/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN})
    assert rotated.status_code == 200
    replacement_token = auth_client.cookies.get(REFRESH_COOKIE_NAME)
    assert replacement_token is not None and replacement_token != original_token

    auth_client.cookies.set(
        REFRESH_COOKIE_NAME,
        original_token,
        domain="testserver.local",
        path="/api/v1/auth",
    )
    replay = await auth_client.post("/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN})
    assert replay.status_code == 401

    auth_client.cookies.set(
        REFRESH_COOKIE_NAME,
        replacement_token,
        domain="testserver.local",
        path="/api/v1/auth",
    )
    family_member = await auth_client.post(
        "/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN}
    )
    assert family_member.status_code == 401


async def test_refresh_requires_exact_origin(auth_client: AsyncClient) -> None:
    await register_and_login(auth_client)

    missing = await auth_client.post("/api/v1/auth/refresh")
    foreign = await auth_client.post(
        "/api/v1/auth/refresh", headers={"Origin": "https://attacker.example"}
    )

    assert missing.status_code == foreign.status_code == 403
    assert missing.json()["error"]["code"] == "INVALID_ORIGIN"


async def test_logout_revokes_family_and_clears_cookie(auth_client: AsyncClient) -> None:
    _payload, _login, refresh_token = await register_and_login(auth_client)

    logout = await auth_client.post("/api/v1/auth/logout", headers={"Origin": ALLOWED_ORIGIN})

    assert logout.status_code == 204
    assert logout.content == b""
    assert "Max-Age=0" in logout.headers["set-cookie"]

    auth_client.cookies.set(
        REFRESH_COOKIE_NAME,
        refresh_token,
        domain="testserver.local",
        path="/api/v1/auth",
    )
    revoked = await auth_client.post("/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN})
    assert revoked.status_code == 401

    auth_client.cookies.clear()
    repeated_logout = await auth_client.post(
        "/api/v1/auth/logout", headers={"Origin": ALLOWED_ORIGIN}
    )
    assert repeated_logout.status_code == 204


async def test_concurrent_refresh_allows_one_rotation_then_revokes_winner(
    auth_client: AsyncClient, auth_app: object
) -> None:
    _payload, _login, original_token = await register_and_login(auth_client)
    app = cast(FastAPI, auth_app)

    async def attempt_refresh() -> Any:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as contender:
            contender.cookies.set(
                REFRESH_COOKIE_NAME,
                original_token,
                domain="testserver.local",
                path="/api/v1/auth",
            )
            return await contender.post("/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN})

    responses = await asyncio.gather(attempt_refresh(), attempt_refresh())
    assert sorted(response.status_code for response in responses) == [200, 401]
    winner = next(response for response in responses if response.status_code == 200)
    winner_token = winner.cookies.get(REFRESH_COOKIE_NAME)
    assert winner_token is not None

    auth_client.cookies.set(
        REFRESH_COOKIE_NAME,
        winner_token,
        domain="testserver.local",
        path="/api/v1/auth",
    )
    revoked_winner = await auth_client.post(
        "/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN}
    )
    assert revoked_winner.status_code == 401


async def test_cleanup_preserves_active_family_chain(
    auth_client: AsyncClient, auth_app: object, integration_settings: Settings
) -> None:
    _payload, _login, original_token = await register_and_login(auth_client)
    rotated = await auth_client.post("/api/v1/auth/refresh", headers={"Origin": ALLOWED_ORIGIN})
    assert rotated.status_code == 200
    replacement_token = auth_client.cookies.get(REFRESH_COOKIE_NAME)
    assert replacement_token is not None
    app = cast(FastAPI, auth_app)
    now = datetime.now(tz=UTC)

    async with app.state.session_factory() as session:
        original = await session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(original_token)
            )
        )
        replacement = await session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(replacement_token)
            )
        )
        assert original is not None and replacement is not None
        original.revoked_at = now - timedelta(days=8)
        original.expires_at = now - timedelta(days=1)
        await session.commit()

    async with app.state.session_factory() as session:
        assert (
            await cleanup_inactive_refresh_tokens(
                session=session, settings=integration_settings, now=now
            )
            == 0
        )

    async with app.state.session_factory() as session:
        replacement = await session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(replacement_token)
            )
        )
        assert replacement is not None
        replacement.expires_at = now - timedelta(seconds=1)
        await session.commit()

    async with app.state.session_factory() as session:
        assert (
            await cleanup_inactive_refresh_tokens(
                session=session, settings=integration_settings, now=now
            )
            == 2
        )
