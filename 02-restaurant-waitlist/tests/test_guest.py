def test_guest_join_creates_pending_entry_in_staff_review_mode(client):
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 2,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "entry"
    assert body["entry"]["status"] == "pending"
    assert body["entry"]["ticketCode"].startswith("A-")
    assert body["accessToken"]


def test_guest_join_creates_waiting_entry_in_automatic_mode(client, auth_headers):
    client.patch("/api/venue", json={"entryMode": "automatic"}, headers=auth_headers)
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 2,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["entry"]["status"] == "waiting"


def test_guest_join_requires_policy_acknowledgement(client):
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 2,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": False,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "policy_not_acknowledged"


def test_guest_join_rejects_invalid_mobile_number(client):
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 2,
            "mobileNumber": "not-a-number",
            "policyAcknowledged": True,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_mobile_number"


def test_guest_join_rejects_invalid_party_size(client):
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 0,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_party_size"


def test_guest_join_above_max_party_size_creates_large_party_enquiry(client):
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Big Group",
            "partySize": 20,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "large_party_enquiry"
    assert body["enquiry"]["reference"] == "LP-001"
    assert body["enquiry"]["partySize"] == 20


def test_guest_join_rejected_when_waitlist_closed(client, auth_headers):
    client.patch("/api/venue", json={"waitlistOpen": False}, headers=auth_headers)
    resp = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 2,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "closed"
    assert "closed" in body["message"].lower()


def test_guest_can_view_and_cancel_own_entry(client):
    join = client.post(
        "/api/waitlist-entries",
        json={
            "guestName": "Jamie Rivers",
            "partySize": 2,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    ).json()
    access_token = join["accessToken"]

    status_resp = client.get(f"/api/guest/entries/{access_token}")
    assert status_resp.status_code == 200
    assert status_resp.json()["ticketCode"] == join["entry"]["ticketCode"]

    cancel_resp = client.post(f"/api/guest/entries/{access_token}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"


def test_guest_cannot_access_another_entry_with_unknown_token(client):
    resp = client.get("/api/guest/entries/tok_does_not_exist")
    assert resp.status_code == 404
