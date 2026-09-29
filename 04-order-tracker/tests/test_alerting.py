"""The provisioned Grafana 5xx alert rule (spec Q4): checks the committed file, not a running Grafana."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ALERTS_FILE = ROOT / "observability/grafana/provisioning/alerting/order-tracker-alerts.json"
DASHBOARD_FILE = ROOT / "observability/grafana/dashboards/order-tracker-requests.json"
DASHBOARD_PROVIDER_FILE = ROOT / "observability/grafana/provisioning/dashboards/dashboards.yaml"


def seconds(duration):
    match = re.fullmatch(r"(\d+)([smh])", duration)
    assert match, f"unexpected duration {duration!r}"
    return int(match.group(1)) * {"s": 1, "m": 60, "h": 3600}[match.group(2)]


@pytest.fixture(scope="module")
def config():
    return json.loads(ALERTS_FILE.read_text())


@pytest.fixture(scope="module")
def group(config):
    assert config["apiVersion"] == 1
    assert len(config["groups"]) == 1
    return config["groups"][0]


@pytest.fixture(scope="module")
def rule(group):
    assert len(group["rules"]) == 1
    return group["rules"][0]


@pytest.fixture(scope="module")
def queries(rule):
    return {query["refId"]: query for query in rule["data"]}


@pytest.fixture(scope="module")
def expr(queries):
    return queries["A"]["model"]["expr"]


def test_rule_is_in_the_dashboard_folder(group):
    assert group["folder"] == "Order Tracker"
    assert "folder: Order Tracker" in DASHBOARD_PROVIDER_FILE.read_text()


def test_evaluation_interval_is_at_most_one_minute(group):
    assert seconds(group["interval"]) <= 60


def test_rule_has_fixed_uid_and_title(rule):
    assert rule["uid"] == "order-tracker-5xx"
    assert rule["title"] == "Order Tracker 5xx responses"


def test_query_uses_prometheus_by_fixed_uid_as_instant_query(queries):
    query = queries["A"]
    assert query["datasourceUid"] == "prometheus"
    assert query["model"]["instant"] is True
    assert query["model"]["range"] is False


def test_query_counts_5xx_of_the_service_over_five_minutes(expr):
    selector = 'http_server_request_duration_seconds_count{service_name="order-tracker", http_response_status_code=~"5.."}'
    assert f"increase({selector}[5m])" in expr


def test_query_covers_every_route(expr):
    assert "http_route=" not in expr
    assert "http_route!" not in expr


def test_query_keeps_service_labels_and_drops_instance(expr):
    assert "sum by (http_route, service_name, deployment_environment, service_version) (increase(" in expr
    assert "instance" not in expr


def test_endpoint_mirrors_route_with_unmatched_fallback(expr):
    assert 'label_replace(label_replace(sum by' in expr
    assert '"endpoint", "$1", "http_route", "(.+)")' in expr
    assert expr.endswith('"endpoint", "(unmatched)", "http_route", "")')


def test_fires_when_count_is_above_zero(rule, queries):
    assert rule["condition"] == "C"
    condition = queries["C"]
    assert condition["datasourceUid"] == "__expr__"
    assert condition["model"]["type"] == "threshold"
    assert condition["model"]["expression"] == "A"
    assert condition["model"]["conditions"] == [{"evaluator": {"type": "gt", "params": [0]}}]


def test_pending_period_and_state_handling(rule):
    assert seconds(rule["for"]) == 60
    assert rule["noDataState"] == "OK"
    assert rule["execErrState"] == "Error"
    assert rule["isPaused"] is False


def test_labels(rule):
    assert rule["labels"] == {"owner": "order-tracker-oncall", "window": "5m"}


def test_annotations_name_endpoint_service_environment_and_version(rule):
    annotations = rule["annotations"]
    assert "{{ $labels.endpoint }}" in annotations["summary"]
    for label in ("service_name", "deployment_environment", "service_version", "endpoint"):
        assert f"{{{{ $labels.{label} }}}}" in annotations["description"]


def test_dashboard_url_follows_grafana_root_url(rule):
    dashboard_uid = json.loads(DASHBOARD_FILE.read_text())["uid"]
    assert rule["annotations"]["dashboard_url"] == f"{{{{ externalURL }}}}d/{dashboard_uid}"
    assert dashboard_uid == "order-tracker-requests"


def test_file_has_no_env_placeholders_or_escaped_dollars():
    # Grafana doesn't expand env vars in alerting provisioning files, so "${...}"
    # or "$$" would reach the rule as literal text and break its templates.
    text = ALERTS_FILE.read_text()
    assert "${" not in text
    assert "$$" not in text
