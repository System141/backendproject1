"""Unit tests for the auto-migration system (app/core/migrations.py)."""
from sqlalchemy import text

from app.core.migrations import run_migration_async, MISSING_INDEXES
from tests.conftest import test_engine


async def test_run_migration_creates_missing_indexes():
    """MISSING_INDEXES backs the columns app/api/auctions.py's list_auctions
    filters/sorts on (status, category_id, end_time, ...) - every auctions.html
    load, chip click, filter apply and sort change routes through that query.
    run_migration_async is the only path that adds these to a DB that already
    existed before domain.py's columns gained index=True, so a typo or a
    dropped loop here would silently leave a deployed DB unindexed."""
    async with test_engine.begin() as conn:
        for _, _, name in MISSING_INDEXES:
            await conn.execute(text(f'DROP INDEX IF EXISTS "{name}"'))
        await run_migration_async(conn)
        await run_migration_async(conn)
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index'")
        )
        names = {row[0] for row in result.fetchall()}
    missing = {name for _, _, name in MISSING_INDEXES} - names
    assert not missing, f"migration did not create: {missing}"
