'''import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.db.database import Base
from app.db import models
config=context.config

if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except (KeyError, ValueError):
        pass

def run_migrations_offline():
    context.configure(url=config.get_main_option('sqlalchemy.url'),target_metadata=target_metadata,literal_binds=True,compare_type=True)
    with context.begin_transaction(): context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
    with context.begin_transaction(): context.run_migrations()

async def run_async():
    connectable=async_engine_from_config(config.get_section(config.config_ini_section,{}),prefix='sqlalchemy.',poolclass=None)
    async with connectable.connect() as connection: await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online(): asyncio.run(run_async())
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()'''

#********************************************************************


import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.db.database import Base

from app.db.database import Base
from app.db import models

target_metadata = Base.metadata

# IMPORTANT:
# Import models so SQLAlchemy registers all model tables
# with Base.metadata.
from app.db import models  # noqa: F401


config = context.config


# Alembic logging is optional.
# Your current alembic.ini does not contain the standard
# logging configuration, so don't let that stop migrations.
if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except (KeyError, ValueError):
        pass


# This was missing in your previous env.py.
# Alembic needs this to know about our SQLAlchemy tables.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without connecting to the database."""

    url = settings.database_url

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using an existing database connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create async engine and run migrations."""

    configuration = config.get_section(config.config_ini_section)

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations against the database."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
