from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.factory import create_app
from app.shared.config import Settings

ALLOWED_ORIGIN = "http://localhost:5173"


async def test_allowed_origin_receives_exact_cors_and_security_headers(
    auth_client: AsyncClient,
) -> None:
    response = await auth_client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["Vary"] == "Origin"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in response.headers


async def test_foreign_origin_receives_no_cors_authorization(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/health", headers={"Origin": "https://attacker.example"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


async def test_valid_preflight_uses_narrow_allowlist(auth_client: AsyncClient) -> None:
    response = await auth_client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-Request-ID",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "content-type" in response.headers["Access-Control-Allow-Headers"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


async def test_rejected_preflight_uses_common_error_envelope(auth_client: AsyncClient) -> None:
    response = await auth_client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Forbidden-Header",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CORS_REJECTED"
    assert response.json()["error"]["requestId"] == response.headers["X-Request-ID"]
    assert response.headers["X-Frame-Options"] == "DENY"


async def test_hsts_is_enabled_only_in_production(
    integration_settings: Settings,
) -> None:
    production_settings = integration_settings.model_copy(update={"APP_ENV": "production"})
    app = create_app(production_settings)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="https://testserver") as client:
            response = await client.get("/health")

    assert response.headers["Strict-Transport-Security"] == ("max-age=31536000; includeSubDomains")
