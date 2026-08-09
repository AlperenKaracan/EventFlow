from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.shared.errors import AppError

router = APIRouter(tags=["system"])


@router.get("/health", operation_id="getHealth")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", operation_id="getReadiness")
async def readiness(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    failures: list[str] = []

    try:
        async with asyncio.timeout(settings.DEPENDENCY_TIMEOUT_SECONDS):
            async with request.app.state.db_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except Exception:
        failures.append("postgresql")

    try:
        async with asyncio.timeout(settings.DEPENDENCY_TIMEOUT_SECONDS):
            await request.app.state.redis.ping()
    except Exception:
        failures.append("redis")

    if failures:
        raise AppError(
            status_code=503,
            code="DEPENDENCIES_NOT_READY",
            message="Uygulama bağımlılıkları henüz hazır değil.",
            details=[{"dependency": name, "status": "unavailable"} for name in failures],
        )
    return {"status": "ready", "dependencies": {"postgresql": "ok", "redis": "ok"}}
