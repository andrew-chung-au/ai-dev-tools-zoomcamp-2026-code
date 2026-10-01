"""`make probe URL=...` (incident-response/probe.py): the on-call agent's only way to curl, localhost only."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("probe", ROOT / "incident-response/probe.py")
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


@pytest.mark.parametrize("url", [
    "http://localhost",
    "http://localhost/",
    "http://localhost:8000/api/orders/express-1002",
    "http://127.0.0.1:8000/api/orders/standard-1001",
    "http://127.0.0.1/healthz?x=1",
    "http://localhost:65535/",
])
def test_accepts_local_http_urls(url):
    assert probe.is_allowed(url)


@pytest.mark.parametrize("url", [
    "",
    "localhost:8000/",
    "https://localhost:8000/",
    "file:///etc/passwd",
    "ftp://localhost/",
    "HTTP://localhost/",
    "http://example.com/",
    "http://localhost.example.com/",
    "http://localhost.invalid:8000/",
    "http://127.0.0.1.nip.io/",
    "http://127.0.0.2/",
    "http://0.0.0.0:8000/",
    "http://[::1]:8000/",
    "http://localhost:8000@example.com/",
    "http://user@localhost/",
    "http://localhost/@example.com",
    "http://localhost:8000/ http://example.com/",
    "http://localhost:8000/ -o /tmp/x",
    "http://localhost:8000/\n-K/etc/passwd",
    "http://localhost:8000/\tx",
    "http://localhost:99999/",
    "http://localhost:0/",
    "http://localhost:80a/",
    "http://localhostevil/",
    "http://localhost\\@example.com/",
    "-K /etc/passwd",
])
def test_rejects_everything_else(url):
    assert not probe.is_allowed(url)


def test_curl_command_is_curl_i_with_short_timeout_and_no_config_or_proxy():
    command = probe.curl_command("http://localhost:8000/")
    assert command[:2] == ["curl", "-q"]  # -q first: ignore ~/.curlrc
    assert "-i" in command and command[-1] == "http://localhost:8000/"
    assert command[command.index("--max-time") + 1] == str(probe.TIMEOUT_SECONDS) and probe.TIMEOUT_SECONDS <= 10
    assert command[command.index("--proto") + 1] == "=http"
    assert command[command.index("--noproxy") + 1] == "*"
    assert "-L" not in command and "--location" not in command


@pytest.fixture
def fake_curl(tmp_path):
    """A `curl` on PATH that records its arguments instead of making a request."""
    calls = tmp_path / "calls.json"
    script = tmp_path / "bin" / "curl"
    script.parent.mkdir()
    script.write_text(f"#!{sys.executable}\nimport json, sys\n"
                      f"open({str(calls)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
                      "print('HTTP/1.1 200 OK')\n")
    script.chmod(0o755)
    env = {**os.environ, "PATH": f"{script.parent}{os.pathsep}{os.environ['PATH']}"}
    return env, calls


def make_probe(env, url):
    return subprocess.run(["make", "--no-print-directory", "probe", f"URL={url}"], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=60)


def test_make_probe_runs_curl_for_a_local_url(fake_curl):
    env, calls = fake_curl
    result = make_probe(env, "http://localhost:8000/api/orders/standard-1001")
    assert result.returncode == 0, result.stderr
    assert "HTTP/1.1 200 OK" in result.stdout
    [argv] = [json.loads(line) for line in calls.read_text().splitlines()]
    assert argv == probe.curl_command("http://localhost:8000/api/orders/standard-1001")[1:]


@pytest.mark.parametrize("url", [
    "http://localhost:8000@example.invalid/",
    "http://localhost:8000/ http://example.invalid/",
    'http://localhost/"; touch probe-injected; echo "',
])
def test_make_probe_refuses_other_urls_without_running_curl(fake_curl, url):
    env, calls = fake_curl
    result = make_probe(env, url)
    assert result.returncode != 0
    assert "probe: refused" in result.stderr
    assert not calls.exists()
    assert not (ROOT / "probe-injected").exists()


@pytest.mark.parametrize("url", ["http://localhost/$(touch probe-injected)", "http://localhost/$$(touch probe-injected)",
                                 "http://localhost/`touch probe-injected`"])
def test_make_probe_never_runs_the_url_through_a_shell(fake_curl, url):
    env, _ = fake_curl
    make_probe(env, url)
    assert not (ROOT / "probe-injected").exists()
