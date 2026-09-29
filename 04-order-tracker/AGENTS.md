# AGENTS.md

<!-- PROJECT: specific to this folder. Protected: changes need human approval. -->

Order Tracker: a small FastAPI + SQLite order-tracking service for an observability/incident-response exercise.
Layout: `app/main.py` (FastAPI app + SQLite access), `app/telemetry.py` (OpenTelemetry setup, console export), `static/index.html` (web page), `tests/` (pytest; `conftest.py` installs in-memory telemetry providers), `Dockerfile` + `compose.yaml` (run), `pyproject.toml`/`uv.lock` (uv-managed deps).
This project is one folder of a larger repository. Work only inside this folder, and run commands from here.

## Commands

<!-- Every slot is a make target or "none". -->

- **Install:** `make install`
- **Run:** `make run`: builds and starts the app plus the observability stack in `observability/`, and waits until healthy. Ports (all on 127.0.0.1, overridable by env vars) and the Grafana login are in the README.
- **Stop:** `make stop`: stops the stack and keeps all data volumes.
- **Logs:** `make logs` (follows the `app` service); `make logs-all` (follows every service)
- **Test (all):** `make test`
- **Test (one file):** `make test-one FILE=tests/test_api.py`
- **Verify:** `make verify`: tests, whitespace and weakened-test checks. How to use it: `_docs/agent-kit/procedures/verify.md`.
- **Assert clean:** `make assert-clean`: confirms nothing in this folder changed (used after QA).
- **E2E:** none
- **New migration:** none

## Project settings

- **Branching:** commit directly to `main` (observed from current repo state — confirm or correct)
- **Commits:** commit after each meaningful change, so any step can be rolled back.
- **Dependencies:** `uv add <package>` for runtime deps, `uv add --dev <package>` for dev deps.
- **Session summaries:** `_session-summaries/`, named `issue-<NNN>-<short-name>.md` (issue work) or `planning-<YYYY-MM-DD>-<short-name>.md` (planning/backlog review) — the kit's default scheme, since none exists yet.

## Project gotchas

- Run one app container at a time: SQLite has no concurrent-writer story, and the course exercise is about detecting/handling an incident, not scaling the database.
- `ORDER_DB_PATH` controls the DB file location (default `data/orders.db`); tests instead monkeypatch `main.DB_PATH` directly, so the env var doesn't affect them.
- Telemetry: `DEPLOYMENT_ENVIRONMENT` / `SERVICE_VERSION` (set in `compose.yaml`) feed the resource attributes. The app exports over OTLP only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set (Compose sets it to the Collector); console export is off unless `OTEL_CONSOLE_EXPORT=true`. Tests get in-memory OpenTelemetry providers from `tests/conftest.py`, which must be set before `app.main` is imported; `telemetry.setup()` reuses them instead of building exporters.

<!-- SHARED: from _docs/agent-kit/templates/AGENTS.md.template. Change it there first, then copy it here. -->

## Conventions

- The product spec is `_docs/specs.md`. The human owns it: propose changes, and make them only after approval. If it doesn't exist yet, the project is in planning (see `_docs/agent-kit/process.md`).
- Run project commands through `make`. If you need a command that has no target, propose a new Makefile target instead of documenting a raw command. When a target changes, propose the matching change to Commands above.
- Change only files the current task needs. If you spot an unrelated problem, note it in the session summary instead of fixing it.
- Ask before adding a dependency.
- Stage explicit paths only (`git add path/to/file`). Never use `git add .`, `git add -A` or `git commit -a`.
- Before each commit, show `git status --short`, `git diff --check`, and the exact paths being staged.
- Protected files, listed in `agent-kit.conf` (including this file and the spec), change only with human approval. Commit them with `HUMAN_APPROVED=1` only after the human has approved that specific change in this session.
- Never bypass git hooks with `--no-verify`. If a hook blocks you, fix the cause or ask the human.
- Never open, print or copy `.env` files; use `.env.example`.
- Don't push. The human reviews the diff and pushes; the pre-push hook runs `make verify`.
- Work isn't done until `make verify` passes. Never weaken or skip a test to make it pass.
- Working a GitHub issue → `_docs/agent-kit/process.md`. The main session orchestrates; each role follows its file in `_docs/agent-kit/team/`.
