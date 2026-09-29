# Issue #009: Order Tracker: Q4 — Provisioned Grafana alert on 5xx order lookups

**Date:** 2026-09-29
**Spec version:** 5161b1d

## What changed and why

Worked #9 following `_docs/agent-kit/process.md`, with PM, Engineer and QA run as subagents. The spec had no commits since `5161b1d`, so no backlog review was needed. **The issue is not done:** QA stopped partway without a verdict, so #9 stays open.

- **PM:** named the real #8 metric and labels (`http_server_request_duration_seconds_count`; `http_route`, `http_response_status_code`, `service_name`, `deployment_environment`, `service_version`) and dropped `instance`, which changes on every restart. Also pinned the rule's location (`observability/grafana/provisioning/alerting/`, the existing `Order Tracker` folder), a fixed rule UID and data source UID `prometheus`. Added edge cases: restart without duplicates, re-provisioning after the `grafana-data` volume is removed, and Prometheus recovery. Reworded the `DatasourceError` criterion so it can be checked without #11.
- **Human decisions:**
  - `DatasourceError` (Prometheus down) keeps the rule's labels and is meant to reach the responder. A matching criterion for #11 is to be proposed later; #11 and the spec were not touched.
  - The dashboard URL must follow `GRAFANA_PORT`.
  - A 5xx on an unmatched path fires with `endpoint="(unmatched)"`.
  - Each alert has an `endpoint` label mirroring `http_route`, so #10 has a stable key.
  - Accepted `{{ externalURL }}d/order-tracker-requests` in place of env interpolation. Grafana 12.4.11 doesn't expand env vars in alerting provisioning files. `externalURL` comes from `GF_SERVER_ROOT_URL`, so the link still follows the port. The PM reworded that criterion.
  - Approved the same temporary firewall rule as #8 for QA's live checks.
- **Engineer:** `41cbfbb` adds rule `order-tracker-5xx` ("Order Tracker 5xx responses"):
  - evaluates every 30s, pending `1m`; no data maps to OK, a query error to Error;
  - labels `owner=order-tracker-oncall` and `window=5m`; annotations `summary`, `description` and `dashboard_url`;
  - the query is `sum by (http_route, service_name, deployment_environment, service_version) (increase(...{status 5..}[5m])) > 0`, with `label_replace` setting `endpoint`.

  The rule file is JSON so the tests can read it without a new dependency (14 tests). The Engineer's comment on #9: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/9#issuecomment-5892567686. The firing path couldn't be checked live there, because the firewall blocked Grafana → Prometheus.
- **QA (incomplete):** at `41cbfbb`, `make verify` passed. These passed live:
  - the rule is provisioned from the file, with the right UID, folder and data source, and no manual steps;
  - the pending period, evaluation interval and no-data/error states are as specified;
  - a fresh stack is Normal;
  - after the 404 it stays Normal;
  - 3× `express-1002` went Pending at 14:55:30 and Firing at 14:56:30 UTC.

  The auto-mode safety classifier then failed on 9 calls in a row, so QA stopped before capturing the firing alert's labels and posted no verdict. Afterwards, Assert clean passed and HEAD was unchanged (`41cbfbb`).
- **Incident, firewall rule left in place:** QA added the approved `iptables-legacy` `DOCKER-USER` ACCEPT rule (`br-5ff826b3a353`, `10.215.24.0/24`) at about 14:46 UTC. Classifier errors blocked its removal, and my own read-only checks failed the same way. Once the classifier recovered, the orchestrator removed the rule at about 15:08 UTC, which was within the human's "remove it afterwards" approval. `DOCKER-USER` now holds only `RETURN`, and `make stop` was run (volumes kept).

## Files created or modified

- `observability/grafana/provisioning/alerting/order-tracker-alerts.json` (new)
- `tests/test_alerting.py` (new, 14 tests)
- GitHub: #9 body edited by the PM (grooming and the human's decisions), PM and Engineer comments. No QA comment.

Commits: `41cbfbb` (issue work).

## Mismatches with the spec or design docs

- The #9 criterion first asked for env interpolation of `GF_SERVER_ROOT_URL`, which Grafana alerting provisioning doesn't support. The criterion was reworded to `externalURL`, with human approval. The spec itself is unaffected.
- #9 expects `DatasourceError` to reach the responder, but #11 (and possibly spec Q5) doesn't say what the responder does with it yet.

## Commands to validate

- **Verify:** `make verify` (48 passed)
- **Run:** `make run`, then `curl -i http://localhost:8000/api/orders/express-1002` three times. Watch the rule under Grafana → Alerting → Alert rules → `Order Tracker` → "Order Tracker 5xx responses" at <http://127.0.0.1:3000>. In this codespace, Grafana needs the temporary firewall rule (see #8's summary) to reach Prometheus.
- **Stop:** `make stop`
- **Assert clean:** `make assert-clean`

## Proposed AGENTS.md changes

Proposed by the Engineer; not yet shown to the human for approval (the process does that after QA passes):

```diff
+- Grafana alerting provisioning (`observability/grafana/provisioning/alerting/`) doesn't expand env vars, unlike the data source file: write template variables as `$labels` (not `$$labels`), and use `{{ externalURL }}` (Grafana's root URL, from `GF_SERVER_ROOT_URL`) for links back to Grafana. Grafana re-applies provisioned rules on every start, so their `version`/`updated` go up even when nothing changed.
```

## Unrelated problems noticed but not fixed

- The codespace firewall problem (host, not repo), as in #8.
- The auto-mode safety classifier outage blocked cleanup commands, including removing a firewall rule. A role that adds a temporary system change can't always undo it.

## Follow-ups for the next session

- Run a **fresh QA pass** of #9 at `41cbfbb` covering every criterion. Ask the human to approve the temporary firewall rule again first (the approval was for the QA run that just ended). Still unchecked:
  - the firing alert's labels and annotations, including the rendered `dashboard_url`;
  - return to Normal after 5 minutes;
  - Prometheus stop/start giving Error, a `DatasourceError` carrying `owner`, and recovery;
  - restart persistence and re-provisioning after the `grafana-data` volume is removed;
  - `GRAFANA_PORT=13000`;
  - counter resets when the app restarts;
  - the `(unmatched)` endpoint;
  - the issue-comment criterion.
- The `(unmatched)` criterion can't be triggered live without an API change. The Engineer checked it only with a `label_replace` on `vector(1)`. QA should say whether that is enough.
- On PASS: show the human the AGENTS.md diff above, then close #9.
- Propose the #11 criterion for how the responder treats `DatasourceError` (record it without starting the agent, or report "infrastructure, no code fix"), and check whether spec Q5 needs a change.
- `.scratch/` holds files from #8 and #9 (issue bodies, QA helper `state.sh`); all of them can be deleted.

## Suggested commit message

```
Add session summary for issue #009 (in progress)

Record the Q4 alert work so far: PM grooming, the human's decisions
(DatasourceError routing, externalURL dashboard link, endpoint label with
(unmatched) fallback), the rule in 41cbfbb, the partial QA run stopped by
classifier errors, and the firewall rule removed afterwards. #9 stays open
pending a fresh QA pass.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
