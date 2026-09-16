"""Integration test for SPEC.md acceptance scenario 1, run against a live server.

Register two agents. One sends a task; the other claims and completes it;
the sender reads the result.

Requires the app to already be running (e.g. `uv run uvicorn main:app --reload`).
"""

from __future__ import annotations

import httpx

BASE_URL = "http://127.0.0.1:8000"


def register(client: httpx.Client, name: str) -> dict[str, str]:
    response = client.post("/api/v1/agents", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def test_send_claim_complete_and_read_result() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        sender = register(client, "flow-sender")
        recipient = register(client, "flow-recipient")

        sender_headers = {"Authorization": f"Bearer {sender['token']}"}
        recipient_headers = {"Authorization": f"Bearer {recipient['token']}"}

        create = client.post(
            "/api/v1/tasks",
            json={"to": recipient["agent_id"], "input": "Review this Python function: ..."},
            headers=sender_headers,
        )
        assert create.status_code == 201, create.text
        task_id = create.json()["task_id"]
        assert create.json()["status"] == "queued"

        claim = client.post(
            "/api/v1/tasks/claim",
            json={"worker_id": "flow-worker-1", "wait_seconds": 5},
            headers=recipient_headers,
        )
        assert claim.status_code == 200, claim.text
        claim_body = claim.json()
        assert claim_body["task_id"] == task_id
        claim_token = claim_body["claim_token"]

        complete = client.post(
            f"/api/v1/tasks/{task_id}/complete",
            json={"claim_token": claim_token, "output": "No issues found."},
            headers=recipient_headers,
        )
        assert complete.status_code == 200, complete.text

        result = client.get(f"/api/v1/tasks/{task_id}", headers=sender_headers)
        assert result.status_code == 200, result.text
        result_body = result.json()

        print(f"Final task status (sender's view): {result_body['status']}")
        print(f"Output: {result_body['output']}")

        assert result_body["status"] == "completed"
        assert result_body["output"] == "No issues found."
