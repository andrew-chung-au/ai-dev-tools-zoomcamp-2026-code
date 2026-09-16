"""Fixtures for integration tests against the live docker-compose stack.

Unlike `tests/conftest.py`'s in-process `TestClient` fixture (SQLite,
no containers), these tests talk over real HTTP to the `app` container
started from `docker-compose.yml`, which is wired to a real `postgres`
container. They need Docker and are excluded from the default
`uv run pytest` run — see the `integration` marker registered in
`pyproject.toml`.
"""

import json
import subprocess
import time
from pathlib import Path

import httpx2
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "http://localhost:8091"
READY_TIMEOUT_SECONDS = 90


def _compose(*args: str) -> None:
    subprocess.run(["docker", "compose", *args], cwd=PROJECT_ROOT, check=True)


def _app_is_up() -> bool:
    try:
        return httpx2.get(f"{BASE_URL}/api/venue", timeout=2).status_code < 500
    except httpx2.HTTPError:
        return False


def _wait_until_ready(timeout: float = READY_TIMEOUT_SECONDS) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _app_is_up():
            return
        time.sleep(1)
    raise RuntimeError(f"app service did not become ready within {timeout}s")


@pytest.fixture(scope="session")
def docker_stack():
    """Ensure the docker-compose `app` + `postgres` stack is running.

    Reuses a stack a developer already started by hand and leaves it
    running afterwards; only starts/stops it here when it had to bring it
    up itself, so it doesn't tear down state someone else is using.
    """
    started_here = False
    if not _app_is_up():
        _compose("up", "-d", "--build")
        started_here = True
        _wait_until_ready()

    yield BASE_URL

    if started_here:
        _compose("down")


def _query_postgres(sql: str, params: tuple = ()) -> list:
    """Run `sql` against Postgres using the `app` container's own
    `DATABASE_URL`, proving a row really landed in the `postgres` service
    (as opposed to merely being echoed back by the API).
    """
    script = (
        "import json, os, psycopg2\n"
        "conn = psycopg2.connect(os.environ['DATABASE_URL'])\n"
        "cur = conn.cursor()\n"
        f"cur.execute({sql!r}, {params!r})\n"
        "print(json.dumps(cur.fetchall()))\n"
    )
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "app", "uv", "run", "--no-sync", "python", "-c", script],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


@pytest.fixture
def postgres_query():
    return _query_postgres
