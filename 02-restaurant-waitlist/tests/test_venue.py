def test_get_venue_requires_no_auth(client):
    resp = client.get("/api/venue")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Demo Restaurant"


def test_update_venue_requires_auth(client):
    resp = client.patch("/api/venue", json={"name": "New Name"})
    assert resp.status_code == 401


def test_update_venue_changes_fields(client, auth_headers):
    resp = client.patch(
        "/api/venue",
        json={
            "name": "Renamed Bistro",
            "gracePeriodMinutes": 15,
            "maxOnlinePartySize": 10,
            "defaultWaitEstimateMinutes": {"A": 20},
            "messages": {"joinMessage": "Welcome!"},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renamed Bistro"
    assert body["gracePeriodMinutes"] == 15
    assert body["maxOnlinePartySize"] == 10
    assert body["defaultWaitEstimateMinutes"]["A"] == 20
    assert body["defaultWaitEstimateMinutes"]["B"] == 25
    assert body["messages"]["joinMessage"] == "Welcome!"
    assert body["messages"]["cancellationMessage"]


def test_update_venue_rejects_blank_name(client, auth_headers):
    resp = client.patch("/api/venue", json={"name": "   "}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_name"


def test_update_venue_rejects_invalid_grace_period(client, auth_headers):
    resp = client.patch("/api/venue", json={"gracePeriodMinutes": 0}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_grace_period"
