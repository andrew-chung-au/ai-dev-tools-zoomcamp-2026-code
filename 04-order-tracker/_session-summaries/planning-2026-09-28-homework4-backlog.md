# Planning: Homework 4 backlog (Q2–Q6)

**Date:** 2026-09-28
**Spec version:** baa3f14

## What changed and why

Built the backlog following `_docs/agent-kit/process.md` → Backlog. The repo had no open issues (#1–#6 are closed and belong to other projects), and none of Q2–Q6 in the spec is built yet. The orchestrator ran the PM role (`_docs/agent-kit/team/pm.md`) as a subagent. The PM groomed the five drafts in `planning-2026-09-28-homework4-issue-drafts.md` into final issue text. It kept every acceptance criterion and constraint, added criteria for edge cases, and replaced the `#<Qn issue>` placeholders with the expected numbers #7–#11.

The proposal was shown to the human, who answered all six open questions (see Decisions). The answers are folded into the issue bodies below. The spec change for decision 1 is written but not yet committed, and the issues aren't created yet.

### Proposed backlog

| # | Title | Goal | Depends on |
|---|---|---|---|
| #7 | Order Tracker: Q2 — Instrument order lookups with OpenTelemetry (console export) | Order lookups emit metrics, traces and logs to the console (`make logs`), with route-template and status-code attributes | none |
| #8 | Order Tracker: Q3 — Telemetry pipeline to Prometheus, Loki, Tempo and Grafana | Signals go over OTLP through a Collector to Prometheus, Loki and Tempo; Grafana is provisioned from files | #7 |
| #9 | Order Tracker: Q4 — Provisioned Grafana alert on 5xx order lookups | Any 5xx on a route within 5 minutes fires (pending about 1 minute); no data counts as Normal | #8 |
| #10 | Order Tracker: Q5 — Incident responder on port 8001 that starts a headless on-call agent | A host-run responder records incidents with Loki and Tempo evidence and runs `claude -p`, one at a time | #8 |
| #11 | Order Tracker: Q6 — Deliver the 5xx alert to the responder by webhook | Grafana sends the #9 alert by webhook to `host.docker.internal:8001/alerts` | #9, #10 |

The numbers assume creation in this order with no other issues created first. Check them before creating, and fix the cross-links if they differ.

### What grooming added (summary)

- **#7:**
  - The HTTP method goes on the metric (PATCH shares the route template).
  - The `express-1002` span has status ERROR and records the exception.
  - An unmatched path never leaks into the route attribute.
  - `/healthz` noise is kept out of `make logs`.
  - Tests cover the 200, 404 and 500 cases (`raise_server_exceptions=False`).
  - Tests still work with the `DB_PATH` monkeypatch, and the app isn't instrumented twice.
- **#8:**
  - The app stays healthy if the Collector is down.
  - Grafana's root URL is set for links opened from the host.
  - Host ports can be overridden by env vars.
  - Port 8001 stays free.
  - Provisioning survives deleting Grafana's volume.
  - `express-1002` shows in the dashboard's 5xx series.
  - The existing subnet is kept.
- **#9:**
  - The alert covers every route.
  - App restarts don't cause false fires or missed fires (the query uses `increase`).
  - The service, environment and version labels are kept through aggregation.
  - The evaluation interval is 1 minute or less.
  - The rule lives in a provisioned folder.
- **#10:**
  - Folders with the same name don't collide.
  - Missing labels are shown as "unknown".
  - A missing `claude` is recorded as an error.
  - The responder fails fast if port 8001 is busy.
  - A new firing after an incident has finished is a new incident.
  - The README notes that the queue is in memory.
  - Tool permissions are passed explicitly to `claude -p`.
- **#11:**
  - Resolved messages are enabled.
  - The alert routes to the webhook, not the default email contact point.
  - Later alerts in the same group don't create a second incident.
  - Provisioning doesn't depend on the responder being up.

The orchestrator corrected one PM statement: express orders fail on the **last two days of a month** (for example 29–30 September, or 27–28 February in a common year), not the 29th–31st. The #7 body below uses the corrected wording.

## Files created or modified

- `_session-summaries/planning-2026-09-28-homework4-backlog.md`: this file (new).
- Still uncommitted from earlier today: `_session-summaries/planning-2026-09-28-homework4-issue-drafts.md`.
- No product code, spec or protected files changed. Nothing changed on GitHub.

## Mismatches with the spec or design docs

- **Responder bind address vs "all ports bound to `127.0.0.1`":** resolved by decision 1. The spec now makes the responder the one exception (`RESPONDER_HOST`, default `127.0.0.1`, token required off loopback). Uncommitted edit to `_docs/specs.md`, pending the human's OK on the diff.
- **Fixed interface 4 vs the token:** the ResponderTest curl has no `Authorization` header, so it only works with the responder on the default `127.0.0.1`. Q5's check runs in that mode. Q6 runs off loopback with the token. Proposed to the human: a clarifying line under fixed interface 4.
- The alert's query-failure state is now defined: Error (decision 5).
- `order_detail` also runs on POST and PATCH, so the seeded express bug shows up on other routes on the last two days of a month. This is still the one intended incident, not a new bug. QA may see unexpected 500s on `POST /api/orders` on those days.

## Decisions (human, this session)

1. **Bind address:** `RESPONDER_HOST`, default `127.0.0.1`. Spec exception approved (diff shown). Grafana can't reach the host's loopback, so off-loopback use requires a shared token in the `Authorization` header, set on the webhook contact point; requests without it are rejected.
2. **Owner:** `owner=order-tracker-oncall`.
3. **Queueing:** different incidents are queued and duplicates dropped. Duplicates are identified by alert fingerprint. Status `resolved` is ignored. The queue holds at most 3.
4. **httpx:** moved to runtime dependencies, with explicit timeouts on every call.
5. **Query failure:** the alert goes to Error. The responder saves evidence for `DatasourceError`/`DatasourceNoData` alerts but doesn't run the agent.
6. **Q6 tracking:** no tracking issue. The human records the Q6 run in a session summary.

Interpretations the orchestrator made (check these): "ignore resolved" means no incident folder at all, only a log line. A payload without a fingerprint falls back to a hash of its labels. The queue cap of 3 doesn't count the running incident. A full queue still saves evidence but marks the incident dropped.

## Commands to validate

- Nothing to run. This session produced issue text only.
- Before creating: `gh issue list --state open` (expect none), then create #7 → #11 in order with `gh issue create --title ... --body-file ...` and check that the numbers match.

## Proposed AGENTS.md changes

- none new. #8 and #10 ask the engineer to propose Commands changes (full-stack Run/Stop/Logs; a responder target).
- Still open: confirm the **Branching** line.

## Unrelated problems noticed but not fixed

- none new.

## Follow-ups for the next session

- Commit the spec change on its own after the human OKs the diff (`HUMAN_APPROVED=1`).
- Create #7–#11 in order from the bodies below, and check the numbers match.
- Then start the lifecycle with #7: the PM checks the grooming, then the Engineer implements.

---

## Final issue bodies

### #7 — Order Tracker: Q2 — Instrument order lookups with OpenTelemetry (console export)

```markdown
## Goal
Order lookups (`GET /api/orders/{order_id}`) emit OpenTelemetry metrics, traces and logs, exported to the console so they show in `make logs`. Spec: `_docs/specs.md` → Q2.

## Acceptance criteria
- [ ] After `make run`, `curl -i http://localhost:8000/api/orders/standard-1001` returns 200, and within one export interval `make logs` shows a request metric data point with route `/api/orders/{order_id}` and status code 200
- [ ] `curl -i http://localhost:8000/api/orders/standard-1002` returns 404, and the metric records route `/api/orders/{order_id}` with status code 404
- [ ] `curl -i http://localhost:8000/api/orders/express-1002` returns 500 (unchanged), and the metric records route `/api/orders/{order_id}` with status code 500
- [ ] The route attribute is always the template, never the raw id (no `standard-1001` in any metric attribute)
- [ ] A request to a path that matches no route (for example `curl -i http://localhost:8000/nope`, 404) doesn't put the raw path in the route attribute
- [ ] The request metric also carries the HTTP method, so `GET` lookups can be told apart from `PATCH /api/orders/{order_id}`, which uses the same route template
- [ ] Each lookup creates a server span with the route template and status code
- [ ] The `express-1002` span has status ERROR and records the `ValueError` as an exception event
- [ ] Lookup logs are structured and include the trace ID and span ID of the request's span
- [ ] All three signals carry resource attributes `service.name=order-tracker`, `deployment.environment` and `service.version`
- [ ] Environment and version come from env vars set in `compose.yaml`. With nothing set they default to `local` and the image tag (`ORDER_TRACKER_TAG`, itself defaulting to `local`)
- [ ] Logs contain no request bodies, headers or secrets
- [ ] The Compose healthcheck (`/healthz`, every 5 s) still passes, and its telemetry doesn't drown out lookup output in `make logs` (excluding `/healthz` from instrumentation is fine)
- [ ] `make test` passes with no Collector or other telemetry service running
- [ ] Tests cover the 200, 404 and 500 lookups being recorded with the route template and status code. The 500 case uses `TestClient(..., raise_server_exceptions=False)`
- [ ] Instrumentation doesn't break the tests' `monkeypatch` of `main.DB_PATH`, and the app isn't instrumented twice when several tests create a `TestClient`
- [ ] The issue comment names the log lines or fields to search for in `make logs` to find the request metric, and the export interval used
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Collector, Prometheus, Loki, Tempo, Grafana and OTLP export: #8
- Fixing the `express-1002` 500: #11

## Constraints
- Console exporters only. No Collector yet
- Set the metric export interval short enough (for example 5–10 s) that the check doesn't need a minute's wait
- Don't change `order_detail` or any API behavior; the express-1002 failure is the Q6 incident. `order_detail` also runs for POST and PATCH, so express orders created on the last two days of a month also return 500. That is the same seeded bug: leave it alone
- Tests must not need the telemetry stack running
- Work stays inside this folder: `app/`, `compose.yaml`, `Dockerfile`, `pyproject.toml`/`uv.lock`, `tests/`
- Approved dependencies: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi` (plus `opentelemetry-instrumentation-logging` if used). Anything else needs approval
```

### #8 — Order Tracker: Q3 — Telemetry pipeline to Prometheus, Loki, Tempo and Grafana

```markdown
## Goal
The app's metrics, logs and traces flow over OTLP through an OpenTelemetry Collector to Prometheus, Loki and Tempo, and Grafana shows them from provisioned data sources and a dashboard. Spec: `_docs/specs.md` → Q3 and fixed interface 5.

## Acceptance criteria
- [ ] Config for the Collector, Prometheus, Loki, Tempo and Grafana lives in `observability/`. Their services join the main `compose.yaml` (for example with `include:`)
- [ ] `docker compose up --build -d --wait` (and `make run`), run from this folder, exits 0 with the app and all five services running, and the app healthy
- [ ] Every published port is bound to `127.0.0.1`. Grafana, Loki's query API and Tempo's query API are reachable from the host (the responder in #10 queries Loki and Tempo)
- [ ] No Compose service publishes host port 8001 (reserved for the responder in #10)
- [ ] The host ports of the new services can be overridden by env vars (like `ORDER_TRACKER_PORT`), with defaults documented in the issue comment
- [ ] The app exports all three signals over OTLP to the Collector. The endpoint is set by env var in `compose.yaml`
- [ ] If the Collector is down or starts after the app, the app still starts, stays healthy and answers requests with their normal status codes (export errors never turn into 5xx)
- [ ] The Collector routes metrics → Prometheus, logs → Loki, traces → Tempo
- [ ] Grafana has Prometheus, Loki and Tempo provisioned as data sources, with log → trace links (trace ID in a Loki log opens the Tempo trace) and trace → logs links
- [ ] A provisioned dashboard with a fixed UID shows request count by route and status code and error count (4xx and 5xx as separate series), filterable by environment and version
- [ ] Grafana's root URL is set so dashboard links open from the host (`http://localhost:<grafana port>/d/<uid>`)
- [ ] Nothing needs to be set up by hand in Grafana: after `make stop` and `make run`, data sources and the dashboard are still there
- [ ] The same holds after Grafana's data volume is deleted: provisioning recreates data sources and the dashboard
- [ ] After `curl -i http://localhost:8000/api/orders/standard-1002` (404), within a minute the dashboard shows the request with status 404, and its log line in Loki links to its trace in Tempo
- [ ] After `curl -i http://localhost:8000/api/orders/express-1002` (500), within a minute the dashboard shows it in the 5xx series (#9 alerts on this)
- [ ] Running the stack leaves the working tree clean (`git status --short` shows nothing new)
- [ ] `make test` passes with the stack stopped
- [ ] The issue comment gives: the Grafana URL and login, the dashboard name, the exact Prometheus metric name and label names for the request metric (#9 needs them), and the steps to find one request's log and trace
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Alert rules: #9
- Contact points and notification policies: #11
- Retention, HA, auth/TLS (spec: out of scope)

## Constraints
- All configuration is committed. Grafana provisioning is mounted read-only
- Service data goes in named Docker volumes, not folders in the repo, so the working tree stays clean (QA's **Assert clean** depends on this)
- Pin image tags; no `latest`
- The stack runs without a `.env` file. Local-only default credentials are fine
- Environment and version must be Prometheus labels on the request metric (for example with resource-to-telemetry conversion), or the dashboard filters can't work
- The new services join the project's default network. Keep its `ORDER_TRACKER_SUBNET` setting
- Console export from #7 may stay or become optional behind an env var
- Don't change `order_detail` or any API behavior
- Propose Run/Stop/Logs updates to AGENTS.md (and a `make logs` variant for all services if useful). Don't edit AGENTS.md
- Approved dependency: `opentelemetry-exporter-otlp` (or its `-proto-http` / `-proto-grpc` variant)
```

### #9 — Order Tracker: Q4 — Provisioned Grafana alert on 5xx order lookups

```markdown
## Goal
A Grafana alert rule, provisioned from files in the repo, fires when a route returns any 5xx response within 5 minutes. Spec: `_docs/specs.md` → Q4.

## Acceptance criteria
- [ ] The alert rule is provisioned from a file in `observability/` (in a provisioned folder) and appears in Grafana after `make run` with no manual steps
- [ ] The rule queries the #8 request metric for status codes 500–599 over a 5-minute window, split by route, and fires when the count is above 0
- [ ] The rule covers 5xx on every route, not only `GET /api/orders/{order_id}`
- [ ] The query keeps the service, environment and version labels when splitting by route (for example `sum by (route, service, environment, version)`), so each alert instance carries them
- [ ] The query handles counter resets when the app restarts (`make run`) (for example with `increase`), so a restart neither fires the alert nor hides 5xx responses
- [ ] Pending period is 1 minute, and the evaluation interval is 1 minute or less
- [ ] Labels or annotations include: endpoint (route), time window (`5m`), service, environment, deployed version, owner, and the dashboard URL (using the dashboard's fixed UID)
- [ ] The dashboard URL opens the #8 dashboard from the host
- [ ] On a fresh stack with no requests yet (no series at all) the alert is Normal, not No Data or Error
- [ ] When the query fails (for example Prometheus stopped with `docker compose stop prometheus`), the rule goes to Error and Grafana raises a `DatasourceError` alert carrying the rule's labels. The `DatasourceError` alert's labels match the #11 notification policy, so it reaches the responder
- [ ] After `curl -i http://localhost:8000/api/orders/standard-1002` (404) and one evaluation, the alert is Normal
- [ ] After three `curl -i http://localhost:8000/api/orders/express-1002` requests (500), the alert goes to Pending and then Firing within about 2 minutes, labelled with route `/api/orders/{order_id}`
- [ ] With no further 5xx, the alert returns to Normal once the 5-minute window has passed
- [ ] The issue comment explains the threshold and window in terms of user impact, and says where to see the alert state in Grafana
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Contact points, notification policies and the webhook to the responder: #11
- Fixing the `express-1002` 500: #11

## Constraints
- No contact point or notification policy yet. Grafana's default policy may try its default contact point; that's expected here
- Threshold, window and pending period are set by the spec. Changing them needs a spec change
- `owner` label value: `order-tracker-oncall` (approved)
- Set the execution error state to Error explicitly (approved), and set no data to Normal (OK). Don't map query failures to Normal
- Don't change `order_detail` or any API behavior. Use express-1002 only to trigger the alert
- All configuration is committed in `observability/`
```

### #10 — Order Tracker: Q5 — Incident responder on port 8001 that starts a headless on-call agent

```markdown
## Goal
A host-run responder receives Grafana webhook alerts on `POST /alerts` (port 8001), saves an incident record with the evidence, and runs Claude Code headless as the on-call engineer, one incident at a time. Spec: `_docs/specs.md` → Q5, fixed interfaces 3 and 4.

## Acceptance criteria
- [ ] The responder lives in `incident-response/`, runs as a host process (not in Compose) from this folder, and listens on port 8001 at `POST /alerts`
- [ ] If port 8001 is already in use, the responder exits at startup with a clear error message
- [ ] The bind address comes from `RESPONDER_HOST`, default `127.0.0.1`
- [ ] When `RESPONDER_HOST` isn't a loopback address, the responder refuses to start unless `RESPONDER_TOKEN` is set, and rejects any `POST /alerts` without `Authorization: Bearer <RESPONDER_TOKEN>` with 401 (compared in constant time), recording nothing
- [ ] On the default `127.0.0.1`, no token is needed and the ResponderTest curl (no `Authorization` header) is accepted
- [ ] It accepts Grafana's webhook body (`{"alerts":[{"status","labels","annotations",...}]}`) and returns 2xx within 2 seconds, before collecting evidence or running the agent
- [ ] Invalid JSON or a body without `alerts` gets 4xx, and the responder keeps running
- [ ] For each firing alert it creates `incident-response/incidents/<UTC timestamp>-<alertname>/` (alertname reduced to safe filename characters) with: the raw payload, and a summary giving alert name, status, labels, annotations, affected endpoint and dashboard URL
- [ ] Two incidents with the same timestamp and alertname get separate folders (for example with a numeric suffix); neither overwrites the other
- [ ] Missing labels or annotations (for example ResponderTest has no route or dashboard URL) are shown as "unknown" in the summary and cause no error
- [ ] The folder also has recent logs from Loki and related traces from Tempo for the alert window (read-only, bounded time window and result count, with request timeouts). If Loki or Tempo can't be reached, the record says so and the responder continues
- [ ] Alerts with status `resolved` are ignored: no incident folder, no agent, no effect on the queue or duplicate tracking (the responder logs one line saying it skipped them). A payload with several alerts is handled alert by alert
- [ ] `DatasourceError` and `DatasourceNoData` alerts get an incident folder with evidence, but no agent run. The summary says the telemetry pipeline, not the app, is the likely problem
- [ ] After saving the record, it runs `claude -p` in this folder with `incident-response/responder-task.md` and the incident folder path, and saves the agent's full output and exit code in the incident folder
- [ ] If `claude` isn't found or fails to start, the error is recorded in the incident folder and the responder keeps running
- [ ] One agent runs at a time. A different alert arriving meanwhile is queued. A duplicate is logged and not queued again
- [ ] Duplicates are identified by the alert's `fingerprint` (queued or running with the same fingerprint). When a payload has no `fingerprint` (for example the ResponderTest curl), a stable hash of its labels is used instead
- [ ] At most 3 incidents wait in the queue (not counting the one running). A new firing alert that arrives when the queue is full gets its incident folder with evidence, is marked "dropped: queue full", and doesn't run the agent. The webhook still gets 2xx
- [ ] Once an incident's agent has finished, a new firing of the same alert is a new incident, not a duplicate
- [ ] If the agent crashes or exceeds a timeout (for example 30 minutes), the error is recorded and the next incident can start
- [ ] With `RESPONDER_DRY_RUN=1`, it saves the incident record but doesn't run the agent
- [ ] **ResponderTest:** with the stack and responder running, the exact curl in spec fixed interface 4 gets 2xx, creates an incident folder, and the agent's saved output ends with `RESULT: FALSE_POSITIVE - ...`, with no code changed or committed (`git status --short` and `git log -1` unchanged apart from gitignored incident files)
- [ ] `incident-response/responder-task.md` contains the task below word for word
- [ ] Every HTTP call to Loki and Tempo uses `httpx` with an explicit timeout; a timeout is recorded in the incident like any other unreachable source
- [ ] Tests in `tests/` cover: payload parsing (firing, resolved ignored, several alerts, invalid body), the incident folder contents, missing labels/annotations, folder-name collisions, Loki/Tempo unreachable and timing out, `claude` missing or failing, queueing, the queue cap, duplicate suppression by fingerprint and by label hash, `DatasourceError`/`DatasourceNoData` handling, token checks (missing, wrong and correct token; refusing to start on a non-loopback host without a token; no token needed on loopback), and dry run. The agent run and Loki/Tempo are mocked, and the tests run in `make test` without the stack
- [ ] The README (`README.md` in this folder) documents how to start the responder, `RESPONDER_HOST` and `RESPONDER_TOKEN`, where incidents are saved, and that queued incidents are held in memory and lost if the responder restarts
- [ ] `.env.example` lists `RESPONDER_HOST` and `RESPONDER_TOKEN` with placeholder values
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Grafana contact point, notification policy and network access from Grafana: #11
- Escalating to a human (spec: out of scope). ESCALATE is only a result the agent reports
- Pushing code or opening PRs (spec: out of scope)

## Constraints
- Port 8001 and `POST /alerts` exactly. Loki and Tempo URLs come from env vars, defaulting to the `127.0.0.1` ports from #8
- Bind address and token as in spec → Q5 (approved): `RESPONDER_HOST` defaults to `127.0.0.1`; a non-loopback address requires `RESPONDER_TOKEN`. #11 runs it on a non-loopback address so Grafana's container can reach it via `host.docker.internal`
- Never log or save the token (not in incident folders, not in the raw payload file, not in the agent prompt)
- `incident-response/incidents/` goes in `.gitignore`. It's runtime output, and the working tree must stay clean for **Assert clean**
- The agent's allowed tools are limited to: reading and editing files, `make` (including `make run` to restart the app), `curl` to `localhost`, `git status`/`diff`/`add`/`commit`. No push, no other network access, no broad credentials. Pass these as explicit tool permissions on the `claude -p` call, because a headless run can't ask for permission
- Reuse FastAPI and uvicorn (already runtime dependencies). Approved: move `httpx` from dev to runtime dependencies (`uv add httpx`), with an explicit timeout on every call
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

### #11 — Order Tracker: Q6 — Deliver the 5xx alert to the responder by webhook

```markdown
## Goal
Grafana delivers the Q4 5xx alert to the responder at `http://host.docker.internal:8001/alerts` through a provisioned webhook contact point and notification policy. Spec: `_docs/specs.md` → Q6.

## Acceptance criteria
- [ ] A provisioned webhook contact point targets `http://host.docker.internal:8001/alerts` and sends `Authorization: Bearer <token>`, with the token read from the `RESPONDER_TOKEN` env var (not committed)
- [ ] `make run` still succeeds when `RESPONDER_TOKEN` isn't set (fixed interface 5); deliveries then fail with 401, and the issue comment says so
- [ ] Grafana's Compose service maps `host.docker.internal` to the host (`extra_hosts: ["host.docker.internal:host-gateway"]`), so the address works on Linux
- [ ] A provisioned notification policy routes the #9 5xx alert to that contact point (not to Grafana's default email contact point). Group wait and repeat interval are set so one incident gives one delivery, not a stream of repeats
- [ ] Later alerts joining the same group within the group interval don't create a second incident folder for the same route
- [ ] After `make run`, the contact point and policy are there with no manual steps, whether or not the responder is running when Grafana starts
- [ ] With the responder running with `RESPONDER_DRY_RUN=1` on a non-loopback `RESPONDER_HOST` that Grafana's container can reach, with `RESPONDER_TOKEN` set to the same value as Grafana's, three `curl -i http://localhost:8000/api/orders/express-1002` requests fire the alert, Grafana delivers the webhook, and exactly one incident folder is created. It names route `/api/orders/{order_id}` and contains 500-status logs and traces from Loki and Tempo
- [ ] When the alert resolves, the responder receives the resolved notification (2xx) and ignores it: no new incident folder, no agent
- [ ] A webhook sent with a wrong or missing token gets 401 and creates no incident folder
- [ ] With the responder stopped, Grafana records the failed delivery and nothing else breaks
- [ ] The issue comment says how to confirm webhook delivery in Grafana (contact point status or last delivery), and gives the command to run the full Q6 check with the agent
- [ ] **Verify** (`make verify`) passes

## Out of scope
- Investigating or fixing the express-1002 failure. The human runs the full Q6 check (responder without dry run) after this issue closes and records it in a session summary (no tracking issue, by decision); the on-call agent has to find the cause itself
- Other alert routes (email, Slack and so on; spec: out of scope)

## Constraints
- Test in dry-run mode only, so no on-call agent commits during this issue
- Use the responder's bind and token rules from #10 (spec → Q5). Prefer the Docker host-gateway address for `RESPONDER_HOST` over `0.0.0.0` if Grafana can reach it; the issue comment says which one and why
- Don't commit a real token. Document `RESPONDER_TOKEN` in `.env.example`
- Don't change `order_detail` or any API behavior
- All configuration is committed in `observability/`
- Other Compose ports stay bound to `127.0.0.1`
```

---

## Suggested commit message

Commit both of today's uncommitted summaries together, after `git add _session-summaries/planning-2026-09-28-homework4-issue-drafts.md _session-summaries/planning-2026-09-28-homework4-backlog.md`:

```
Add session summaries for Homework 4 issue drafts and backlog

Record the review of the Q2-Q6 issue drafts against the spec, and the
PM-groomed backlog (#7-#11) with final issue bodies, dependencies and
the human's decisions on the responder bind address and token,
owner label, queueing, httpx, alert error state and Q6 tracking.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
