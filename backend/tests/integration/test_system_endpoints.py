from uuid import UUID

from httpx import AsyncClient
from prometheus_client.parser import text_string_to_metric_families


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


async def test_metrics_use_route_templates_and_bounded_labels(client: AsyncClient) -> None:
    request_id = "01989cb0-7423-7a3a-8930-5ed69dd4b854"
    await client.get("/health", headers={"X-Request-ID": request_id})
    await client.get(f"/missing/{request_id}")
    await client.get("/ready")

    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert 'eventflow_http_requests_total{method="GET",route="/health",status="200"} 1.0' in body
    assert 'eventflow_http_requests_total{method="GET",route="unmatched",status="404"} 1.0' in body
    assert request_id not in body
    assert 'eventflow_readiness_status{dependency="postgresql"} 0.0' in body
    assert 'eventflow_readiness_status{dependency="redis"} 0.0' in body
    assert "eventflow_http_requests_in_progress 0.0" in body
    assert "eventflow_process_start_time_seconds" in body

    allowed_label_names = {
        "dependency",
        "endpoint",
        "le",
        "method",
        "operation",
        "outcome",
        "route",
        "status",
    }
    observed_label_names = {
        label
        for family in text_string_to_metric_families(body)
        for sample in family.samples
        for label in sample.labels
    }
    assert observed_label_names <= allowed_label_names
