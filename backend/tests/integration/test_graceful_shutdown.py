from __future__ import annotations

import asyncio
import os
import signal
import socket
import sys
from pathlib import Path

import httpx
import pytest


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


async def _wait_for_health(client: httpx.AsyncClient) -> None:
    for _ in range(100):
        try:
            response = await client.get("/health")
            if response.status_code == 200:
                return
        except httpx.TransportError:
            pass
        await asyncio.sleep(0.05)
    raise AssertionError("graceful test server did not become healthy")


async def _wait_for_marker(marker: Path) -> None:
    for _ in range(100):
        if await asyncio.to_thread(marker.exists):
            return
        await asyncio.sleep(0.02)
    raise AssertionError(f"marker was not created: {marker}")


@pytest.mark.skipif(os.name == "nt", reason="Windows cannot deliver POSIX SIGTERM")
async def test_sigterm_drains_inflight_request_before_lifespan_shutdown(
    tmp_path: Path,
) -> None:
    port = _free_port()
    started_marker = tmp_path / "started"
    stopped_marker = tmp_path / "stopped"
    environment = os.environ.copy()
    environment.update(
        {
            "APP_ENV": "test",
            "DATABASE_URL": "postgresql+asyncpg://eventflow:eventflow@127.0.0.1:1/eventflow",
            "REDIS_URL": "redis://127.0.0.1:1/0",
            "JWT_SECRET": "graceful-test-secret-that-is-at-least-32-characters",
            "JWT_ISSUER": "eventflow-graceful-test",
            "JWT_AUDIENCE": "eventflow-graceful-test",
            "ACCESS_TOKEN_TTL_MINUTES": "15",
            "REFRESH_TOKEN_TTL_DAYS": "7",
            "REFRESH_TOKEN_REVOKED_RETENTION_DAYS": "7",
            "CORS_ALLOWED_ORIGINS": "http://localhost:5173",
            "LOG_LEVEL": "INFO",
            "LOGIN_RATE_LIMIT_PER_MINUTE": "5",
            "RESERVATION_RATE_LIMIT_PER_MINUTE": "10",
            "DEPENDENCY_TIMEOUT_SECONDS": "1",
            "GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS": "5",
            "FRONTEND_PUBLIC_URL": "http://localhost:5173",
            "BACKEND_PUBLIC_URL": f"http://localhost:{port}",
            "GRACEFUL_STARTED_MARKER": str(started_marker),
            "GRACEFUL_STOPPED_MARKER": str(stopped_marker),
            "GRACEFUL_TEST_PORT": str(port),
        }
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "tests.support.graceful_server",
        cwd=Path(__file__).parents[2],
        env=environment,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=10) as client:
            await _wait_for_health(client)
            request = asyncio.create_task(client.get("/slow"))
            await _wait_for_marker(started_marker)
            process.send_signal(signal.SIGTERM)

            response = await request
            assert response.status_code == 200
            assert response.json() == {"status": "completed"}

        return_code = await asyncio.wait_for(process.wait(), timeout=5)
        stopped = await asyncio.to_thread(stopped_marker.read_text, encoding="utf-8")
        assert stopped == "stopped"
        # Uvicorn 0.52+ restores and re-raises the captured shutdown signal after
        # the request drain and lifespan shutdown have completed.
        assert return_code in {0, -signal.SIGTERM}
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
