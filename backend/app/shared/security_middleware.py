from __future__ import annotations

from collections.abc import Iterable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.shared.config import Settings
from app.shared.errors import error_response

ALLOWED_CORS_METHODS = frozenset({"GET", "POST", "PATCH", "DELETE", "OPTIONS"})
ALLOWED_CORS_HEADERS = frozenset(
    {"authorization", "content-type", "idempotency-key", "x-request-id"}
)
EXPOSED_CORS_HEADERS = (
    "X-Request-ID",
    "Idempotency-Original-Request-ID",
    "Retry-After",
)


def _append_vary(response: Response, value: str) -> None:
    existing = response.headers.get("Vary")
    values = {part.strip() for part in existing.split(",")} if existing else set()
    values.add(value)
    response.headers["Vary"] = ", ".join(sorted(values))


def _cors_response_headers(origin: str) -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Expose-Headers": ", ".join(EXPOSED_CORS_HEADERS),
        "Vary": "Origin",
    }


class ExactCORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, allowed_origins: Iterable[str]) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.allowed_origins = frozenset(allowed_origins)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        origin = request.headers.get("Origin")
        is_preflight = request.method == "OPTIONS" and request.headers.get(
            "Access-Control-Request-Method"
        )
        if is_preflight:
            return self._preflight_response(request, origin)

        response = await call_next(request)
        if origin in self.allowed_origins:
            for name, value in _cors_response_headers(origin).items():
                if name != "Vary":
                    response.headers[name] = value
            _append_vary(response, "Origin")
        return response

    def _preflight_response(self, request: Request, origin: str | None) -> Response:
        requested_method = request.headers.get("Access-Control-Request-Method", "").upper()
        requested_headers = {
            header.strip().lower()
            for header in request.headers.get("Access-Control-Request-Headers", "").split(",")
            if header.strip()
        }
        if (
            origin not in self.allowed_origins
            or requested_method not in ALLOWED_CORS_METHODS
            or not requested_headers.issubset(ALLOWED_CORS_HEADERS)
        ):
            return error_response(
                status_code=400,
                code="CORS_REJECTED",
                message="Cross-origin isteğine izin verilmiyor.",
            )

        response = Response(status_code=204, headers=_cors_response_headers(origin))
        response.headers["Access-Control-Allow-Methods"] = ", ".join(sorted(ALLOWED_CORS_METHODS))
        response.headers["Access-Control-Allow-Headers"] = ", ".join(sorted(ALLOWED_CORS_HEADERS))
        response.headers["Access-Control-Max-Age"] = "600"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, settings: Settings) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.production = settings.APP_ENV == "production"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = self._content_security_policy()
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if self.production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    def _content_security_policy(self) -> str:
        if self.production:
            return "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        return (
            "default-src 'none'; script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
