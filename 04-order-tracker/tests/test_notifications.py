"""Grafana's webhook to the responder (spec Q6): checks the committed files, not a running Grafana."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
OBSERVABILITY = ROOT / "observability"
NOTIFICATIONS_FILE = OBSERVABILITY / "grafana/provisioning/alerting/order-tracker-notifications.json"
ALERTS_FILE = OBSERVABILITY / "grafana/provisioning/alerting/order-tracker-alerts.json"
COMPOSE_FILE = OBSERVABILITY / "compose.yaml"

TOKEN_PLACEHOLDER = "${RESPONDER_TOKEN}"


@pytest.fixture(scope="module")
def config():
    config = json.loads(NOTIFICATIONS_FILE.read_text())
    assert config["apiVersion"] == 1
    return config


@pytest.fixture(scope="module")
def contact_point(config):
    assert len(config["contactPoints"]) == 1
    return config["contactPoints"][0]


@pytest.fixture(scope="module")
def receiver(contact_point):
    assert len(contact_point["receivers"]) == 1
    return contact_point["receivers"][0]


@pytest.fixture(scope="module")
def root_policy(config):
    assert len(config["policies"]) == 1
    return config["policies"][0]


@pytest.fixture(scope="module")
def route(root_policy):
    assert len(root_policy["routes"]) == 1
    return root_policy["routes"][0]


@pytest.fixture(scope="module")
def grafana_service():
    # The grafana service block of observability/compose.yaml (no YAML library needed).
    text = COMPOSE_FILE.read_text()
    match = re.search(r"^  grafana:\n(.*?)(?=^  \S|^\S)", text, re.MULTILINE | re.DOTALL)
    assert match, "no grafana service in observability/compose.yaml"
    return match.group(1)


def test_contact_point_is_a_webhook_to_the_responder(receiver):
    assert receiver["type"] == "webhook"
    assert receiver["uid"] == "order-tracker-responder"
    assert receiver["settings"]["url"] == "http://host.docker.internal:8001/alerts"
    assert receiver["settings"]["httpMethod"] == "POST"


def test_contact_point_sends_the_token_from_the_environment_as_bearer(receiver):
    settings = receiver["settings"]
    assert settings["authorization_scheme"] == "Bearer"
    assert settings["authorization_credentials"] == TOKEN_PLACEHOLDER


def test_contact_point_uses_no_other_auth_or_headers(receiver):
    settings = receiver["settings"]
    for key in ("username", "password", "basicAuthUser", "basicAuthPassword", "http_config", "headers"):
        assert key not in settings


def test_resolved_notifications_are_sent(receiver):
    # The responder must see (and ignore) resolved notifications.
    assert receiver["disableResolveMessage"] is False


def test_root_route_keeps_grafanas_default_contact_point(root_policy, contact_point):
    # Grafana 12.4.11's default policy on a fresh database: receiver "empty" (no integrations),
    # grouped by folder and alert name.
    assert root_policy["orgId"] == 1
    assert root_policy["receiver"] == "empty"
    assert root_policy["group_by"] == ["grafana_folder", "alertname"]
    assert root_policy["receiver"] != contact_point["name"]
    assert "object_matchers" not in root_policy
    assert "matchers" not in root_policy


def test_child_route_matches_only_the_oncall_owner(route):
    assert route["object_matchers"] == [["owner", "=", "order-tracker-oncall"]]
    assert "matchers" not in route
    assert route.get("continue", False) is False
    assert "routes" not in route


def test_child_route_goes_to_the_responder_contact_point(route, contact_point):
    assert route["receiver"] == contact_point["name"]


def test_matcher_label_is_the_alert_rules_owner_label(route):
    rule = json.loads(ALERTS_FILE.read_text())["groups"][0]["rules"][0]
    name, op, value = route["object_matchers"][0]
    assert op == "="
    assert rule["labels"][name] == value


def test_child_route_grouping_and_timings(route):
    assert route["group_by"] == ["alertname", "endpoint"]
    assert route["group_wait"] == "30s"
    assert route["group_interval"] == "5m"
    assert route["repeat_interval"] == "4h"


def test_grafana_gets_the_token_from_the_environment_empty_when_unset(grafana_service):
    assert "      RESPONDER_TOKEN: ${RESPONDER_TOKEN:-}\n" in grafana_service


def test_grafana_maps_host_docker_internal_to_the_host(grafana_service):
    assert re.search(r'^    extra_hosts:\n      - "host\.docker\.internal:host-gateway"\n', grafana_service, re.MULTILINE)


def test_grafana_port_stays_on_loopback(grafana_service):
    assert '"127.0.0.1:${GRAFANA_PORT:-3000}:3000"' in grafana_service


def _token_assignments(text):
    """Values given to token-like settings, in JSON (`"key": "value"`) or YAML (`key: value`) form."""
    pattern = r'"?(authorization_credentials|RESPONDER_TOKEN|bearer_token|token)"?\s*[:=]\s*"?([^"\n,]*)"?'
    return [(key, value.strip()) for key, value in re.findall(pattern, text, re.IGNORECASE)]


def test_no_committed_file_under_observability_contains_a_token_literal():
    allowed = {TOKEN_PLACEHOLDER, "${RESPONDER_TOKEN:-}"}
    files = [path for path in OBSERVABILITY.rglob("*") if path.is_file()]
    assert NOTIFICATIONS_FILE in files and COMPOSE_FILE in files
    found, seen = [], set()
    for path in files:
        text = path.read_text(errors="replace")
        for key, value in _token_assignments(text):
            seen.add((path, value))
            if value and value not in allowed:
                found.append((path.relative_to(ROOT), key, value))
        for literal in re.findall(r"Bearer\s+([A-Za-z0-9._~+/=-]{8,})", text):
            found.append((path.relative_to(ROOT), "Bearer", literal))
    assert found == []
    # The scan did see the two places the token is wired in.
    assert (NOTIFICATIONS_FILE, TOKEN_PLACEHOLDER) in seen
    assert (COMPOSE_FILE, "${RESPONDER_TOKEN:-}") in seen


def test_token_check_catches_a_literal():
    # The scanner above must flag a committed token, in JSON and YAML form.
    assert _token_assignments('"authorization_credentials": "s3cret-value"') == [
        ("authorization_credentials", "s3cret-value")
    ]
    assert _token_assignments("      RESPONDER_TOKEN: s3cret-value\n") == [("RESPONDER_TOKEN", "s3cret-value")]
    assert _token_assignments(f'"authorization_credentials": "{TOKEN_PLACEHOLDER}"') == [
        ("authorization_credentials", TOKEN_PLACEHOLDER)
    ]
