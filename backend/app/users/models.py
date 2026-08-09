from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, String, func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class UserRole(enum.StrEnum):
    ORGANIZER = "ORGANIZER"
    ATTENDEE = "ATTENDEE"


class UserStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    ANONYMIZED = "ANONYMIZED"
    DISABLED = "DISABLED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(btrim(email))", name="email_normalized"),
        CheckConstraint("char_length(email) BETWEEN 3 AND 320", name="email_length"),
        CheckConstraint("full_name = btrim(full_name)", name="full_name_trimmed"),
        CheckConstraint("char_length(full_name) BETWEEN 1 AND 120", name="full_name_length"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=True),
        nullable=False,
        server_default=UserStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
