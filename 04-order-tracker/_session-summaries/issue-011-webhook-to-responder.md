# Issue #011: Order Tracker: Q6 — Deliver the 5xx alert to the responder by webhook

**Date:** 2026-10-02
**Spec version:** 8ee8884

## What changed and why

Worked #11 following `_docs/agent-kit/process.md`, with PM, Engineer and QA run as subagents. The spec had no commits since `5161b1d`, so no backlog review was needed at the start. QA passed on the first full run; #11 was closed. The spec changed at the end of the issue (`8ee8884`, below).

- **PM:** groomed #11. Child route on `owner=order-tracker-oncall`, grouped by `alertname`/`endpoint`, 30s/5m/4h. `DatasourceError` routed to the responder and recorded as a telemetry problem with no agent. Token redaction, refused cases, re-provisioning after `grafana-data` removal, offline tests. PM comment: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/11#issuecomment-5944910716
- **Human decisions:**
  - How Grafana gets the token: check env expansion first, else a startup wrapper. Expansion works, so no wrapper (Orchestrator comment on #11).
  - Approved a `DOCKER-USER` firewall rule, which the human added themselves, so Grafana can reach Prometheus inside Docker (see Follow-ups).
  - Discarded the first QA run (below), kept the volume removal as a human step, and ran it when QA asked.
  - At the decision point: approved the AGENTS.md change and the spec line; accepted the Engineer's extra choices and QA's risk recommendations; kept the `make run`/`make stop` block that the PM put in #14.
- **Engineer:** `c9602f7`, `d9689ec`, `5e93d83`. Contact point `Order Tracker responder` (webhook to `http://host.docker.internal:8001/alerts`, `Bearer ${RESPONDER_TOKEN}`), notification policy, Compose `RESPONDER_TOKEN: ${RESPONDER_TOKEN:-}` plus `extra_hosts: host-gateway`, 14 tests, README and `.env.example`. Choices beyond the issue:
  - the root route uses `empty` (12.4.11 has no `grafana-default-email`; naming it crash-looped Grafana);
  - `RESPONDER_HOST=172.17.0.1` (the host-gateway address) rather than `0.0.0.0`;
  - a letters-and-digits token, because Grafana expands `$`.

  The first live run was blocked by the firewall; once the rule was added, all live checks passed with no new commits.
- **QA run 1:** stopped and discarded by the human after auto mode blocked four of its actions: `docker volume rm order-tracker_grafana-data` (irreversible deletion), a script that read a token file into `RESPONDER_TOKEN` for `make run`, a plain `make run`, and a read-only `grep`. The human also rejected an `rm` of QA's token files. Nothing was deleted (all volumes, incident folders and `.scratch/` intact; Assert clean passed). I deleted the two token files afterwards with the human's approval.
- **QA run 2: PASS** at `5e93d83`: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/11#issuecomment-5945855909. Token passed as a make variable; the human removed `grafana-data` when QA asked. QA judged "500-status logs and traces" met: the Loki lines are the INFO "order lookup" lines whose trace IDs match the 500 traces. Assert clean passed and HEAD was unchanged.
- **PM (after the decision point):** drafted the spec line; filed follow-ups #14, #15, #16.

## Files created or modified

- `observability/grafana/provisioning/alerting/order-tracker-notifications.json` (new), `observability/compose.yaml`
- `tests/test_notifications.py` (new)
- `README.md`, `.env.example`
- `AGENTS.md` (human-approved, `b449679`), `_docs/specs.md` (human-approved, `8ee8884`)
- GitHub: #11 body edited by the PM; PM, Orchestrator, Engineer (×2), QA and PM follow-up comments; #14, #15, #16 filed; #11 closed.

Commits: `c9602f7`, `d9689ec`, `5e93d83` (issue work), `b449679` (AGENTS.md), `8ee8884` (spec).

## Mismatches with the spec or design docs

- Resolved: Q5's "on each firing alert" vs skipping the agent for `DatasourceError`/`DatasourceNoData`; the spec now says so (`8ee8884`).
- Q6's check uses `curl`, while the on-call agent can only use `make probe`. The human decided no change (the `curl` steps are the human's).

