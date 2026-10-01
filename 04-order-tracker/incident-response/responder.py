"""Incident responder (spec Q5): Grafana webhook in, incident record out, headless on-call agent.

Run from the project folder with `make responder`. It listens on port 8001 at
`POST /alerts`, saves each firing alert as an incident folder with Loki logs and
Tempo traces for the alert window, and runs `claude -p` on it, one incident at a
time. Queued incidents live in memory only and are lost when the responder stops.
"""

import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import signal
import socket
import subprocess
import sys
import threading
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PORT = 8001
PROJECT_DIR = Path(__file__).resolve().parent.parent
RESPONDER_DIR = Path(__file__).resolve().parent
TASK_FILE = RESPONDER_DIR / "responder-task.md"
INCIDENTS_DIR = RESPONDER_DIR / "incidents"

MAX_QUEUED = 3
AGENT_TIMEOUT_SECONDS = 30 * 60
HTTP_TIMEOUT_SECONDS = 5.0
LOKI_LIMIT = 100
TEMPO_LIMIT = 20
DEFAULT_WINDOW = timedelta(minutes=5)
MAX_WINDOW = timedelta(hours=1)
FALLBACK_WINDOW = timedelta(minutes=15)
TELEMETRY_ALERTS = {"DatasourceError", "DatasourceNoData"}
SERVICE_NAME = "order-tracker"
UNKNOWN = "unknown"

# Tools the headless agent may use without asking (it can't ask). Anything else is denied.
# No direct curl: prefix rules can't limit it to localhost. The agent uses `make probe URL=...`
# (incident-response/probe.py), which accepts only http://localhost and http://127.0.0.1 URLs.
ALLOWED_TOOLS = [
    "Read", "Glob", "Grep", "Edit", "Write",
    "Bash(make:*)",
    "Bash(git status:*)", "Bash(git diff:*)", "Bash(git add:*)", "Bash(git commit:*)",
]
DISALLOWED_TOOLS = ["Bash(git push:*)", "Bash(curl:*)", "WebFetch", "WebSearch"]
# Added after the task text: responder-task.md must stay word for word as approved.
PROBE_NOTE = (
    "How to send HTTP requests here: you can't run `curl` directly. Wherever the steps above say `curl -i`, "
    "run `make probe URL=http://localhost:8000/<path>` instead. It runs `curl -i` and accepts only "
    "http://localhost or http://127.0.0.1 URLs (the app is on port 8000 unless ORDER_TRACKER_PORT says otherwise)."
)

logger = logging.getLogger("responder")


class ConfigError(Exception):
    """The responder can't start with this configuration."""


@dataclass
class Config:
    host: str = "127.0.0.1"
    token: str | None = None
    dry_run: bool = False
    loki_url: str = "http://127.0.0.1:3100"
    tempo_url: str = "http://127.0.0.1:3200"
    agent_timeout: float = AGENT_TIMEOUT_SECONDS
    claude_command: str = "claude"
    incidents_dir: Path = INCIDENTS_DIR
    project_dir: Path = PROJECT_DIR
    task_file: Path = TASK_FILE

    @property
    def token_required(self):
        return not is_loopback(self.host)

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        timeout = env.get("RESPONDER_AGENT_TIMEOUT", "").strip()
        try:
            agent_timeout = float(timeout) if timeout else AGENT_TIMEOUT_SECONDS
        except ValueError:
            raise ConfigError(f"RESPONDER_AGENT_TIMEOUT must be a number of seconds, got {timeout!r}") from None
        return cls(
            host=env.get("RESPONDER_HOST", "").strip() or "127.0.0.1",
            token=env.get("RESPONDER_TOKEN") or None,
            dry_run=env.get("RESPONDER_DRY_RUN", "").strip().lower() in {"1", "true", "yes"},
            loki_url=(env.get("LOKI_URL", "").strip() or "http://127.0.0.1:3100").rstrip("/"),
            tempo_url=(env.get("TEMPO_URL", "").strip() or "http://127.0.0.1:3200").rstrip("/"),
            agent_timeout=agent_timeout,
        )

    def validate(self):
        if self.token_required and not self.token:
            raise ConfigError(
                f"RESPONDER_HOST={self.host} is not a loopback address, so RESPONDER_TOKEN must be set "
                "(Grafana sends it as 'Authorization: Bearer <token>'). Refusing to start."
            )


