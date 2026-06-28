import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.database import engine, Base, get_db
from app.core.scheduler import run_scheduler
from app.core.migrations import run_migration_async
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.models.domain import Category
from app.api import auth_router, users_router, auctions_router, uploads_router, bids_router, ws_router, payments_router, support_router, admin_router, notifications_router
from app.api.credits import credits_router
from app.api.ws import manager

# Import all models so Base metadata is populated
from app.models import *

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bidmont")

# ---- Rate limiter ----
limiter = Limiter(key_func=get_remote_address)


UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "backend", "uploads"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Run auto-migration for missing columns
        await run_migration_async(conn)
    logger.info("Tables created, migrations complete.")
    # Start background scheduler for auto-finalize
    scheduler_task = asyncio.create_task(run_scheduler())
    await manager.start_heartbeat()
    logger.info("Startup complete (scheduler + heartbeat started).")
    yield
    # Shutdown: cancel scheduler
    scheduler_task.cancel()
    logger.info("Shutdown complete (scheduler cancelled).")


app = FastAPI(
    title="BidMont API",
    description="Online auctions for Montenegro",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Register rate-limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS – tightened for production
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://bidmont.onrender.com,http://localhost:8000,http://localhost:3000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(auctions_router)
app.include_router(uploads_router)
app.include_router(bids_router)
app.include_router(ws_router)
app.include_router(payments_router)
app.include_router(support_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(credits_router)

# Mount static files for uploads (before SPA catch-all)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ---- Health check (required for Render) ----
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


# ---- Public categories list (for sell form) ----
@app.get("/api/categories")
async def list_categories_public(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.id))
    cats = result.scalars().all()
    return [{"id": c.id, "name": c.name, "slug": c.slug, "status": c.status or "active"} for c in cats]


# ---- Serve the SPA index.html ----
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Don't intercept API routes
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    index_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "index.html"
    )
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html", headers={"Cache-Control": "no-cache, must-revalidate"})
    return JSONResponse(status_code=404, content={"detail": "index.html not found"})