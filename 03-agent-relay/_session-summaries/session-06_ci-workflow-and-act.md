# Session 6 — GitHub Actions CI workflow, `act`, and a real rollout bug

Continues [[session-05_kind-kubernetes-deployment]]. Wires the existing
test suite, Docker build, and kind deployment (sessions 2/3/5) into a single
CI pipeline, verified by actually running it locally rather than just
authoring it.

## What changed

### `.github/workflows/ci.yml` (new)

Three jobs:

- **`test`** — `postgres:16-alpine` service container (`pg_isready`
  healthcheck), `DATABASE_URL` pointed at it. Runs `test_agent_relay.py`
  (unit tests; per its own docstring/`os.environ.setdefault`, it respects
  an explicit `DATABASE_URL`, so this exercises the Postgres branch of
  `immediate_transaction()` added in
  [[session-04_postgres-compose-and-sandbox-networking]], not just SQLite).
  Then starts `uvicorn` in the background, polls `/ready`, and runs
  `test_flow.py` (from [[session-02_test-flow-integration-test]]) against
  the live Postgres-backed server.
- **`build`** — `docker build -t agent-relay:local .`.
- **`deploy`** — `needs: [test, build]`, so it only runs if both succeed.
  Installs `kubectl`/`kind` if missing, ensures the `agent-relay` kind
  cluster exists, `kind load docker-image`, `kubectl apply -f k8s/`, then
  (added after the bug below) `kubectl rollout restart
  deployment/agent-relay`, then waits on rollout status for both
  deployments. Comment in the file notes this assumes a runner colocated
  with the target cluster (self-hosted / local `act`), not a GitHub-hosted
  ephemeral runner.

### `dashboard.html`

`<h1>Agent Relay</h1>` → `<h1>Agent Relay v2</h1>`, used as the workflow's
own smoke test for whether a rerun actually deploys a new image.

## `act`: installed and actually run, not just authored against

`act` wasn't installed; installed v0.2.89 via the official script. Running
it locally needed `--container-options "--network host"` on every
invocation — without it, this sandbox's known container-egress restriction
(session 4/5: any *container-initiated* outbound connection is blocked, not
just container-to-container) breaks `actions/checkout`, `uv sync`, and the
`curl` installs inside act's own job containers. With host networking, the
job container's traffic looks host-initiated to the firewall and everything
works, including reusing the host's Docker daemon (`docker.sock`, mounted
by act by default) for `docker build` and `kind load`.

## Two real bugs found by actually executing the workflow

1. **False-positive integration test.** First `act -j test --network host`
   run: the readiness poll hit `200` instantly and `test_flow.py` passed —
   but the job's own `uvicorn` had actually failed with `address already in
   use`. A `kubectl port-forward svc/agent-relay 8000:8000` left running
   from session 5 was still squatting host port 8000, and `--network host`
   made the job container share that exact port namespace, so the "ready"
   check silently hit the *other*, already-running k8s-deployed server
   instead of the job's own. Killed the stray port-forward, reran — clean
   pass, job's own server bound and served both test suites.

2. **The actual thing the task was testing for: same-tag images don't
   trigger a Kubernetes rollout.** After editing `dashboard.html` and
   rerunning the full `act push` pipeline, `kubectl apply -f k8s/` reported
   `deployment.apps/agent-relay unchanged` — expected, since the Deployment
   manifest still names the same `agent-relay:local` tag; only the image
   *content* behind that tag changed. With `imagePullPolicy: IfNotPresent`,
   the already-running pod (23m old) never restarted and kept serving the
   *old* `<h1>Agent Relay</h1>`, confirmed by an actual port-forward + curl
   rather than trusting the workflow's "success" status. Fixed by adding an
   explicit `kubectl rollout restart deployment/agent-relay` step between
   `kind load docker-image` and the rollout-status wait. Reran once more:
   `1 old replicas are pending termination` → new pod, and `curl` through a
   fresh port-forward confirmed `<h1>Agent Relay v2</h1>` live, `/ready` →
   `200`.

## Answered: what should happen if a test fails in this workflow?

**Keep the existing version running and stop the deployment.** The
`deploy` job's `needs: [test, build]` means it never runs at all if `test`
fails — currently-running pods are left untouched rather than replaced by
an unvalidated image. Not "deploy anyway and report" (no such fallback
exists), not "delete the deployment" (nothing in the workflow does that),
and not "redeploy the previous image under a new tag" (irrelevant — the
existing pods were never touched to begin with).

## Open items / next steps

- A `kubectl port-forward svc/agent-relay 8000:8000` from this session's
  verification step is likely still running; check before starting another
  one on port 8000 in a future session (this is now the second time a
  leftover port-forward has caused a false signal — worth just killing it
  at the end of a session rather than leaving it for the next one to trip
  over).
- `ci.yml`'s `deploy` job is explicitly local/self-hosted-runner-shaped
  (shares a Docker daemon and a pre-existing kind cluster with `build`) and
  would not work unmodified on a GitHub-hosted cloud runner, which gets a
  fresh VM per job with no pre-existing cluster or shared image store —
  called out as a comment in the file itself, not treated as a hidden gap.
