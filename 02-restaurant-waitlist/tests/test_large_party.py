def test_create_large_party_enquiry_directly(client):
    resp = client.post(
        "/api/large-party-enquiries",
        json={"guestName": "Group Organiser", "partySize": 18, "mobileNumber": "+61 400 555 000"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["reference"] == "LP-001"
    assert body["partySize"] == 18


def test_create_large_party_enquiry_rejects_invalid_mobile(client):
    resp = client.post(
        "/api/large-party-enquiries",
        json={"guestName": "Group Organiser", "partySize": 18, "mobileNumber": "bad"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_mobile_number"


def test_notifications_list_requires_auth(client):
    resp = client.get("/api/notifications")
    assert resp.status_code == 401


def test_notifications_list_returns_most_recently_created_first(client, auth_headers):
    before = client.get("/api/notifications", headers=auth_headers).json()

    entries = client.get("/api/waitlist-entries", headers=auth_headers).json()
    ava = next(e for e in entries if e["guestName"] == "Ava Lindqvist")
    client.post(f"/api/waitlist-entries/{ava['id']}/notify", headers=auth_headers)

    after = client.get("/api/notifications", headers=auth_headers).json()
    assert len(after) == len(before) + 1
    assert after[0]["templateType"] == "table_ready"
    assert after[0]["entryId"] == ava["id"]
