import pytest
from fastapi.testclient import TestClient

from backend.db import Base, make_engine
from backend.main import create_app

STAFF_USERNAME = "manager"
STAFF_PASSWORD = "waitlist123"


@pytest.fixture
def client(tmp_path):
    # Each test gets its own SQLite file so tests stay isolated from each
    # other and from a developer's local waitlist.db. Production/Docker
    # schemas come from Alembic migrations (see backend/alembic/), but that's
    # unnecessary ceremony for these ephemeral per-test databases, so create
    # the schema directly from the ORM metadata instead.
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    Base.metadata.create_all(bind=make_engine(database_url))
    app = create_app(database_url=database_url)
    return TestClient(app)


@pytest.fixture
def staff_token(client):
    resp = client.post(
        "/api/auth/login", json={"username": STAFF_USERNAME, "password": STAFF_PASSWORD}
    )
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def auth_headers(staff_token):
    return {"Authorization": f"Bearer {staff_token}"}
