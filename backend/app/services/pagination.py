"""Bounded list queries, preserving the existing array response contract."""
from fastapi import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def page_query(db: AsyncSession, query, response: Response, limit: int, offset: int):
    count = await db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    response.headers["X-Total-Count"] = str(count)
    return await db.execute(query.limit(limit).offset(offset))
