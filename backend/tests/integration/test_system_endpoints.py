from uuid import UUID

from httpx import AsyncClient


async def test_health_reports_process_liveness_without_dependencies(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert UUID(response.headers["X-Request-ID"]).version == 7


async def test_ready_reports_dependency_failure_with_consistent_error(client: AsyncClient) -> None:
    response = await client.get("/ready", headers={"X-Request-ID": "invalid"})

    assert response.status_code == 503
    payload = response.json()
    request_id = response.headers["X-Request-ID"]
    assert payload["error"]["code"] == "DEPENDENCIES_NOT_READY"
    assert payload["error"]["requestId"] == request_id
    assert {item["dependency"] for item in payload["error"]["details"]} == {
        "postgresql",
        "redis",
    }


async def test_unknown_route_uses_request_id_header(client: AsyncClient) -> None:
    request_id = "01989cb0-7423-7a3a-8930-5ed69dd4b854"

    response = await client.get("/does-not-exist", headers={"X-Request-ID": request_id})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["error"] == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "İstenen kaynak bulunamadı.",
        "requestId": request_id,
        "details": [],
    }