def is_loopback(host):
    """127.0.0.0/8, ::1 and localhost are loopback; anything else (0.0.0.0, ::, names) isn't."""
    if host.strip().lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip().strip("[]")).is_loopback
    except ValueError:
        return False


# --- Alert parsing ---------------------------------------------------------


class PayloadError(ValueError):
    pass


def parse_payload(body):
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError) as error:
        raise PayloadError(f"invalid JSON: {error}") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("alerts"), list):
        raise PayloadError('body must be a JSON object with an "alerts" list')
    if not all(isinstance(alert, dict) for alert in payload["alerts"]):
        raise PayloadError('every item in "alerts" must be an object')
    return payload


def _dict(value):
    return {str(k): v for k, v in value.items()} if isinstance(value, dict) else {}


def _text(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def alert_key(alert):
    """The fingerprint, or a stable hash of the labels when there's none."""
    fingerprint = _text(alert.get("fingerprint"))
    if fingerprint:
        return f"fingerprint:{fingerprint}"
    labels = json.dumps(_dict(alert.get("labels")), sort_keys=True, separators=(",", ":"), default=str)
    return "labels:" + hashlib.sha256(labels.encode()).hexdigest()[:16]


def parse_time(value):
    """An RFC 3339 time as Grafana sends it, or None when missing, invalid or Go's zero time."""
    text = _text(value)
    if not text:
        return None
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})", text)
    if not match:
        return None
    fraction = (match.group(2) or ".0")[:7]
    zone = "+00:00" if match.group(3) == "Z" else match.group(3)
    try:
        parsed = datetime.fromisoformat(match.group(1) + fraction + zone)
    except ValueError:
        return None
    return None if parsed.year <= 1 else parsed.astimezone(timezone.utc)


def parse_duration(value):
    match = re.fullmatch(r"(\d+)(s|m|h)", (_text(value) or ""))
    if not match or int(match.group(1)) == 0:
        return None
    return timedelta(seconds=int(match.group(1)) * {"s": 1, "m": 60, "h": 3600}[match.group(2)])


def alert_window(alert, received_at):
    """From startsAt minus the window label (default 5m) to received_at, at most 1 hour.

    Without a valid startsAt: the last 15 minutes.
    """
    starts_at = parse_time(alert.get("startsAt"))
    if starts_at is None:
        return received_at - FALLBACK_WINDOW, received_at
    window = parse_duration(_dict(alert.get("labels")).get("window")) or DEFAULT_WINDOW
    start = min(starts_at, received_at) - window
    return max(start, received_at - MAX_WINDOW), received_at


def safe_name(value):
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "").strip("._-")[:80]
    return name or UNKNOWN


# --- Incidents -------------------------------------------------------------


@dataclass
class Incident:
    alert: dict
    raw_body: bytes
    received_at: datetime
    key: str
    kind: str  # "agent", "telemetry", "dry_run" or "dropped"
    folder: Path | None = None
    outcome: str = ""
    evidence: dict = field(default_factory=dict)

    @property
    def labels(self):
        return _dict(self.alert.get("labels"))

    @property
    def annotations(self):
        return _dict(self.alert.get("annotations"))

    @property
    def alertname(self):
        return _text(self.labels.get("alertname")) or UNKNOWN

    @property
    def endpoint(self):
        return _text(self.labels.get("endpoint")) or _text(self.labels.get("http_route")) or UNKNOWN

    @property
    def dashboard_url(self):
        return _text(self.annotations.get("dashboard_url")) or UNKNOWN

    @property
    def starts_at(self):
        return _text(self.alert.get("startsAt"))


