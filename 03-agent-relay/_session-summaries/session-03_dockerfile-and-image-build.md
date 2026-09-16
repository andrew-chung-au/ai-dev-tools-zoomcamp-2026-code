# Session 3 — Dockerfile, image build, and `-p` vs `--expose`

Continues [[session-02_test-flow-integration-test]]. Adds containerization
for Agent Relay; no application code changed.

## What changed

### `Dockerfile` (new)

Based on `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, using the standard
`uv` two-stage-sync pattern for layer caching:

1. Set `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`, `PYTHONUNBUFFERED=1`.
2. Copy only `pyproject.toml` + `uv.lock` and run
   `uv sync --locked --no-install-project --no-dev` so dependency layers
   stay cached across source-only changes.
3. Copy the rest of the project, then `uv sync --locked --no-dev` to install
   the project itself.
4. Put `/app/.venv/bin` on `PATH`, `EXPOSE 8000`.
5. `CMD ["uv", "run", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`.

### `.dockerignore` (new)

Mirrors `.gitignore` (`.venv`, `__pycache__/`, `*.db*`, `*-credentials.json`,
`.pytest_cache/`) plus `_session-summaries/` and `.git`, keeping the build
context small and avoiding a stale local `.venv`/db leaking into the image.

## Bug caught by smoke-testing before handing off

First build's `CMD` used plain `uv run uvicorn ...` (no `--no-sync`). A
smoke test (`docker run ... -p 8001:8000`, then `curl /health`) initially
returned `000`; container logs showed `uv run` re-resolving and installing
the **dev** dependency group (pytest, httpx, and their transitive
`pygments`) on every container start, since the build's `uv sync` had used
`--no-dev` but the runtime `uv run` did not. That's a real problem beyond
slow startup: a locked-down/offline production runtime would fail to start
at all if it can't reach the package index. Fixed by adding `--no-sync` to
the `CMD`'s `uv run` so the container strictly uses the venv baked in at
build time. Rebuilt and reconfirmed: `/health` → `200` within ~3s, no
runtime downloads in the logs.

**Takeaway for future Dockerfiles in this repo:** when a `uv sync` at build
time uses `--no-dev`, the runtime `uv run` in `CMD`/`ENTRYPOINT` needs
`--no-sync` (or matching flags) — otherwise `uv run`'s default sync-on-run
behavior silently installs the dev group at container start.

## Result

- Built `docker build -t agent-relay:local .` successfully after the fix.
- Verified with a throwaway container on host port 8001 before delivering
  the final run command.
- Delivered run command: `docker run -d --name agent-relay -p 8000:8000 agent-relay:local`.
- Noted the container's default SQLite DB (`./agent-relay.db`) is
  ephemeral without a volume mount or `RELAY_DATABASE_URL` override.
- Answered a follow-up quiz question: `-p` publishes a container port to
  the host (`--expose` only declares it within Docker networking, `-v` is
  volumes, `--name` just names the container).

## Open items / next steps

- No volume/persistence strategy was set up for the containerized DB —
  worth revisiting if this Dockerfile is meant for anything beyond a local
  demo (compare to `02-restaurant-waitlist`'s Postgres Compose stack from
  its own step 8).
- The `agent-relay:local` image and any test containers from this session
  are local-only; nothing was pushed to a registry.
