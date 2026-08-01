"""Unit tests for the doc §7.2.1 category taxonomy seed."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.category_seed import COMMERCIAL_SUBCATEGORIES, TOP_LEVEL, seed_default_categories
from app.models.domain import Category


class TestSeedDefaultCategories:
    async def test_seeds_top_level_and_commercial_subcategories(self, db_session: AsyncSession):
        await seed_default_categories(db_session)
        result = await db_session.execute(select(Category))
        rows = result.scalars().all()
        names = {c.name for c in rows}
        assert set(TOP_LEVEL) <= names
        assert set(COMMERCIAL_SUBCATEGORIES) <= names

        commercial = next(c for c in rows if c.name == "Commercial Assets")
        children = {c.name for c in rows if c.parent_id == commercial.id}
        assert children == set(COMMERCIAL_SUBCATEGORIES)

    async def test_idempotent_on_repeated_runs(self, db_session: AsyncSession):
        """Doc-driven seed must be safe to run on every startup - no
        duplicate rows on a second pass over an already-seeded DB."""
        await seed_default_categories(db_session)
        await seed_default_categories(db_session)
        result = await db_session.execute(select(Category))
        rows = result.scalars().all()
        names = [c.name for c in rows]
        assert len(names) == len(set(names)), "seeding a second time created duplicate rows"
        assert len(rows) == len(TOP_LEVEL) + len(COMMERCIAL_SUBCATEGORIES)

    async def test_preserves_pre_existing_row_with_different_slug(self, db_session: AsyncSession):
        """A category with the same name but a pre-existing (differently
        formatted) slug must not be duplicated or overwritten - matches
        the real deployment state (a "Vehicles" row with a random-suffixed
        slug already existed before this seed was introduced)."""
        db_session.add(Category(name="Vehicles", slug="vehicles-preexisting", status="active"))
        await db_session.commit()

        await seed_default_categories(db_session)
        result = await db_session.execute(select(Category).where(Category.name == "Vehicles"))
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].slug == "vehicles-preexisting"
