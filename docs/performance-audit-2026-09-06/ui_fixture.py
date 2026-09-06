"""Local UI smoke fixture. Isolated memory DB; http://127.0.0.1:8765."""
import os
import sys
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
os.environ.update(DATABASE_URL="sqlite+aiosqlite://", JWT_SECRET="local-ui-fixture",
                  ENVIRONMENT="development", SMTP_HOST="", SMTP_USER="", SMTP_PASSWORD="")

import uvicorn
from sqlalchemy import insert
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.domain import Auction, User, _utcnow
from main import app, lifespan


@asynccontextmanager
async def fixture_lifespan(app):
    async with lifespan(app):
        async with AsyncSessionLocal() as db:
            db.add(User(id="ui-admin", name="Preview Admin", email="preview@example.invalid",
                password_hash=hash_password("PreviewOnly123!"), role="admin", email_verified=True))
            await db.flush()
            now = _utcnow()
            await db.execute(insert(Auction), [dict(id=f"ui-a{i:03}", seller_id="ui-admin", category_id=1,
                title=f"Preview auction {i:03}", description="Synthetic UI fixture", status="live",
                start_price=1, current_price=10, min_increment=1, start_time=now,
                end_time=now+timedelta(hours=2)) for i in range(125)])
            await db.commit()
        yield


if __name__ == "__main__":
    app.router.lifespan_context = fixture_lifespan
    uvicorn.run(app, host="127.0.0.1", port=8765)
