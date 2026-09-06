import os
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.database import engine, Base, get_db, AsyncSessionLocal
from app.core.scheduler import run_scheduler
from app.core.migrations import run_migration_async
from app.core.category_seed import seed_default_categories
from app.core.credit_package_seed import seed_default_credit_packages
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.models.domain import Category
from app.api import auth_router, users_router, auctions_router, uploads_router, bids_router, ws_router, support_router, admin_router, notifications_router, watchlist_router, legal_router, sellers_router
from app.api.credits import credits_router
from app.api.ws import manager
from app.services.notifications import alert_admins, run_email_worker

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


class _RequestBodyTooLarge(Exception):
    pass


class RequestBodyLimitMiddleware:
    """Reject oversized upload bodies before Starlette parses multipart data."""

    LIMITS = (
        ("/api/auctions/bulk-import", 3 * 1024 * 1024),
        ("/api/uploads/batch", 52 * 1024 * 1024),
        ("/api/uploads/documents", 52 * 1024 * 1024),
        ("/api/uploads", 12 * 1024 * 1024),
        ("/api/sellers/me/verification-document", 12 * 1024 * 1024),
    )

    def __init__(self, app):
        self.app = app

    @classmethod
    def limit_for(cls, path: str) -> int | None:
        for prefix, limit in cls.LIMITS:
            if path == prefix or path.startswith(prefix + "?"):
                return limit
        return None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        limit = self.limit_for(scope["path"])
        if limit is None:
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for key, value in scope.get("headers", []) if key.lower() == b"content-length"),
            None,
        )
        if content_length is not None:
            try:
                if int(content_length) > limit:
                    await self._send_rejection(send)
                    return
            except ValueError:
                pass

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    await self._send_rejection(send)
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            return

    @staticmethod
    async def _send_rejection(send):
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"detail":"Request body too large"}',
        })


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Run auto-migration for missing columns
        await run_migration_async(conn)
    logger.info("Tables created, migrations complete.")
    async with AsyncSessionLocal() as seed_db:
        await seed_default_categories(seed_db)
        await seed_default_credit_packages(seed_db)
    # Start background scheduler for auto-finalize
    scheduler_task = asyncio.create_task(run_scheduler())
    email_task = asyncio.create_task(run_email_worker())
    await manager.start_heartbeat()
    logger.info("Startup complete (scheduler + heartbeat started).")
    yield
    # Shutdown: cancel scheduler
    scheduler_task.cancel()
    email_task.cancel()
    await asyncio.gather(scheduler_task, email_task, return_exceptions=True)
    await manager.stop_heartbeat()
    logger.info("Shutdown complete (scheduler cancelled).")


app = FastAPI(
    title="BidMont API",
    description="Online auctions for Montenegro",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

class TextCompressionMiddleware(GZipMiddleware):
    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if path.startswith(("/api/uploads", "/assets/img/")) or path.endswith((".png", ".ico", ".webp", ".jpg")):
            await self.app(scope, receive, send)
        else:
            await super().__call__(scope, receive, send)


app.add_middleware(RequestBodyLimitMiddleware)
# Disable when the deployment proxy already compresses responses.
if os.getenv("HTTP_COMPRESSION", "true").lower() == "true":
    app.add_middleware(TextCompressionMiddleware, minimum_size=1000, compresslevel=5)

# Register rate-limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Doc §19.7: "Centralized application error logs" + "kritik hata icin admin
# teknik ekibe uyari uretmeli". Catches anything an endpoint didn't already
# handle (HTTPException still goes through FastAPI's own handler, never
# reaches here) so no 500 is ever silent - logged at CRITICAL, and every
# admin gets an in-app + email alert via the same notification system as
# the two other §19.7 call sites (scheduler.py, credits.py).
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    try:
        async with AsyncSessionLocal() as db:
            # event_key scoped to endpoint+exception type+calendar day (not
            # per-request) so a persistently broken endpoint alerts once per
            # day, not once per failed request - and, unlike an undated key,
            # still re-alerts the next day if the bug isn't fixed, rather
            # than firing exactly once for the lifetime of that row.
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            await alert_admins(
                db,
                f"Unhandled server error: {request.method} {request.url.path}",
                f"{type(exc).__name__}: {exc}",
                event_key=f"unhandled_error:{request.method}:{request.url.path}:{type(exc).__name__}:{today}",
            )
    except Exception:
        pass  # ponytail: never let the alerting path itself take down error handling
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Doc §19.1: redirect HTTP -> HTTPS in production. Gated by ENVIRONMENT so
# local dev/tests (plain HTTP, no TLS) and the docker-compose stack aren't
# broken by default. Only correct once a reverse proxy actually terminates
# TLS in front of this app - if that proxy also forwards X-Forwarded-Proto,
# fine; if it doesn't, this middleware alone can't detect an already-HTTPS
# request from the proxy and would loop. That reverse-proxy wiring is the
# infra half of §19.1 (domain/TLS/proxy choice), outside this repo's scope.
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS – tightened for production
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8000,http://localhost:3000",
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
app.include_router(support_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(credits_router)
app.include_router(watchlist_router)
app.include_router(legal_router)
app.include_router(sellers_router)

# Uploads are served only through the authorization-aware media endpoint.
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount the site's own asset bundle (css/js/img) - also before the catch-all
SITE_DIR = os.path.dirname(os.path.dirname(__file__))
app.mount("/assets", StaticFiles(directory=os.path.join(SITE_DIR, "assets")), name="assets")


# ---- Health check ----
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
    return [{"id": c.id, "name": c.name, "slug": c.slug, "parent_id": c.parent_id, "status": c.status or "active"} for c in cats]


# ---- Serve the static site (multi-page, no build step) ----
# Whitelisted, not a path join off `full_path` - that's user input and
# `.env` (with JWT_SECRET) lives in this same directory.
SITE_FILES = {
    "index.html", "auctions.html", "auth.html", "credits.html", "auction.html", "account.html", "support.html",
    "admin.html",
    "favicon.ico", "favicon-32.png", "apple-touch-icon.png",
    "robots.txt", "sitemap.xml",
}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Don't intercept API routes
    if full_path.startswith("api/") or full_path == "uploads" or full_path.startswith("uploads/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    filename = full_path if full_path in SITE_FILES else "index.html"
    file_path = os.path.join(SITE_DIR, filename)
    if os.path.exists(file_path):
        media_type = "text/html" if filename.endswith(".html") else None
        return FileResponse(file_path, media_type=media_type, headers={"Cache-Control": "no-cache, must-revalidate"})
    return JSONResponse(status_code=404, content={"detail": "Not found"})
