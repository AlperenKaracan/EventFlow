from __future__ import annotations

from collections.abc import Mapping
from logging import Logger
from typing import cast

from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.observability.metrics import EventFlowMetrics
from app.observability.middleware import RequestContextMiddleware


class RecordingLogger:
    def __init__(self) -> None:
        self.events: list[Mapping[str, object]] = []

    def info(self, _message: str, *, extra: Mapping[str, object]) -> None:
        self.events.append(extra)


class RecordingMetrics:
    def __init__(self) -> None:
        self.started = 0
        self.completed: list[dict[str, object]] = []

    def request_started(self) -> None:
        self.started += 1

    def request_completed(
        self,
        *,
        method: str,
        route: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        self.completed.append(
            {
                "method": method,
                "route": route,
                "status": status,
                "duration_seconds": duration_seconds,
            }
        )


async def test_request_middleware_logs_started_and_completed_lifecycle() -> None:
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    logger = RecordingLogger()
    metrics = RecordingMetrics()
    app = Starlette(routes=[Route("/health", health)])
    app.add_middleware(
        RequestContextMiddleware,
        logger=cast(Logger, logger),
        metrics=cast(EventFlowMetrics, metrics),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "01989cb0-7423-7a3a-8930-5ed69dd4b854"},
        )

    assert response.status_code == 200
    assert [event["event"] for event in logger.events] == [
        "http.request.started",
        "http.request.completed",
    ]
    assert metrics.started == 1
    assert metrics.completed[0]["status"] == 200
