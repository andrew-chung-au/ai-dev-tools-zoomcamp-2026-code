# Issue #010: Order Tracker: Q5 — Incident responder on port 8001 that starts a headless on-call agent

**Date:** 2026-10-01
**Spec version:** 5161b1d

## What changed and why

Worked #10 following `_docs/agent-kit/process.md`, with PM, Engineer and QA run as subagents. The spec had no commits since `5161b1d`, so no backlog review was needed. QA failed the first implementation; the fixes and one approved task-text change each passed QA; #10 was closed.

- **PM:** restored the full `responder-task.md` text, which was dropped when the issue was created; its source is `_session-summaries/planning-2026-09-28-homework4-backlog.md`. Added Loki/Tempo defaults (`LOKI_URL` `http://127.0.0.1:3100`, `TEMPO_URL` `http://127.0.0.1:3200`), query limits and the alert window, and matched endpoint/dashboard fields to the #9 rule. Edge cases added: `0.0.0.0`/`::` count as non-loopback, an empty token counts as unset, the token is kept out of the agent's environment, and the agent is stopped on timeout. Also a repeat-notification rule. PM comment: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/10#issuecomment-5926445937
- **Human decisions:**
  - Kept the repeat rule: a Grafana resend with the same fingerprint and the same non-empty `startsAt`, after its agent finished, is a duplicate. A repeated curl without `startsAt` is a new incident.
  - Deferred whether spec Q5 needs a line saying the agent doesn't run for `DatasourceError`/`DatasourceNoData` (see Mismatches).
  - "curl to localhost" is enforced through a `make probe URL=...` wrapper. Direct `curl` is denied for the agent.
  - Step 4 of `responder-task.md` now names `make probe` instead of `curl -i`. The PM updated the issue's copy of the text; the Engineer updated the file and removed the extra prompt note.
  - The `$(shell ...)` gap and the other sandbox gaps went to follow-up #12.
  - Approved the AGENTS.md and `agent-kit.conf` changes below.
- **Engineer:** `4e76226`, `b3bfeb4`, `6308602`, `b6d370c` built the responder (`incident-response/responder.py`, `responder-task.md`, `make responder`, `.env.example`, README section, 63 tests). Choices beyond the spec, listed in its #10 comment:
  - an alert status other than `firing`/`resolved` is skipped with a log line;
  - dry-run incidents count as handled for the repeat rule;
  - `DatasourceError`/`DatasourceNoData` stay out of duplicate tracking;
  - `RESPONDER_AGENT_TIMEOUT` (default 1800 s) is documented in the README.
- **QA run 1: FAIL** at `b6d370c`, on two points:
  - Permission rules like `Bash(curl http://localhost:*)` matched nothing (the colon before `:*` breaks them), so the agent couldn't use curl at all.
  - With the responder idle, a 4-alert payload dropped the 4th, because the incident about to run counted as waiting.
- **Engineer fixes:** `eafe72f` (queue cap) and `4ccec24`: `make probe` plus `incident-response/probe.py` (localhost/127.0.0.1 only, no shell in the path, `Bash(curl:*)` disallowed, 40 tests).
- **QA run 2: PASS** at `4ccec24`: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/10#issuecomment-5927198792. QA found that `make probe 'URL=$(shell <cmd>)'` runs any command under the agent's permissions; this is now #12.
- **Engineer:** `5cdec65` changed step 4 and dropped the prompt note.
- **QA run 3: PASS** at `5cdec65`: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/10#issuecomment-5930999633. This time `make run` worked, so the ResponderTest ran with the full stack: 202 in 5 ms, then `RESULT: FALSE_POSITIVE - ...` with git unchanged.
- After every QA run, Assert clean passed and HEAD was unchanged.
- The PM subagent hit a session rate limit once, before making any change. I checked the issue and issue list, then resumed it.

## Files created or modified

