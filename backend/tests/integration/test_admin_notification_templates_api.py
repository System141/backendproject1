"""Integration tests for admin notification template management (doc §17)."""
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Notification, NotificationType, User
from app.services.notifications import send_notification


class TestListTemplates:
    async def test_lists_only_templatable_types_with_no_overrides(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.get("/api/admin/notification-templates", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        types = {row["type"] for row in data}
        assert "auction_approved" in types
        assert "credit_purchase_successful" in types
        # A type that never passes template_vars must not be offered - editing
        # it would silently do nothing at send time.
        assert "outbid" not in types
        approved_row = next(r for r in data if r["type"] == "auction_approved")
        assert approved_row["placeholders"] == ["auction_title"]
        assert approved_row["title_en"] is None

    async def test_requires_admin(self, async_client: AsyncClient, auth_headers: dict):
        response = await async_client.get("/api/admin/notification-templates", headers=auth_headers)
        assert response.status_code == 403


class TestUpdateTemplate:
    async def test_update_unknown_type_rejected(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.put(
            "/api/admin/notification-templates/not_a_real_type",
            json={"title_en": "x"}, headers=admin_headers,
        )
        assert response.status_code == 404

    async def test_update_non_templatable_type_rejected(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.put(
            "/api/admin/notification-templates/outbid",
            json={"title_en": "x"}, headers=admin_headers,
        )
        assert response.status_code == 400

    async def test_update_with_unknown_placeholder_rejected(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.put(
            "/api/admin/notification-templates/auction_approved",
            json={"title_en": "Approved: {typo_field}"}, headers=admin_headers,
        )
        assert response.status_code == 400
        assert "typo_field" in response.json()["detail"]

    async def test_update_and_persist(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.put(
            "/api/admin/notification-templates/auction_approved",
            json={"title_en": "Custom: {auction_title} is live!"}, headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["title_en"] == "Custom: {auction_title} is live!"

        list_response = await async_client.get("/api/admin/notification-templates", headers=admin_headers)
        row = next(r for r in list_response.json() if r["type"] == "auction_approved")
        assert row["title_en"] == "Custom: {auction_title} is live!"

    async def test_reset_clears_override(self, async_client: AsyncClient, admin_headers: dict):
        await async_client.put(
            "/api/admin/notification-templates/auction_approved",
            json={"title_en": "Custom text"}, headers=admin_headers,
        )
        response = await async_client.delete("/api/admin/notification-templates/auction_approved", headers=admin_headers)
        assert response.status_code == 200

        list_response = await async_client.get("/api/admin/notification-templates", headers=admin_headers)
        row = next(r for r in list_response.json() if r["type"] == "auction_approved")
        assert row["title_en"] is None


class TestTemplateAppliedAtSendTime:
    async def test_custom_template_used_when_placeholders_resolve(
        self, async_client: AsyncClient, admin_headers: dict, db_session: AsyncSession, test_user: User,
    ):
        await async_client.put(
            "/api/admin/notification-templates/auction_approved",
            json={"title_en": "Your listing {auction_title} went live!"}, headers=admin_headers,
        )

        await send_notification(
            db_session, test_user.id, NotificationType.auction_approved,
            "Auction approved: default title", "default message",
            send_email=False, template_vars={"auction_title": "Toyota Corolla"},
        )
        result = await db_session.execute(
            select(Notification).where(Notification.user_id == test_user.id, Notification.type == NotificationType.auction_approved)
        )
        notif = result.scalars().first()
        assert notif.title == "Your listing Toyota Corolla went live!"

    async def test_falls_back_when_no_template_customized(
        self, db_session: AsyncSession, test_user: User,
    ):
        await send_notification(
            db_session, test_user.id, NotificationType.auction_rejected,
            "Auction rejected: default title", "default message",
            send_email=False, template_vars={"auction_title": "Skoda Octavia"},
        )
        result = await db_session.execute(
            select(Notification).where(Notification.user_id == test_user.id, Notification.type == NotificationType.auction_rejected)
        )
        notif = result.scalars().first()
        assert notif.title == "Auction rejected: default title"
