from __future__ import annotations

from logging import Logger
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.events.models import EventStatus
from app.idempotency.models import IdempotencyRecord, IdempotencyState
from app.idempotency.repository import (
    claim_idempotency_key,
    complete_idempotency_record,
    lock_idempotency_key,
)
from app.idempotency.responses import SemanticResponse, semantic_error_body
from app.observability.metrics import (
    observe_reservation_lock_wait,
    record_idempotency_request,
    record_reservation_attempt,
)
from app.reservations.cursor import (
    ReservationCursorKind,
    decode_reservation_cursor,
    encode_reservation_cursor,
    reservation_filter_fingerprint,
)
from app.reservations.models import Reservation, ReservationStatus
from app.reservations.repository import (
    add_reservation_in_savepoint,
    get_attendee_event_reservation_for_update,
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
    ReservationMutationResponse,
)
from app.shared.config import Settings
from app.shared.errors import AppError
from app.shared.request_context import get_request_id

RESERVATION_CREATE_OPERATION = "reservation.create"
IDEMPOTENCY_RETRY_AFTER_SECONDS = 1


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


async def create_reservation(
    *,
    session: AsyncSession,
    event_id: UUID,
    attendee_id: UUID,
    idempotency_key: str,
    request_hash: str,
    logger: Logger,
) -> SemanticResponse:
    request_id = UUID(get_request_id())
    try:
        owner_record, replay = await _claim_or_replay(
            session=session,
            attendee_id=attendee_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            logger=logger,
        )
        if replay is not None:
            record_reservation_attempt(outcome="replayed")
            logger.info(
                "Reservation request replayed",
                extra={
                    "event": "reservation.request.replayed",
                    "actorId": attendee_id,
                    "eventId": event_id,
                    "outcome": "replayed",
                },
            )
            return replay
        if owner_record is None:
            raise RuntimeError("idempotency claim returned neither owner nor replay")

        lock_started_at = perf_counter()
        try:
            event = await get_event_for_update(session=session, event_id=event_id)
        finally:
            observe_reservation_lock_wait(operation="create", started_at=lock_started_at)
        if event is None:
            response = await _complete_deterministic_error(
                session=session,
                record=owner_record,
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="İstenen kaynak bulunamadı.",
                request_id=request_id,
            )
            record_reservation_attempt(outcome="not_found")
            return response
        database_now = await get_database_now(session)
        if event.status is not EventStatus.ACTIVE:
            response = await _complete_deterministic_error(
                session=session,
                record=owner_record,
                status_code=409,
                code="EVENT_NOT_ACTIVE",
                message="Yalnızca aktif etkinliklere rezervasyon yapılabilir.",
                request_id=request_id,
            )
            record_reservation_attempt(outcome="inactive")
            return response
        if event.starts_at <= database_now:
            response = await _complete_deterministic_error(
                session=session,
                record=owner_record,
                status_code=409,
                code="EVENT_STARTED",
                message="Başlamış etkinliğe rezervasyon yapılamaz.",
                request_id=request_id,
            )
            record_reservation_attempt(outcome="started")
            return response

        reservation = await get_attendee_event_reservation_for_update(
            session=session,
            event_id=event_id,
            attendee_id=attendee_id,
        )
        if reservation is not None and reservation.status is ReservationStatus.ACTIVE:
            response = await _complete_deterministic_error(
                session=session,
                record=owner_record,
                status_code=409,
                code="ALREADY_RESERVED",
                message="Bu etkinlik için zaten aktif rezervasyonunuz var.",
                request_id=request_id,
            )
            record_reservation_attempt(outcome="duplicate")
            return response
        if event.reserved_count >= event.capacity:
            response = await _complete_deterministic_error(
                session=session,
                record=owner_record,
                status_code=409,
                code="EVENT_FULL",
                message="Etkinlik kapasitesi dolu.",
                request_id=request_id,
            )
            record_reservation_attempt(outcome="full")
            return response

        before = _reservation_snapshot(reservation) if reservation is not None else None
        action = "reservation.reactivated"
        if reservation is None:
            reservation = Reservation(
                event_id=event_id,
                attendee_id=attendee_id,
                status=ReservationStatus.ACTIVE,
                updated_at=database_now,
            )
            inserted = await add_reservation_in_savepoint(
                session=session,
                reservation=reservation,
            )
            if not inserted:
                conflicting = await get_attendee_event_reservation_for_update(
                    session=session,
                    event_id=event_id,
                    attendee_id=attendee_id,
                )
                if conflicting is None:
                    raise RuntimeError("reservation insert failed without a conflicting row")
                response = await _complete_deterministic_error(
                    session=session,
                    record=owner_record,
                    status_code=409,
                    code="ALREADY_RESERVED",
                    message="Bu etkinlik için zaten rezervasyon kaydı bulunuyor.",
                    request_id=request_id,
                )
                record_reservation_attempt(outcome="duplicate")
                return response
            action = "reservation.created"
        else:
            reservation.status = ReservationStatus.ACTIVE
            reservation.cancelled_at = None
            reservation.updated_at = database_now

        event.reserved_count += 1
        event.updated_at = database_now
        await session.flush()
        session.add(
            AuditLog(
                actor_id=attendee_id,
                action=action,
                resource_type="reservation",
                resource_id=reservation.id,
                changes={
                    **({"before": before} if before is not None else {}),
                    "after": _reservation_snapshot(reservation),
                },
                request_id=request_id,
            )
        )
        body = ReservationMutationResponse.from_reservation(reservation).model_dump(
            mode="json",
            by_alias=True,
        )
        complete_idempotency_record(
            owner_record,
            status_code=201,
            response_body=body,
            original_request_id=request_id,
        )
        await session.commit()
        record_reservation_attempt(
            outcome="created" if action == "reservation.created" else "reactivated"
        )
        logger.info(
            "Reservation mutation completed",
            extra={
                "event": action,
                "actorId": attendee_id,
                "eventId": event_id,
                "reservationId": reservation.id,
                "outcome": "created" if action == "reservation.created" else "reactivated",
            },
        )
        return SemanticResponse(
            status_code=201,
            body=body,
            original_request_id=request_id,
            replayed=False,
        )
    except Exception:
        await session.rollback()
        raise


