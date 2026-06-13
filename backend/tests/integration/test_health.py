"""Integration tests for the health check endpoint."""
from httpx import AsyncClient


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