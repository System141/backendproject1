import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.core.database import engine, Base
from app.api import auth_router, users_router

# Import all models so Base metadata is populated
from app.models import *

app = FastAPI(title="BidMont API", description="Online auctions for Montenegro")

# CORS — allow frontend from any origin in dev, lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Render frontend will be same-origin; for dev we allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(users_router)


@app.on_event("startup")
async def startup():
    # Create tables. In production, use Alembic migrations instead.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def serve_index():
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found."}


# For serving static assets if we add a static folder later
# app.mount("/static", StaticFiles(directory="static"), name="static")