from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.request_context import REQUEST_ID_HEADER, get_request_id


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str = Field(serialization_alias="requestId")
    details: list[dict[str, Any]]


class ErrorEnvelope(BaseModel):
    error: ErrorBody


@dataclass(slots=True)
class AppError(Exception):
    status_code: int
    code: str
    message: str
    details: list[dict[str, Any]] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


def error_payload(
    *, code: str, message: str, details: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "requestId": get_request_id(),
            "details": details or [],
        }
    }


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = get_request_id()
    response_headers = {REQUEST_ID_HEADER: request_id}
    response_headers.update(headers or {})
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
                "details": details or [],
            }
        },
        headers=response_headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return error_response(
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="İstenen kaynak bulunamadı.",
            )
        return error_response(
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message="İstek tamamlanamadı.",
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        safe_details = [
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Gönderilen alanları kontrol edin.",
            details=safe_details,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request.app.state.logger.exception(
            "Unhandled request exception",
            extra={"event": "request.unhandled_exception", "errorCode": "INTERNAL_ERROR"},
        )
        return error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Beklenmeyen bir hata oluştu.",
        )