- `incident-response/responder.py`, `incident-response/responder-task.md`, `incident-response/probe.py` (new)
- `tests/test_responder.py`, `tests/test_probe.py` (new)
- `.env.example` (new), `.gitignore`, `Makefile`, `README.md`, `pyproject.toml`, `uv.lock`
- `AGENTS.md`, `agent-kit.conf` (human-approved, see below)
- GitHub: #10 body edited by the PM twice (grooming, then step 4); PM, Engineer and QA comments; #12 filed; #10 closed.

Commits: `4e76226`, `b3bfeb4`, `6308602`, `b6d370c`, `eafe72f`, `4ccec24`, `5cdec65` (issue work), `44d113e` (AGENTS.md, agent-kit.conf).

## Mismatches with the spec or design docs

- Spec Q5 says to start the agent "on each firing alert", but the backlog's decision 5 (and #10) skips the agent for `DatasourceError`/`DatasourceNoData`. The human deferred a spec change.
- The spec has no full text for `responder-task.md` (only a short prompt "along these lines"); the authoritative text is in #10's body. Step 4 now differs from the backlog summary's copy, by human decision.
- Q5 allows the agent "curl to localhost"; in practice it's `make probe`, because permission prefix rules can't limit curl to localhost.

## Commands to validate

- **Verify:** `make verify` (152 passed)
- **Run:** `make run`, then **Responder:** `make responder`, then the ResponderTest curl from spec fixed interface 4. The incident folder appears under `incident-response/incidents/`, and `agent-output.txt` ends with `RESULT: FALSE_POSITIVE - ...`.
- **Probe:** `make probe URL=http://localhost:8000/api/orders/express-1002`
- **Stop:** `make stop`
- **Assert clean:** `make assert-clean`

## Proposed AGENTS.md changes

Proposed by the Engineer; approved by the human after QA passed, and applied in `44d113e`:

```diff
 Commands, after Logs:
+- **Responder:** `make responder`: runs the incident responder (`incident-response/`) on the host, on port 8001 (`POST /alerts`); Ctrl-C to stop. Env vars (`RESPONDER_HOST`, `RESPONDER_TOKEN`, `RESPONDER_DRY_RUN`, `LOKI_URL`, `TEMPO_URL`) are in the README.
+- **Probe:** `make probe URL=http://localhost:8000/<path>`: `curl -i` (10 s timeout) to `http://localhost` or `http://127.0.0.1` only; anything else is refused. The on-call agent's only way to send HTTP requests.
 Project gotchas:
+- Incident records go to `incident-response/incidents/` (git-ignored). The responder keeps its queue in memory only; a restart loses queued incidents.
```

Also in `44d113e`: `agent-kit.conf` PROTECTED gains `incident-response/responder-task.md`, `incident-response/probe.py` and `Makefile`. From now on, any Makefile change needs `HUMAN_APPROVED=1`.

## Unrelated problems noticed but not fixed

- During the Engineer's run and QA run 1, `make run` failed while building the app image (Docker "parent snapshot … does not exist"). It worked again in QA run 3. No Docker state was pruned.

## Follow-ups for the next session

- Next issue: #11 (Grafana contact point and notification policy to the responder). When grooming it, decide whether `DatasourceError` is routed to the responder too. #11 runs the responder off loopback, so it needs `RESPONDER_TOKEN`.
- #12: harden the agent's command sandbox (`$(shell ...)` in `make probe`, any make target or `--eval`, editing the Makefile or `probe.py` and then running them).
- Decide whether spec Q5 should mention the `DatasourceError`/`DatasourceNoData` exception.
- `.scratch/` holds issue bodies and QA/Engineer scripts from #10 (`issue-10*.md`, `qa10*`, `eng10*`); all can be deleted. `incident-response/incidents/` has folders from live runs (git-ignored).

## Suggested commit message

```
Add session summary for issue #010

Record the PM grooming, the human's decisions (repeat rule, make probe,
step 4 change, follow-up #12), QA's FAIL and two PASS runs, and the
AGENTS.md / agent-kit.conf changes applied in 44d113e.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
