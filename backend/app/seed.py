from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from argon2 import PasswordHasher
from argon2.low_level import Type
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.categories.models import Category
from app.events.models import Event, EventStatus
from app.reservations.models import Reservation, ReservationStatus
from app.users.models import User, UserRole, UserStatus


class SeedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, case_sensitive=True, extra="ignore")

    DATABASE_URL: str
    SEED_ORGANIZER_PASSWORD: SecretStr = Field(min_length=12)
    SEED_ATTENDEE_PASSWORD: SecretStr = Field(min_length=12)


@dataclass(frozen=True, slots=True)
class SeedIdentity:
    organizer_id: UUID = UUID("10000000-0000-7000-8000-000000000001")
    attendee_id: UUID = UUID("10000000-0000-7000-8000-000000000002")
    technology_category_id: UUID = UUID("20000000-0000-7000-8000-000000000001")
    music_category_id: UUID = UUID("20000000-0000-7000-8000-000000000002")
    sports_category_id: UUID = UUID("20000000-0000-7000-8000-000000000003")
    education_category_id: UUID = UUID("20000000-0000-7000-8000-000000000004")
    art_category_id: UUID = UUID("20000000-0000-7000-8000-000000000005")
    business_category_id: UUID = UUID("20000000-0000-7000-8000-000000000006")
    istanbul_event_id: UUID = UUID("30000000-0000-7000-8000-000000000001")
    berlin_event_id: UUID = UUID("30000000-0000-7000-8000-000000000002")
    full_event_id: UUID = UUID("30000000-0000-7000-8000-000000000003")
    empty_event_id: UUID = UUID("30000000-0000-7000-8000-000000000004")
    past_event_id: UUID = UUID("30000000-0000-7000-8000-000000000005")
    cancelled_event_id: UUID = UUID("30000000-0000-7000-8000-000000000006")
    full_reservation_id: UUID = UUID("40000000-0000-7000-8000-000000000001")
    cancelled_reservation_id: UUID = UUID("40000000-0000-7000-8000-000000000002")


IDENTITY = SeedIdentity()
PASSWORD_HASHER = PasswordHasher(type=Type.ID)


async def seed_users(
    connection: AsyncConnection,
    *,
    organizer_password: str,
    attendee_password: str,
) -> None:
    rows = [
        {
            "id": IDENTITY.organizer_id,
            "email": "organizer@eventflow.local",
            "full_name": "Demo Organizatör",
            "password_hash": PASSWORD_HASHER.hash(organizer_password),
            "role": UserRole.ORGANIZER,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": IDENTITY.attendee_id,
            "email": "attendee@eventflow.local",
            "full_name": "Demo Katılımcı",
            "password_hash": PASSWORD_HASHER.hash(attendee_password),
            "role": UserRole.ATTENDEE,
            "status": UserStatus.ACTIVE,
        },
    ]
    statement = insert(User).values(rows)
    await connection.execute(statement.on_conflict_do_nothing(index_elements=[User.email]))


async def seed_categories(connection: AsyncConnection) -> None:
    rows = [
        {"id": IDENTITY.technology_category_id, "slug": "teknoloji", "name": "Teknoloji"},
        {"id": IDENTITY.music_category_id, "slug": "muzik", "name": "Müzik"},
        {"id": IDENTITY.sports_category_id, "slug": "spor", "name": "Spor"},
        {"id": IDENTITY.education_category_id, "slug": "egitim", "name": "Eğitim"},
        {"id": IDENTITY.art_category_id, "slug": "sanat", "name": "Sanat"},
        {"id": IDENTITY.business_category_id, "slug": "is-dunyasi", "name": "İş Dünyası"},
    ]
    statement = insert(Category).values(rows)
    await connection.execute(
        statement.on_conflict_do_update(
            index_elements=[Category.slug],
            set_={"name": statement.excluded.name, "is_active": True},
        )
    )


