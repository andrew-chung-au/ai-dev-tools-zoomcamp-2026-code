# Planning: review of the Homework 4 issue drafts (Q2–Q6)

**Date:** 2026-09-28
**Spec version:** baa3f14

## What changed and why

Reviewed the five drafted issues (A–E, one per homework question) against `_docs/specs.md`, the code (`app/main.py`, `compose.yaml`, `Dockerfile`, `pyproject.toml`), the `Makefile` and the kit's task template and PM role. Rewrote each one so it matches the spec, every criterion can be checked, and the issues agree with each other. The revised issue texts are below, ready to paste into GitHub once the human approves them. Nothing was created on GitHub and no other files changed.

### Changes that apply to all five drafts

- **`make up` doesn't exist.** The target is `make run` (`docker compose up --build -d --wait`). Fixed in A and B.
- **Each issue links its spec section**, so an engineer can work from the issue and the spec alone (PM definition of done).
- **Out of scope items point to the follow-up issue** as `#<Qn issue>`. Replace these with real numbers once the issues exist.
- **Spec-wide constraints were missing.** Each issue now says: don't touch the express delivery-date logic in `order_detail` (spec: the incident stays unfixed until Q6), tests must not need the telemetry stack running, and ports are bound to `127.0.0.1`.
- **Dependencies:** the spec says new packages need approval. The drafts' "Approved dependencies" lines are kept, now with the package names, so approving the issue approves them. FastAPI and uvicorn are already runtime dependencies, so the responder (D) needs no new web framework.

### Per-draft findings

**A (Q2 instrumentation)**
- Missing the **environment** and **deployed version** resource attributes and their env vars and defaults (`local`, image tag). Only service name was covered, and without its fixed value `order-tracker`.
- "Includes the route" was ambiguous. The spec requires the route template `/api/orders/{order_id}`, not the raw id. Without that, every order id gets its own series.
- Added 404 and 500 cases. Q3 depends on 404s being recorded and Q4 on 500s. `express-1002` fails with an unhandled `ValueError`, and some instrumentation setups miss the status of unhandled exceptions, so the 500 has to be checked explicitly.
- The console metric exporter only flushes every 60 s by default, so the `make logs` check can look like a failure. Added a short export interval as a constraint.
- "Verify passes" was replaced by an explicit check that tests pass without a Collector.

**B (Q3 pipeline)**
- Missing: `observability/` folder, Compose `include:` into the main `compose.yaml`, `127.0.0.1` port binding, **log ↔ trace links** in the data sources, and dashboard **filters for environment and version**.
- `docker compose up --build -d --wait` must exit successfully with every service up (fixed interface 5). Services without a healthcheck don't block `--wait`, so the criterion now names the exit status.
- Found a cross-issue dependency: D queries Loki and Tempo from the host, so B must publish their query ports on `127.0.0.1`.
- Q4 needs the exact Prometheus metric and label names, which OTLP → Prometheus translation changes (for example, dots become underscores and a `_count` suffix is added). B's issue comment now has to record them.
- Environment and version have to be Prometheus labels for the dashboard filters (for example with resource-to-telemetry conversion). Noted this as an edge case.
- Grafana provisioning mounts are read-only, and image tags are pinned rather than `latest`.
- `.env` wording tightened: the stack must run without a `.env` file. Agents may not open `.env` (AGENTS.md), and auth is out of scope.

**C (Q4 alert)**
- The draft let the engineer choose the threshold and window. The spec fixes them: any 5xx on a route within 5 minutes, with a pending period of about 1 minute. The issue comment now explains that choice rather than inventing one.
- Missing labels and annotations: **service, environment, deployed version, owner**. The spec doesn't give a value for `owner` (open question below).
- No-data handling now also covers "no series at all" (a fresh stack before any request).
- Added a positive check (a few `express-1002` lookups make the alert fire) and the spec's negative check (`standard-1002` → Normal). Without a positive check, QA can't tell whether the rule works at all.
- The alert is split per route, so the endpoint label comes from the data.
- The dashboard link needs a stable dashboard UID from B.

