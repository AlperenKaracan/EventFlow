from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from app.shared.config import Settings
from app.shared.errors import AppError

CURSOR_VERSION = 1


class CursorKind(StrEnum):
    PUBLIC_START = "public-start"
    OWNER_CREATED = "owner-created"


@dataclass(frozen=True, slots=True)
class EventCursor:
    kind: CursorKind
    timestamp: datetime
    event_id: UUID


def filter_fingerprint(filters: dict[str, Any]) -> str:
    canonical = json.dumps(filters, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def encode_event_cursor(
    *,
    kind: CursorKind,
    timestamp: datetime,
    event_id: UUID,
    filter_hash: str,
    settings: Settings,
) -> str:
    payload = {
        "v": CURSOR_VERSION,
        "kind": kind.value,
        "timestamp": timestamp.astimezone(UTC).isoformat(),
        "eventId": str(event_id),
        "filterHash": filter_hash,
    }
    encoded_payload = _base64_encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(
        settings.JWT_SECRET.get_secret_value().encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_base64_encode(signature)}"


def decode_event_cursor(
    raw_cursor: str,
    *,
    expected_kind: CursorKind,
    expected_filter_hash: str,
    settings: Settings,
) -> EventCursor:
    try:
        encoded_payload, encoded_signature = raw_cursor.split(".", maxsplit=1)
        supplied_signature = _base64_decode(encoded_signature)
        expected_signature = hmac.new(
            settings.JWT_SECRET.get_secret_value().encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("cursor signature mismatch")
        payload = json.loads(_base64_decode(encoded_payload))
        if not isinstance(payload, dict) or set(payload) != {
            "v",
            "kind",
            "timestamp",
            "eventId",
            "filterHash",
        }:
            raise ValueError("cursor payload shape mismatch")
        if payload["v"] != CURSOR_VERSION:
            raise ValueError("cursor version mismatch")
        kind = CursorKind(payload["kind"])
        if kind is not expected_kind or payload["filterHash"] != expected_filter_hash:
            raise ValueError("cursor context mismatch")
        timestamp = datetime.fromisoformat(payload["timestamp"])
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("cursor timestamp is naive")
        event_id = UUID(payload["eventId"])
    except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise invalid_cursor_error() from exc
    return EventCursor(
        kind=kind,
        timestamp=timestamp.astimezone(UTC),
        event_id=event_id,
    )


def invalid_cursor_error() -> AppError:
    return AppError(
        status_code=400,
        code="INVALID_CURSOR",
        message="Sayfalama bilgisi geçersiz.",
    )


def _base64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
