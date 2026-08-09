from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.shared.request_context import (
    REQUEST_ID_HEADER,
    normalize_request_id,
    reset_request_id,
    set_request_id,
)

if TYPE_CHECKING:
    from logging import Logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, logger: Logger) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.logger = logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = set_request_id(request_id)
        started_at = perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            route = request.scope.get("route")
            route_template = getattr(route, "path", request.url.path)
            self.logger.info(
                "Request completed",
                extra={
                    "event": "http.request.completed",
                    "method": request.method,
                    "route": route_template,
                    "status": response.status_code if response is not None else 500,
                    "durationMs": round((perf_counter() - started_at) * 1000, 3),
                },
            )
            reset_request_id(token)
