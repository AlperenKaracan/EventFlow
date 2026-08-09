from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID, uuid7

import jwt
from fastapi import Depends, FastAPI
from httpx import AsyncClient

from app.auth.dependencies import CurrentUser, RequireRole, ensure_owner_or_not_found
from app.auth.security import JWT_ALGORITHM
from app.shared.config import Settings
from app.users.models import User, UserRole


async def authenticated_attendee(
    client: AsyncClient,
) -> tuple[dict[str, object], str]:
    email = f"attacker-matrix-{uuid7()}@example.com"
    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "fullName": "Attack Matrix",
            "password": "integration-password",
            "role": "attendee",
        },
    )
    assert registered.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "integration-password"},
    )
    assert login.status_code == 200
    return registered.json(), cast(str, login.json()["accessToken"])


async def test_missing_and_forged_bearer_tokens_return_401(
    auth_client: AsyncClient,
) -> None:
    missing = await auth_client.get("/api/v1/auth/me")
    forged = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer attacker-controlled-token"},
    )

    assert missing.status_code == forged.status_code == 401
    assert missing.headers["WWW-Authenticate"] == "Bearer"
    assert forged.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_modified_role_and_subject_claims_are_rejected(
    auth_client: AsyncClient, integration_settings: Settings
) -> None:
    registered, access_token = await authenticated_attendee(auth_client)
    payload = jwt.decode(access_token, options={"verify_signature": False})

    payload["role"] = UserRole.ORGANIZER.value
    role_mismatch = jwt.encode(
        payload,
        integration_settings.JWT_SECRET.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    role_response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {role_mismatch}"},
    )

    payload["role"] = UserRole.ATTENDEE.value
    payload["sub"] = str(uuid7())
    subject_mismatch = jwt.encode(
        payload,
        integration_settings.JWT_SECRET.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    subject_response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {subject_mismatch}"},
    )

    assert UUID(cast(str, registered["id"])) != UUID(payload["sub"])
    assert role_response.status_code == subject_response.status_code == 401
    assert role_response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert subject_response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_capability_is_403_but_ownership_uuid_is_hidden_with_404(
    auth_client: AsyncClient, auth_app: object
) -> None:
    app = cast(FastAPI, auth_app)

    @app.post("/_test/organizer-capability")
    async def organizer_capability(
        _user: Annotated[User, Depends(RequireRole(UserRole.ORGANIZER))],
    ) -> dict[str, bool]:
        return {"allowed": True}

    @app.get("/_test/owned-resource/{owner_id}")
    async def owned_resource(owner_id: UUID, current_user: CurrentUser) -> dict[str, bool]:
        ensure_owner_or_not_found(owner_id=owner_id, user=current_user)
        return {"allowed": True}

    registered, access_token = await authenticated_attendee(auth_client)
    headers = {"Authorization": f"Bearer {access_token}"}
    capability = await auth_client.post("/_test/organizer-capability", headers=headers)
    inaccessible = await auth_client.get(f"/_test/owned-resource/{uuid7()}", headers=headers)
    another_unknown = await auth_client.get(f"/_test/owned-resource/{uuid7()}", headers=headers)
    own = await auth_client.get(f"/_test/owned-resource/{registered['id']}", headers=headers)

    assert capability.status_code == 403
    assert capability.json()["error"]["code"] == "FORBIDDEN"
    assert inaccessible.status_code == another_unknown.status_code == 404
    assert inaccessible.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert another_unknown.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert own.status_code == 200
