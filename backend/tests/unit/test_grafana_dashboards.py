import json
import re
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).parents[3]
LOG_DASHBOARD_PATH = (
    REPOSITORY_ROOT / "observability" / "grafana" / "dashboards" / "logs" / "eventflow-logs.json"
)


def _load_log_dashboard() -> dict[str, Any]:
    return json.loads(LOG_DASHBOARD_PATH.read_text(encoding="utf-8"))


def test_log_dashboard_has_complete_analysis_workflow() -> None:
    dashboard = _load_log_dashboard()
    panels = dashboard["panels"]
    analysis_panels = [panel for panel in panels if panel["type"] != "row"]

    assert dashboard["uid"] == "eventflow-logs"
    assert dashboard["title"] == "EventFlow - Log Analizi"
    assert dashboard["editable"] is False
    assert len(analysis_panels) == 17
    assert len({panel["id"] for panel in panels}) == len(panels)
    assert {panel["title"] for panel in panels if panel["type"] == "row"} == {
        "Operasyon özeti",
        "HTTP trafik ve performans analizi",
        "İş alanı ve hata analizi",
        "Request ID incelemesi ve canlı log akışı",
    }
    assert {
        "Toplam log",
        "Hata logları",
        "Başarısız HTTP",
        "En yüksek istek süresi p95",
        "Yapılandırılmamış loglar",
        "Log hızı ve seviye eğilimi",
        "HTTP durum dağılımı",
        "En yoğun rotalar",
        "Rota bazında p95 istek süresi",
        "Yavaş istekler",
        "İş alanı olay eğilimi",
        "İşlem sonuçları",
        "Uygulama hata kodları",
        "İş alanı olay ayrıntıları",
        "Request ID uçtan uca zaman çizelgesi",
        "Filtrelenmiş canlı log akışı",
        "Ayrıştırılamayan loglar",
    } == {panel["title"] for panel in analysis_panels}


def test_log_dashboard_queries_keep_high_cardinality_fields_out_of_selectors() -> None:
    dashboard = _load_log_dashboard()
    expressions = [
        target["expr"] for panel in dashboard["panels"] for target in panel.get("targets", [])
    ]

    assert len(expressions) == 17
    assert any('requestId=~"$request_id"' in expression for expression in expressions)
    assert any("durationMs >= $slow_ms" in expression for expression in expressions)
    assert any("errorCode" in expression for expression in expressions)
    for expression in expressions:
        for selector in re.findall(r"\{([^{}]+)\}", expression):
            assert "requestId" not in selector
            assert "actorId" not in selector
            assert "eventId" not in selector
            assert "reservationId" not in selector


def test_log_dashboard_exposes_actionable_filters() -> None:
    dashboard = _load_log_dashboard()
    variables = {item["name"]: item for item in dashboard["templating"]["list"]}

    assert set(variables) == {
        "environment",
        "service",
        "level",
        "route",
        "status",
        "slow_ms",
        "interval",
        "search",
        "request_id",
    }
    assert variables["request_id"]["type"] == "textbox"
    assert variables["search"]["type"] == "textbox"
    assert variables["slow_ms"]["current"]["value"] == "500"
