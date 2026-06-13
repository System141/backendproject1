"""Unit tests for SQLAlchemy model definitions."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    User,
    UserRole,
    Category,
    Auction,
    AuctionStatus,
    Bid,
    AuctionImage,
    AuditLog,
)
from app.core.security import hash_password


class TestUserModel:
    async def test_create_user(self, db_session: AsyncSession):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            name="Test User",
            email=f"create_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id == uid
        assert user.name == "Test User"
        assert user.role == UserRole.buyer
        assert user.status == "active"
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_user_roles(self, db_session: AsyncSession):
        roles = [
            (UserRole.buyer, "buyer"),
            (UserRole.seller, "seller"),
            (UserRole.corporate_seller, "corporate_seller"),
            (UserRole.admin, "admin"),
        ]
        for role_enum, role_str in roles:
            uid = str(uuid.uuid4())
            user = User(
                id=uid,
                name=f"{role_str.title()} User",
                email=f"{role_str}_{uuid.uuid4().hex[:8]}@example.com",
                password_hash=hash_password("pass"),
                role=role_enum,
                accepted_terms=True,
                accepted_privacy=True,
            )
            db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 4

    async def test_unique_email_constraint(self, db_session: AsyncSession):
        email = f"unique_{uuid.uuid4().hex[:8]}@example.com"
        user1 = User(
            id=str(uuid.uuid4()),
            name="User One",
            email=email,
            password_hash=hash_password("pass"),
            accepted_terms=True,
            accepted_privacy=True,
        )
        db_session.add(user1)
        await db_session.commit()

        user2 = User(
            id=str(uuid.uuid4()),
            name="User Two",
            email=email,  # Same email
            password_hash=hash_password("pass"),
            accepted_terms=True,
            accepted_privacy=True,
        )
        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_default_values(self, db_session: AsyncSession):
        user = User(
            id=str(uuid.uuid4()),
            name="Default Test",
            email=f"default_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("pass"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.role == UserRole.buyer  # default
        assert user.status == "active"  # default
        assert user.marketing_consent is False  # default
        assert user.accepted_terms is False  # default
        assert user.accepted_privacy is False  # default


class TestCategoryModel:
    async def test_create_category(self, db_session: AsyncSession):
        category = Category(
            name="Electronics",
            slug=f"electronics_{uuid.uuid4().hex[:4]}",
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        assert category.name == "Electronics"
        assert category.status == "active"  # default

    async def test_category_with_parent(self, db_session: AsyncSession):
        parent = Category(name="Parent", slug=f"parent_{uuid.uuid4().hex[:4]}")
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        child = Category(
            name="Child",
            slug=f"child_{uuid.uuid4().hex[:4]}",
            parent_id=parent.id,
        )
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        assert child.parent_id == parent.id


class TestAuctionModel:
    async def test_create_auction(self, db_session: AsyncSession, test_user: User):
        category = Category(name="Test Cat", slug=f"cat_{uuid.uuid4().hex[:4]}")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=test_user.id,
            category_id=category.id,
            title="Test Auction",
            description="A test auction item",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        db_session.add(auction)
        await db_session.commit()
        await db_session.refresh(auction)

        assert auction.title == "Test Auction"
        assert auction.status == AuctionStatus.pending_approval  # default
        assert auction.start_price == 100.0


class TestBidModel:
    async def test_create_bid(self, db_session: AsyncSession, test_user: User):
        category = Category(name="Bid Cat", slug=f"bidcat_{uuid.uuid4().hex[:4]}")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=test_user.id,
            category_id=category.id,
            title="Biddable Auction",
            description="Something to bid on",
            start_price=50.0,
            current_price=50.0,
            min_increment=5.0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        db_session.add(auction)
        await db_session.commit()
        await db_session.refresh(auction)

        bid = Bid(
            id=str(uuid.uuid4()),
            auction_id=auction.id,
            user_id=test_user.id,
            amount=55.0,
        )
        db_session.add(bid)
        await db_session.commit()
        await db_session.refresh(bid)

        assert bid.amount == 55.0
        assert bid.auction_id == auction.id
        assert bid.user_id == test_user.id


class TestAuctionImageModel:
    async def test_create_auction_image(self, db_session: AsyncSession, test_user: User):
        category = Category(name="Img Cat", slug=f"imgcat_{uuid.uuid4().hex[:4]}")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=test_user.id,
            category_id=category.id,
            title="Img Auction",
            description="Has images",
            start_price=10.0,
            current_price=10.0,
            min_increment=1.0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        db_session.add(auction)
        await db_session.commit()
        await db_session.refresh(auction)

        img = AuctionImage(
            id=str(uuid.uuid4()),
            auction_id=auction.id,
            image_url="https://example.com/image.jpg",
            sort_order=1,
        )
        db_session.add(img)
        await db_session.commit()
        await db_session.refresh(img)

        assert img.image_url == "https://example.com/image.jpg"
        assert img.sort_order == 1


class TestAuditLogModel:
    async def test_create_audit_log(self, db_session: AsyncSession, test_user: User):
        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            action="USER_LOGIN",
            entity_type="user",
            entity_id=test_user.id,
        )
        db_session.add(log)
        await db_session.commit()
        await db_session.refresh(log)

        assert log.action == "USER_LOGIN"
        assert log.entity_type == "user"
        assert log.created_at is not None