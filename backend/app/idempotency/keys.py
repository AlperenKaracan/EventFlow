from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from uuid import UUID

from app.shared.errors import AppError

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,200}$")


def validate_idempotency_key(raw_key: str) -> str:
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(raw_key):
        raise AppError(
            status_code=422,
            code="INVALID_IDEMPOTENCY_KEY",
            message="Idempotency-Key 1-200 güvenli karakter içermelidir.",
        )
    return raw_key


def reservation_create_request_hash(*, event_id: UUID, body: dict[str, Any]) -> str:
    canonical = json.dumps(
        {
            "method": "POST",
            "route": "reservation.create",
            "eventId": str(event_id),
            "body": body,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
