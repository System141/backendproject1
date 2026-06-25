import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from app.core.database import engine, Base
from app.api import auth_router, users_router, auctions_router, uploads_router, bids_router, ws_router, payments_router, support_router, admin_router, notifications_router

# Import all models so Base metadata is populated
from app.models import *

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bidmont")


# ---- Rate limiter ----
limiter = Limiter(key_func=get_remote_address)


# ---- Auto-migration: add missing columns safely ----
MISSING_COLUMNS = {
    "users": [
        ("accepted_terms", "BOOLEAN DEFAULT FALSE"),
        ("accepted_privacy", "BOOLEAN DEFAULT FALSE"),
        ("marketing_consent", "BOOLEAN DEFAULT FALSE"),
        ("reset_token_hash", "VARCHAR"),
        ("reset_token_expires_at", "TIMESTAMP"),
        ("phone", "VARCHAR"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "auctions": [
        ("brand", "VARCHAR"),
        ("model", "VARCHAR"),
        ("year", "INTEGER"),
        ("mileage", "INTEGER"),
        ("fuel_type", "VARCHAR"),
        ("transmission", "VARCHAR"),
        ("damage_status", "VARCHAR"),
        ("equipment_brand", "VARCHAR"),
        ("serial_number", "VARCHAR"),
        ("condition", "VARCHAR"),
        ("location", "VARCHAR"),
        ("winner_user_id", "VARCHAR"),
    ],
    "bids": [
        ("ip_address", "VARCHAR"),
    ],
    "payments": [
        ("stripe_session_id", "VARCHAR"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
    "support_tickets": [
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
}


async def run_migration():
    """Add missing columns to existing tables. Safe for repeated runs."""
    async with engine.begin() as conn:
        for table, columns in MISSING_COLUMNS.items():
            for col_name, col_type in columns:
                try:
                    sql = text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS {col_name} {col_type}')
                    await conn.execute(sql)
                    logger.info(f"Migration: added {table}.{col_name}")
                except Exception as e:
                    logger.warning(f"Migration: skipped {table}.{col_name} ({e})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created. Running auto-migration...")
    await run_migration()
    logger.info("Startup complete.")
    yield
    # Shutdown: nothing to clean up
    logger.info("Shutdown complete.")


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


# ---- Health check (required for Render) ----
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


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
        return FileResponse(index_path, media_type="text/html")
    return JSONResponse(status_code=404, content={"detail": "index.html not found"})