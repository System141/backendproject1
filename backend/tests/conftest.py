import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Set JWT_SECRET before any security imports
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-production"

# We need to override the database URL before any app imports resolve the engine
import app.core.database as db_module
from app.core.security import hash_password, create_access_token

# ----- Override the database to use in-memory SQLite for tests -----
TEST_DATABASE_URL = "sqlite+aiosqlite://"
db_module.DATABASE_URL = TEST_DATABASE_URL

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

# Now it's safe to import the rest
from main import app
from app.models.base import Base
from app.models.domain import User, UserRole, Category, Auction, AuctionStatus
from app.core.database import get_db

# Disable rate limiting during tests (app-level)
app.state.limiter.enabled = False

# Also disable the per-endpoint limiter from auth module
from app.api.auth import limiter as auth_limiter
auth_limiter.enabled = False


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create a new event loop per session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the get_db dependency with a test session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean DB session for each test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client with the test DB dependency overridden."""
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_data() -> dict:
    """Return sample valid registration data."""
    return {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "role": "buyer",
        "accepted_terms": True,
        "accepted_privacy": True,
        "marketing_consent": False,
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a persisted test user fixture."""
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        name="Persisted User",
        email=f"persisted_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.buyer,
        status="active",
        accepted_terms=True,
        accepted_privacy=True,
        marketing_consent=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def seller_user(db_session: AsyncSession) -> User:
    """Create and return a persisted seller user fixture."""
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        name="Seller User",
        email=f"seller_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("SellerPass123!"),
        role=UserRole.seller,
        status="active",
        accepted_terms=True,
        accepted_privacy=True,
        marketing_consent=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create and return a persisted admin user fixture."""
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.admin,
        status="active",
        accepted_terms=True,
        accepted_privacy=True,
        marketing_consent=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """Create and return a persisted category fixture."""
    category = Category(
        name="Vehicles",
        slug=f"vehicles_{uuid.uuid4().hex[:4]}",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Return Authorization headers for a normal test user."""
    token = create_access_token(data={"sub": test_user.id, "role": test_user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seller_headers(seller_user: User) -> dict:
    """Return Authorization headers for a seller user."""
    token = create_access_token(data={"sub": seller_user.id, "role": seller_user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict:
    """Return Authorization headers for an admin user."""
    token = create_access_token(data={"sub": admin_user.id, "role": admin_user.role.value})
    return {"Authorization": f"Bearer {token}"}