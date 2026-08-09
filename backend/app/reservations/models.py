from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint, func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class ReservationStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    CANCELLED_BY_ATTENDEE = "CANCELLED_BY_ATTENDEE"
    CANCELLED_BY_EVENT = "CANCELLED_BY_EVENT"


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        UniqueConstraint("event_id", "attendee_id", name="uq_reservations_event_attendee"),
        Index("ix_reservations_attendee_id_created_at_id", "attendee_id", "created_at", "id"),
        Index("ix_reservations_event_id_status_created_at", "event_id", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attendee_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status", native_enum=True),
        nullable=False,
        server_default=ReservationStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
