import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# For MVP local development we'll use SQLite via aiosqlite, but it's configured for PostgreSQL in production.
# To use postgres, set DATABASE_URL=postgresql+asyncpg://user:pass@localhost/bidmont
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bidmont.db")

# Render provides 'postgres://' or 'postgresql://' connection strings. 
# We need to ensure it uses the asyncpg driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
