# Repository Guidelines

## Project Structure & Module Organization

BidMont is a FastAPI backend that serves both the API and a Single-Page Application (SPA). Backend code lives in `backend/`: `main.py` creates the app, `app/api/` contains routes, `app/models/` SQLAlchemy models, `app/schemas/` Pydantic schemas, `app/core/` infrastructure, `app/services/` helpers (including shared business logic in `app/services/auctions.py`), and `app/core/migrations.py` for unified auto-migration. Backend tests are under `backend/tests/unit/` and `backend/tests/integration/`.

The frontend is an SPA served from the backend root route via `index.html` (located at project root). A legacy Next.js frontend is archived at `docs/legacy/frontend-nextjs/`. Deployment files are `Dockerfile` and `docker-compose.yml`; documentation is in `docs/`.

**Key service modules:**
- `app/services/auctions.py` — shared `finalize_auction()` (used by REST + scheduler) and `build_auction_response()`
- `app/services/notifications.py` — in-app + email notification service
- `app/core/migrations.py` — single source of truth for missing column auto-migration
- `app/api/ws.py` — WebSocket `ConnectionManager` for live bid broadcasts

## Build, Test, and Development Commands

- `cd backend && pip install -r requirements.txt`: install Python dependencies.
- `cd backend && uvicorn main:app --reload`: run the API locally on port `8000`. The SPA is served at `http://localhost:8000/`.
- `cd backend && pytest`: run all backend tests (107 tests: 54 unit + 53 integration).
- `cd backend && pytest tests/unit`: run only unit tests.
- `cd backend && pytest tests/integration`: run only integration tests.
- `docker compose up --build`: run the API with PostgreSQL.

## Coding Style & Naming Conventions

Use 4-space indentation for Python and keep FastAPI routers grouped by domain in `backend/app/api/`. Prefer async SQLAlchemy queries and Pydantic schemas for API boundaries. Python files and functions use `snake_case`; classes use `PascalCase`.

Service-layer functions that are shared between REST endpoints and background tasks should live in `app/services/` and avoid circular imports by keeping WebSocket imports lazy.

## Testing Guidelines

Pytest is the backend test runner, with `pytest-asyncio` enabled automatically. Name tests `test_*.py`. Keep model/schema/security tests in `backend/tests/unit/`; put API and database workflow tests in `backend/tests/integration/`. Mark slow or integration-specific cases with configured markers when useful.

## Commit & Pull Request Guidelines

Recent history mixes short phase labels and imperative summaries. Prefer imperative commits such as `Add auction bid validation tests` or `Fix Docker CMD syntax`. For pull requests, include a description, test results, linked issue when applicable, and screenshots for frontend-visible changes. Call out impacts involving `DATABASE_URL`, `JWT_SECRET`, CORS, or Docker settings.

## Security & Configuration Tips

Do not commit real secrets. `JWT_SECRET` must never be hardcoded in `Dockerfile` — supply through runtime environment. Production values for `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS` should be supplied through the runtime environment. The `forgot-password` endpoint hashes reset tokens and only returns them in `development` mode.

## Deployment Targets

- **Private Linux server via Docker** (primary demo, `Dockerfile` + `docker-compose.yml`): persistent process, local disk uploads, in-process WebSocket broadcast, continuous background scheduler (`app/core/scheduler.py`). No extra config needed beyond `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS` in the runtime environment.
