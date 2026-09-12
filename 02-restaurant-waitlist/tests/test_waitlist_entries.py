def find_entry(entries, guest_name):
    return next(e for e in entries if e["guestName"] == guest_name)


def list_entries(client, auth_headers):
    resp = client.get("/api/waitlist-entries", headers=auth_headers)
    assert resp.status_code == 200
    return resp.json()


def test_list_waitlist_entries_returns_seeded_data(client, auth_headers):
    entries = list_entries(client, auth_headers)
    assert len(entries) == 7
    names = {e["guestName"] for e in entries}
    assert "Ava Lindqvist" in names
    assert "Diego Salas" in names


def test_approve_pending_entry(client, auth_headers):
    entries = list_entries(client, auth_headers)
    hannah = find_entry(entries, "Hannah Cole")
    assert hannah["status"] == "pending"

    resp = client.post(f"/api/waitlist-entries/{hannah['id']}/approve", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "waiting"


def test_approve_rejects_non_pending_entry(client, auth_headers):
    entries = list_entries(client, auth_headers)
    ava = find_entry(entries, "Ava Lindqvist")
    assert ava["status"] == "waiting"

    resp = client.post(f"/api/waitlist-entries/{ava['id']}/approve", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_status"


def test_notify_waiting_entry_records_notification_and_return_by(client, auth_headers):
    entries = list_entries(client, auth_headers)
    ava = find_entry(entries, "Ava Lindqvist")

    resp = client.post(f"/api/waitlist-entries/{ava['id']}/notify", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["entry"]["status"] == "notified"
    assert body["entry"]["notifiedAt"] is not None
    assert body["entry"]["returnByAt"] is not None
    assert body["notification"]["templateType"] == "table_ready"
    assert body["notification"]["renderedMessage"]


def test_return_to_waiting_clears_notification_state(client, auth_headers):
    entries = list_entries(client, auth_headers)
    marco = find_entry(entries, "Marco Feld")
    assert marco["status"] == "notified"

    resp = client.post(f"/api/waitlist-entries/{marco['id']}/return-to-waiting", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "waiting"
    assert body["notifiedAt"] is None
    assert body["returnByAt"] is None


def test_extend_return_by_pushes_return_by_time_later(client, auth_headers):
    entries = list_entries(client, auth_headers)
    marco = find_entry(entries, "Marco Feld")
    before = marco["returnByAt"]

    resp = client.post(
        f"/api/waitlist-entries/{marco['id']}/extend-return-by",
        json={"additionalMinutes": 15},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["returnByAt"] > before


def test_update_wait_estimate(client, auth_headers):
    entries = list_entries(client, auth_headers)
    tomas = find_entry(entries, "Tomas Berg")
    assert tomas["reviewRequired"] is True

    resp = client.patch(
        f"/api/waitlist-entries/{tomas['id']}/wait-estimate",
        json={"estimatedWaitMinutes": 33},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["estimatedWaitMinutes"] == 33


def test_seat_entry_at_compatible_available_table(client, auth_headers):
    entries = list_entries(client, auth_headers)
    ava = find_entry(entries, "Ava Lindqvist")

    resp = client.post(
        f"/api/waitlist-entries/{ava['id']}/seat",
        json={"tableId": "tbl_1"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "seated"
    assert body["tableId"] == "tbl_1"

    table_resp = client.get("/api/tables", headers=auth_headers)
    table = next(t for t in table_resp.json() if t["id"] == "tbl_1")
    assert table["availabilityState"] == "occupied"
    assert table["occupyingEntryId"] == ava["id"]


def test_seat_entry_rejects_occupied_table(client, auth_headers):
    entries = list_entries(client, auth_headers)
    ava = find_entry(entries, "Ava Lindqvist")

    resp = client.post(
        f"/api/waitlist-entries/{ava['id']}/seat",
        json={"tableId": "tbl_5"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "table_occupied"


def test_seat_entry_rejects_table_too_small(client, auth_headers):
    entries = list_entries(client, auth_headers)
    okonkwo = find_entry(entries, "The Okonkwo Party")
    assert okonkwo["partySize"] == 6

    resp = client.post(
        f"/api/waitlist-entries/{okonkwo['id']}/seat",
        json={"tableId": "tbl_1"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "table_too_small"


def test_seat_entry_rejects_inactive_table(client, auth_headers):
    entries = list_entries(client, auth_headers)
    ava = find_entry(entries, "Ava Lindqvist")

    resp = client.post(
        f"/api/waitlist-entries/{ava['id']}/seat",
        json={"tableId": "tbl_6"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "table_inactive"


def test_complete_seated_party_releases_table_to_needs_tidying(client, auth_headers):
    entries = list_entries(client, auth_headers)
    diego = find_entry(entries, "Diego Salas")
    assert diego["status"] == "seated"
    assert diego["tableId"] == "tbl_5"

    resp = client.post(f"/api/waitlist-entries/{diego['id']}/complete", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    table_resp = client.get("/api/tables", headers=auth_headers)
    table = next(t for t in table_resp.json() if t["id"] == "tbl_5")
    assert table["availabilityState"] == "needs_tidying"
    assert table["occupyingEntryId"] is None


def test_cancel_entry_releases_table_when_seated(client, auth_headers):
    entries = list_entries(client, auth_headers)
    diego = find_entry(entries, "Diego Salas")

    resp = client.post(f"/api/waitlist-entries/{diego['id']}/cancel", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    table_resp = client.get("/api/tables", headers=auth_headers)
    table = next(t for t in table_resp.json() if t["id"] == "tbl_5")
    assert table["availabilityState"] == "needs_tidying"


def test_mark_no_show_requires_notified_status(client, auth_headers):
    entries = list_entries(client, auth_headers)
    priya = find_entry(entries, "Priya Raman")
    assert priya["status"] == "notified"

    resp = client.post(f"/api/waitlist-entries/{priya['id']}/no-show", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_show"

    ava = find_entry(entries, "Ava Lindqvist")
    bad_resp = client.post(f"/api/waitlist-entries/{ava['id']}/no-show", headers=auth_headers)
    assert bad_resp.status_code == 400
    assert bad_resp.json()["code"] == "invalid_status"


def test_needs_attention_flag_for_overdue_notified_entry(client, auth_headers):
    entries = list_entries(client, auth_headers)
    priya = find_entry(entries, "Priya Raman")
    assert priya["returnByAt"] is not None

    resp = client.get(
        "/api/waitlist-entries", params={"needsAttentionOnly": True}, headers=auth_headers
    )
    assert resp.status_code == 200
    names = {e["guestName"] for e in resp.json()}
    assert "Priya Raman" in names


def test_compatible_tables_only_returns_available_matching_tables(client, auth_headers):
    entries = list_entries(client, auth_headers)
    ava = find_entry(entries, "Ava Lindqvist")

    resp = client.get(f"/api/waitlist-entries/{ava['id']}/compatible-tables", headers=auth_headers)
    assert resp.status_code == 200
    table_ids = {t["id"] for t in resp.json()}
    assert "tbl_1" in table_ids
    assert "tbl_5" not in table_ids
    assert "tbl_6" not in table_ids
