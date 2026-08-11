from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class EventStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("title = btrim(title)", name="title_trimmed"),
        CheckConstraint("char_length(title) BETWEEN 1 AND 160", name="title_length"),
        CheckConstraint("char_length(description) <= 5000", name="description_length"),
        CheckConstraint("location = btrim(location)", name="location_trimmed"),
        CheckConstraint("char_length(location) BETWEEN 1 AND 255", name="location_length"),
        CheckConstraint("char_length(timezone) BETWEEN 1 AND 64", name="timezone_length"),
        CheckConstraint("capacity > 0", name="capacity_positive"),
        CheckConstraint("reserved_count >= 0", name="reserved_count_nonnegative"),
        CheckConstraint("reserved_count <= capacity", name="reserved_count_within_capacity"),
        CheckConstraint("version > 0", name="version_positive"),
        Index(
            "ix_events_active_starts_at_id",
            "starts_at",
            "id",
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        Index("ix_events_search_vector_gin", "search_vector", postgresql_using="gin"),
        Index("ix_events_organizer_id_created_at_id", "organizer_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    organizer_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status", native_enum=True),
        nullable=False,
        server_default=EventStatus.ACTIVE.value,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_vector: Mapped[str] = mapped_column(
        postgresql.TSVECTOR,
        Computed(
            "setweight(to_tsvector('pg_catalog.turkish', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('pg_catalog.turkish', coalesce(description, '')), 'B')",
            persisted=True,
        ),
        nullable=False,
    )
