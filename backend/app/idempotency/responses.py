from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SemanticResponse:
    status_code: int
    body: dict[str, Any]
    original_request_id: UUID
    replayed: bool

    def materialize_body(self, *, current_request_id: UUID) -> dict[str, Any]:
        body = deepcopy(self.body)
        error = body.get("error")
        if isinstance(error, dict):
            error["requestId"] = str(current_request_id)
        return body

    def replay_headers(self) -> dict[str, str]:
        if not self.replayed:
            return {}
        return {
            "Idempotent-Replayed": "true",
            "Idempotency-Original-Request-ID": str(self.original_request_id),
        }


def semantic_error_body(*, code: str, message: str) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": [],
        }
    }
