def test_list_tables_returns_seeded_tables(client, auth_headers):
    resp = client.get("/api/tables", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 6


def test_list_tables_requires_auth(client):
    resp = client.get("/api/tables")
    assert resp.status_code == 401


def test_create_table(client, auth_headers):
    resp = client.post(
        "/api/tables",
        json={"name": "T7", "minCapacity": 2, "maxCapacity": 8, "notes": "Patio"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "T7"
    assert body["active"] is True
    assert body["availabilityState"] == "available"


def test_create_table_rejects_invalid_capacity(client, auth_headers):
    resp = client.post(
        "/api/tables",
        json={"name": "Bad", "minCapacity": 4, "maxCapacity": 2},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_max_capacity"


def test_update_table_name_and_capacity(client, auth_headers):
    resp = client.patch(
        "/api/tables/tbl_3",
        json={"name": "T3 Renamed", "maxCapacity": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "T3 Renamed"
    assert body["maxCapacity"] == 5


def test_update_table_can_deactivate(client, auth_headers):
    resp = client.patch("/api/tables/tbl_3", json={"active": False}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["active"] is False


def test_update_nonexistent_table_returns_404(client, auth_headers):
    resp = client.patch("/api/tables/does_not_exist", json={"name": "X"}, headers=auth_headers)
    assert resp.status_code == 404


def test_delete_table(client, auth_headers):
    resp = client.delete("/api/tables/tbl_3", headers=auth_headers)
    assert resp.status_code == 204

    list_resp = client.get("/api/tables", headers=auth_headers)
    ids = {t["id"] for t in list_resp.json()}
    assert "tbl_3" not in ids


def test_delete_occupied_table_is_rejected(client, auth_headers):
    resp = client.delete("/api/tables/tbl_5", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "table_occupied"


def test_set_table_availability_needs_tidying_to_available(client, auth_headers):
    resp = client.patch(
        "/api/tables/tbl_2/availability",
        json={"availabilityState": "available"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["availabilityState"] == "available"


def test_set_table_availability_rejects_available_from_available(client, auth_headers):
    resp = client.patch(
        "/api/tables/tbl_1/availability",
        json={"availabilityState": "available"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_availability_transition"


def test_set_table_availability_occupied_to_needs_tidying_clears_occupant(client, auth_headers):
    resp = client.patch(
        "/api/tables/tbl_5/availability",
        json={"availabilityState": "needs_tidying"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["availabilityState"] == "needs_tidying"
    assert body["occupyingEntryId"] is None
