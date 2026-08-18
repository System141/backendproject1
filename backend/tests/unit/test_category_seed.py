"""Unit tests for the default category taxonomy seed (matches the
auctions.html filter chips - see app/core/category_seed.py)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.category_seed import TOP_LEVEL, seed_default_categories
from app.models.domain import Category


class TestSeedDefaultCategories:
    async def test_seeds_top_level_categories(self, db_session: AsyncSession):
        await seed_default_categories(db_session)
        result = await db_session.execute(select(Category))
        rows = result.scalars().all()
        names = {c.name for c in rows}
        assert set(TOP_LEVEL) == names

    async def test_idempotent_on_repeated_runs(self, db_session: AsyncSession):
        """Doc-driven seed must be safe to run on every startup - no
        duplicate rows on a second pass over an already-seeded DB."""
        await seed_default_categories(db_session)
        await seed_default_categories(db_session)
        result = await db_session.execute(select(Category))
        rows = result.scalars().all()
        names = [c.name for c in rows]
        assert len(names) == len(set(names)), "seeding a second time created duplicate rows"
        assert len(rows) == len(TOP_LEVEL)

    async def test_preserves_pre_existing_row_with_different_slug(self, db_session: AsyncSession):
        """A category with the same name but a pre-existing (differently
        formatted) slug must not be duplicated or overwritten."""
        db_session.add(Category(name="Cars", slug="cars-preexisting", status="active"))
        await db_session.commit()

        await seed_default_categories(db_session)
        result = await db_session.execute(select(Category).where(Category.name == "Cars"))
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].slug == "cars-preexisting"
