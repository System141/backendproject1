"""
Doc §7.2.1: "Menu, category slug, admin taxonomy ve filters aynı yapıdan
beslenmeli" - the top-level categories and the nine named Commercial Assets
subcategories must exist as real Category rows (using the existing
parent_id column), not just hardcoded frontend strings.

Idempotent by design so it's safe to run on every startup: checked by name
(top-level) and (name, parent_id) (children) rather than by slug, since an
existing deployment's slugs may not match a freshly-derived one.
"""
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Category

logger = logging.getLogger("bidmont.category_seed")

TOP_LEVEL = ["Vehicles", "Equipment", "Commercial Assets"]

# Doc §7.2.1's exact subcategory list, seeded under "Commercial Assets".
COMMERCIAL_SUBCATEGORIES = [
    "Hospitality", "Restaurant Equipment", "Electronics", "Office",
    "Retail Equipment", "Inventory & Stock", "Furniture", "Tools", "Other",
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
        await db.flush()
        by_name[name] = cat
        logger.info(f"Category seed: added top-level '{name}'")

    commercial_parent = by_name["Commercial Assets"]
    existing_children = {c.name for c in existing if c.parent_id == commercial_parent.id}
    for name in COMMERCIAL_SUBCATEGORIES:
        if name in existing_children:
            continue
        cat = Category(
            name=name, slug=f"{_slugify(name)}-{uuid.uuid4().hex[:6]}",
            parent_id=commercial_parent.id, status="active",
        )
        db.add(cat)
        logger.info(f"Category seed: added '{name}' under Commercial Assets")

    await db.commit()
