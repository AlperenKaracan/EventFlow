from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.reservations.cursor import (
    ReservationCursorKind,
    decode_reservation_cursor,
    encode_reservation_cursor,
    reservation_filter_fingerprint,
)
from app.reservations.models import Reservation, ReservationStatus
from app.reservations.repository import (
    get_database_now,
    get_event_for_update,
    get_owned_reservation_event_id,
    get_owned_reservation_for_update,
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
from app.shared.request_context import get_request_id


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


async def cancel_reservation(
    *,
    session: AsyncSession,
    reservation_id: UUID,
    attendee_id: UUID,
) -> None:
    try:
        event_id = await get_owned_reservation_event_id(
            session=session,
            reservation_id=reservation_id,
            attendee_id=attendee_id,
        )
        if event_id is None:
            raise resource_not_found_error()
        event = await get_event_for_update(session=session, event_id=event_id)
        if event is None:
            raise RuntimeError("reservation event disappeared inside transaction")
        reservation = await get_owned_reservation_for_update(
            session=session,
            reservation_id=reservation_id,
            attendee_id=attendee_id,
            event_id=event_id,
        )
        if reservation is None:
            raise resource_not_found_error()
        if reservation.status is not ReservationStatus.ACTIVE:
            await session.commit()
            return
        database_now = await get_database_now(session)
        if event.starts_at <= database_now:
            raise AppError(
                status_code=409,
                code="EVENT_STARTED",
                message="Başlamış etkinliğin rezervasyonu iptal edilemez.",
            )
        if event.reserved_count <= 0:
            raise RuntimeError("active reservation has no reserved_count seat")

        before = _reservation_snapshot(reservation)
        reservation.status = ReservationStatus.CANCELLED_BY_ATTENDEE
        reservation.cancelled_at = database_now
        reservation.updated_at = database_now
        event.reserved_count -= 1
        event.updated_at = database_now
        await session.flush()
        session.add(
            AuditLog(
                actor_id=attendee_id,
                action="reservation.cancelled_by_attendee",
                resource_type="reservation",
                resource_id=reservation.id,
                changes={
                    "before": before,
                    "after": _reservation_snapshot(reservation),
                },
                request_id=UUID(get_request_id()),
            )
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise


def _reservation_snapshot(reservation: Reservation) -> dict[str, Any]:
    return {
        "eventId": str(reservation.event_id),
        "attendeeId": str(reservation.attendee_id),
        "status": reservation.status.value,
        "cancelledAt": (
            reservation.cancelled_at.isoformat() if reservation.cancelled_at is not None else None
        ),
    }


def resource_not_found_error() -> AppError:
    return AppError(
        status_code=404,
        code="RESOURCE_NOT_FOUND",
        message="İstenen kaynak bulunamadı.",
    )