def _value(value):
    if value is None or value == "":
        return UNKNOWN
    return value if isinstance(value, str) else json.dumps(value)


def render_summary(incident):
    alert = incident.alert
    window_start, window_end = alert_window(alert, incident.received_at)
    lines = [
        f"# Incident: {incident.alertname}",
        "",
        f"- Alert name: {incident.alertname}",
        f"- Status: {_value(alert.get('status'))}",
        f"- Affected endpoint: {incident.endpoint}",
        f"- Dashboard URL: {incident.dashboard_url}",
        f"- Received at: {incident.received_at.isoformat()}",
        f"- Starts at: {_value(alert.get('startsAt'))}",
        f"- Fingerprint: {_value(alert.get('fingerprint'))}",
        f"- Alert window: {window_start.isoformat()} to {window_end.isoformat()}",
        f"- Outcome: {incident.outcome}",
    ]
    if incident.kind == "telemetry":
        lines += [
            "",
            "## Likely cause",
            "",
            f"This is a {incident.alertname} alert: Grafana couldn't evaluate the alert rule. The telemetry "
            "pipeline (Prometheus, the Collector or a data source), not the app, is the likely problem. "
            "No agent was run.",
            "",
            f"- Original rule (rulename): {_value(incident.labels.get('rulename'))}",
        ]
    for title, values in (("Labels", incident.labels), ("Annotations", incident.annotations)):
        lines += ["", f"## {title}", ""]
        lines += [f"- {key}: {_value(value)}" for key, value in sorted(values.items())] or ["- none"]
    lines += ["", "## Evidence", ""]
    for name, label in (("logs", "Logs (Loki)"), ("traces", "Traces (Tempo)")):
        record = incident.evidence.get(name)
        if record is None:
            lines.append(f"- {label}: not collected yet")
        elif record.get("error"):
            lines.append(f"- {label}: unavailable ({record['error']}), see {name}.json")
        else:
            lines.append(f"- {label}: {record['count']} found, see {name}.json")
    lines += [
        "",
        "## Files",
        "",
        "- payload.json: the webhook body as received",
        "- summary.md: this summary",
        "- logs.json: Loki query, time range and result (or the error)",
        "- traces.json: Tempo query, time range and result (or the error)",
        "- agent-output.txt, agent-stderr.txt, agent-status.json: the agent's output, errors and exit code "
        "(only when the agent ran or failed to start)",
        "",
    ]
    return "\n".join(lines)


def make_http_client():
    return httpx.Client(timeout=httpx.Timeout(HTTP_TIMEOUT_SECONDS))


def _get(client, url, params):
    response = client.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def collect_logs(client, config, start, end):
    query = f'{{service_name="{SERVICE_NAME}"}}'
    record = {"source": config.loki_url, "query": query, "start": start.isoformat(), "end": end.isoformat(),
              "limit": LOKI_LIMIT}
    params = {"query": query, "start": str(int(start.timestamp() * 1e9)), "end": str(int(end.timestamp() * 1e9)),
              "limit": LOKI_LIMIT, "direction": "backward"}
    try:
        data = _get(client, f"{config.loki_url}/loki/api/v1/query_range", params)
        result = data.get("data", {}).get("result", [])
        record.update(error=None, count=sum(len(stream.get("values", [])) for stream in result), result=result)
    except (httpx.HTTPError, ValueError, AttributeError) as error:
        record.update(error=f"Loki unreachable or failed: {type(error).__name__}: {error}", count=0, result=None)
    return record


def traceql(endpoint):
    query = f'resource.service.name="{SERVICE_NAME}" && span.http.response.status_code >= 500'
    if endpoint not in (UNKNOWN, "(unmatched)"):
        escaped = endpoint.replace("\\", "\\\\").replace('"', '\\"')
        query += f' && span.http.route="{escaped}"'
    return "{" + query + "}"


