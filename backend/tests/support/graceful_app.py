from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI


def _marker_path(variable: str) -> Path:
    value = os.environ.get(variable)
    if value is None:
        raise RuntimeError(f"{variable} is required")
    return Path(value)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        marker = _marker_path("GRACEFUL_STOPPED_MARKER")
        await asyncio.to_thread(marker.write_text, "stopped", encoding="utf-8")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/slow")
async def slow_request() -> dict[str, str]:
    marker = _marker_path("GRACEFUL_STARTED_MARKER")
    await asyncio.to_thread(marker.write_text, "started", encoding="utf-8")
    await asyncio.sleep(1)
    return {"status": "completed"}
