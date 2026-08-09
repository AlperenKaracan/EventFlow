from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.shared.errors import AppError


def validate_event_datetime(*, starts_at: datetime, timezone_name: str) -> datetime:
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise AppError(
            status_code=422,
            code="DATETIME_OFFSET_REQUIRED",
            message="Etkinlik başlangıcı açık bir UTC offset içermelidir.",
        )

    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise AppError(
            status_code=422,
            code="INVALID_TIMEZONE",
            message="Geçerli bir IANA zaman dilimi gönderin.",
        ) from exc

    zoned_instant = starts_at.astimezone(timezone)
    if zoned_instant.utcoffset() != starts_at.utcoffset():
        raise AppError(
            status_code=422,
            code="TIMEZONE_OFFSET_MISMATCH",
            message="Tarih offset'i seçilen zaman dilimiyle uyuşmuyor.",
        )
    return starts_at.astimezone(UTC)
