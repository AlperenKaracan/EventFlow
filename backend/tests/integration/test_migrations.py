from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

EXPECTED_TABLES = {
    "alembic_version",
    "audit_logs",
    "categories",
    "events",
    "idempotency_records",
    "refresh_tokens",
    "reservations",
    "users",
}
EXPECTED_REFRESH_INDEXES = {
    "ix_refresh_tokens_family_id_revoked_at",
    "ix_refresh_tokens_user_id_expires_at",
    "uq_refresh_tokens_token_hash",
}
EXPECTED_EVENT_INDEXES = {
    "ix_events_active_starts_at_id",
    "ix_events_organizer_id_created_at_id",
    "ix_events_search_vector_gin",
}


@pytest.fixture
async def migrated_connection(migrated_postgres_url: str) -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(migrated_postgres_url, pool_pre_ping=True)
    async with engine.connect() as connection:
        yield connection
    await engine.dispose()


async def fetch_table_names(connection: AsyncConnection) -> set[str]:
    return await connection.run_sync(
        lambda sync_connection: set(inspect(sync_connection).get_table_names())
    )


async def fetch_index_names(connection: AsyncConnection, table_name: str) -> set[str]:
    result = await connection.execute(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname = 'public' AND tablename = :table_name"
        ),
        {"table_name": table_name},
    )
    return set(result.scalars())


async def insert_user(connection: AsyncConnection, *, role: str = "ATTENDEE") -> UUID:
    result = await connection.execute(
        text(
            """
            INSERT INTO users (email, full_name, password_hash, role)
            VALUES (:email, :full_name, :password_hash, CAST(:role AS user_role))
            RETURNING id
            """
        ),
        {
            "email": f"{uuid4()}@example.test",
            "full_name": "Migration Test User",
            "password_hash": "not-a-real-password-hash",
            "role": role,
        },
    )
    return cast(UUID, result.scalar_one())


async def test_upgrade_head_is_repeatable_and_creates_expected_schema(
    migrated_connection: AsyncConnection,
) -> None:
    assert await fetch_table_names(migrated_connection) == EXPECTED_TABLES

    revision = await migrated_connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert revision == "20260811_0002"
    assert (
        await fetch_index_names(migrated_connection, "refresh_tokens") >= EXPECTED_REFRESH_INDEXES
    )
    assert await fetch_index_names(migrated_connection, "events") >= EXPECTED_EVENT_INDEXES

    generated_expression = await migrated_connection.scalar(
        text(
            """
            SELECT pg_get_expr(attribute_default.adbin, attribute_default.adrelid)
            FROM pg_attribute AS attribute
            JOIN pg_attrdef AS attribute_default
              ON attribute_default.adrelid = attribute.attrelid
             AND attribute_default.adnum = attribute.attnum
            WHERE attribute.attrelid = 'events'::regclass
              AND attribute.attname = 'search_vector'
              AND attribute.attgenerated = 's'
            """
        )
    )
    assert generated_expression is not None
    assert "to_tsvector('turkish'::regconfig" in generated_expression

    self_fk = await migrated_connection.scalar(
        text(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'fk_refresh_tokens_replaced_by_id_refresh_tokens'
            """
        )
    )
    assert self_fk is not None
    assert "ON DELETE SET NULL" in self_fk


async def test_refresh_token_hash_and_replacement_constraints(
    migrated_connection: AsyncConnection,
) -> None:
    user_id = await insert_user(migrated_connection)
    family_id = uuid4()
    token_hash = "a" * 64
    first_token_id = await migrated_connection.scalar(
        text(
            """
            INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at)
            VALUES (:user_id, :token_hash, :family_id, now() + interval '1 day')
            RETURNING id
            """
        ),
        {"user_id": user_id, "token_hash": token_hash, "family_id": family_id},
    )
    assert first_token_id is not None
    await migrated_connection.commit()

    with pytest.raises(IntegrityError):
        await migrated_connection.execute(
            text(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at)
                VALUES (:user_id, :token_hash, :family_id, now() + interval '1 day')
                """
            ),
            {"user_id": user_id, "token_hash": token_hash, "family_id": family_id},
        )
    await migrated_connection.rollback()

    with pytest.raises(IntegrityError):
        await migrated_connection.execute(
            text("UPDATE refresh_tokens SET replaced_by_id = id WHERE id = :token_id"),
            {"token_id": first_token_id},
        )
    await migrated_connection.rollback()


