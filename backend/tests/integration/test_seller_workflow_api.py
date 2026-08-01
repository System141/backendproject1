"""Integration tests for seller application/verification + listing review (doc §11)."""
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.domain import Category, User, UserRole


def _auth_headers(user: User) -> dict:
    token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


def _listing_payload(category_id: int, **overrides) -> dict:
    payload = {
        "title": "Workflow Test Auction",
        "description": "Testing the seller review workflow",
        "category_id": category_id,
        "start_price": 100.0,
        "min_increment": 10.0,
        "end_time": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        "declaration_accepted": True,
    }
    payload.update(overrides)
    return payload


class TestSellerApplication:
    async def test_apply_creates_pending_profile(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.post(
            "/api/sellers/apply",
            json={"account_type": "individual", "city": "Podgorica"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["verification_status"] == "pending"

    async def test_reapply_while_pending_conflicts(self, async_client: AsyncClient, auth_headers: dict):
        payload = {"account_type": "individual"}
        await async_client.post("/api/sellers/apply", json=payload, headers=auth_headers)
        resp = await async_client.post("/api/sellers/apply", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    async def test_apply_blocked_without_email_verification(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Doc §11.2's "Phone + email verification" application field: an
        unverified email must block the application (the phone/SMS half
        stays unenforced - it needs an SMS gateway decision, see C-list)."""
        user = User(
            id=str(uuid.uuid4()),
            name="Unverified Applicant",
            email=f"unverified_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
            email_verified=False,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await async_client.post(
            "/api/sellers/apply", json={"account_type": "individual"}, headers=_auth_headers(user)
        )
        assert resp.status_code == 403

    async def test_unverified_seller_cannot_create_listing(
        self, async_client: AsyncClient, auth_headers: dict, test_category: Category
    ):
        await async_client.post("/api/sellers/apply", json={"account_type": "individual"}, headers=auth_headers)
        resp = await async_client.post("/api/auctions", json=_listing_payload(test_category.id), headers=auth_headers)
        assert resp.status_code == 403

    async def test_self_declared_seller_role_without_profile_is_still_blocked(
        self, async_client: AsyncClient, db_session: AsyncSession, test_category: Category
    ):
        """Registering with role=seller alone (no application/verification) must not be enough (doc §11.1/§11.5)."""
        user = User(
            id=str(uuid.uuid4()),
            name="Self Declared Seller",
            email=f"selfdeclared_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.seller,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await async_client.post(
            "/api/auctions", json=_listing_payload(test_category.id), headers=_auth_headers(user)
        )
        assert resp.status_code == 403

    async def test_verify_promotes_role_and_unlocks_listing(
        self, async_client: AsyncClient, test_user: User, auth_headers: dict, admin_headers: dict, test_category: Category
    ):
        await async_client.post("/api/sellers/apply", json={"account_type": "individual"}, headers=auth_headers)
        me = await async_client.get("/api/sellers/me", headers=auth_headers)
        profile_id = me.json()["id"]

        verify_resp = await async_client.post(f"/api/admin/sellers/{profile_id}/verify", headers=admin_headers)
        assert verify_resp.status_code == 200
        assert verify_resp.json()["verification_status"] == "verified"

        # test_user is a generic buyer fixture with 0 credits by design (so the
        # insufficient-balance path in test_credit_engine.py stays meaningful) -
        # top it up here just enough to cover the listing fee for this test.
        await async_client.post(
            "/api/admin/credits/adjust",
            json={"user_id": test_user.id, "amount": 100, "reason": "test setup"},
            headers=admin_headers,
        )

        create_resp = await async_client.post(
            "/api/auctions", json=_listing_payload(test_category.id), headers=auth_headers
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["status"] == "under_review"

    async def test_reject_requires_reason(
        self, async_client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        await async_client.post("/api/sellers/apply", json={"account_type": "individual"}, headers=auth_headers)
        me = await async_client.get("/api/sellers/me", headers=auth_headers)
        profile_id = me.json()["id"]

        missing_reason = await async_client.post(f"/api/admin/sellers/{profile_id}/reject", json={}, headers=admin_headers)
        assert missing_reason.status_code == 422

        resp = await async_client.post(
            "/api/admin/sellers/{}/reject".format(profile_id),
            json={"reason": "Missing supporting documents"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["verification_status"] == "rejected"
        assert resp.json()["rejection_reason"] == "Missing supporting documents"

    async def test_reapply_after_rejection_allowed(
        self, async_client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        await async_client.post("/api/sellers/apply", json={"account_type": "individual"}, headers=auth_headers)
        me = await async_client.get("/api/sellers/me", headers=auth_headers)
        profile_id = me.json()["id"]
        await async_client.post(
            f"/api/admin/sellers/{profile_id}/reject", json={"reason": "no docs"}, headers=admin_headers
        )

        resp = await async_client.post(
            "/api/sellers/apply", json={"account_type": "company", "company_name": "ACME DOO"}, headers=auth_headers
        )
        assert resp.status_code == 201
        assert resp.json()["verification_status"] == "pending"
        assert resp.json()["company_name"] == "ACME DOO"


class TestListingReviewWorkflow:
    async def test_request_changes_then_resubmit(
        self, async_client: AsyncClient, seller_headers: dict, admin_headers: dict, test_category: Category
    ):
        create_resp = await async_client.post(
            "/api/auctions", json=_listing_payload(test_category.id), headers=seller_headers
        )
        auction_id = create_resp.json()["id"]

        changes_resp = await async_client.post(
            f"/api/auctions/{auction_id}/request-changes",
            json={"reason": "Please add more photos"},
            headers=admin_headers,
        )
        assert changes_resp.status_code == 200
        assert changes_resp.json()["status"] == "draft"
        assert changes_resp.json()["review_notes"] == "Please add more photos"

        # Seller can still edit while in draft
        edit_resp = await async_client.put(
            f"/api/auctions/{auction_id}",
            json={"description": "Updated with more detail about the item for sale"},
            headers=seller_headers,
        )
        assert edit_resp.status_code == 200

        submit_resp = await async_client.post(f"/api/auctions/{auction_id}/submit", headers=seller_headers)
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] == "under_review"

    async def test_request_changes_only_from_under_review(
        self, async_client: AsyncClient, seller_headers: dict, admin_headers: dict, test_category: Category
    ):
        create_resp = await async_client.post(
            "/api/auctions", json=_listing_payload(test_category.id), headers=seller_headers
        )
        auction_id = create_resp.json()["id"]
        await async_client.post(f"/api/auctions/{auction_id}/approve", headers=admin_headers)

        resp = await async_client.post(
            f"/api/auctions/{auction_id}/request-changes", json={"reason": "too late"}, headers=admin_headers
        )
        assert resp.status_code == 400

    async def test_contact_info_in_description_is_flagged(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        resp = await async_client.post(
            "/api/auctions",
            json=_listing_payload(
                test_category.id,
                description="Great car, call me directly at +38267123456 for details",
            ),
            headers=seller_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["contact_flagged"] is True

    async def test_clean_description_not_flagged(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        resp = await async_client.post(
            "/api/auctions", json=_listing_payload(test_category.id), headers=seller_headers
        )
        assert resp.status_code == 201
        assert resp.json()["contact_flagged"] is False
