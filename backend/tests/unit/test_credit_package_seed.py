"""Unit tests for the default credit package seed (matches the
credits.html plan cards - see app/core/credit_package_seed.py)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credit_package_seed import DEFAULT_PACKAGES, seed_default_credit_packages
from app.models.domain import CreditPackage


class TestSeedDefaultCreditPackages:
    async def test_seeds_default_packages(self, db_session: AsyncSession):
        await seed_default_credit_packages(db_session)
        result = await db_session.execute(select(CreditPackage))
        rows = result.scalars().all()
        names = {p.name for p in rows}
        assert names == {name for name, *_ in DEFAULT_PACKAGES}
        assert all(p.active for p in rows), "seeded packages must be active or wirePlans() won't show them"

    async def test_idempotent_on_repeated_runs(self, db_session: AsyncSession):
        """Must be safe to run on every startup - no duplicate rows on a
        second pass over an already-seeded DB."""
        await seed_default_credit_packages(db_session)
        await seed_default_credit_packages(db_session)
        result = await db_session.execute(select(CreditPackage))
        rows = result.scalars().all()
        names = [p.name for p in rows]
        assert len(names) == len(set(names)), "seeding a second time created duplicate rows"
        assert len(rows) == len(DEFAULT_PACKAGES)

    async def test_preserves_admin_edited_package(self, db_session: AsyncSession):
        """An admin-edited package (different price, same name) must not be
        duplicated or reverted by a later seed pass."""
        db_session.add(CreditPackage(name="Starter", credits=999.0, price_eur=1.0, active=True, sort_order=0))
        await db_session.commit()

        await seed_default_credit_packages(db_session)
        result = await db_session.execute(select(CreditPackage).where(CreditPackage.name == "Starter"))
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].price_eur == 1.0
