import json
from pathlib import Path
from typing import Any, cast

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_loki_uses_tsdb_filesystem_and_seven_day_retention() -> None:
    config = (REPOSITORY_ROOT / "observability" / "loki.yaml").read_text(encoding="utf-8")

    assert "store: tsdb" in config
    assert "object_store: filesystem" in config
    assert "schema: v13" in config
    assert "retention_enabled: true" in config
    assert "delete_request_store: filesystem" in config
    assert "retention_period: ${LOKI_RETENTION_PERIOD}" in config


def test_alloy_limits_discovery_and_index_labels() -> None:
    config = (REPOSITORY_ROOT / "observability" / "alloy" / "config.alloy").read_text(
        encoding="utf-8"
    )

    assert 'values = ["com.docker.compose.project=eventflow"]' in config
    assert 'values = ["service_name", "environment", "level", "route"]' in config
    assert "drop_malformed = false" in config
    assert 'source   = "parse_error"' in config
    assert "requestId" not in config
    assert "actorId" not in config
    assert "email" not in config
    assert config.count('sys.env("ALLOY_DOCKER_REFRESH_INTERVAL")') == 2


def test_compose_mounts_docker_socket_read_only_and_uses_named_storage() -> None:
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "grafana/loki:3.7.6" in compose
    assert "grafana/alloy:v1.18.1" in compose
    assert "/var/run/docker.sock:/var/run/docker.sock:ro" in compose
    assert "loki_data:/loki" in compose
    assert 'user: "473:473"' in compose
    assert "${DOCKER_SOCKET_GID:-0}" in compose


def test_prometheus_scrapes_only_the_backend_metrics_endpoint() -> None:
    config = (REPOSITORY_ROOT / "observability" / "prometheus" / "prometheus.yml").read_text(
        encoding="utf-8"
    )
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "job_name: eventflow-backend" in config
    assert "metrics_path: /metrics" in config
    assert 'targets: ["backend:8000"]' in config
    assert "prom/prometheus:v3.13.2" in compose
    assert "prometheus_data:/prometheus" in compose


def _dashboard(kind: str, filename: str) -> dict[str, Any]:
    path = REPOSITORY_ROOT / "observability" / "grafana" / "dashboards" / kind / filename
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_grafana_provisions_fixed_datasources_folders_and_home_dashboard() -> None:
    datasource_config = (
        REPOSITORY_ROOT
        / "observability"
        / "grafana"
        / "provisioning"
        / "datasources"
        / "eventflow.yaml"
    ).read_text(encoding="utf-8")
    dashboard_config = (
        REPOSITORY_ROOT
        / "observability"
        / "grafana"
        / "provisioning"
        / "dashboards"
        / "eventflow.yaml"
    ).read_text(encoding="utf-8")
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "uid: eventflow-prometheus" in datasource_config
    assert "uid: eventflow-loki" in datasource_config
    assert 'matcherRegex: \'"requestId":"([0-9a-fA-F-]{36})"\'' in datasource_config
    assert "$${__value.raw}" in datasource_config
    assert "folder: EventFlow - Metrikler" in dashboard_config
    assert "folder: EventFlow - Loglar" in dashboard_config
    assert "grafana/grafana:13.1.3" in compose
    assert "GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH" in compose
    assert "grafana-lokiexplore-app@2.5.0" in compose
    assert "grafana-metricsdrilldown-app@2.4.0" in compose


def test_grafana_dashboards_cover_every_required_operations_view() -> None:
    overview = _dashboard("overview", "eventflow-overview.json")
    metrics = _dashboard("metrics", "eventflow-metrics.json")
    logs = _dashboard("logs", "eventflow-logs.json")

    assert overview["uid"] == "eventflow-overview"
    assert metrics["uid"] == "eventflow-metrics"
    assert logs["uid"] == "eventflow-logs"
    assert len(metrics["panels"]) == 12
    assert len(logs["panels"]) == 3

    required_titles = {
        "İstek trafiği",
        "HTTP durum dağılımı",
        "İstek gecikmesi yüzdelikleri",
        "En yavaş rotalar",
        "Rezervasyon sonuçları",
        "Kapasite reddi oranı",
        "Etkinlik kilidi bekleme p95",
        "İdempotent istek tekrar oranı",
        "İstek sınırı reddi",
        "Bağımlılık sağlığı",
        "HTTP 5xx eğilimi",
        "Backend çalışma süresi",
        "Son hata logları",
        "Seçili rota için canlı loglar",
        "Request ID uçtan uca logları",
    }
    operation_panels = metrics["panels"] + logs["panels"]
    assert {panel["title"] for panel in operation_panels} == required_titles
    assert all(panel.get("description") for panel in operation_panels)

    variable_names = {
        variable["name"]
        for dashboard in (metrics, logs)
        for variable in dashboard["templating"]["list"]
    }
    assert {"route", "status", "level", "service", "interval"} <= variable_names

    non_log_panels = [panel for panel in metrics["panels"] if panel["type"] != "logs"]
    assert all(
        panel.get("fieldConfig", {}).get("defaults", {}).get("noValue") == "Veri yok"
        for panel in non_log_panels
    )
