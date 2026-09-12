def test_login_succeeds_with_valid_credentials(client):
    resp = client.post("/api/auth/login", json={"username": "manager", "password": "waitlist123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "manager"
    assert body["token"]
    assert body["mocked"] is True


def test_login_fails_with_invalid_password(client):
    resp = client.post("/api/auth/login", json={"username": "manager", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


def test_login_fails_with_unknown_username(client):
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "whatever"})
    assert resp.status_code == 401


def test_protected_endpoint_rejects_missing_token(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401


def test_protected_endpoint_rejects_invalid_token(client):
    resp = client.get("/api/dashboard", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_protected_endpoint_accepts_valid_token(client, auth_headers):
    resp = client.get("/api/dashboard", headers=auth_headers)
    assert resp.status_code == 200