## Commands to validate

- **Verify:** `make verify` (166 passed)
- **Run:** `make run RESPONDER_TOKEN=<token>`, then `make responder-start RESPONDER_DRY_RUN=1 RESPONDER_HOST=172.17.0.1 RESPONDER_TOKEN=<same token>`
- **Fire the alert:** `make probe URL=http://localhost:8000/api/orders/express-1002` three times. Within about 2 minutes, one folder `*-Order_Tracker_5xx_responses` appears under `incident-response/incidents/`.
- **Delivery status:** Grafana → Alerting → Contact points → "Order Tracker responder" shows the last delivery and any error.
- **Stop:** `make responder-stop`, `make stop`
- **Full Q6 run (human, with the agent):** as above but without `RESPONDER_DRY_RUN=1`.

## Proposed AGENTS.md changes

Proposed by the Engineer; approved by the human after QA passed, and applied in `b449679`:

```diff
-- Grafana alerting provisioning (`observability/grafana/provisioning/alerting/`) doesn't expand env vars, unlike the data source file: write template variables as `$labels` (not `$$labels`), …
+- Grafana alert rule provisioning (`observability/grafana/provisioning/alerting/order-tracker-alerts.json`) doesn't expand env vars: … Contact point settings do expand `${VAR}` (checked on 12.4.11): the responder webhook's token is `${RESPONDER_TOKEN}`, which Compose passes into Grafana's container. …
+- Grafana 12.4.11's default contact point is `empty` (no `grafana-default-email`); a provisioned policy whose root names a missing receiver stops Grafana from starting.
```

## Unrelated problems noticed but not fixed

- The Engineer's first `make run` failed again with Docker's "parent snapshot … does not exist" (as in #10). Pulling the base images fixed it; nothing was pruned.
- Auto mode blocks `docker volume rm` and scripts that load secrets into env vars, so QA steps that need them have to be done by the human or with make variables.

## Follow-ups for the next session

- **Firewall rule still in place, on purpose:** the human keeps it for their full Q6 run. Remove afterwards with:
  `sudo iptables-legacy -D DOCKER-USER -s 10.215.24.0/24 -d 10.215.24.0/24 -j ACCEPT`
  Without it, Grafana can't reach Prometheus in this codespace and the 5xx rule stays in Error.
- The human runs the full Q6 check (responder without dry run) and records it in a session summary.
- #14 (do before the full Q6 run if possible): `make restart-app` so the on-call agent doesn't drop Grafana's token; the responder disallows `make run`/`make stop` for the agent (human confirmed). Without it, an agent `make run` makes later deliveries get 401.
- #15: fetch Loki logs by the 500 traces' IDs; today's query is unfiltered and could miss the failure under real traffic.
- #16 (low): de-duplicate repeated `DatasourceError` notifications.
- #12: agent sandbox hardening (unchanged).
- QA risks the human accepted: the token is readable through `docker inspect` on Grafana; `decrypt=true` export untested; leak scan covered only current logs.
- `.scratch/` holds #11 scripts and texts (`q6*`, `qa11*`, `qa11b_*`, `issue-11-*`, `issue-*.md` follow-up bodies, `spec-q6-*`, `qa_blocked.py`, `qa-transcript.jsonl`, `check_*.py/sh`, `cpenv/`); all can be deleted. No large installs. `incident-response/incidents/` has dry-run folders (git-ignored).

## Suggested commit message

```
Add session summary for issue #011

Record the PM grooming, the human's token and firewall decisions, the
discarded first QA run and the PASS at 5e93d83, the AGENTS.md (b449679)
and spec (8ee8884) changes, and follow-ups #14-#16. The DOCKER-USER rule
stays for the human's Q6 run; the undo command is in the summary.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
