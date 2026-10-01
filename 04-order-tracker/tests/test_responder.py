"""Incident responder (spec Q5). Loki, Tempo and the agent are mocked: no stack and no `claude` needed."""

import importlib.util
import json
import logging
import os
import socket
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("responder", ROOT / "incident-response/responder.py")
responder_module = importlib.util.module_from_spec(_spec)
sys.modules["responder"] = responder_module
_spec.loader.exec_module(responder_module)
r = responder_module

RESPONDER_TEST = (
    '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"true"},'
    '"annotations":{"summary":"Test notification; no incident to fix"}}]}'
)
NOW = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


def five_xx_alert(fingerprint="abc123", starts_at="2026-10-01T11:58:00Z", **labels):
    return {
        "status": "firing",
        "labels": {"alertname": "Order Tracker 5xx responses", "endpoint": "/api/orders/{order_id}",
                   "http_route": "/api/orders/{order_id}", "window": "5m", "owner": "order-tracker-oncall",
                   **labels},
        "annotations": {"summary": "5xx on /api/orders/{order_id}",
                        "dashboard_url": "http://localhost:3000/d/order-tracker-requests"},
        "startsAt": starts_at,
        "fingerprint": fingerprint,
    }


def body(*alerts, status="firing"):
    return json.dumps({"status": status, "alerts": list(alerts)})


class FakeTelemetry:
    """Mock Loki and Tempo. Records every request."""

    def __init__(self, error=None, gate=None):
        self.requests = []
        self.error = error
        self.gate = gate

    def __call__(self, request):
        self.requests.append(request)
        if self.gate is not None:
            self.gate.wait(10)
        if self.error is not None:
            raise self.error("simulated", request=request)
        if request.url.path == "/loki/api/v1/query_range":
            return httpx.Response(200, json={"status": "success", "data": {"resultType": "streams", "result": [
                {"stream": {"service_name": "order-tracker"}, "values": [["1", "GET /api/orders/x 500"]]}]}})
        if request.url.path == "/api/search":
            return httpx.Response(200, json={"traces": [{"traceID": "t1"}, {"traceID": "t2"}]})
        return httpx.Response(404)

    def params(self, path):
        return [request.url.params for request in self.requests if request.url.path == path]


class FakeAgent:
    """Records runs; each run blocks until released (all at once by default)."""

    def __init__(self, block=False, exit_code=0):
        self.prompts = []
        self.started = threading.Semaphore(0)
        self.release = threading.Event()
        self.block = block
        self.exit_code = exit_code
        self.running = 0
        self.max_running = 0
        self._lock = threading.Lock()

    def run(self, config, prompt, folder):
        with self._lock:
            self.prompts.append(prompt)
            self.running += 1
            self.max_running = max(self.max_running, self.running)
        self.started.release()
        if self.block:
            self.release.wait(10)
        (folder / "agent-output.txt").write_text("RESULT: FALSE_POSITIVE - fake\n")
        with self._lock:
            self.running -= 1
        return r.AgentResult(self.exit_code)

    def stop(self):
        self.release.set()


@pytest.fixture
def make(tmp_path):
    created = []

    def make(agent=None, telemetry=None, **config):
        config.setdefault("incidents_dir", tmp_path / "incidents")
        telemetry = telemetry or FakeTelemetry()
        responder = r.Responder(
            r.Config(**config),
            http_client=httpx.Client(transport=httpx.MockTransport(telemetry), timeout=5),
            agent_runner=agent or FakeAgent(),
        )
        responder.telemetry = telemetry
        client = TestClient(r.create_app(responder))
        client.__enter__()
        created.append(client)
        return responder, client

    yield make
    for client in created:
        client.__exit__(None, None, None)


def folders(responder):
    root = responder.config.incidents_dir
    return sorted(p for p in root.iterdir()) if root.exists() else []


def summary(folder):
    return (folder / "summary.md").read_text()


def post(client, content, **headers):
    return client.post("/alerts", content=content, headers={"Content-Type": "application/json", **headers})


# --- Payload parsing --------------------------------------------------------