async def _claim_or_replay(
    *,
    session: AsyncSession,
    attendee_id: UUID,
    idempotency_key: str,
    request_hash: str,
    logger: Logger,
) -> tuple[IdempotencyRecord | None, SemanticResponse | None]:
    for attempt in range(2):
        record = await claim_idempotency_key(
            session=session,
            user_id=attendee_id,
            operation=RESERVATION_CREATE_OPERATION,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if record is not None:
            record_idempotency_request(outcome="owner")
            return record, None
        record = await lock_idempotency_key(
            session=session,
            user_id=attendee_id,
            operation=RESERVATION_CREATE_OPERATION,
            key=idempotency_key,
        )
        if record is None:
            await session.rollback()
            if attempt == 0:
                continue
            break
        if record.request_hash != request_hash:
            await session.rollback()
            record_idempotency_request(outcome="conflict")
            raise AppError(
                status_code=409,
                code="IDEMPOTENCY_KEY_REUSED",
                message="Idempotency-Key farklı bir istek için kullanılmış.",
            )
        if record.state is IdempotencyState.COMPLETED:
            if (
                record.response_status is None
                or record.response_body is None
                or record.original_request_id is None
            ):
                raise RuntimeError("completed idempotency record has no response snapshot")
            replay = SemanticResponse(
                status_code=record.response_status,
                body=record.response_body,
                original_request_id=record.original_request_id,
                replayed=True,
            )
            await session.commit()
            record_idempotency_request(outcome="replay")
            return None, replay
        await session.rollback()
        record_idempotency_request(outcome="in_progress")
        logger.warning(
            "Visible idempotency record remained in processing state",
            extra={"event": "idempotency.processing_visible"},
        )
        raise AppError(
            status_code=409,
            code="IDEMPOTENCY_IN_PROGRESS",
            message="Aynı anahtarla başlatılan işlem henüz tamamlanmadı.",
            headers={"Retry-After": str(IDEMPOTENCY_RETRY_AFTER_SECONDS)},
        )

    logger.warning(
        "Idempotency record disappeared while resolving a conflict",
        extra={"event": "idempotency.record_missing"},
    )
    record_idempotency_request(outcome="in_progress")
    raise AppError(
        status_code=409,
        code="IDEMPOTENCY_IN_PROGRESS",
        message="İstek durumu geçici olarak doğrulanamıyor.",
        headers={"Retry-After": str(IDEMPOTENCY_RETRY_AFTER_SECONDS)},
    )


async def _complete_deterministic_error(
    *,
    session: AsyncSession,
    record: IdempotencyRecord,
    status_code: int,
    code: str,
    message: str,
    request_id: UUID,
) -> SemanticResponse:
    body = semantic_error_body(code=code, message=message)
    complete_idempotency_record(
        record,
        status_code=status_code,
        response_body=body,
        original_request_id=request_id,
    )
    await session.commit()
    return SemanticResponse(
        status_code=status_code,
        body=body,
        original_request_id=request_id,
        replayed=False,
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
        lock_started_at = perf_counter()
        try:
            event = await get_event_for_update(session=session, event_id=event_id)
        finally:
            observe_reservation_lock_wait(operation="cancel", started_at=lock_started_at)
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
