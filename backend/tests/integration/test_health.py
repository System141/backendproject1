"""Integration tests for the health check endpoint."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Category


class TestHealth:
    async def test_health_endpoint(self, async_client: AsyncClient):
        """GET /api/health should return 200 with status info."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data

    async def test_health_includes_version(self, async_client: AsyncClient):
        """Health response should include version string."""
        response = await async_client.get("/api/health")
        data = response.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    async def test_health_includes_environment(self, async_client: AsyncClient):
        """Health response should include environment."""
        response = await async_client.get("/api/health")
        data = response.json()
        # In test context, the env var may not be set, so should default
        assert data["environment"] is not None

    async def test_health_not_authenticated(self, async_client: AsyncClient):
        """Health endpoint should be accessible without auth."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        # Ensure no auth redirect
        assert "access_token" not in response.json() or response.json()["status"] == "ok"


class TestPublicCategories:
    async def test_includes_parent_id(self, async_client: AsyncClient, db_session: AsyncSession):
        """doc §7.2.1: the frontend resolves a subcategory up to its
        top-level ancestor via parent_id - this field was silently missing
        from the public list response, which made every subcategory look
        like an unrelated top-level category to the client."""
        parent = Category(name="Commercial Assets Test", slug="commercial-assets-test", status="active")
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)
        child = Category(name="Hospitality Test", slug="hospitality-test", parent_id=parent.id, status="active")
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)

        response = await async_client.get("/api/categories")
        assert response.status_code == 200
        rows = {row["id"]: row for row in response.json()}
        assert rows[parent.id]["parent_id"] is None
        assert rows[child.id]["parent_id"] == parent.id