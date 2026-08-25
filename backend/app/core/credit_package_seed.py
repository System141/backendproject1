"""
Default credit packages so the public "buy credits" plan cards on
index.html/credits.html have something to render. Without any row in
credit_packages, GET /api/credits/packages returns [] and
assets/js/api.js's wirePlans() hides every static .plan card it can't
match to a package - the buy button never appears at all.

Prices/credits match the four tiers already baked into build.py's
credits.html pricing section (Starter/Plus/Pro/Business) - that copy was
the one already shipped and user-facing, so the seed rows were brought in
line with it rather than inventing new numbers.

Idempotent by design so it's safe to run on every startup: checked by
name, mirrors app/core/category_seed.py's pattern.

# ponytail: seeding is additive-only (never renames/re-prices/deletes). An
# admin who edits a package via PUT /admin/credit-packages/{id} keeps that
# edit across restarts - this only fills in rows missing by name.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import CreditPackage

logger = logging.getLogger("bidmont.credit_package_seed")

# (name, credits, price_eur, sort_order) - matches build.py's credits.html plan_card() calls
DEFAULT_PACKAGES = [
    ("Starter", 50.0, 49.0, 0),
    ("Plus", 175.0, 149.0, 1),
    ("Pro", 650.0, 499.0, 2),
    ("Business", 1400.0, 999.0, 3),
]


async def seed_default_credit_packages(db: AsyncSession) -> None:
    result = await db.execute(select(CreditPackage))
    existing_names = {p.name for p in result.scalars().all()}

    for name, credits, price_eur, sort_order in DEFAULT_PACKAGES:
        if name in existing_names:
            continue
        db.add(CreditPackage(name=name, credits=credits, price_eur=price_eur, active=True, sort_order=sort_order))
        logger.info(f"Credit package seed: added '{name}'")

    await db.commit()