**D (Q5 responder)**
- **The ResponderTest acceptance criterion was missing** (fixed interface 4 and the Q5 check). Added.
- **The prompt dropped "restart the app and verify the failing request now succeeds"**, which the spec's prompt and the Q6 check require. Added as a step, and the agent's permissions now include `make run` and `curl` to localhost.
- Missing: runs as a **host process**, **returns 2xx quickly** with the agent running asynchronously, and the incident record includes **alert name, status, labels, annotations and the dashboard URL**.
- "One at a time" plus "duplicates ignored" didn't say what happens to a *different* alert arriving while the agent runs. The revision queues it and drops only duplicates of an incident already queued or running. It also says what counts as a duplicate.
- Added edge cases: `resolved` alerts (record, no agent), several alerts in one payload, invalid JSON (4xx), Loki or Tempo unreachable (still record and launch, and note the gap), agent timeout or crash (lock released, error recorded), unsafe characters in `alertname` in the folder name.
- `pyproject.toml` has `testpaths = ["tests"]`, so tests under `incident-response/` wouldn't run in `make test` or `make verify`. The revision puts them under `tests/`. `incident-response` also isn't an importable Python package name (hyphen), so the tests load the module by path.
- `httpx` is dev-only. The responder can use the standard library's `urllib`, or `httpx` moves to runtime dependencies (needs approval).
- The ESCALATE result is kept only as a report outcome. Escalating to a human is out of scope in the spec, so nothing acts on it.

**E (Q6 wiring)**
- The draft left the approach open ("Compose network or host address"). The spec (R4, approved) fixes it: `http://host.docker.internal:8001/alerts`. On Linux that needs `extra_hosts: host.docker.internal:host-gateway` on Grafana.
- **Found a conflict:** if the responder binds `127.0.0.1`, Grafana's container can't reach it through the host gateway. The bind address is an open question below.
- Added a notification policy timing check (group wait and repeat interval), resolved notifications, and what the dry-run incident folder must contain.
- Made explicit that the human runs the homework's full Q6 check (agent fixes `express-1002`) after this issue closes.

---

## Revised issue texts

### Issue 1 (Q2): Instrument order lookups with OpenTelemetry (console export)

```markdown
## Goal
Order lookups (`GET /api/orders/{order_id}`) emit OpenTelemetry metrics, traces and logs, exported to the console so they show in `make logs`. Spec: `_docs/specs.md` → Q2.

## Acceptance criteria
- [ ] After `make run`, `curl -i http://localhost:8000/api/orders/standard-1001` returns 200, and within one export interval `make logs` shows a request metric data point with route `/api/orders/{order_id}` and status code 200
- [ ] `curl -i http://localhost:8000/api/orders/standard-1002` returns 404, and the metric records route `/api/orders/{order_id}` with status code 404
- [ ] `curl -i http://localhost:8000/api/orders/express-1002` returns 500 (unchanged), and the metric records route `/api/orders/{order_id}` with status code 500
- [ ] The route attribute is always the template, never the raw id (no `standard-1001` in any metric attribute)
- [ ] Each lookup creates a server span with the route and status code
- [ ] Lookup logs are structured and include the trace ID and span ID of the request's span
- [ ] All three signals carry resource attributes `service.name=order-tracker`, `deployment.environment` and `service.version`
- [ ] Environment and version come from env vars set in `compose.yaml`. With nothing set they default to `local` and the image tag (`ORDER_TRACKER_TAG`, itself defaulting to `local`)
- [ ] Logs contain no request bodies, headers or secrets
- [ ] `make test` passes with no Collector or other telemetry service running
- [ ] The issue comment names the log lines or fields to search for in `make logs` to find the request metric, and the export interval used
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Collector, Prometheus, Loki, Tempo, Grafana and OTLP export: #<Q3 issue>
- Fixing the `express-1002` 500: #<Q6 issue>

## Constraints
- Console exporters only. No Collector yet
- Set the metric export interval short enough (for example 5–10 s) that the check doesn't need a minute's wait
- Don't change `order_detail` or any API behavior; the express-1002 failure is the Q6 incident
- Tests must not need the telemetry stack running
- Work stays inside this folder: `app/`, `compose.yaml`, `Dockerfile`, `pyproject.toml`/`uv.lock`, `tests/`
- Approved dependencies: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi` (plus `opentelemetry-instrumentation-logging` if used). Anything else needs approval
```

### Issue 2 (Q3): Telemetry pipeline to Prometheus, Loki, Tempo and Grafana

