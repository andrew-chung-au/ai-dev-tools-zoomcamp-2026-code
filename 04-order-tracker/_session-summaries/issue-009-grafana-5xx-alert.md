# Issue #009: Order Tracker: Q4 — Provisioned Grafana alert on 5xx order lookups

**Date:** 2026-09-29
**Spec version:** 5161b1d

## What changed and why

Worked #9 following `_docs/agent-kit/process.md`, with PM, Engineer and QA run as subagents. The spec had no commits since `5161b1d`, so no backlog review was needed. The first QA run stopped partway; the same QA agent was resumed and passed all 20 criteria, and #9 was closed.

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
- **QA (resumed): PASS** on all 20 criteria at `41cbfbb`: https://github.com/andrew-chung-au/ai-dev-tools-zoomcamp-2026-code/issues/9#issuecomment-5893861034. Highlights:
  - an app restart plus a new 500 gave one alert instance with no `instance` label, and a restart alone stayed Normal;
  - stopping Prometheus put the rule in Error and raised a `DatasourceError` carrying `owner`, which cleared after Prometheus restarted;
  - the rule was re-provisioned after the `grafana-data` volume was removed, and the dashboard URL followed `GRAFANA_PORT=13000`;
  - `(unmatched)` was judged on indirect evidence: a real unmatched 404 series run through the rule's expression with only the status filter changed.

  Afterwards, Assert clean passed, HEAD was unchanged (`1f1445a`, docs only on top of `41cbfbb`), `DOCKER-USER` held only `RETURN` and the stack was stopped.
- **Firewall on resume:** `make stop` recreates the Compose network, so the bridge name changes on every stop and start (`br-<network id>`); the subnet stays `10.215.24.0/24`. QA stopped when the bridge no longer matched the approved rule. The human then approved the same rule on whatever bridge the project network gets, removed before each `make stop` and at the end.
- **Incident, firewall rule left in place:** QA added the approved `iptables-legacy` `DOCKER-USER` ACCEPT rule (`br-5ff826b3a353`, `10.215.24.0/24`) at about 14:46 UTC. Classifier errors blocked its removal, and my own read-only checks failed the same way. Once the classifier recovered, the orchestrator removed the rule at about 15:08 UTC, which was within the human's "remove it afterwards" approval. `DOCKER-USER` now holds only `RETURN`, and `make stop` was run (volumes kept).

## Files created or modified

- `observability/grafana/provisioning/alerting/order-tracker-alerts.json` (new)
- `tests/test_alerting.py` (new, 14 tests)
- `AGENTS.md` (human-approved gotcha, see below)
- GitHub: #9 body edited by the PM (grooming and the human's decisions), PM, Engineer and QA comments; #9 closed.

Commits: `41cbfbb` (issue work), `1f1445a` (first version of this summary), `0f81495` (AGENTS.md).

## Mismatches with the spec or design docs

- The #9 criterion first asked for env interpolation of `GF_SERVER_ROOT_URL`, which Grafana alerting provisioning doesn't support. The criterion was reworded to `externalURL`, with human approval. The spec itself is unaffected.
- #9 expects `DatasourceError` to reach the responder, but #11 (and possibly spec Q5) doesn't say what the responder does with it yet.

## Commands to validate

- **Verify:** `make verify` (48 passed)
- **Run:** `make run`, then `curl -i http://localhost:8000/api/orders/express-1002` three times. Watch the rule under Grafana → Alerting → Alert rules → `Order Tracker` → "Order Tracker 5xx responses" at <http://127.0.0.1:3000>. In this codespace, Grafana needs the temporary firewall rule (see #8's summary) to reach Prometheus.
- **Stop:** `make stop`
- **Assert clean:** `make assert-clean`

## Proposed AGENTS.md changes

Proposed by the Engineer; approved by the human after QA passed and applied in `0f81495` under Project gotchas:

```diff
+- Grafana alerting provisioning (`observability/grafana/provisioning/alerting/`) doesn't expand env vars, unlike the data source file: write template variables as `$labels` (not `$$labels`), and use `{{ externalURL }}` (Grafana's root URL, from `GF_SERVER_ROOT_URL`) for links back to Grafana. Grafana re-applies provisioned rules on every start, so their `version`/`updated` go up even when nothing changed.
```

## Unrelated problems noticed but not fixed

- The codespace firewall problem (host, not repo), as in #8.
- The auto-mode safety classifier outage blocked cleanup commands, including removing a firewall rule. A role that adds a temporary system change can't always undo it.

## Follow-ups for the next session

- Next issue: #10, which uses the rule UID `order-tracker-5xx`, its labels (`endpoint`, `http_route`, `owner`, `window`, service/env/version) and annotations (`summary`, `description`, `dashboard_url`).
- Any future firewall approval for live checks in this codespace should name the subnet and the project network, not a bridge name, since the bridge changes on every `make stop` + `make run`.
- Propose the #11 criterion for how the responder treats `DatasourceError` (record it without starting the agent, or report "infrastructure, no code fix"), and check whether spec Q5 needs a change.
- `.scratch/` holds files from #8 and #9 (issue bodies, QA helper `state.sh`); all of them can be deleted.

## Suggested commit message

```
Complete session summary for issue #009

Record the resumed QA run (PASS on all 20 criteria at 41cbfbb), the
firewall approval widened to any project bridge, the AGENTS.md gotcha
applied in 0f81495, and the issue's closure.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
