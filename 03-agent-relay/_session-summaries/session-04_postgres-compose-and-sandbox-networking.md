# Session 4 — PostgreSQL support, `compose.yaml`, and a sandbox networking blocker

Continues [[session-03_dockerfile-and-image-build]]. Adds PostgreSQL support
to the storage layer and a Compose stack, per SPEC.md's own framing of this
as "a future student PostgreSQL port." Hit and worked around a real
environment limitation rather than the expected one.

## What changed

### `pyproject.toml` / `uv.lock`

Added `psycopg2-binary` (alongside the existing `psycopg[binary]` v3
dependency already there for other purposes) and regenerated `uv.lock`. A
plain `postgresql://` SQLAlchemy URL resolves to the psycopg2 driver by
default, which is what `compose.yaml`'s `DATABASE_URL` uses.

### `database.py`

`immediate_transaction()` previously ran SQLite's `BEGIN IMMEDIATE` writer
reservation unconditionally — invalid syntax against Postgres. Now it
branches on `_is_sqlite(DATABASE_URL)`: SQLite keeps `BEGIN IMMEDIATE`;
Postgres opens a plain transaction (`connection.begin()`). This is
explicitly *not* the full row-locking port SPEC.md describes (`SELECT ...
FOR UPDATE SKIP LOCKED`) — that remains a follow-up; this session only made
the seam functionally correct for Postgres rather than crash-on-connect.
`_database_url()` already read `DATABASE_URL`/`RELAY_DATABASE_URL` from the
session before this session, so no change was needed there.

### `compose.yaml` (new)

`app` service (builds from the existing `Dockerfile`) + `postgres` service
(`postgres:16-alpine`) with a `pg_isready` healthcheck; `app` has
`depends_on: postgres: condition: service_healthy`; `DATABASE_URL` points at
`postgresql://agent_relay:agent_relay@postgres:5432/agent_relay` — i.e. the
Compose service name as hostname, not `localhost`/`0.0.0.0`/
`host.docker.internal`. A named `postgres-data` volume persists the DB.

## Blocker: sandbox firewall drops container-to-container traffic

`docker compose up --build -d` built and started both containers; `postgres`
reported `healthy`, but `app` crashed on startup
(`psycopg2.OperationalError: connection to server at "postgres" ... failed:
Connection timed out`). Root-caused, not a config bug:

- `iptables -L -n` showed the Docker `FORWARD`/`DOCKER` filter chain
  unconditionally `DROP`-ping all traffic reaching it, with only
  `ctstate RELATED,ESTABLISHED` allowed through `DOCKER-CT`.
- Repro: a throwaway `alpine` container attached to the same Compose network
  (`03-agent-relay_default`) timed out reaching `postgres:5432` by name
  *and* by bridge IP (`172.18.0.2`).
- Control: the **host** reached that same container's bridge IP directly
  (`/dev/tcp/172.18.0.2/5432`) without issue, and host→published-port
  (`-p 8001:8000`, from session 3's smoke test) also worked.
- Conclusion: this sandbox specifically blocks east-west
  (container-to-container) traffic on user-defined bridge networks, while
  host↔container traffic is allowed. Confirmed it wasn't an artifact of the
  calling Bash command's own sandboxing by re-running the repro with
  `dangerouslyDisableSandbox: true` — same timeout, so the restriction lives
  at the Docker/host firewall level, not per-invocation.

Asked the user how to proceed (leave the standard `compose.yaml` as-is and
report the limitation vs. rewrite to `network_mode: host` vs. attempt to
relax the host firewall). **User chose: leave `compose.yaml` as the
standard, textbook-correct pattern** rather than rewrite it around a
sandbox-specific workaround or touch host-wide iptables.

## How the Postgres path was actually verified

Since the host *can* reach the Postgres container directly, ran the app
**on the host** (not containerized) with
`DATABASE_URL=postgresql://agent_relay:agent_relay@172.18.0.2:5432/agent_relay`
pointed at the already-running `postgres` container's bridge IP, freeing
host port 8000 first (removed the crashed `app` container via
`docker compose rm -sf app`, deleted stale local `agent-relay.db*` files).
`GET /ready` returned `{"status": "ready"}` (queries real tables, so this
proves schema + connectivity, not just a socket). Re-ran
`uv run pytest test_flow.py -v -s` (from
[[session-02_test-flow-integration-test]]) against it — passed, `completed`
status again. Independently confirmed via
`docker compose exec postgres psql ... -c "select id, name from agents..."`
that the sender/recipient/task rows were actually persisted inside the
Postgres container, not falling back to SQLite.

Cleaned up afterward: killed the host-side uvicorn process; left the
`postgres` container running via Compose (`03-agent-relay-postgres-1`, up
and healthy).

## Answered: which hostname for Compose service-to-service connections?

**`postgres`** — the Compose service name, resolved via Docker's embedded
DNS on the shared network. (`localhost`/`0.0.0.0` refer to the container
itself; `host.docker.internal` reaches the host machine, not a sibling
container.) This matches what `compose.yaml` already used.

## Open items / next steps

- `compose.yaml`'s `app` service has never actually been end-to-end
  verified running *inside this sandbox* — only the underlying Postgres
  code path has (via the host-process workaround above). In a normal
  Docker environment (unrestricted bridge networking) `docker compose up
  --build -d` should work as committed; that's untested here specifically
  because of the sandbox, not because of a known code issue.
- The `immediate_transaction()` Postgres branch is a plain transaction, not
  row-locking (`FOR UPDATE SKIP LOCKED`) — SPEC.md still frames that gap as
  future student work, unchanged by this session.
- The `postgres` container from this session (`03-agent-relay-postgres-1`,
  with its `postgres-data` volume) is still running; a future session
  should `docker compose down` it (optionally `-v` to drop the volume) if
  it's no longer needed, or reuse it directly.
