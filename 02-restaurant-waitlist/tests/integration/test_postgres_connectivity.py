"""Verify the backend actually connects to and communicates with Postgres.

Runs against the live `docker-compose.yml` stack (see `conftest.py`): a
guest join is created through the running `app` container's real HTTP API,
then read back two ways — through the API again, and with a direct query
against the same database the `app` container is configured to use — to
confirm the entry was truly persisted in Postgres rather than kept only
in-process.
"""

import uuid

import httpx2
import pytest

pytestmark = pytest.mark.integration


def test_guest_entry_round_trips_through_postgres(docker_stack, postgres_query):
    guest_name = f"Integration Test Guest {uuid.uuid4().hex[:8]}"

    create_resp = httpx2.post(
        f"{docker_stack}/api/waitlist-entries",
        json={
            "guestName": guest_name,
            "partySize": 2,
            "mobileNumber": "+61 400 123 456",
            "policyAcknowledged": True,
        },
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["kind"] == "entry"
    access_token = body["accessToken"]
    ticket_code = body["entry"]["ticketCode"]

    # Read back through the API.
    status_resp = httpx2.get(f"{docker_stack}/api/guest/entries/{access_token}")
    assert status_resp.status_code == 200
    assert status_resp.json()["ticketCode"] == ticket_code

    # Read back directly from Postgres, independent of the API, confirming
    # the `app` container actually wrote the row to the `postgres` service.
    rows = postgres_query(
        'SELECT "guestName", "ticketCode" FROM waitlist_entries WHERE "accessToken" = %s',
        (access_token,),
    )
    assert rows == [[guest_name, ticket_code]]
