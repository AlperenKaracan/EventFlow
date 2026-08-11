from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import (
    EventFlowMetrics,
    reset_current_metrics,
    set_current_metrics,
)
from app.shared.request_context import (
    REQUEST_ID_HEADER,
    normalize_request_id,
    reset_request_id,
    set_request_id,
)

if TYPE_CHECKING:
    from logging import Logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, logger: Logger, metrics: EventFlowMetrics) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.logger = logger
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = set_request_id(request_id)
        metrics_token = set_current_metrics(self.metrics)
        started_at = perf_counter()
        response: Response | None = None
        track_request = request.url.path != "/metrics"
        if track_request:
            self.metrics.request_started()
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            route = request.scope.get("route")
            route_template = getattr(route, "path", "unmatched")
            status = response.status_code if response is not None else 500
            duration_seconds = perf_counter() - started_at
            if track_request:
                self.metrics.request_completed(
                    method=request.method,
                    route=route_template,
                    status=status,
                    duration_seconds=duration_seconds,
                )
            self.logger.info(
                "Request completed",
                extra={
                    "event": "http.request.completed",
                    "method": request.method,
                    "route": route_template,
                    "status": status,
                    "durationMs": round(duration_seconds * 1000, 3),
                },
            )
            reset_current_metrics(metrics_token)
            reset_request_id(token)
