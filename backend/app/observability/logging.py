from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from app.shared.request_context import peek_request_id

_RESERVED_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Serialize LogRecord values as one redaction-safe JSON object per line."""

    def __init__(self, *, service: str = "backend", environment: str | None = None) -> None:
        super().__init__()
        self.service = service
        self.environment = environment or os.getenv("APP_ENV", "unknown")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "environment": self.environment,
            "requestId": peek_request_id(),
            "event": getattr(record, "event", record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_FIELDS and key not in {"event", "exc_info", "exc_text"}:
                payload[key] = value
        if record.exc_info:
            exception_type = record.exc_info[0]
            if exception_type is not None:
                payload["exceptionType"] = exception_type.__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def configure_logging(*, level: str, environment: str) -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service="backend", environment=environment))

    logger = logging.getLogger("eventflow")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
