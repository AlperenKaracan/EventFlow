from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class IdempotencyState(enum.StrEnum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "operation", "key", name="uq_idempotency_records_user_operation_key"
        ),
        CheckConstraint("char_length(operation) BETWEEN 1 AND 80", name="operation_length"),
        CheckConstraint("char_length(key) BETWEEN 1 AND 200", name="key_length"),
        CheckConstraint("char_length(request_hash) = 64", name="request_hash_sha256"),
        CheckConstraint(
            "(state = 'PROCESSING' AND response_status IS NULL AND response_body IS NULL) OR "
            "(state = 'COMPLETED' AND response_status IS NOT NULL AND response_body IS NOT NULL "
            "AND original_request_id IS NOT NULL)",
            name="state_response_consistency",
        ),
        CheckConstraint(
            "response_status IS NULL OR response_status BETWEEN 100 AND 599",
            name="response_status_http_range",
        ),
        Index("ix_idempotency_records_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[IdempotencyState] = mapped_column(
        Enum(IdempotencyState, name="idempotency_state", native_enum=True),
        nullable=False,
    )
    response_status: Mapped[int | None] = mapped_column(SmallInteger)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(postgresql.JSONB)
    original_request_id: Mapped[UUID | None] = mapped_column(postgresql.UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
