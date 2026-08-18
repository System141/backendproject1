"""
Top-level categories match the marketing taxonomy shown across the site
(hero trending cards, auctions.html category chips) rather than the doc's
original Vehicles/Equipment/Commercial-Assets grouping - the frontend
copy was the one already shipped and user-facing, so the category rows
were brought in line with it instead of relabeling the whole site.

Idempotent by design so it's safe to run on every startup: checked by name,
since an existing deployment's slugs may not match a freshly-derived one.

# ponytail: seeding is additive-only (never renames/deletes). A deployment
# migrated from the old Vehicles/Equipment/Commercial Assets taxonomy keeps
# those rows alongside the new ones until an admin manually deactivates them
# via PUT /admin/categories/{id} (status=inactive). Fine for the current
# single-admin/dev stage; write a one-off cleanup script if that changes.
"""
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Category

logger = logging.getLogger("bidmont.category_seed")

# Must match the CHIPS list in build.py (auctions.html filter chips) by name.
TOP_LEVEL = [
    "Cars", "Heavy Equipment", "Real Estate", "Marine",
    "Luxury", "Industrial Machinery", "Electronics", "Trucks",
]


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def seed_default_categories(db: AsyncSession) -> None:
    result = await db.execute(select(Category))
    existing = result.scalars().all()
    by_name = {c.name: c for c in existing}

    for name in TOP_LEVEL:
        if name in by_name:
            continue
        cat = Category(name=name, slug=f"{_slugify(name)}-{uuid.uuid4().hex[:6]}", status="active")
        db.add(cat)
        logger.info(f"Category seed: added '{name}'")

    await db.commit()
