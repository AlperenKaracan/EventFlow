from __future__ import annotations

from typing import Any

import pytest

from app import server
from app.shared.config import Settings


def test_server_passes_configured_graceful_timeout(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(app_import: str, **options: Any) -> None:
        captured["app_import"] = app_import
        captured.update(options)

    monkeypatch.setattr("app.server.uvicorn.run", fake_run)

    server.run_server(settings=settings)

    assert captured["app_import"] == "app.main:app"
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8000
    assert captured["access_log"] is False
    assert captured["timeout_graceful_shutdown"] == 20
