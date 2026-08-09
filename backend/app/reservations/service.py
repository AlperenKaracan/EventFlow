from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.reservations.cursor import (
    ReservationCursorKind,
    decode_reservation_cursor,
    encode_reservation_cursor,
    reservation_filter_fingerprint,
)
from app.reservations.repository import (
    list_active_event_attendees,
    list_attendee_reservations,
    owned_event_exists,
)
from app.reservations.schemas import (
    EventAttendeePage,
    EventAttendeeResponse,
    ReservationHistoryPage,
    ReservationHistoryResponse,
)
from app.shared.config import Settings
from app.shared.errors import AppError


async def get_reservation_history_page(
    *,
    session: AsyncSession,
    attendee_id: UUID,
    limit: int,
    raw_cursor: str | None,
    settings: Settings,
) -> ReservationHistoryPage:
    fingerprint = reservation_filter_fingerprint({"attendeeId": str(attendee_id)})
    cursor = (
        decode_reservation_cursor(
            raw_cursor,
            expected_kind=ReservationCursorKind.ATTENDEE_HISTORY,
            expected_filter_hash=fingerprint,
            settings=settings,
        )
        if raw_cursor is not None
        else None
    )
    records = await list_attendee_reservations(
        session=session,
        attendee_id=attendee_id,
        limit=limit + 1,
        cursor=cursor,
    )
    has_more = len(records) > limit
    page_records = records[:limit]
    next_cursor = None
    if has_more and page_records:
        last = page_records[-1]
        next_cursor = encode_reservation_cursor(
            kind=ReservationCursorKind.ATTENDEE_HISTORY,
            timestamp=last.created_at,
            reservation_id=last.id,
            filter_hash=fingerprint,
            settings=settings,
        )
    return ReservationHistoryPage(
        items=[ReservationHistoryResponse.from_record(record) for record in page_records],
        next_cursor=next_cursor,
        has_more=has_more,
    )


async def get_event_attendee_page(
    *,
    session: AsyncSession,
    event_id: UUID,
    organizer_id: UUID,
    limit: int,
    raw_cursor: str | None,
    settings: Settings,
) -> EventAttendeePage:
    if not await owned_event_exists(
        session=session,
        event_id=event_id,
        organizer_id=organizer_id,
    ):
        raise resource_not_found_error()
    fingerprint = reservation_filter_fingerprint(
        {"eventId": str(event_id), "organizerId": str(organizer_id)}
    )
    cursor = (
        decode_reservation_cursor(
            raw_cursor,
            expected_kind=ReservationCursorKind.EVENT_ATTENDEES,
            expected_filter_hash=fingerprint,
            settings=settings,
        )
        if raw_cursor is not None
        else None
    )
    records = await list_active_event_attendees(
        session=session,
        event_id=event_id,
        limit=limit + 1,
        cursor=cursor,
    )
    has_more = len(records) > limit
    page_records = records[:limit]
    next_cursor = None
    if has_more and page_records:
        last = page_records[-1]
        next_cursor = encode_reservation_cursor(
            kind=ReservationCursorKind.EVENT_ATTENDEES,
            timestamp=last.reserved_at,
            reservation_id=last.reservation_id,
            filter_hash=fingerprint,
            settings=settings,
        )
    return EventAttendeePage(
        items=[EventAttendeeResponse.from_record(record) for record in page_records],
        next_cursor=next_cursor,
        has_more=has_more,
    )


def resource_not_found_error() -> AppError:
    return AppError(
        status_code=404,
        code="RESOURCE_NOT_FOUND",
        message="İstenen kaynak bulunamadı.",
    )
