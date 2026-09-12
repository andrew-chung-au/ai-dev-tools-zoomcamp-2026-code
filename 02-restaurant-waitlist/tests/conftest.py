import pytest
from fastapi.testclient import TestClient

from backend.main import create_app

STAFF_USERNAME = "manager"
STAFF_PASSWORD = "waitlist123"


@pytest.fixture
def client():
    app = create_app()
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
