from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import Date, and_, func, or_, select
from sqlalchemy import cast as sa_cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category
from app.events.cursor import EventCursor
from app.events.models import Event, EventStatus
from app.reservations.models import Reservation, ReservationStatus


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


@dataclass(frozen=True, slots=True)
class PublicEventFilters:
    query: str | None = None
    category_slug: str | None = None
    date_from: date | None = None
    date_to: date | None = None


async def list_active_categories(session: AsyncSession) -> list[CategoryRecord]:
    categories = (
        await session.scalars(
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.name.asc(), Category.id.asc())
        )
    ).all()
    return [CategoryRecord(id=row.id, slug=row.slug, name=row.name) for row in categories]


async def get_active_category(*, session: AsyncSession, category_id: UUID) -> CategoryRecord | None:
    category = await session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
    )
    return (
        CategoryRecord(id=category.id, slug=category.slug, name=category.name)
        if category is not None
        else None
    )


async def get_category(*, session: AsyncSession, category_id: UUID) -> CategoryRecord:
    category = await session.get(Category, category_id)
    if category is None:
        raise RuntimeError("event category disappeared inside transaction")
    return CategoryRecord(id=category.id, slug=category.slug, name=category.name)


async def get_database_now(session: AsyncSession) -> datetime:
    value = await session.scalar(select(func.now()))
    if value is None:
        raise RuntimeError("database clock did not return a value")
    return value


async def add_event(*, session: AsyncSession, event: Event) -> None:
    session.add(event)
    await session.flush()


async def get_owned_event_for_update(
    *,
    session: AsyncSession,
    event_id: UUID,
    organizer_id: UUID,
    expected_version: int,
) -> Event | None:
    return cast(
        Event | None,
        await session.scalar(
            select(Event)
            .where(
                Event.id == event_id,
                Event.organizer_id == organizer_id,
                Event.version == expected_version,
            )
            .with_for_update()
        ),
    )


async def lock_active_event_reservations(
    *, session: AsyncSession, event_id: UUID
) -> list[Reservation]:
    return list(
        (
            await session.scalars(
                select(Reservation)
                .where(
                    Reservation.event_id == event_id,
                    Reservation.status == ReservationStatus.ACTIVE,
                )
                .order_by(Reservation.id.asc())
                .with_for_update()
            )
        ).all()
    )


def event_to_record(*, event: Event, category: CategoryRecord) -> EventRecord:
    return EventRecord(
        id=event.id,
        category=category,
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


async def list_public_events(
    *,
    session: AsyncSession,
    limit: int,
    cursor: EventCursor | None,
    filters: PublicEventFilters,
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
    if filters.query is not None:
        search_query = func.websearch_to_tsquery("pg_catalog.turkish", filters.query)
        statement = statement.where(Event.search_vector.bool_op("@@")(search_query))
    if filters.category_slug is not None:
        statement = statement.where(Category.slug == filters.category_slug)
    local_event_date = sa_cast(func.timezone(Event.timezone, Event.starts_at), Date)
    if filters.date_from is not None:
        statement = statement.where(local_event_date >= filters.date_from)
    if filters.date_to is not None:
        statement = statement.where(local_event_date <= filters.date_to)
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
    return event_to_record(
        event=event,
        category=CategoryRecord(id=category.id, slug=category.slug, name=category.name),
    )