@pytest.mark.parametrize("content", ["not json", "[]", '{"alerts": "x"}', '{"status": "firing"}', '{"alerts": [1]}'])
def test_invalid_body_gets_4xx_and_responder_keeps_running(make, content):
    responder, client = make()
    assert post(client, content).status_code == 400
    assert post(client, RESPONDER_TEST).status_code == 202
    assert responder.wait_idle()
    assert len(folders(responder)) == 1


def test_responder_test_curl_is_accepted_on_loopback_and_runs_the_agent(make):
    agent = FakeAgent()
    responder, client = make(agent=agent)
    response = post(client, RESPONDER_TEST)
    assert response.status_code == 202
    assert responder.wait_idle()
    [folder] = folders(responder)
    assert folder.name.endswith("-ResponderTest")
    assert len(agent.prompts) == 1
    assert "outcome: agent finished (exit code 0)" in summary(folder).lower()


def test_webhook_answers_before_evidence_is_collected(make):
    gate = threading.Event()
    responder, client = make(telemetry=FakeTelemetry(gate=gate))
    started = time.monotonic()
    response = post(client, body(five_xx_alert()))
    assert response.status_code == 202
    assert time.monotonic() - started < 2
    assert not (folders(responder) and (folders(responder)[0] / "logs.json").exists())
    gate.set()
    assert responder.wait_idle()
    assert (folders(responder)[0] / "logs.json").exists()


def test_resolved_alerts_are_skipped_and_logged(make, caplog):
    agent = FakeAgent()
    responder, client = make(agent=agent)
    resolved = {**five_xx_alert(), "status": "resolved"}
    with caplog.at_level(logging.INFO, logger="responder"):
        assert post(client, body(resolved, status="resolved")).status_code == 202
        assert responder.wait_idle()
    assert folders(responder) == []
    assert agent.prompts == []
    assert len([rec for rec in caplog.records if "Skipped resolved alert" in rec.message]) == 1


def test_resolved_alert_does_not_affect_duplicate_tracking(make):
    agent = FakeAgent(block=True)
    responder, client = make(agent=agent)
    post(client, body(five_xx_alert(fingerprint="f1")))
    assert agent.started.acquire(timeout=5)
    post(client, body({**five_xx_alert(fingerprint="f1"), "status": "resolved"}))
    assert post(client, body(five_xx_alert(fingerprint="f1"))).json()["accepted"] == ["duplicate"]
    agent.release.set()
    assert responder.wait_idle()
    assert len(folders(responder)) == 1


def test_each_alert_is_handled_by_its_own_status(make):
    agent = FakeAgent()
    responder, client = make(agent=agent)
    payload = body(five_xx_alert(fingerprint="a"), {**five_xx_alert(fingerprint="b"), "status": "resolved"},
                   five_xx_alert(fingerprint="c", endpoint="/api/orders"), status="resolved")
    response = post(client, payload)
    assert response.json()["accepted"] == ["agent", "skipped: resolved", "agent"]
    assert responder.wait_idle()
    assert len(folders(responder)) == 2
    assert len(agent.prompts) == 2


# --- Incident record --------------------------------------------------------


def test_incident_folder_contents(make):
    responder, client = make()
    raw = body(five_xx_alert())
    post(client, raw)
    assert responder.wait_idle()
    [folder] = folders(responder)
    assert folder.name.endswith("-Order_Tracker_5xx_responses")
    assert folder.name[:16][8] == "T" and folder.name[15] == "Z"
    assert (folder / "payload.json").read_text() == raw
    text = summary(folder)
    for expected in ("Alert name: Order Tracker 5xx responses", "Status: firing",
                     "Affected endpoint: /api/orders/{order_id}",
                     "Dashboard URL: http://localhost:3000/d/order-tracker-requests",
                     "- owner: order-tracker-oncall", "- summary: 5xx on /api/orders/{order_id}",
                     "Logs (Loki): 1 found", "Traces (Tempo): 2 found", "Outcome: agent finished (exit code 0)"):
        assert expected in text
    logs = json.loads((folder / "logs.json").read_text())
    assert logs["error"] is None and logs["count"] == 1
    traces = json.loads((folder / "traces.json").read_text())
    assert [t["traceID"] for t in traces["result"]] == ["t1", "t2"]


