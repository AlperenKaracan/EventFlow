from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("slug = lower(btrim(slug))", name="slug_normalized"),
        CheckConstraint("char_length(slug) BETWEEN 1 AND 80", name="slug_length"),
        CheckConstraint("name = btrim(name)", name="name_trimmed"),
        CheckConstraint("char_length(name) BETWEEN 1 AND 120", name="name_length"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
