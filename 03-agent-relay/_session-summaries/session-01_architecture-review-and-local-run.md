# Session 1 — Architecture review and local run

First session in this module (`03-agent-relay`, the SQLite-starter FastAPI
service from Module 3). No prior `_session-summaries` existed here yet; this
file establishes the convention for the module. No code was changed.

## What happened

### Architecture identification

Read `SPEC.md`, `main.py`, and `database.py` to answer which of four
candidate architectures the project implements:

- ~~Agents exchange tasks directly with each other~~
- **Agents claim tasks from a DB through an HTTP API** ← correct
- ~~Agents consume tasks from a message broker~~
- ~~The browser stores and executes tasks~~

Evidence:

- `main.py` exposes `POST /api/v1/tasks/claim`, which agents poll (with long
  polling via `wait_seconds`) to pull work addressed to their own identity —
  there is no agent-to-agent channel and no broker/queue dependency.
- `database.py` persists agents, tasks, and attempts in SQLite via
  SQLAlchemy, and serializes claims across API/worker processes with a
  `BEGIN IMMEDIATE` writer transaction (`immediate_transaction()`) — SQLite's
  stand-in for `SELECT ... FOR UPDATE SKIP LOCKED`, called out in `SPEC.md`
  as the seam for a future Postgres port.
- `SPEC.md` §"Components and identity" states execution happens in the
  agent's own process ("Agents execute tasks on their own machines"); the
  relay only stores state and never runs submitted task content. The
  dashboard (`GET /` and `/dashboard`) is read-only observability over the
  same authenticated API, not a task executor.

### Local run

Started the app per the README's documented command:

```bash
uv run uvicorn main:app --reload
```

First invocation triggered a cold `uv` environment bootstrap (downloaded
CPython 3.11.16, resolved and installed 32 packages into `.venv`) before
Uvicorn came up. Confirmed healthy via `GET /health` → `200`. Server is
running in the background at `http://127.0.0.1:8000/`, with the dashboard at
`/` or `/dashboard`.

## Open items / next steps

- No agents were registered and no task was sent end-to-end in this session
  — only a health check. A natural next step is running the README's
  register-two-agents-and-send-a-task walkthrough, or exercising the
  deterministic worker (`python main.py worker ...`) against the running
  server.
- The background Uvicorn process (`--reload`) from this session is still
  running; a future session picking this module back up should check
  whether it's still alive before starting another instance on the same
  port.
