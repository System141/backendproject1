import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.core.database import engine, Base
# Import all models so Base metadata is populated
from app.models import *

app = FastAPI(title="BidMont API", description="Online auctions for Montenegro")

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
    return {"error": "index.html bulunamiyor."}
# For serving static assets if we add a static folder later
# app.mount("/static", StaticFiles(directory="static"), name="static")
