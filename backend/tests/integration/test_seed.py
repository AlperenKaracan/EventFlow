from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.seed import seed_database


async def snapshot(database_url: str) -> dict[str, Any]:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        counts = {
            table: await connection.scalar(text(f"SELECT count(*) FROM {table}"))
            for table in ("users", "categories", "events", "reservations")
        }
        password_hashes = tuple(
            (
                await connection.execute(text("SELECT password_hash FROM users ORDER BY email"))
            ).scalars()
        )
        full_event = (
            await connection.execute(
                text(
                    """
                    SELECT e.capacity, e.reserved_count, count(r.id)
                    FROM events e
                    LEFT JOIN reservations r
                      ON r.event_id = e.id AND r.status = 'ACTIVE'
                    WHERE e.title = 'Dolu Konser'
                    GROUP BY e.id
                    """
                )
            )
        ).one()
    await engine.dispose()
    return {"counts": counts, "password_hashes": password_hashes, "full_event": tuple(full_event)}


async def test_seed_is_repeatable_without_duplicates(migrated_postgres_url: str) -> None:
    engine = create_async_engine(migrated_postgres_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                TRUNCATE TABLE audit_logs, idempotency_records, reservations, events,
                    refresh_tokens, categories, users
                RESTART IDENTITY CASCADE
                """
            )
        )
    await engine.dispose()

    parameters = {
        "organizer_password": "OrganizerDemo123!",
        "attendee_password": "AttendeeDemo123!",
    }

    await seed_database(migrated_postgres_url, **parameters)
    first_snapshot = await snapshot(migrated_postgres_url)
    await seed_database(migrated_postgres_url, **parameters)
    second_snapshot = await snapshot(migrated_postgres_url)

    assert first_snapshot == second_snapshot
    assert second_snapshot["counts"] == {
        "users": 2,
        "categories": 6,
        "events": 6,
        "reservations": 2,
    }
    assert all(value.startswith("$argon2id$") for value in second_snapshot["password_hashes"])
    assert second_snapshot["full_event"] == (1, 1, 1)