def collect_traces(client, config, start, end, endpoint):
    query = traceql(endpoint)
    record = {"source": config.tempo_url, "query": query, "start": start.isoformat(), "end": end.isoformat(),
              "limit": TEMPO_LIMIT}
    params = {"q": query, "start": int(start.timestamp()), "end": int(end.timestamp()) + 1, "limit": TEMPO_LIMIT}
    try:
        traces = _get(client, f"{config.tempo_url}/api/search", params).get("traces") or []
        record.update(error=None, count=len(traces), result=traces[:TEMPO_LIMIT])
    except (httpx.HTTPError, ValueError, AttributeError) as error:
        record.update(error=f"Tempo unreachable or failed: {type(error).__name__}: {error}", count=0, result=None)
    return record


# --- Agent -----------------------------------------------------------------


@dataclass
class AgentResult:
    exit_code: int | None
    error: str | None = None


def agent_command(config, prompt):
    return [config.claude_command, "-p", prompt, "--output-format", "text",
            "--allowedTools", *ALLOWED_TOOLS, "--disallowedTools", *DISALLOWED_TOOLS]


def agent_env():
    """The responder's environment without the shared token."""
    return {key: value for key, value in os.environ.items() if key != "RESPONDER_TOKEN"}


def _stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        process.wait()


class AgentRunner:
    """Runs `claude -p` in the project folder; stoppable on timeout and on shutdown."""

    def __init__(self):
        self._lock = threading.Lock()
        self._process = None
        self._interrupted = False

    def run(self, config, prompt, folder):
        with self._lock:
            if self._interrupted:
                return AgentResult(None, "interrupted: the responder stopped before the agent started")
        out_path, err_path = folder / "agent-output.txt", folder / "agent-stderr.txt"
        with open(out_path, "wb") as out, open(err_path, "wb") as err:
            try:
                process = subprocess.Popen(
                    agent_command(config, prompt), cwd=config.project_dir, env=agent_env(),
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True,
                )
            except OSError as error:
                return AgentResult(None, f"agent failed to start: {type(error).__name__}: {error}")
            with self._lock:
                self._process = process
            try:
                process.wait(timeout=config.agent_timeout)
            except subprocess.TimeoutExpired:
                _stop_process(process)
                return AgentResult(process.returncode, f"agent timed out after {config.agent_timeout:g} s and was stopped")
            finally:
                with self._lock:
                    self._process = None
        if self._interrupted:
            return AgentResult(process.returncode, "interrupted: the responder stopped while the agent was running")
        if process.returncode != 0:
            return AgentResult(process.returncode, f"agent exited with code {process.returncode}")
        return AgentResult(0)

    def stop(self):
        with self._lock:
            self._interrupted = True
            process = self._process
        if process is not None and process.poll() is None:
            _stop_process(process)


# --- Responder -------------------------------------------------------------


