# Repository Guidelines

## Project Structure & Module Organization

BidMont is split into a FastAPI backend and a Next.js frontend. Backend code lives in `backend/`: `main.py` creates the app, `app/api/` contains routes, `app/models/` SQLAlchemy models, `app/schemas/` Pydantic schemas, `app/core/` infrastructure, and `app/services/` helpers. Backend tests are under `backend/tests/unit/` and `backend/tests/integration/`. Frontend code lives in `frontend/`: `pages/` for routes, `components/` for shared UI, `hooks/` for React hooks, `lib/` for API/i18n helpers, `styles/` for global CSS, and `public/locales/` for translations. Deployment files are `Dockerfile`, `docker-compose.yml`, and `render.yaml`; documentation is in `docs/`.

## Build, Test, and Development Commands

- `cd backend && pip install -r requirements.txt`: install Python dependencies.
- `cd backend && uvicorn main:app --reload`: run the API locally on port `8000`.
- `cd backend && pytest`: run all backend tests configured by `pytest.ini`.
- `cd backend && pytest tests/unit`: run only unit tests.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: run the Next.js app on port `3000`.
- `cd frontend && npm run build`: create a production frontend build.
- `cd frontend && npm run lint`: run Next.js linting.
- `docker compose up --build`: run the API with PostgreSQL.

## Coding Style & Naming Conventions

Use 4-space indentation for Python and keep FastAPI routers grouped by domain in `backend/app/api/`. Prefer async SQLAlchemy queries and Pydantic schemas for API boundaries. Python files and functions use `snake_case`; classes use `PascalCase`.

Frontend files use TypeScript/React conventions: components are `PascalCase`, hooks start with `use`, and route files follow Next.js naming such as `pages/auctions/[id].tsx`. Keep Tailwind utilities local to JSX unless a style is global.

## Testing Guidelines

Pytest is the backend test runner, with `pytest-asyncio` enabled automatically. Name tests `test_*.py`. Keep model/schema/security tests in `backend/tests/unit/`; put API and database workflow tests in `backend/tests/integration/`. Mark slow or integration-specific cases with configured markers when useful.

## Commit & Pull Request Guidelines

Recent history mixes short phase labels and imperative summaries. Prefer imperative commits such as `Add auction bid validation tests` or `Fix Docker CMD syntax`. For pull requests, include a description, test results, linked issue when applicable, and screenshots for frontend-visible changes. Call out impacts involving `DATABASE_URL`, `JWT_SECRET`, CORS, Docker, or Render settings.

## Security & Configuration Tips

Do not commit real secrets. Local defaults exist for development, but production values for `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS`, and `NEXT_PUBLIC_API_URL` should be supplied through the runtime environment.