def test_endpoint_falls_back_to_http_route():
    alert = five_xx_alert()
    del alert["labels"]["endpoint"]
    incident = r.Incident(alert=alert, raw_body=b"", received_at=NOW, key="k", kind="agent")
    assert incident.endpoint == "/api/orders/{order_id}"


def test_missing_labels_and_annotations_show_unknown(make):
    responder, client = make()
    post(client, '{"alerts":[{"status":"firing"}]}')
    post(client, RESPONDER_TEST)
    assert responder.wait_idle()
    for folder in folders(responder):
        text = summary(folder)
        for line in ("Affected endpoint: unknown", "Dashboard URL: unknown", "Starts at: unknown",
                     "Fingerprint: unknown"):
            assert line in text
    assert any(f.name.endswith("-unknown") for f in folders(responder))


def test_same_timestamp_and_alertname_get_separate_folders(tmp_path):
    responder = r.Responder(r.Config(incidents_dir=tmp_path), http_client=httpx.Client(
        transport=httpx.MockTransport(FakeTelemetry())), agent_runner=FakeAgent())
    alert = json.loads(RESPONDER_TEST)["alerts"][0]
    first = r.Incident(alert=alert, raw_body=b"1", received_at=NOW, key="k", kind="dry_run")
    second = r.Incident(alert=alert, raw_body=b"2", received_at=NOW, key="k", kind="dry_run")
    responder.record(first)
    responder.record(second)
    assert first.folder.name == "20261001T120000Z-ResponderTest"
    assert second.folder.name == "20261001T120000Z-ResponderTest-2"
    assert (first.folder / "payload.json").read_bytes() == b"1"
    assert (second.folder / "payload.json").read_bytes() == b"2"


def test_alertname_is_reduced_to_safe_characters():
    assert r.safe_name("../../etc/passwd x") == "etc_passwd_x"
    assert r.safe_name("") == "unknown"


# --- Alert window and evidence queries ---------------------------------------


def test_alert_window_from_starts_at_minus_window_label():
    alert = five_xx_alert(starts_at="2026-10-01T11:58:00.123456789Z", window="10m")
    start, end = r.alert_window(alert, NOW)
    assert start == datetime(2026, 10, 1, 11, 48, 0, 123456, tzinfo=timezone.utc)
    assert end == NOW


def test_alert_window_defaults_to_five_minutes_and_is_capped_at_one_hour():
    alert = five_xx_alert(starts_at="2026-10-01T11:58:00Z")
    del alert["labels"]["window"]
    assert r.alert_window(alert, NOW)[0] == NOW - timedelta(minutes=7)
    old = five_xx_alert(starts_at="2026-10-01T08:00:00Z")
    assert r.alert_window(old, NOW)[0] == NOW - timedelta(hours=1)


@pytest.mark.parametrize("starts_at", [None, "", "yesterday", "0001-01-01T00:00:00Z"])
def test_alert_window_without_valid_starts_at_is_last_15_minutes(starts_at):
    alert = five_xx_alert(starts_at=starts_at)
    assert r.alert_window(alert, NOW) == (NOW - timedelta(minutes=15), NOW)


def test_loki_and_tempo_queries_are_bounded(make):
    responder, client = make()
    starts_at = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=2)
    post(client, body(five_xx_alert(starts_at=starts_at.isoformat().replace("+00:00", "Z"))))
    assert responder.wait_idle()
    [loki] = responder.telemetry.params("/loki/api/v1/query_range")
    assert loki["query"] == '{service_name="order-tracker"}'
    assert loki["limit"] == "100"
    assert int(loki["end"]) > int(loki["start"]) > 0
    [tempo] = responder.telemetry.params("/api/search")
    assert tempo["q"] == ('{resource.service.name="order-tracker" && span.http.response.status_code >= 500'
                          ' && span.http.route="/api/orders/{order_id}"}')
    assert tempo["limit"] == "20"
    assert int(tempo["end"]) > int(tempo["start"]) > 0
    window_start = int((starts_at - timedelta(minutes=5)).timestamp())
    assert int(loki["start"]) // 10**9 == int(tempo["start"]) == window_start


@pytest.mark.parametrize("endpoint", ["unknown", "(unmatched)"])
def test_tempo_query_has_no_route_filter_without_a_known_route(endpoint):
    assert "http.route" not in r.traceql(endpoint)


