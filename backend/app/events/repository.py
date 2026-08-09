from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category
from app.events.cursor import EventCursor
from app.events.models import Event, EventStatus


@dataclass(frozen=True, slots=True)
class CategoryRecord:
    id: UUID
    slug: str
    name: str


@dataclass(frozen=True, slots=True)
class EventRecord:
    id: UUID
    category: CategoryRecord
    title: str
    description: str
    location: str
    starts_at: datetime
    timezone: str
    capacity: int
    reserved_count: int
    status: EventStatus
    version: int
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None


async def list_active_categories(session: AsyncSession) -> list[CategoryRecord]:
    categories = (
        await session.scalars(
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.name.asc(), Category.id.asc())
        )
    ).all()
    return [CategoryRecord(id=row.id, slug=row.slug, name=row.name) for row in categories]


async def list_public_events(
    *, session: AsyncSession, limit: int, cursor: EventCursor | None
) -> list[EventRecord]:
    statement = (
        select(Event, Category)
        .join(Category, Category.id == Event.category_id)
        .where(
            Event.status == EventStatus.ACTIVE,
            Event.starts_at > func.now(),
        )
        .order_by(Event.starts_at.asc(), Event.id.asc())
        .limit(limit)
    )
    if cursor is not None:
        statement = statement.where(
            or_(
                Event.starts_at > cursor.timestamp,
                and_(
                    Event.starts_at == cursor.timestamp,
                    Event.id > cursor.event_id,
                ),
            )
        )
    rows = (await session.execute(statement)).all()
    return [_to_event_record(event, category) for event, category in rows]


async def get_public_event(*, session: AsyncSession, event_id: UUID) -> EventRecord | None:
    row = (
        await session.execute(
            select(Event, Category)
            .join(Category, Category.id == Event.category_id)
            .where(
                Event.id == event_id,
                Event.status == EventStatus.ACTIVE,
            )
        )
    ).one_or_none()
    return _to_event_record(*row) if row is not None else None


async def list_owned_events(
    *,
    session: AsyncSession,
    organizer_id: UUID,
    limit: int,
    cursor: EventCursor | None,
) -> list[EventRecord]:
    statement = (
        select(Event, Category)
        .join(Category, Category.id == Event.category_id)
        .where(Event.organizer_id == organizer_id)
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(limit)
    )
    if cursor is not None:
        statement = statement.where(
            or_(
                Event.created_at < cursor.timestamp,
                and_(
                    Event.created_at == cursor.timestamp,
                    Event.id < cursor.event_id,
                ),
            )
        )
    rows = (await session.execute(statement)).all()
    return [_to_event_record(event, category) for event, category in rows]


async def get_owned_event(
    *, session: AsyncSession, event_id: UUID, organizer_id: UUID
) -> EventRecord | None:
    row = (
        await session.execute(
            select(Event, Category)
            .join(Category, Category.id == Event.category_id)
            .where(
                Event.id == event_id,
                Event.organizer_id == organizer_id,
            )
        )
    ).one_or_none()
    return _to_event_record(*row) if row is not None else None


def _to_event_record(event: Event, category: Category) -> EventRecord:
    return EventRecord(
        id=event.id,
        category=CategoryRecord(id=category.id, slug=category.slug, name=category.name),
        title=event.title,
        description=event.description,
        location=event.location,
        starts_at=event.starts_at,
        timezone=event.timezone,
        capacity=event.capacity,
        reserved_count=event.reserved_count,
        status=event.status,
        version=event.version,
        created_at=event.created_at,
        updated_at=event.updated_at,
        cancelled_at=event.cancelled_at,
    )
