"""Add the generated event full-text search vector.

Revision ID: 20260811_0002
Revises: 20260809_0001
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260811_0002"
down_revision: str | None = "20260809_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('pg_catalog.turkish', coalesce(title, '')), 'A') || "
                "setweight(to_tsvector('pg_catalog.turkish', coalesce(description, '')), 'B')",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_events_search_vector_gin",
        "events",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_events_search_vector_gin", table_name="events")
    op.drop_column("events", "search_vector")
