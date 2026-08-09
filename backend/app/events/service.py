from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.cursor import (
    CursorKind,
    decode_event_cursor,
    encode_event_cursor,
    filter_fingerprint,
)
from app.events.repository import (
    get_owned_event,
    get_public_event,
    list_owned_events,
    list_public_events,
)
from app.events.schemas import (
    OwnerEventPage,
    OwnerEventResponse,
    PublicEventPage,
    PublicEventResponse,
)
from app.shared.config import Settings
from app.shared.errors import AppError


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


def resource_not_found_error() -> AppError:
    return AppError(
        status_code=404,
        code="RESOURCE_NOT_FOUND",
        message="İstenen kaynak bulunamadı.",
    )