def test_http_client_has_explicit_timeout():
    client = r.make_http_client()
    assert client.timeout.read == r.HTTP_TIMEOUT_SECONDS
    assert client.timeout.connect == r.HTTP_TIMEOUT_SECONDS


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout])
def test_loki_and_tempo_unreachable_or_timing_out_is_recorded(make, error):
    agent = FakeAgent()
    responder, client = make(agent=agent, telemetry=FakeTelemetry(error=error))
    post(client, body(five_xx_alert()))
    assert responder.wait_idle()
    [folder] = folders(responder)
    for name, source in (("logs", "Loki"), ("traces", "Tempo")):
        record = json.loads((folder / f"{name}.json").read_text())
        assert record["error"].startswith(f"{source} unreachable") and error.__name__ in record["error"]
    assert "Logs (Loki): unavailable" in summary(folder)
    assert "Traces (Tempo): unavailable" in summary(folder)
    assert len(agent.prompts) == 1


def test_loki_http_error_status_is_recorded(make):
    responder, client = make(telemetry=lambda request: httpx.Response(503))
    post(client, RESPONDER_TEST)
    assert responder.wait_idle()
    [folder] = folders(responder)
    assert "503" in json.loads((folder / "logs.json").read_text())["error"]


# --- Telemetry-pipeline alerts ----------------------------------------------


@pytest.mark.parametrize("alertname", ["DatasourceError", "DatasourceNoData"])
def test_datasource_alerts_get_evidence_but_no_agent_and_no_queue_place(make, alertname):
    agent = FakeAgent(block=True)
    responder, client = make(agent=agent)
    post(client, body(five_xx_alert(fingerprint="q0")))
    assert agent.started.acquire(timeout=5)
    for n in range(1, 4):
        post(client, body(five_xx_alert(fingerprint=f"q{n}")))
    alert = five_xx_alert(fingerprint="ds", alertname=alertname, rulename="Order Tracker 5xx responses")
    assert post(client, body(alert)).json()["accepted"] == ["telemetry"]
    agent.release.set()
    assert responder.wait_idle()
    [folder] = [f for f in folders(responder) if alertname in f.name]
    text = summary(folder)
    assert "telemetry pipeline" in text and "not the app" in text
    assert "Original rule (rulename): Order Tracker 5xx responses" in text
    assert "Outcome: telemetry problem (no agent run)" in text
    assert (folder / "logs.json").exists() and (folder / "traces.json").exists()
    assert len(agent.prompts) == 4
    assert all("Outcome: agent finished" in summary(f) for f in folders(responder) if f != folder)


# --- Queueing and duplicates --------------------------------------------------


def test_one_agent_at_a_time_and_queue_cap(make):
    agent = FakeAgent(block=True)
    responder, client = make(agent=agent)
    post(client, body(five_xx_alert(fingerprint="f0")))
    assert agent.started.acquire(timeout=5)
    accepted = [post(client, body(five_xx_alert(fingerprint=f"f{n}"))) for n in range(1, 5)]
    assert all(response.status_code == 202 for response in accepted)
    assert [response.json()["accepted"] for response in accepted] == [["agent"]] * 3 + [["dropped"]]
    agent.release.set()
    assert responder.wait_idle()
    assert agent.max_running == 1
    assert len(agent.prompts) == 4
    texts = [summary(f) for f in folders(responder)]
    assert len(texts) == 5
    dropped = [t for t in texts if "Outcome: dropped: queue full" in t]
    assert len(dropped) == 1 and "Logs (Loki): 1 found" in dropped[0]


def test_burst_into_idle_responder_runs_one_and_queues_three(make):
    agent = FakeAgent(block=True)
    responder, client = make(agent=agent)
    alerts = [five_xx_alert(fingerprint=f"b{n}", endpoint=f"/e{n}") for n in range(5)]
    response = post(client, body(*alerts))
    assert response.status_code == 202
    assert response.json()["accepted"] == ["agent"] * 4 + ["dropped"]
    agent.release.set()
    assert responder.wait_idle()
    assert len(agent.prompts) == 4
    assert agent.max_running == 1
    assert sum("Outcome: dropped: queue full" in summary(f) for f in folders(responder)) == 1