def event_rows() -> list[dict[str, object]]:
    common = {
        "organizer_id": IDENTITY.organizer_id,
        "description": "EventFlow yerel geliştirme için örnek etkinlik.",
        "version": 1,
    }
    return [
        common
        | {
            "id": IDENTITY.istanbul_event_id,
            "category_id": IDENTITY.technology_category_id,
            "title": "İstanbul Teknoloji Buluşması",
            "location": "İstanbul",
            "starts_at": datetime(2035, 5, 12, 16, 0, tzinfo=UTC),
            "timezone": "Europe/Istanbul",
            "capacity": 120,
            "reserved_count": 0,
            "status": EventStatus.ACTIVE,
        },
        common
        | {
            "id": IDENTITY.berlin_event_id,
            "category_id": IDENTITY.education_category_id,
            "title": "Berlin Yazılım Atölyesi",
            "location": "Berlin",
            "starts_at": datetime(2035, 6, 18, 15, 0, tzinfo=UTC),
            "timezone": "Europe/Berlin",
            "capacity": 40,
            "reserved_count": 0,
            "status": EventStatus.ACTIVE,
        },
        common
        | {
            "id": IDENTITY.full_event_id,
            "category_id": IDENTITY.music_category_id,
            "title": "Dolu Konser",
            "location": "İzmir",
            "starts_at": datetime(2035, 7, 20, 17, 0, tzinfo=UTC),
            "timezone": "Europe/Istanbul",
            "capacity": 1,
            "reserved_count": 1,
            "status": EventStatus.ACTIVE,
        },
        common
        | {
            "id": IDENTITY.empty_event_id,
            "category_id": IDENTITY.sports_category_id,
            "title": "Boş Kontenjanlı Koşu",
            "location": "Ankara",
            "starts_at": datetime(2035, 8, 2, 6, 0, tzinfo=UTC),
            "timezone": "Europe/Istanbul",
            "capacity": 200,
            "reserved_count": 0,
            "status": EventStatus.ACTIVE,
        },
        common
        | {
            "id": IDENTITY.past_event_id,
            "category_id": IDENTITY.business_category_id,
            "title": "Geçmiş İş Dünyası Paneli",
            "location": "Londra",
            "starts_at": datetime(2020, 2, 1, 10, 0, tzinfo=UTC),
            "timezone": "Europe/London",
            "capacity": 80,
            "reserved_count": 0,
            "status": EventStatus.ACTIVE,
        },
        common
        | {
            "id": IDENTITY.cancelled_event_id,
            "category_id": IDENTITY.art_category_id,
            "title": "İptal Edilmiş Sergi",
            "location": "Paris",
            "starts_at": datetime(2035, 9, 10, 17, 0, tzinfo=UTC),
            "timezone": "Europe/Paris",
            "capacity": 60,
            "reserved_count": 0,
            "status": EventStatus.CANCELLED,
            "cancelled_at": datetime(2030, 1, 1, 12, 0, tzinfo=UTC),
        },
    ]


async def seed_events(connection: AsyncConnection) -> None:
    rows = event_rows()
    statement = insert(Event).values(rows)
    await connection.execute(statement.on_conflict_do_nothing(index_elements=[Event.id]))


async def seed_reservations(connection: AsyncConnection) -> None:
    rows = [
        {
            "id": IDENTITY.full_reservation_id,
            "event_id": IDENTITY.full_event_id,
            "attendee_id": IDENTITY.attendee_id,
            "status": ReservationStatus.ACTIVE,
            "cancelled_at": None,
        },
        {
            "id": IDENTITY.cancelled_reservation_id,
            "event_id": IDENTITY.cancelled_event_id,
            "attendee_id": IDENTITY.attendee_id,
            "status": ReservationStatus.CANCELLED_BY_EVENT,
            "cancelled_at": datetime(2030, 1, 1, 12, 0, tzinfo=UTC),
        },
    ]
    statement = insert(Reservation).values(rows)
    await connection.execute(
        statement.on_conflict_do_nothing(
            constraint="uq_reservations_event_attendee",
        )
    )


async def seed_database(
    database_url: str,
    *,
    organizer_password: str,
    attendee_password: str,
) -> None:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await seed_users(
                connection,
                organizer_password=organizer_password,
                attendee_password=attendee_password,
            )
            await seed_categories(connection)
            await seed_events(connection)
            await seed_reservations(connection)
    finally:
        await engine.dispose()


async def main() -> None:
    settings = SeedSettings()
    await seed_database(
        settings.DATABASE_URL,
        organizer_password=settings.SEED_ORGANIZER_PASSWORD.get_secret_value(),
        attendee_password=settings.SEED_ATTENDEE_PASSWORD.get_secret_value(),
    )


if __name__ == "__main__":
    asyncio.run(main())
