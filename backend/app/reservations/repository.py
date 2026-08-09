from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import Event, EventStatus
from app.reservations.cursor import ReservationCursor
from app.reservations.models import Reservation, ReservationStatus
from app.users.models import User


@dataclass(frozen=True, slots=True)
class ReservationEventRecord:
    id: UUID
    title: str
    location: str
    starts_at: datetime
    timezone: str
    status: EventStatus


@dataclass(frozen=True, slots=True)
class ReservationHistoryRecord:
    id: UUID
    status: ReservationStatus
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None
    event: ReservationEventRecord


@dataclass(frozen=True, slots=True)
class EventAttendeeRecord:
    reservation_id: UUID
    attendee_id: UUID
    full_name: str
    email: str
    reserved_at: datetime


async def owned_event_exists(*, session: AsyncSession, event_id: UUID, organizer_id: UUID) -> bool:
    return (
        await session.scalar(
            select(Event.id).where(
                Event.id == event_id,
                Event.organizer_id == organizer_id,
            )
        )
    ) is not None


async def get_owned_reservation_event_id(
    *, session: AsyncSession, reservation_id: UUID, attendee_id: UUID
) -> UUID | None:
    return cast(
        UUID | None,
        await session.scalar(
            select(Reservation.event_id).where(
                Reservation.id == reservation_id,
                Reservation.attendee_id == attendee_id,
            )
        ),
    )


async def get_event_for_update(*, session: AsyncSession, event_id: UUID) -> Event | None:
    return cast(
        Event | None,
        await session.scalar(select(Event).where(Event.id == event_id).with_for_update()),
    )


async def get_attendee_event_reservation_for_update(
    *, session: AsyncSession, event_id: UUID, attendee_id: UUID
) -> Reservation | None:
    return cast(
        Reservation | None,
        await session.scalar(
            select(Reservation)
            .where(
                Reservation.event_id == event_id,
                Reservation.attendee_id == attendee_id,
            )
            .with_for_update()
        ),
    )


async def add_reservation_in_savepoint(
    *, session: AsyncSession, reservation: Reservation
) -> bool:
    try:
        async with session.begin_nested():
            session.add(reservation)
            await session.flush()
    except IntegrityError as exc:
        driver_error = getattr(exc.orig, "__cause__", None)
        constraint_name = getattr(driver_error, "constraint_name", None)
        if constraint_name != "uq_reservations_event_attendee":
            raise
        return False
    return True


async def get_owned_reservation_for_update(
    *,
    session: AsyncSession,
    reservation_id: UUID,
    attendee_id: UUID,
    event_id: UUID,
) -> Reservation | None:
    return cast(
        Reservation | None,
        await session.scalar(
            select(Reservation)
            .where(
                Reservation.id == reservation_id,
                Reservation.attendee_id == attendee_id,
                Reservation.event_id == event_id,
            )
            .with_for_update()
        ),
    )


async def get_database_now(session: AsyncSession) -> datetime:
    value = await session.scalar(select(func.now()))
    if value is None:
        raise RuntimeError("database clock did not return a value")
    return value


async def list_attendee_reservations(
    *,
    session: AsyncSession,
    attendee_id: UUID,
    limit: int,
    cursor: ReservationCursor | None,
) -> list[ReservationHistoryRecord]:
    statement = (
        select(Reservation, Event)
        .join(Event, Event.id == Reservation.event_id)
        .where(Reservation.attendee_id == attendee_id)
        .order_by(Reservation.created_at.desc(), Reservation.id.desc())
        .limit(limit)
    )
    if cursor is not None:
        statement = statement.where(
            or_(
                Reservation.created_at < cursor.timestamp,
                and_(
                    Reservation.created_at == cursor.timestamp,
                    Reservation.id < cursor.reservation_id,
                ),
            )
        )
    rows = (await session.execute(statement)).all()
    return [_history_record(reservation, event) for reservation, event in rows]


async def list_active_event_attendees(
    *,
    session: AsyncSession,
    event_id: UUID,
    limit: int,
    cursor: ReservationCursor | None,
) -> list[EventAttendeeRecord]:
    statement = (
        select(Reservation, User)
        .join(User, User.id == Reservation.attendee_id)
        .where(
            Reservation.event_id == event_id,
            Reservation.status == ReservationStatus.ACTIVE,
        )
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
        .limit(limit)
    )
    if cursor is not None:
        statement = statement.where(
            or_(
                Reservation.created_at > cursor.timestamp,
                and_(
                    Reservation.created_at == cursor.timestamp,
                    Reservation.id > cursor.reservation_id,
                ),
            )
        )
    rows = (await session.execute(statement)).all()
    return [
        EventAttendeeRecord(
            reservation_id=reservation.id,
            attendee_id=user.id,
            full_name=user.full_name,
            email=user.email,
            reserved_at=reservation.created_at,
        )
        for reservation, user in rows
    ]


def _history_record(reservation: Reservation, event: Event) -> ReservationHistoryRecord:
    return ReservationHistoryRecord(
        id=reservation.id,
        status=reservation.status,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
        cancelled_at=reservation.cancelled_at,
        event=ReservationEventRecord(
            id=event.id,
            title=event.title,
            location=event.location,
            starts_at=event.starts_at,
            timezone=event.timezone,
            status=event.status,
        ),
    )