async def test_capacity_duplicate_reservation_and_idempotency_state_constraints(
    migrated_connection: AsyncConnection,
) -> None:
    organizer_id = await insert_user(migrated_connection, role="ORGANIZER")
    attendee_id = await insert_user(migrated_connection)
    category_id = await migrated_connection.scalar(
        text(
            """
            INSERT INTO categories (slug, name)
            VALUES ('migration-test', 'Migration Test')
            ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """
        )
    )
    event_id = await migrated_connection.scalar(
        text(
            """
            INSERT INTO events
                (organizer_id, category_id, title, description, location,
                 starts_at, timezone, capacity)
            VALUES
                (:organizer_id, :category_id, 'Constraint Test', '', 'Istanbul',
                 now() + interval '1 day', 'Europe/Istanbul', 1)
            RETURNING id
            """
        ),
        {"organizer_id": organizer_id, "category_id": category_id},
    )
    await migrated_connection.execute(
        text(
            """
            INSERT INTO reservations (event_id, attendee_id)
            VALUES (:event_id, :attendee_id)
            """
        ),
        {"event_id": event_id, "attendee_id": attendee_id},
    )
    await migrated_connection.commit()

    with pytest.raises(IntegrityError):
        await migrated_connection.execute(
            text(
                """
                INSERT INTO reservations (event_id, attendee_id)
                VALUES (:event_id, :attendee_id)
                """
            ),
            {"event_id": event_id, "attendee_id": attendee_id},
        )
    await migrated_connection.rollback()

    with pytest.raises(IntegrityError):
        await migrated_connection.execute(
            text("UPDATE events SET reserved_count = 2 WHERE id = :event_id"),
            {"event_id": event_id},
        )
    await migrated_connection.rollback()

    with pytest.raises(IntegrityError):
        await migrated_connection.execute(
            text(
                """
                INSERT INTO idempotency_records
                    (user_id, operation, key, request_hash, state,
                     response_status, response_body, expires_at)
                VALUES
                    (:user_id, 'reservation.create', 'constraint-test', :request_hash,
                     'COMPLETED', 201, '{}'::jsonb, now() + interval '1 day')
                """
            ),
            {"user_id": attendee_id, "request_hash": "b" * 64},
        )
    await migrated_connection.rollback()


async def create_audit_fixture(connection: AsyncConnection) -> UUID:
    actor_id = await insert_user(connection, role="ORGANIZER")
    audit_id = await connection.scalar(
        text(
            """
            INSERT INTO audit_logs
                (actor_id, action, resource_type, resource_id, changes, request_id)
            VALUES
                (:actor_id, 'event.created', 'event', :resource_id,
                 CAST(:changes AS jsonb), :request_id)
            RETURNING id
            """
        ),
        {
            "actor_id": actor_id,
            "resource_id": uuid4(),
            "changes": '{"title": {"to": "Test Event"}}',
            "request_id": uuid4(),
        },
    )
    assert audit_id is not None
    await connection.commit()
    return cast(UUID, audit_id)


@pytest.mark.parametrize(
    ("statement", "parameters"),
    [
        ("UPDATE audit_logs SET action = 'tampered' WHERE id = :audit_id", {}),
        ("DELETE FROM audit_logs WHERE id = :audit_id", {}),
    ],
)
async def test_audit_rows_reject_update_and_delete(
    migrated_postgres_url: str,
    statement: str,
    parameters: dict[str, Any],
) -> None:
    engine: AsyncEngine = create_async_engine(migrated_postgres_url)
    async with engine.connect() as connection:
        audit_id = await create_audit_fixture(connection)
        with pytest.raises(DBAPIError, match="audit_logs are immutable"):
            await connection.execute(text(statement), parameters | {"audit_id": audit_id})
        await connection.rollback()

        row_count = await connection.scalar(
            text("SELECT count(*) FROM audit_logs WHERE id = :audit_id"),
            {"audit_id": audit_id},
        )
        assert row_count == 1
    await engine.dispose()