class Responder:
    def __init__(self, config, http_client=None, agent_runner=None):
        self.config = config
        self.http = http_client or make_http_client()
        self.agent = agent_runner or AgentRunner()
        self._lock = threading.Condition()
        # Keys of incidents queued or running: one per incident (duplicates are refused), so at most
        # one of them is running and the rest are waiting.
        self._active = set()
        self._finished = set()  # (key, startsAt) of firings whose agent finished
        self._pending = 0  # incidents not fully handled yet (for wait_idle)
        self._intake = deque()
        self._agent_queue = deque()
        self._stopping = False
        self._threads = []

    # Called from the request handler: in-memory decisions only, so the webhook answers fast.
    def accept(self, payload, raw_body, received_at=None):
        received_at = received_at or datetime.now(timezone.utc)
        decisions = []
        for alert in payload["alerts"]:
            decisions.append(self._accept_alert(alert, raw_body, received_at))
        return decisions

    def _accept_alert(self, alert, raw_body, received_at):
        status = alert.get("status")
        name = _text(_dict(alert.get("labels")).get("alertname")) or UNKNOWN
        if status == "resolved":
            logger.info("Skipped resolved alert %s", name)
            return "skipped: resolved"
        if status != "firing":
            logger.info("Skipped alert %s with unsupported status %r", name, status)
            return "skipped: unsupported status"
        key = alert_key(alert)
        starts_at = _text(alert.get("startsAt"))
        with self._lock:
            if name in TELEMETRY_ALERTS:
                kind = "telemetry"
            elif key in self._active:
                logger.info("Duplicate of a queued or running incident, not queued again: %s (%s)", name, key)
                return "duplicate"
            elif starts_at and (key, starts_at) in self._finished:
                logger.info("Repeat notification of a handled firing, not run again: %s (%s, startsAt %s)",
                            name, key, starts_at)
                return "duplicate"
            elif self.config.dry_run:
                kind = "dry_run"
                if starts_at:
                    self._finished.add((key, starts_at))
            elif len(self._active) >= MAX_QUEUED + 1:  # one running plus MAX_QUEUED waiting
                kind = "dropped"
                logger.warning("Queue full (1 running, %d waiting): incident %s dropped, no agent run",
                               MAX_QUEUED, name)
            else:
                kind = "agent"
                self._active.add(key)
            incident = Incident(alert=alert, raw_body=raw_body, received_at=received_at, key=key, kind=kind)
            incident.outcome = {
                "agent": "queued: waiting for the agent",
                "telemetry": "telemetry problem (no agent run)",
                "dry_run": "dry run (RESPONDER_DRY_RUN is set, no agent run)",
                "dropped": f"dropped: queue full ({MAX_QUEUED} incidents already waiting), no agent run",
            }[kind]
            self._pending += 1
            self._intake.append(incident)
            self._lock.notify_all()
        logger.info("Accepted firing alert %s as %s", name, kind)
        return kind

    def start(self):
        for target in (self._intake_loop, self._agent_loop):
            thread = threading.Thread(target=target, daemon=True, name=target.__name__)
            thread.start()
            self._threads.append(thread)

    def shutdown(self):
        with self._lock:
            self._stopping = True
            self._lock.notify_all()
        self.agent.stop()
        for thread in self._threads:
            thread.join(timeout=30)

    def wait_idle(self, timeout=10):
        with self._lock:
            return self._lock.wait_for(lambda: self._pending == 0, timeout=timeout)

    def _next(self, items):
        with self._lock:
            self._lock.wait_for(lambda: items or self._stopping)
            return None if self._stopping else items.popleft()

    def _intake_loop(self):
        while (incident := self._next(self._intake)) is not None:
            try:
                self.record(incident)
            except Exception:
                logger.exception("Failed to record incident %s", incident.alertname)
            if incident.kind == "agent":
                with self._lock:
                    self._agent_queue.append(incident)
                    self._lock.notify_all()
            else:
                self._done(incident)

    def _agent_loop(self):
        while (incident := self._next(self._agent_queue)) is not None:
            try:
                self.run_agent(incident)
            except Exception:
                logger.exception("Agent run failed for incident %s", incident.alertname)
            finally:
                with self._lock:
                    self._active.discard(incident.key)
                    if incident.starts_at:
                        self._finished.add((incident.key, incident.starts_at))
                self._done(incident)

    def _done(self, incident):
        with self._lock:
            self._pending -= 1
            self._lock.notify_all()

    def _make_folder(self, incident):
        self.config.incidents_dir.mkdir(parents=True, exist_ok=True)
        base = f"{incident.received_at.strftime('%Y%m%dT%H%M%SZ')}-{safe_name(incident.alertname)}"
        suffix = 1
        while True:
            folder = self.config.incidents_dir / (base if suffix == 1 else f"{base}-{suffix}")
            try:
                folder.mkdir()
                return folder
            except FileExistsError:
                suffix += 1

    def write_summary(self, incident):
        (incident.folder / "summary.md").write_text(render_summary(incident))

    def record(self, incident):
        incident.folder = self._make_folder(incident)
        (incident.folder / "payload.json").write_bytes(incident.raw_body)
        self.write_summary(incident)
        start, end = alert_window(incident.alert, incident.received_at)
        incident.evidence["logs"] = collect_logs(self.http, self.config, start, end)
        incident.evidence["traces"] = collect_traces(self.http, self.config, start, end, incident.endpoint)
        for name, record in incident.evidence.items():
            (incident.folder / f"{name}.json").write_text(json.dumps(record, indent=2) + "\n")
        self.write_summary(incident)
        logger.info("Saved incident %s (%s)", incident.folder, incident.outcome)

    def prompt(self, incident):
        try:
            folder = incident.folder.relative_to(self.config.project_dir)
        except ValueError:
            folder = incident.folder
        return f"{self.config.task_file.read_text().rstrip()}\n\n{PROBE_NOTE}\n\nIncident folder: {folder}\n"

    def run_agent(self, incident):
        incident.outcome = "running: the agent is working on it"
        self.write_summary(incident)
        logger.info("Starting the agent for %s", incident.folder)
        started_at = datetime.now(timezone.utc)
        try:
            result = self.agent.run(self.config, self.prompt(incident), incident.folder)
        except Exception as error:  # a broken runner must not stop the queue
            result = AgentResult(None, f"agent failed: {type(error).__name__}: {error}")
        finished_at = datetime.now(timezone.utc)
        status = {"exit_code": result.exit_code, "error": result.error,
                  "started_at": started_at.isoformat(), "finished_at": finished_at.isoformat()}
        (incident.folder / "agent-status.json").write_text(json.dumps(status, indent=2) + "\n")
        if result.error is None:
            incident.outcome = f"agent finished (exit code {result.exit_code})"
        else:
            incident.outcome = f"agent failed/timed out: {result.error}"
        self.write_summary(incident)
        logger.info("Agent done for %s: %s", incident.folder, incident.outcome)


