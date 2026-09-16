# Table Ready

Configurable restaurant waitlist and table‑management application for independent venues.

Guests join the queue via a mobile‑friendly QR code or link. Staff manage tickets, tables, estimated waits, notifications, seating, cancellations, and no‑shows from an authenticated dashboard.

This repository implements Module 2 of AI Dev Tools Zoomcamp: frontend + FastAPI backend + OpenAPI contract + SQLite persistence with SQLAlchemy.

## Quick start

```bash
# Backend (port 8091)
make run

# Frontend (port 8080)
cd frontend
bun run dev
```

Open `http://localhost:8080` in your browser.

## Tests

```bash
make test
```

Runs both frontend and backend test suites.

## Documentation

- Product specification: [`_docs/specs.md`](_docs/specs.md)
- UAT / manual test script: [`UAT.md`](UAT.md)
- Frontend README: [`frontend/README.md`](frontend/README.md)
- AI usage report: [`docs/ai-usage-report.md`](docs/ai-usage-report.md)

## Configuration

Key environment variables:

- Frontend: `VITE_API_BASE_URL` (default `http://localhost:8091/api`), `VITE_USE_MOCK_SERVICE`
- Backend: `DATABASE_URL` (default `sqlite:///./waitlist.db`), `ALLOWED_ORIGINS`

See `frontend/.env.example` and `_docs/specs.md` for details.

## Tech stack

- Frontend: React, TypeScript, TanStack Start, Tailwind CSS
- Backend: Python, FastAPI, SQLAlchemy, SQLite
- Contract: OpenAPI (`openapi.yaml`)