def test_duplicate_by_fingerprint_is_logged_and_not_queued(make, caplog):
    agent = FakeAgent(block=True)
    responder, client = make(agent=agent)
    post(client, body(five_xx_alert(fingerprint="f1")))
    assert agent.started.acquire(timeout=5)
    post(client, body(five_xx_alert(fingerprint="f2")))
    with caplog.at_level(logging.INFO, logger="responder"):
        running_dup = post(client, body(five_xx_alert(fingerprint="f1", starts_at="2026-10-01T11:59:00Z")))
        queued_dup = post(client, body(five_xx_alert(fingerprint="f2")))
    assert running_dup.json()["accepted"] == queued_dup.json()["accepted"] == ["duplicate"]
    assert len([rec for rec in caplog.records if "Duplicate" in rec.message]) == 2
    agent.release.set()
    assert responder.wait_idle()
    assert len(agent.prompts) == 2
    assert len(folders(responder)) == 2


def test_duplicate_by_label_hash_without_fingerprint(make):
    agent = FakeAgent(block=True)
    responder, client = make(agent=agent)
    post(client, RESPONDER_TEST)
    assert agent.started.acquire(timeout=5)
    reordered = '{"alerts":[{"status":"firing","labels":{"test":"true","alertname":"ResponderTest"}}]}'
    assert post(client, reordered).json()["accepted"] == ["duplicate"]
    other = '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"false"}}]}'
    assert post(client, other).json()["accepted"] == ["agent"]
    agent.release.set()
    assert responder.wait_idle()
    assert len(agent.prompts) == 2


def test_repeat_notification_vs_new_firing_after_the_agent_finished(make):
    agent = FakeAgent()
    responder, client = make(agent=agent)
    post(client, body(five_xx_alert(fingerprint="f1", starts_at="2026-10-01T11:58:00Z")))
    assert responder.wait_idle()
    repeat = post(client, body(five_xx_alert(fingerprint="f1", starts_at="2026-10-01T11:58:00Z")))
    assert repeat.json()["accepted"] == ["duplicate"]
    new_firing = post(client, body(five_xx_alert(fingerprint="f1", starts_at="2026-10-01T13:00:00Z")))
    assert new_firing.json()["accepted"] == ["agent"]
    assert responder.wait_idle()
    assert post(client, RESPONDER_TEST).json()["accepted"] == ["agent"]
    assert responder.wait_idle()
    assert post(client, RESPONDER_TEST).json()["accepted"] == ["agent"]
    assert responder.wait_idle()
    assert len(agent.prompts) == 4


# --- Running the agent ----------------------------------------------------------


def fake_claude(tmp_path, script):
    path = tmp_path / "fake-claude"
    path.write_text(f"#!{sys.executable}\nimport json, os, sys, time\n{script}\n")
    path.chmod(0o755)
    return str(path)


def make_real(make, tmp_path, script, **config):
    return make(agent=r.AgentRunner(), claude_command=fake_claude(tmp_path, script), project_dir=tmp_path,
                **config)


def test_agent_runs_in_project_folder_with_task_and_folder_and_saves_output(make, tmp_path):
    script = ("json.dump({'cwd': os.getcwd(), 'argv': sys.argv[1:]}, open('call.json', 'w'))\n"
              "print('Looked at it.')\nprint('RESULT: FALSE_POSITIVE - test alert')")
    responder, client = make_real(make, tmp_path, script)
    post(client, RESPONDER_TEST)
    assert responder.wait_idle()
    [folder] = folders(responder)
    call = json.loads((tmp_path / "call.json").read_text())
    assert call["cwd"] == str(tmp_path)
    assert call["argv"][0] == "-p"
    prompt = call["argv"][1]
    assert prompt.startswith(r.TASK_FILE.read_text().rstrip())
    assert f"Incident folder: {folder.relative_to(tmp_path)}" in prompt
    assert prompt == f"{r.TASK_FILE.read_text().rstrip()}\n\nIncident folder: {folder.relative_to(tmp_path)}\n"
    assert "--allowedTools" in call["argv"] and "Bash(make:*)" in call["argv"]
    assert "Bash(git push:*)" in call["argv"][call["argv"].index("--disallowedTools"):]
    assert (folder / "agent-output.txt").read_text().splitlines()[-1] == "RESULT: FALSE_POSITIVE - test alert"
    assert json.loads((folder / "agent-status.json").read_text())["exit_code"] == 0
    assert "Outcome: agent finished (exit code 0)" in summary(folder)


