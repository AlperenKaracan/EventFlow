from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.events.models import EventStatus
from app.reservations.models import Reservation, ReservationStatus
from app.reservations.repository import EventAttendeeRecord, ReservationHistoryRecord


class ReservationEventResponse(BaseModel):
    id: UUID
    title: str
    location: str
    starts_at: datetime = Field(serialization_alias="startsAt")
    timezone: str
    status: EventStatus


class ReservationHistoryResponse(BaseModel):
    id: UUID
    status: ReservationStatus
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    cancelled_at: datetime | None = Field(serialization_alias="cancelledAt")
    event: ReservationEventResponse

    @classmethod
    def from_record(cls, record: ReservationHistoryRecord) -> ReservationHistoryResponse:
        return cls(
            id=record.id,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            cancelled_at=record.cancelled_at,
            event=ReservationEventResponse(
                id=record.event.id,
                title=record.event.title,
                location=record.event.location,
                starts_at=record.event.starts_at,
                timezone=record.event.timezone,
                status=record.event.status,
            ),
        )


class ReservationHistoryPage(BaseModel):
    items: list[ReservationHistoryResponse]
    next_cursor: str | None = Field(serialization_alias="nextCursor")
    has_more: bool = Field(serialization_alias="hasMore")


class EventAttendeeResponse(BaseModel):
    reservation_id: UUID = Field(serialization_alias="reservationId")
    attendee_id: UUID = Field(serialization_alias="attendeeId")
    full_name: str = Field(serialization_alias="fullName")
    email: str
    reserved_at: datetime = Field(serialization_alias="reservedAt")

    @classmethod
    def from_record(cls, record: EventAttendeeRecord) -> EventAttendeeResponse:
        return cls(
            reservation_id=record.reservation_id,
            attendee_id=record.attendee_id,
            full_name=record.full_name,
            email=record.email,
            reserved_at=record.reserved_at,
        )


class EventAttendeePage(BaseModel):
    items: list[EventAttendeeResponse]
    next_cursor: str | None = Field(serialization_alias="nextCursor")
    has_more: bool = Field(serialization_alias="hasMore")


class ReservationMutationResponse(BaseModel):
    id: UUID
    event_id: UUID = Field(serialization_alias="eventId")
    attendee_id: UUID = Field(serialization_alias="attendeeId")
    status: ReservationStatus
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    cancelled_at: datetime | None = Field(serialization_alias="cancelledAt")

    @classmethod
    def from_reservation(cls, reservation: Reservation) -> ReservationMutationResponse:
        return cls(
            id=reservation.id,
            event_id=reservation.event_id,
            attendee_id=reservation.attendee_id,
            status=reservation.status,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
            cancelled_at=reservation.cancelled_at,
        )
