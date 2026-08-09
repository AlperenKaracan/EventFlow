from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from testcontainers.community.postgres import PostgresContainer

POSTGRES_IMAGE = "postgres:17.6-alpine"


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(
        POSTGRES_IMAGE,
        username="eventflow",
        password="eventflow_test_password",
        dbname="eventflow_test",
        driver="asyncpg",
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def migrated_postgres_url(postgres_url: str) -> str:
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", postgres_url)

    command.upgrade(config, "head")
    command.upgrade(config, "head")
    command.check(config)
    return postgres_url
