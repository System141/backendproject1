"""Doc §19.7: centralized error logging + admin alerting.

main.py's global exception handler is exercised directly (not via HTTP)
because it opens its own AsyncSessionLocal rather than going through the
get_db dependency override - constructing a fake ASGI Request is simpler
and more direct than routing a deliberately-broken endpoint through the
full HTTP stack just to reach the same handler function.
"""
from starlette.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import main as main_module
from tests.conftest import TestSessionLocal
from app.models.domain import Notification, NotificationType, User


def _fake_request(path="/api/boom"):
    scope = {"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""}
    return Request(scope)


class TestUnhandledExceptionHandler:
    async def test_returns_500_without_leaking_internals(self, monkeypatch):
        monkeypatch.setattr(main_module, "AsyncSessionLocal", TestSessionLocal)
        response = await main_module.unhandled_exception_handler(_fake_request(), ValueError("boom, secret detail"))
        assert response.status_code == 500
        assert response.body == b'{"detail":"Internal server error"}'

    async def test_alerts_admins(self, monkeypatch, db_session: AsyncSession, admin_user: User):
        monkeypatch.setattr(main_module, "AsyncSessionLocal", TestSessionLocal)
        await main_module.unhandled_exception_handler(_fake_request("/api/whatever"), RuntimeError("kaboom"))

        result = await db_session.execute(
            select(Notification).where(Notification.user_id == admin_user.id, Notification.type == NotificationType.system_alert)
        )
        assert len(result.scalars().all()) == 1

    async def test_alerting_failure_does_not_break_response(self, monkeypatch):
        """Even if the alert path itself blows up, the client still gets a 500."""
        def _broken_session_factory():
            raise RuntimeError("DB unreachable")
        monkeypatch.setattr(main_module, "AsyncSessionLocal", _broken_session_factory)
        response = await main_module.unhandled_exception_handler(_fake_request(), ValueError("boom"))
        assert response.status_code == 500
