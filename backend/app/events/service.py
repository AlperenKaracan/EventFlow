from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.events.cursor import (
    CursorKind,
    decode_event_cursor,
    encode_event_cursor,
    filter_fingerprint,
)
from app.events.models import Event, EventStatus
from app.events.repository import (
    add_event,
    event_to_record,
    get_active_category,
    get_database_now,
    get_owned_event,
    get_owned_event_for_update,
    get_public_event,
    list_owned_events,
    list_public_events,
)
from app.events.schemas import (
    EventCreateRequest,
    EventUpdateRequest,
    OwnerEventPage,
    OwnerEventResponse,
    PublicEventPage,
    PublicEventResponse,
)
from app.events.timezone import validate_event_datetime
from app.shared.config import Settings
from app.shared.errors import AppError
from app.shared.request_context import get_request_id


async def get_public_event_page(
    *,
    session: AsyncSession,
    limit: int,
    raw_cursor: str | None,
    settings: Settings,
) -> PublicEventPage:
    fingerprint = filter_fingerprint({})
    cursor = (
        decode_event_cursor(
            raw_cursor,
            expected_kind=CursorKind.PUBLIC_START,
            expected_filter_hash=fingerprint,
            settings=settings,
        )
        if raw_cursor is not None
        else None
    )
    records = await list_public_events(session=session, limit=limit + 1, cursor=cursor)
    has_more = len(records) > limit
    page_records = records[:limit]
    next_cursor = None
    if has_more and page_records:
        last = page_records[-1]
        next_cursor = encode_event_cursor(
            kind=CursorKind.PUBLIC_START,
            timestamp=last.starts_at,
            event_id=last.id,
            filter_hash=fingerprint,
            settings=settings,
        )
    return PublicEventPage(
        items=[PublicEventResponse.from_record(record) for record in page_records],
        next_cursor=next_cursor,
        has_more=has_more,
    )


async def get_public_event_detail(*, session: AsyncSession, event_id: UUID) -> PublicEventResponse:
    record = await get_public_event(session=session, event_id=event_id)
    if record is None:
        raise resource_not_found_error()
    return PublicEventResponse.from_record(record)


async def get_owner_event_page(
    *,
    session: AsyncSession,
    organizer_id: UUID,
    limit: int,
    raw_cursor: str | None,
    settings: Settings,
) -> OwnerEventPage:
    fingerprint = filter_fingerprint({"organizerId": str(organizer_id)})
    cursor = (
        decode_event_cursor(
            raw_cursor,
            expected_kind=CursorKind.OWNER_CREATED,
            expected_filter_hash=fingerprint,
            settings=settings,
        )
        if raw_cursor is not None
        else None
    )
    records = await list_owned_events(
        session=session,
        organizer_id=organizer_id,
        limit=limit + 1,
        cursor=cursor,
    )
    has_more = len(records) > limit
    page_records = records[:limit]
    next_cursor = None
    if has_more and page_records:
        last = page_records[-1]
        next_cursor = encode_event_cursor(
            kind=CursorKind.OWNER_CREATED,
            timestamp=last.created_at,
            event_id=last.id,
            filter_hash=fingerprint,
            settings=settings,
        )
    return OwnerEventPage(
        items=[OwnerEventResponse.from_record(record) for record in page_records],
        next_cursor=next_cursor,
        has_more=has_more,
    )


async def get_owner_event_detail(
    *, session: AsyncSession, event_id: UUID, organizer_id: UUID
) -> OwnerEventResponse:
    record = await get_owned_event(
        session=session,
        event_id=event_id,
        organizer_id=organizer_id,
    )
    if record is None:
        raise resource_not_found_error()
    return OwnerEventResponse.from_record(record)


async def create_event(
    *,
    payload: EventCreateRequest,
    organizer_id: UUID,
    session: AsyncSession,
) -> OwnerEventResponse:
    starts_at = validate_event_datetime(
        starts_at=payload.starts_at,
        timezone_name=payload.timezone,
    )
    category = await get_active_category(session=session, category_id=payload.category_id)
    if category is None:
        raise invalid_category_error()
    database_now = await get_database_now(session)
    if starts_at <= database_now:
        raise event_start_not_future_error()

    event = Event(
        organizer_id=organizer_id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        starts_at=starts_at,
        timezone=payload.timezone,
        capacity=payload.capacity,
        reserved_count=0,
        status=EventStatus.ACTIVE,
        version=1,
    )
    try:
        await add_event(session=session, event=event)
        session.add(
            _audit_log(
                actor_id=organizer_id,
                action="event.created",
                resource_id=event.id,
                changes={"after": _event_snapshot(event)},
            )
        )
        await session.flush()
        record = event_to_record(event=event, category=category)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return OwnerEventResponse.from_record(record)


