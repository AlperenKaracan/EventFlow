from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from uuid import uuid4

REPOSITORY_ROOT = Path(__file__).parents[1]
LOG_DASHBOARD_PATH = (
    REPOSITORY_ROOT / "observability" / "grafana" / "dashboards" / "logs" / "eventflow-logs.json"
)


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def _request_json(
    url: str,
    *,
    authorization: str | None = None,
    payload: dict[str, object] | None = None,
) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if authorization is not None:
        headers["Authorization"] = authorization
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)  # type: ignore[no-any-return]
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        raise RuntimeError(f"{url} returned {error.code}: {body}") from error


def _interpolate(expression: str, *, window_hours: int) -> str:
    replacements = {
        "$environment": ".+",
        "$service": ".+",
        "$level": ".+",
        "$route": ".+",
        "$status": ".+",
        "$search": ".*",
        "$request_id": ".*",
        "$slow_ms": "500",
        "$__range": f"{window_hours}h",
        "$interval": "5m",
    }
    for variable, value in replacements.items():
        expression = expression.replace(variable, value)
    return expression


def _wait_for_dashboard(*, grafana_url: str, authorization: str) -> dict[str, Any]:
    for _ in range(30):
        try:
            provisioned = _request_json(
                f"{grafana_url}/api/dashboards/uid/eventflow-logs",
                authorization=authorization,
            )
            dashboard = provisioned["dashboard"]
            if dashboard.get("title") == "EventFlow - Log Analizi":
                return dashboard  # type: ignore[no-any-return]
        except OSError, RuntimeError:
            pass
        time.sleep(1)
    raise RuntimeError("provisioned EventFlow log dashboard was not ready")


def _emit_structured_rejection(*, backend_url: str, request_id: str) -> None:
    request = urllib.request.Request(
        f"{backend_url}/missing/grafana-log-analysis",
        headers={"X-Request-ID": request_id},
    )
    try:
        urllib.request.urlopen(request, timeout=10).read()
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise


def _query_dashboard_targets(
    *,
    grafana_url: str,
    authorization: str,
    window_hours: int,
) -> int:
    dashboard = json.loads(LOG_DASHBOARD_PATH.read_text(encoding="utf-8"))
    targets = [
        (panel["title"], target["expr"])
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    ]
    now_ms = int(time.time() * 1000)
    for title, expression in targets:
        response = _request_json(
            f"{grafana_url}/api/ds/query",
            authorization=authorization,
            payload={
                "from": str(now_ms - window_hours * 60 * 60 * 1000),
                "to": str(now_ms),
                "queries": [
                    {
                        "datasource": {"type": "loki", "uid": "eventflow-loki"},
                        "direction": "backward",
                        "editorMode": "code",
                        "expr": _interpolate(expression, window_hours=window_hours),
                        "maxLines": 1000,
                        "queryType": "range",
                        "refId": "A",
                    }
                ],
            },
        )
        result = response["results"]["A"]
        if error := result.get("error"):
            raise RuntimeError(f"{title}: {error}")
        print(f"OK: {title}")
    return len(targets)


def _wait_for_rejection_log(
    *,
    grafana_url: str,
    authorization: str,
    request_id: str,
) -> None:
    now_ms = int(time.time() * 1000)
    expression = (
        '{service_name="backend"} | json '
        '| event="http.request.rejected" '
        '| errorCode="RESOURCE_NOT_FOUND" '
        f'| requestId="{request_id}"'
    )
    for _ in range(30):
        response = _request_json(
            f"{grafana_url}/api/ds/query",
            authorization=authorization,
            payload={
                "from": str(now_ms - 10 * 60 * 1000),
                "to": str(int(time.time() * 1000)),
                "queries": [
                    {
                        "datasource": {"type": "loki", "uid": "eventflow-loki"},
                        "expr": expression,
                        "queryType": "range",
                        "refId": "A",
                    }
                ],
            },
        )
        if response["results"]["A"].get("frames"):
            return
        time.sleep(1)
    raise RuntimeError("structured RESOURCE_NOT_FOUND log did not reach Loki")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify every provisioned EventFlow log dashboard query."
    )
    parser.add_argument("--grafana-url", default="http://localhost:3000")
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--window-hours", default=6, type=int)
    args = parser.parse_args()

    defaults = _read_env(REPOSITORY_ROOT / ".env.example")
    local = _read_env(REPOSITORY_ROOT / ".env")
    user = local.get("GRAFANA_ADMIN_USER", defaults["GRAFANA_ADMIN_USER"])
    password = local.get("GRAFANA_ADMIN_PASSWORD", defaults["GRAFANA_ADMIN_PASSWORD"])
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    authorization = f"Basic {token}"

    provisioned = _wait_for_dashboard(
        grafana_url=args.grafana_url,
        authorization=authorization,
    )
    analysis_panels = [panel for panel in provisioned["panels"] if panel["type"] != "row"]
    if len(analysis_panels) != 17:
        raise RuntimeError(f"expected 17 analysis panels, got {len(analysis_panels)}")

    request_id = str(uuid4())
    _emit_structured_rejection(backend_url=args.backend_url, request_id=request_id)
    _wait_for_rejection_log(
        grafana_url=args.grafana_url,
        authorization=authorization,
        request_id=request_id,
    )
    target_count = _query_dashboard_targets(
        grafana_url=args.grafana_url,
        authorization=authorization,
        window_hours=args.window_hours,
    )
    print(f"Verified {len(analysis_panels)} panels and {target_count} LogQL targets.")


if __name__ == "__main__":
    main()
