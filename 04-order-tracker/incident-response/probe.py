"""`make probe URL=...`: `curl -i` to this machine only, for the on-call agent.

The agent may not run `curl` directly (prefix permission rules can't limit it to
localhost), so it uses this target. Only `http://localhost[:port][/path]` and
`http://127.0.0.1[:port][/path]` are accepted: no other host or scheme, no
userinfo (`@`), no whitespace (so no extra URLs or curl options).
The URL comes from the `URL` environment variable (make exports command-line
variables), so it never passes through the shell.
"""

import os
import re
import subprocess
import sys

TIMEOUT_SECONDS = 10
URL_PATTERN = re.compile(r"http://(?:localhost|127\.0\.0\.1)(?::(\d{1,5}))?(?:/[\x21-\x7e]*)?")


def is_allowed(url):
    match = URL_PATTERN.fullmatch(url or "")
    if not match or "@" in url or "\\" in url:
        return False
    port = match.group(1)
    return port is None or 0 < int(port) <= 65535


def curl_command(url):
    return ["curl", "-q", "-sS", "-i", "--globoff", "--noproxy", "*", "--proto", "=http", "--max-redirs", "0",
            "--max-time", str(TIMEOUT_SECONDS), url]


def main(env=None):
    url = (os.environ if env is None else env).get("URL", "")
    if not is_allowed(url):
        print(f"probe: refused {url!r}. Usage: make probe URL=http://localhost:8000/path "
              "(only http://localhost or http://127.0.0.1, with an optional port and path)", file=sys.stderr)
        return 2
    return subprocess.run(curl_command(url), stdin=subprocess.DEVNULL).returncode


if __name__ == "__main__":
    sys.exit(main())
