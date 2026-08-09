"""Create the EventFlow relational foundation.

Revision ID: 20260809_0001
Revises: None
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260809_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = postgresql.ENUM("ORGANIZER", "ATTENDEE", name="user_role", create_type=False)
user_status = postgresql.ENUM(
    "ACTIVE", "ANONYMIZED", "DISABLED", name="user_status", create_type=False
)
event_status = postgresql.ENUM("ACTIVE", "CANCELLED", name="event_status", create_type=False)
reservation_status = postgresql.ENUM(
    "ACTIVE",
    "CANCELLED_BY_ATTENDEE",
    "CANCELLED_BY_EVENT",
    name="reservation_status",
    create_type=False,
)
idempotency_state = postgresql.ENUM(
    "PROCESSING", "COMPLETED", name="idempotency_state", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (
        user_role,
        user_status,
        event_status,
        reservation_status,
        idempotency_state,
    ):
        enum_type.create(bind, checkfirst=False)

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("status", user_status, server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("email = lower(btrim(email))", name="email_normalized"),
        sa.CheckConstraint("char_length(email) BETWEEN 3 AND 320", name="email_length"),
        sa.CheckConstraint("full_name = btrim(full_name)", name="full_name_trimmed"),
        sa.CheckConstraint("char_length(full_name) BETWEEN 1 AND 120", name="full_name_length"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "categories",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("slug = lower(btrim(slug))", name="slug_normalized"),
        sa.CheckConstraint("char_length(slug) BETWEEN 1 AND 80", name="slug_length"),
        sa.CheckConstraint("name = btrim(name)", name="name_trimmed"),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 120", name="name_length"),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("replaced_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("char_length(token_hash) = 64", name="token_hash_sha256"),
        sa.CheckConstraint(
            "replaced_by_id IS NULL OR replaced_by_id <> id",
            name="replacement_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"],
            ["refresh_tokens.id"],
            name="fk_refresh_tokens_replaced_by_id_refresh_tokens",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_refresh_tokens_user_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index(
        "ix_refresh_tokens_user_id_expires_at",
        "refresh_tokens",
        ["user_id", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_tokens_family_id_revoked_at",
        "refresh_tokens",
        ["family_id", "revoked_at"],
        unique=False,
    )
    op.create_table(
        "events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organizer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("reserved_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", event_status, server_default="ACTIVE", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("title = btrim(title)", name="title_trimmed"),
        sa.CheckConstraint("char_length(title) BETWEEN 1 AND 160", name="title_length"),
        sa.CheckConstraint("char_length(description) <= 5000", name="description_length"),
        sa.CheckConstraint("location = btrim(location)", name="location_trimmed"),
        sa.CheckConstraint("char_length(location) BETWEEN 1 AND 255", name="location_length"),
        sa.CheckConstraint("char_length(timezone) BETWEEN 1 AND 64", name="timezone_length"),
        sa.CheckConstraint("capacity > 0", name="capacity_positive"),
        sa.CheckConstraint("reserved_count >= 0", name="reserved_count_nonnegative"),
        sa.CheckConstraint("reserved_count <= capacity", name="reserved_count_within_capacity"),
        sa.CheckConstraint("version > 0", name="version_positive"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_events_category_id_categories",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organizer_id"], ["users.id"], name="fk_events_organizer_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
    )
    op.create_index(
        "ix_events_active_starts_at_id",
        "events",
        ["starts_at", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_index(
        "ix_events_organizer_id_created_at_id",
        "events",
        ["organizer_id", "created_at", "id"],
        unique=False,
    )
    op.create_table(
        "reservations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attendee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", reservation_status, server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["attendee_id"],
            ["users.id"],
            name="fk_reservations_attendee_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"], name="fk_reservations_event_id_events", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservations"),
        sa.UniqueConstraint("event_id", "attendee_id", name="uq_reservations_event_attendee"),
    )
    op.create_index(
        "ix_reservations_attendee_id_created_at_id",
        "reservations",
        ["attendee_id", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_reservations_event_id_status_created_at",
        "reservations",
        ["event_id", "status", "created_at"],
        unique=False,
    )
    op.create_table(
        "idempotency_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation", sa.String(length=80), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("state", idempotency_state, nullable=False),
        sa.Column("response_status", sa.SmallInteger(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("original_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "char_length(operation) BETWEEN 1 AND 80",
            name="operation_length",
        ),
        sa.CheckConstraint("char_length(key) BETWEEN 1 AND 200", name="key_length"),
        sa.CheckConstraint("char_length(request_hash) = 64", name="request_hash_sha256"),
        sa.CheckConstraint(
            "(state = 'PROCESSING' AND response_status IS NULL AND response_body IS NULL) OR "
            "(state = 'COMPLETED' AND response_status IS NOT NULL AND response_body IS NOT NULL "
            "AND original_request_id IS NOT NULL)",
            name="state_response_consistency",
        ),
        sa.CheckConstraint(
            "response_status IS NULL OR response_status BETWEEN 100 AND 599",
            name="response_status_http_range",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_idempotency_records_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_records"),
        sa.UniqueConstraint(
            "user_id", "operation", "key", name="uq_idempotency_records_user_operation_key"
        ),
    )
    op.create_index(
        "ix_idempotency_records_expires_at",
        "idempotency_records",
        ["expires_at"],
        unique=False,
    )
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("char_length(action) BETWEEN 1 AND 120", name="action_length"),
        sa.CheckConstraint(
            "char_length(resource_type) BETWEEN 1 AND 80", name="resource_type_length"
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name="fk_audit_logs_actor_id_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.execute(
        """
        CREATE FUNCTION reject_audit_log_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs are immutable'
                USING ERRCODE = '55000';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_log_mutation()")
    op.drop_table("audit_logs")
    op.drop_index("ix_idempotency_records_expires_at", table_name="idempotency_records")
    op.drop_table("idempotency_records")
    op.drop_index("ix_reservations_event_id_status_created_at", table_name="reservations")
    op.drop_index("ix_reservations_attendee_id_created_at_id", table_name="reservations")
    op.drop_table("reservations")
    op.drop_index("ix_events_organizer_id_created_at_id", table_name="events")
    op.drop_index("ix_events_active_starts_at_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_refresh_tokens_family_id_revoked_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id_expires_at", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("categories")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in (
        idempotency_state,
        reservation_status,
        event_status,
        user_status,
        user_role,
    ):
        enum_type.drop(bind, checkfirst=False)