async def update_event(
    *,
    event_id: UUID,
    payload: EventUpdateRequest,
    organizer_id: UUID,
    session: AsyncSession,
) -> OwnerEventResponse:
    event = await _get_owned_event_for_mutation(
        session=session,
        event_id=event_id,
        organizer_id=organizer_id,
        expected_version=payload.expected_version,
    )
    _validate_mutable_event(event=event, expected_version=payload.expected_version)
    database_now = await get_database_now(session)
    if event.starts_at <= database_now:
        raise event_started_error()

    category_id = payload.category_id or event.category_id
    category = await get_active_category(session=session, category_id=category_id)
    if category is None:
        raise invalid_category_error()
    if payload.starts_at is not None and payload.timezone is not None:
        starts_at = validate_event_datetime(
            starts_at=payload.starts_at,
            timezone_name=payload.timezone,
        )
        timezone_name = payload.timezone
    else:
        starts_at = event.starts_at
        timezone_name = event.timezone
    if starts_at <= database_now:
        raise event_start_not_future_error()
    capacity = payload.capacity if payload.capacity is not None else event.capacity
    if capacity < event.reserved_count:
        raise capacity_below_reservations_error()

    before = _event_snapshot(event)
    event.category_id = category_id
    event.title = payload.title if payload.title is not None else event.title
    event.description = (
        payload.description if payload.description is not None else event.description
    )
    event.location = payload.location if payload.location is not None else event.location
    event.starts_at = starts_at
    event.timezone = timezone_name
    event.capacity = capacity
    event.version += 1
    event.updated_at = database_now
    try:
        await session.flush()
        session.add(
            _audit_log(
                actor_id=organizer_id,
                action="event.updated",
                resource_id=event.id,
                changes={"before": before, "after": _event_snapshot(event)},
            )
        )
        await session.flush()
        record = event_to_record(event=event, category=category)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return OwnerEventResponse.from_record(record)


async def cancel_event(
    *,
    event_id: UUID,
    expected_version: int,
    organizer_id: UUID,
    session: AsyncSession,
) -> None:
    event = await _get_owned_event_for_mutation(
        session=session,
        event_id=event_id,
        organizer_id=organizer_id,
        expected_version=expected_version,
    )
    _validate_mutable_event(event=event, expected_version=expected_version)
    database_now = await get_database_now(session)
    if event.starts_at <= database_now:
        raise event_started_error()

    before = _event_snapshot(event)
    event.status = EventStatus.CANCELLED
    event.cancelled_at = database_now
    event.updated_at = database_now
    event.version += 1
    try:
        await session.flush()
        session.add(
            _audit_log(
                actor_id=organizer_id,
                action="event.cancelled",
                resource_id=event.id,
                changes={"before": before, "after": _event_snapshot(event)},
            )
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise


def _validate_mutable_event(*, event: Event, expected_version: int) -> None:
    if event.version != expected_version:
        raise AppError(
            status_code=409,
            code="EVENT_VERSION_CONFLICT",
            message="Etkinlik başka bir işlem tarafından değiştirilmiş.",
        )
    if event.status is not EventStatus.ACTIVE:
        raise AppError(
            status_code=409,
            code="EVENT_NOT_ACTIVE",
            message="Yalnız aktif etkinlikler değiştirilebilir.",
        )


async def _get_owned_event_for_mutation(
    *,
    session: AsyncSession,
    event_id: UUID,
    organizer_id: UUID,
    expected_version: int,
) -> Event:
    event = await get_owned_event_for_update(
        session=session,
        event_id=event_id,
        organizer_id=organizer_id,
        expected_version=expected_version,
    )
    if event is not None:
        return event
    existing = await get_owned_event(
        session=session,
        event_id=event_id,
        organizer_id=organizer_id,
    )
    if existing is None:
        raise resource_not_found_error()
    raise AppError(
        status_code=409,
        code="EVENT_VERSION_CONFLICT",
        message="Etkinlik başka bir işlem tarafından değiştirilmiş.",
    )


def _event_snapshot(event: Event) -> dict[str, Any]:
    return {
        "categoryId": str(event.category_id),
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "startsAt": event.starts_at.isoformat(),
        "timezone": event.timezone,
        "capacity": event.capacity,
        "reservedCount": event.reserved_count,
        "status": event.status.value,
        "version": event.version,
    }


def _audit_log(
    *, actor_id: UUID, action: str, resource_id: UUID, changes: dict[str, Any]
) -> AuditLog:
    return AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type="event",
        resource_id=resource_id,
        changes=changes,
        request_id=UUID(get_request_id()),
    )


def resource_not_found_error() -> AppError:
    return AppError(
        status_code=404,
        code="RESOURCE_NOT_FOUND",
        message="İstenen kaynak bulunamadı.",
    )


def invalid_category_error() -> AppError:
    return AppError(
        status_code=422,
        code="INVALID_CATEGORY",
        message="Aktif bir kategori seçin.",
    )


def event_start_not_future_error() -> AppError:
    return AppError(
        status_code=422,
        code="EVENT_START_NOT_FUTURE",
        message="Etkinlik başlangıcı gelecekte olmalıdır.",
    )


def event_started_error() -> AppError:
    return AppError(
        status_code=409,
        code="EVENT_STARTED",
        message="Başlamış etkinlik değiştirilemez.",
    )


def capacity_below_reservations_error() -> AppError:
    return AppError(
        status_code=409,
        code="CAPACITY_BELOW_RESERVATIONS",
        message="Kapasite mevcut rezervasyon sayısının altına indirilemez.",
    )