def test_allowed_tools_exclude_push_and_general_network():
    assert not any("push" in tool for tool in r.ALLOWED_TOOLS)
    assert not any("curl" in tool for tool in r.ALLOWED_TOOLS)
    assert "Bash(curl:*)" in r.DISALLOWED_TOOLS
    assert "Bash(make:*)" in r.ALLOWED_TOOLS  # covers `make probe URL=...`


def test_token_does_not_reach_the_agent(make, tmp_path, monkeypatch):
    monkeypatch.setenv("RESPONDER_TOKEN", "s3cret-token")
    script = "json.dump({'env': dict(os.environ), 'argv': sys.argv[1:]}, open('call.json', 'w'))"
    responder, client = make_real(make, tmp_path, script, host="0.0.0.0", token="s3cret-token")
    assert post(client, RESPONDER_TEST, Authorization="Bearer s3cret-token").status_code == 202
    assert responder.wait_idle()
    call = (tmp_path / "call.json").read_text()
    assert "RESPONDER_TOKEN" not in json.loads(call)["env"]
    assert "s3cret-token" not in call
    for path in folders(responder)[0].iterdir():
        assert "s3cret-token" not in path.read_text()


def test_claude_missing_is_recorded_and_responder_keeps_running(make, tmp_path):
    responder, client = make(agent=r.AgentRunner(), claude_command=str(tmp_path / "no-such-claude"))
    post(client, body(five_xx_alert(fingerprint="a")))
    post(client, body(five_xx_alert(fingerprint="b")))
    assert responder.wait_idle()
    for folder in folders(responder):
        status = json.loads((folder / "agent-status.json").read_text())
        assert status["exit_code"] is None and "failed to start" in status["error"]
        assert "Outcome: agent failed/timed out: agent failed to start" in summary(folder)
    assert len(folders(responder)) == 2


def test_claude_failing_is_recorded_with_exit_code(make, tmp_path):
    responder, client = make_real(make, tmp_path, "print('boom', file=sys.stderr); sys.exit(3)")
    post(client, RESPONDER_TEST)
    assert responder.wait_idle()
    [folder] = folders(responder)
    assert json.loads((folder / "agent-status.json").read_text())["exit_code"] == 3
    assert (folder / "agent-stderr.txt").read_text().strip() == "boom"
    assert "agent exited with code 3" in summary(folder)


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    with open(f"/proc/{pid}/stat") as stat:
        return stat.read().split()[2] != "Z"


def wait_for(path, timeout=5):
    deadline = time.monotonic() + timeout
    while not path.exists() or not path.read_text():
        assert time.monotonic() < deadline, f"{path} not written"
        time.sleep(0.02)


def test_agent_timeout_stops_the_process_and_next_incident_runs(make, tmp_path):
    script = ("open(f'pid-{os.getpid()}', 'w').write('x')\n"
              "if os.path.exists('slow'): os.remove('slow'); time.sleep(60)\nprint('RESULT: FIXED - quick')")
    (tmp_path / "slow").write_text("x")
    responder, client = make_real(make, tmp_path, script, agent_timeout=0.5)
    post(client, body(five_xx_alert(fingerprint="slow")))
    post(client, body(five_xx_alert(fingerprint="fast")))
    assert responder.wait_idle(timeout=20)
    timed_out, finished = [summary(f) for f in folders(responder)]
    assert "agent timed out after 0.5 s and was stopped" in timed_out
    assert "Outcome: agent finished (exit code 0)" in finished
    pids = [int(p.name[4:]) for p in tmp_path.glob("pid-*")]
    assert len(pids) == 2 and not any(pid_alive(pid) for pid in pids)


