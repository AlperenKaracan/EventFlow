from __future__ import annotations

import uvicorn

from app.shared.config import Settings, load_settings


def run_server(
    *,
    app_import: str = "app.main:app",
    settings: Settings | None = None,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    active_settings = settings or load_settings()
    uvicorn.run(
        app_import,
        host=host,
        port=port,
        access_log=False,
        log_config="app/observability/uvicorn-log-config.json",
        timeout_graceful_shutdown=active_settings.GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS,
    )


if __name__ == "__main__":
    run_server()