```markdown
## Goal
The app's metrics, logs and traces flow over OTLP through an OpenTelemetry Collector to Prometheus, Loki and Tempo, and Grafana shows them from provisioned data sources and a dashboard. Spec: `_docs/specs.md` → Q3 and fixed interface 5.

## Acceptance criteria
- [ ] Config for the Collector, Prometheus, Loki, Tempo and Grafana lives in `observability/`. Their services join the main `compose.yaml` (for example with `include:`)
- [ ] `docker compose up --build -d --wait` (and `make run`), run from this folder, exits 0 with the app and all five services running, and the app healthy
- [ ] Every published port is bound to `127.0.0.1`. Grafana, Loki's query API and Tempo's query API are reachable from the host (the responder in #<Q5 issue> queries Loki and Tempo)
- [ ] The app exports all three signals over OTLP to the Collector. The endpoint is set by env var in `compose.yaml`
- [ ] The Collector routes metrics → Prometheus, logs → Loki, traces → Tempo
- [ ] Grafana has Prometheus, Loki and Tempo provisioned as data sources, with log → trace links (trace ID in a Loki log opens the Tempo trace) and trace → logs links
- [ ] A provisioned dashboard with a fixed UID shows request count by route and status code and error count (4xx and 5xx as separate series), filterable by environment and version
- [ ] Nothing needs to be set up by hand in Grafana: after `make stop` and `make run`, data sources and the dashboard are still there
- [ ] After `curl -i http://localhost:8000/api/orders/standard-1002` (404), within a minute the dashboard shows the request with status 404, and its log line in Loki links to its trace in Tempo
- [ ] Running the stack leaves the working tree clean (`git status --short` shows nothing new)
- [ ] `make test` passes with the stack stopped
- [ ] The issue comment gives: the Grafana URL and login, the dashboard name, the exact Prometheus metric name and label names for the request metric (#<Q4 issue> needs them), and the steps to find one request's log and trace
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Alert rules: #<Q4 issue>
- Contact points and notification policies: #<Q6 issue>
- Retention, HA, auth/TLS (spec: out of scope)

## Constraints
- All configuration is committed. Grafana provisioning is mounted read-only
- Service data goes in named Docker volumes, not folders in the repo, so the working tree stays clean (QA's **Assert clean** depends on this)
- Pin image tags; no `latest`
- The stack runs without a `.env` file. Local-only default credentials are fine
- Environment and version must be Prometheus labels on the request metric (for example with resource-to-telemetry conversion), or the dashboard filters can't work
- Console export from #<Q2 issue> may stay or become optional behind an env var
- Don't change `order_detail` or any API behavior
- Propose Run/Stop/Logs updates to AGENTS.md (and a `make logs` variant for all services if useful). Don't edit AGENTS.md
- Approved dependency: `opentelemetry-exporter-otlp` (or its `-proto-http` / `-proto-grpc` variant)
```

### Issue 3 (Q4): Provisioned Grafana alert on 5xx order lookups

```markdown
## Goal
A Grafana alert rule, provisioned from files in the repo, fires when a route returns any 5xx response within 5 minutes. Spec: `_docs/specs.md` → Q4.

## Acceptance criteria
- [ ] The alert rule is provisioned from a file in `observability/` and appears in Grafana after `make run` with no manual steps
- [ ] The rule queries the #<Q3 issue> request metric for status codes 500–599 over a 5-minute window, split by route, and fires when the count is above 0
- [ ] Pending period is 1 minute
- [ ] Labels or annotations include: endpoint (route), time window (`5m`), service, environment, deployed version, owner, and the dashboard URL (using the dashboard's fixed UID)
- [ ] On a fresh stack with no requests yet (no series at all) the alert is Normal, not No Data or Error
- [ ] After `curl -i http://localhost:8000/api/orders/standard-1002` (404) and one evaluation, the alert is Normal
- [ ] After three `curl -i http://localhost:8000/api/orders/express-1002` requests (500), the alert goes to Pending and then Firing within about 2 minutes, labelled with route `/api/orders/{order_id}`
- [ ] With no further 5xx, the alert returns to Normal once the 5-minute window has passed
- [ ] The issue comment explains the threshold and window in terms of user impact, and says where to see the alert state in Grafana
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Contact points, notification policies and the webhook to the responder: #<Q6 issue>
- Fixing the `express-1002` 500: #<Q6 issue>

## Constraints
- No contact point or notification policy yet. Grafana's default policy may try its default contact point; that's expected here
- Threshold, window and pending period are set by the spec. Changing them needs a spec change
- Don't change `order_detail` or any API behavior. Use express-1002 only to trigger the alert
- All configuration is committed in `observability/`
```

### Issue 4 (Q5): Incident responder on port 8001 that starts a headless on-call agent

```markdown
## Goal
A host-run responder receives Grafana webhook alerts on `POST /alerts` (port 8001), saves an incident record with the evidence, and runs Claude Code headless as the on-call engineer, one incident at a time. Spec: `_docs/specs.md` → Q5, fixed interfaces 3 and 4.

## Acceptance criteria
- [ ] The responder lives in `incident-response/`, runs as a host process (not in Compose) from this folder, and listens on port 8001 at `POST /alerts`
- [ ] It accepts Grafana's webhook body (`{"alerts":[{"status","labels","annotations",...}]}`) and returns 2xx within 2 seconds, before collecting evidence or running the agent
- [ ] Invalid JSON or a body without `alerts` gets 4xx, and the responder keeps running
- [ ] For each firing alert it creates `incident-response/incidents/<UTC timestamp>-<alertname>/` (alertname reduced to safe filename characters) with: the raw payload, and a summary giving alert name, status, labels, annotations, affected endpoint and dashboard URL
- [ ] The folder also has recent logs from Loki and related traces from Tempo for the alert window (read-only, bounded time window and result count, with request timeouts). If Loki or Tempo can't be reached, the record says so and the responder continues
- [ ] Resolved alerts are recorded but don't start the agent. A payload with several alerts is handled alert by alert
- [ ] After saving the record, it runs `claude -p` in this folder with `incident-response/responder-task.md` and the incident folder path, and saves the agent's full output and exit code in the incident folder
- [ ] One agent runs at a time. A different alert arriving meanwhile is queued. A duplicate (same alertname and labels as an incident queued or running) is recorded and not queued again
- [ ] If the agent crashes or exceeds a timeout (for example 30 minutes), the error is recorded and the next incident can start
- [ ] With `RESPONDER_DRY_RUN=1`, it saves the incident record but doesn't run the agent
- [ ] **ResponderTest:** with the stack and responder running, the exact curl in spec fixed interface 4 gets 2xx, creates an incident folder, and the agent's saved output ends with `RESULT: FALSE_POSITIVE - ...`, with no code changed or committed
- [ ] `incident-response/responder-task.md` contains the task below word for word
- [ ] Tests in `tests/` cover: payload parsing (firing, resolved, several alerts, invalid body), the incident folder contents, Loki/Tempo unreachable, queueing and duplicate suppression, and dry run. The agent run and Loki/Tempo are mocked, and the tests run in `make test` without the stack
- [ ] The README documents how to start the responder and where incidents are saved
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Grafana contact point, notification policy and network access from Grafana: #<Q6 issue>
- Escalating to a human (spec: out of scope). ESCALATE is only a result the agent reports
- Pushing code or opening PRs (spec: out of scope)

## Constraints
- Port 8001 and `POST /alerts` exactly. Loki and Tempo URLs come from env vars, defaulting to the `127.0.0.1` ports from #<Q3 issue>
- Bind address: <decided by the human, see open question 2 in the session summary>
- `incident-response/incidents/` goes in `.gitignore`. It's runtime output, and the working tree must stay clean for **Assert clean**
- The agent's allowed tools are limited to: reading and editing files, `make` (including `make run` to restart the app), `curl` to `localhost`, `git status`/`diff`/`add`/`commit`. No push, no other network access, no broad credentials
- Reuse FastAPI and uvicorn (already runtime dependencies). For HTTP calls to Loki and Tempo, use the standard library, or ask to move `httpx` from dev to runtime dependencies
- `pyproject.toml` only collects `tests/`, so responder tests go there. `incident-response` isn't an importable package name, so load the module by path or keep the logic in an importable module
- Propose a Makefile target (for example `make responder`) and the matching AGENTS.md Commands line. Don't edit AGENTS.md
- Propose adding `incident-response/responder-task.md` to PROTECTED in `agent-kit.conf`, so the on-call agent can't rewrite its own instructions. Don't edit `agent-kit.conf`
- Don't change `order_detail` or any API behavior

## responder-task.md

You are the on-call engineer for this project. An alert just fired. The evidence is in the incident folder you were given.

This is an incident, not a planned issue: don't follow the issue lifecycle in _docs/agent-kit/process.md, but do follow the Conventions in AGENTS.md.

1. Read the evidence first. If the alert has the label test="true", or the evidence shows no real failure, explain why it is a test or a false positive and do not change any code.
2. Otherwise, find the root cause. Read the code and reproduce the failure with a test.
3. If you find a real bug, make the smallest fix and keep the reproducing test as a regression test. Run `make verify`.
4. Restart the app with `make run`, then repeat the failing request with `curl -i` and confirm it no longer fails. If it still fails, go back to step 2.
5. Commit the fix and the test, staging explicit paths only. Don't push, don't edit protected files, and never use --no-verify.
6. If the fix needs anything beyond code and tests (a protected file, a new dependency, a configuration change), don't make it. Report ESCALATE instead.
7. End your answer with a single line: RESULT: <FIXED | FALSE_POSITIVE | ESCALATE> - <one-sentence summary>.
```

### Issue 5 (Q6): Deliver the 5xx alert to the responder by webhook

```markdown
## Goal
Grafana delivers the Q4 5xx alert to the responder at `http://host.docker.internal:8001/alerts` through a provisioned webhook contact point and notification policy. Spec: `_docs/specs.md` → Q6.

## Acceptance criteria
- [ ] A provisioned webhook contact point targets `http://host.docker.internal:8001/alerts`
- [ ] Grafana's Compose service maps `host.docker.internal` to the host (`extra_hosts: ["host.docker.internal:host-gateway"]`), so the address works on Linux
- [ ] A provisioned notification policy routes the #<Q4 issue> 5xx alert to that contact point. Group wait and repeat interval are set so one incident gives one delivery, not a stream of repeats
- [ ] After `make run`, the contact point and policy are there with no manual steps
- [ ] With the responder running with `RESPONDER_DRY_RUN=1`, three `curl -i http://localhost:8000/api/orders/express-1002` requests fire the alert, Grafana delivers the webhook, and exactly one incident folder is created. It names route `/api/orders/{order_id}` and contains 500-status logs and traces from Loki and Tempo
- [ ] When the alert resolves, the resolved notification is recorded and no agent runs
- [ ] With the responder stopped, Grafana records the failed delivery and nothing else breaks
- [ ] The issue comment says how to confirm webhook delivery in Grafana (contact point status or last delivery), and gives the command to run the full Q6 check with the agent
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Investigating or fixing the express-1002 failure. The human runs the full Q6 check (responder without dry run) after this issue closes, and the on-call agent has to find the cause itself
- Other alert routes (email, Slack and so on; spec: out of scope)

## Constraints
- Test in dry-run mode only, so no on-call agent commits during this issue
- Don't change `order_detail` or any API behavior
- All configuration is committed in `observability/`
- Other Compose ports stay bound to `127.0.0.1`
```

---

## Files created or modified

- `_session-summaries/planning-2026-09-28-homework4-issue-drafts.md`: this file (new).

## Mismatches with the spec or design docs

- The drafts differed from the spec in several places (listed per draft above), mainly Draft C's open threshold and Draft E's open network approach. The revisions follow the spec.
- The spec's Q5 prompt says "run the tests, restart the app, verify". The draft's `responder-task.md` dropped restart and verify. The revision restores them.
- **Possible spec gap:** "All ports are bound to `127.0.0.1`" (Q3) combined with a host-run responder reached via `host.docker.internal` (R4, Q6). A responder listening only on `127.0.0.1` can't be reached from a container. See open question 2.

## Open questions for the human

1. **`owner` label value (Q4):** the spec requires it but gives no value. Suggestion: `order-tracker-oncall`.
2. **Responder bind address (Q5/Q6):** `0.0.0.0` (simplest; reachable from Grafana, and also from the LAN; auth is out of scope) or the Docker bridge gateway address only (tighter, but depends on the host). Recommendation: `RESPONDER_HOST` env var, defaulting to `0.0.0.0`, with a README note that it's for local use only. If you'd rather keep the spec's "`127.0.0.1` only" wording strict, the spec needs a line making the responder an exception.
3. **Queue vs drop (Q5):** the revision queues different incidents and drops duplicates. The spec only says "one at a time". Confirm.
4. **`httpx` (Q5):** allow moving it to runtime dependencies, or stick to the standard library?

## Commands to validate

- Nothing to run. This session produced issue text only.
- Once the issues are implemented: **Run:** `make run`, **Logs:** `make logs`, **Test (all):** `make test`, **Verify:** `make verify`.

## Proposed AGENTS.md changes

- none new. Issues 2 and 4 each ask the engineer to propose Commands changes (full-stack Run/Stop/Logs; a responder target).
- Still open: confirm the **Branching** line.

## Unrelated problems noticed but not fixed

- none new.

## Follow-ups for the next session

- Human answers the open questions and approves the revised issue texts.
- Create the five issues in order (Q2 → Q6), then replace the `#<Qn issue>` placeholders with real numbers.
- If open question 2 changes the spec, commit that spec change on its own first (protected file, `HUMAN_APPROVED=1`).

## Suggested commit message

After `git add _session-summaries/planning-2026-09-28-homework4-issue-drafts.md`:

```
Add session summary for Homework 4 issue draft review

Review the Q2-Q6 issue drafts against the spec and record revised,
paste-ready issue texts: align thresholds, labels and the webhook
address with the spec, restore the restart-and-verify step in the
on-call prompt, add the ResponderTest check, and flag open questions
(owner label, responder bind address, queueing, httpx).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