# --- Web app ---------------------------------------------------------------


def create_app(responder):
    config = responder.config

    @asynccontextmanager
    async def lifespan(app):
        responder.start()
        yield
        responder.shutdown()

    app = FastAPI(title="Order Tracker incident responder", lifespan=lifespan)

    @app.post("/alerts")
    async def alerts(request: Request):
        if config.token_required:
            given = request.headers.get("authorization", "").encode()
            if not hmac.compare_digest(given, f"Bearer {config.token}".encode()):
                return JSONResponse({"detail": "missing or wrong bearer token"}, status_code=401)
        body = await request.body()
        try:
            payload = parse_payload(body)
        except PayloadError as error:
            return JSONResponse({"detail": str(error)}, status_code=400)
        return JSONResponse({"accepted": responder.accept(payload, body)}, status_code=202)

    return app


def bind_socket(host, port=PORT):
    """Bind the listening socket up front, so a busy port is a clear startup error."""
    try:
        family, kind, proto, _, address = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)[0]
        sock = socket.socket(family, kind, proto)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(address)
    except OSError as error:
        raise ConfigError(f"Can't listen on {host}:{port}: {error.strerror or error}. "
                          f"Is another responder (or something else) already using port {port}?") from None
    sock.listen(128)
    sock.set_inheritable(True)
    return sock


def main():
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        config = Config.from_env()
        config.validate()
        sock = bind_socket(config.host)
    except ConfigError as error:
        print(f"responder: {error}", file=sys.stderr)
        return 1
    if config.token and not config.token_required:
        logger.info("RESPONDER_HOST is loopback: RESPONDER_TOKEN is set but not required")
    logger.info("Listening on %s:%d (POST /alerts), dry run: %s, incidents in %s",
                config.host, PORT, config.dry_run, config.incidents_dir)
    server = uvicorn.Server(uvicorn.Config(create_app(Responder(config)), log_level="info"))
    try:
        server.run(sockets=[sock])
    except KeyboardInterrupt:  # uvicorn re-raises Ctrl-C after its graceful shutdown
        logger.info("Stopped")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
