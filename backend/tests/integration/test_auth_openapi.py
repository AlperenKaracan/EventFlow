from httpx import AsyncClient


async def test_auth_openapi_documents_stable_operations_and_error_envelopes(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    document = response.json()
    paths = document["paths"]
    assert paths["/api/v1/auth/register"]["post"]["operationId"] == "registerUser"
    assert paths["/api/v1/auth/login"]["post"]["operationId"] == "loginUser"
    assert paths["/api/v1/auth/me"]["get"]["operationId"] == "getCurrentUser"
    assert paths["/api/v1/auth/refresh"]["post"]["operationId"] == "refreshSession"
    assert paths["/api/v1/auth/logout"]["post"]["operationId"] == "logoutUser"

    login_responses = paths["/api/v1/auth/login"]["post"]["responses"]
    for status_code in ("401", "422", "429", "503"):
        schema = login_responses[status_code]["content"]["application/json"]["schema"]
        assert schema["$ref"] == "#/components/schemas/ErrorEnvelope"

    security_schemes = document["components"]["securitySchemes"]
    assert security_schemes["HTTPBearer"]["scheme"] == "bearer"