def test_shutdown_stops_the_running_agent_and_records_interruption(make, tmp_path):
    script = "open('pid', 'w').write(str(os.getpid()))\ntime.sleep(60)"
    responder, client = make_real(make, tmp_path, script)
    post(client, RESPONDER_TEST)
    wait_for(tmp_path / "pid")
    pid = int((tmp_path / "pid").read_text())
    client.__exit__(None, None, None)  # lifespan shutdown, as on Ctrl-C
    assert not pid_alive(pid)
    [folder] = folders(responder)
    assert "interrupted: the responder stopped while the agent was running" in summary(folder)


def test_dry_run_saves_record_without_running_the_agent(make):
    agent = FakeAgent()
    responder, client = make(agent=agent, dry_run=True)
    assert post(client, RESPONDER_TEST).json()["accepted"] == ["dry_run"]
    assert responder.wait_idle()
    [folder] = folders(responder)
    assert agent.prompts == []
    assert "Outcome: dry run" in summary(folder)
    assert not (folder / "agent-output.txt").exists()


def test_dry_run_from_env():
    assert r.Config.from_env({"RESPONDER_DRY_RUN": "1"}).dry_run
    assert not r.Config.from_env({}).dry_run


# --- Startup and access ---------------------------------------------------------


@pytest.mark.parametrize("host,loopback", [
    ("127.0.0.1", True), ("127.1.2.3", True), ("::1", True), ("localhost", True),
    ("0.0.0.0", False), ("::", False), ("192.168.1.10", False), ("example.com", False),
])
def test_loopback_addresses(host, loopback):
    assert r.is_loopback(host) is loopback


def test_defaults_from_env():
    config = r.Config.from_env({})
    assert config.host == "127.0.0.1" and config.token is None
    assert config.loki_url == "http://127.0.0.1:3100" and config.tempo_url == "http://127.0.0.1:3200"
    assert config.agent_timeout == 30 * 60
    config.validate()


@pytest.mark.parametrize("token", [None, ""])
def test_refuses_to_start_off_loopback_without_token(token):
    env = {"RESPONDER_HOST": "0.0.0.0"}
    if token is not None:
        env["RESPONDER_TOKEN"] = token
    with pytest.raises(r.ConfigError, match="RESPONDER_TOKEN must be set"):
        r.Config.from_env(env).validate()


def test_main_exits_with_clear_error_off_loopback_without_token(monkeypatch, capsys):
    monkeypatch.setenv("RESPONDER_HOST", "0.0.0.0")
    monkeypatch.delenv("RESPONDER_TOKEN", raising=False)
    assert r.main() == 1
    assert "RESPONDER_TOKEN must be set" in capsys.readouterr().err


def test_busy_port_is_a_clear_startup_error():
    busy = socket.socket()
    busy.bind(("127.0.0.1", 0))
    busy.listen()
    try:
        with pytest.raises(r.ConfigError, match="already using port"):
            r.bind_socket("127.0.0.1", busy.getsockname()[1])
    finally:
        busy.close()


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "s3cret"}])
def test_off_loopback_rejects_missing_or_wrong_token_and_records_nothing(make, headers):
    agent = FakeAgent()
    responder, client = make(agent=agent, host="0.0.0.0", token="s3cret")
    assert post(client, RESPONDER_TEST, **headers).status_code == 401
    assert post(client, "not json", **headers).status_code == 401
    assert responder.wait_idle()
    assert folders(responder) == [] and agent.prompts == []


def test_off_loopback_accepts_correct_token(make):
    responder, client = make(host="0.0.0.0", token="s3cret")
    assert post(client, RESPONDER_TEST, Authorization="Bearer s3cret").status_code == 202
    assert responder.wait_idle()
    assert len(folders(responder)) == 1


def test_loopback_needs_no_token(make):
    responder, client = make(host="127.0.0.1", token=None)
    assert post(client, RESPONDER_TEST).status_code == 202


def test_task_file_has_the_on_call_instructions():
    text = r.TASK_FILE.read_text()
    assert text.startswith("You are the on-call engineer for this project. An alert just fired.")
    assert text.rstrip().endswith(
        "7. End your answer with a single line: RESULT: <FIXED | FALSE_POSITIVE | ESCALATE> - <one-sentence summary>.")
    assert ("4. Restart the app with `make run`, then repeat the failing request with "
            "`make probe URL=http://localhost:8000/<path>` (which runs `curl -i`) and confirm it no longer fails. "
            "If it still fails, go back to step 2.\n") in text
