# Session 5 — kind cluster, Kubernetes manifests, and container-egress blocker

Continues [[session-04_postgres-compose-and-sandbox-networking]]. Ports the
Compose stack to Kubernetes via `kind`, since the task explicitly asked to
first assess feasibility in this sandbox before committing to it.

## Feasibility check

`kubectl` was already installed; `kind` was not — installed v0.30.0 via the
official release binary (`curl`+`chmod`+`sudo mv` into
`/usr/local/bin`). Confirmed `sudo` (passwordless) and outbound internet
both work from the host shell before proceeding.

Given session 4's finding that this sandbox's host firewall drops
container-to-container traffic on custom Docker bridge networks, the open
question was whether `kind create cluster` would hit the same wall. It
didn't: kind runs a "cluster" as a single Docker container (the node), with
pod-to-pod networking handled entirely inside that container's own
netns/CNI (kindnet) — invisible to the host's inter-container firewall
rules, which only govern traffic between *separate* Docker containers.
`kind create cluster --name agent-relay` succeeded; node reached `Ready`
with all system pods (`coredns`, `kindnet`, `kube-proxy`,
`local-path-provisioner`) `Running` shortly after.

## What changed

### `k8s/` (new directory, 6 manifests)

- `postgres-secret.yaml` — `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`
  plus a precomputed `DATABASE_URL` key (same credentials as
  `compose.yaml`'s: `agent_relay`/`agent_relay`/`agent_relay`).
- `postgres-pvc.yaml` — 1Gi `ReadWriteOnce` PVC (kind's default
  `local-path` StorageClass, `WaitForFirstConsumer` binding).
- `postgres-deployment.yaml` — `postgres:16-alpine`, PVC mounted at
  `/var/lib/postgresql/data` with `subPath: pgdata` (avoids a `lost+found`
  edge case on some volume plugins), `pg_isready` readiness + liveness
  probes, `strategy: Recreate` (RWO volume can't support a rolling update
  with two pods mounting it at once).
- `postgres-service.yaml` — ClusterIP `postgres:5432`.
- `agent-relay-deployment.yaml` — `agent-relay:local`,
  `imagePullPolicy: IfNotPresent` (critical — must never try a registry
  pull for a `kind load`-ed image), `DATABASE_URL` from the Secret,
  readiness probe `GET /ready`, liveness probe `GET /health`.
- `agent-relay-service.yaml` — ClusterIP `agent-relay:8000`.

## Two real blockers hit and worked around

1. **In-cluster image pulls are blocked.** The sandbox's egress
   restriction turned out to be broader than "container-to-container": any
   outbound network call *initiated from inside a container* is blocked,
   including the kind node's own containerd trying to `docker pull
   postgres:16-alpine` from Docker Hub (DNS to the bridge gateway timed
   out). Host-initiated Docker operations (`docker pull`, `docker build`,
   `kind load docker-image`) are unaffected since they go through the host
   daemon, not a container's own network stack. Fix: load already-cached
   images into kind via `kind load docker-image` instead of letting pods
   pull them.

2. **`kind load docker-image postgres:16-alpine` itself failed**
   (`ctr: content digest ... not found` during `ctr images import
   --all-platforms`). Root cause: this Docker Engine uses the
   containerd-backed image store, and pulled multi-platform images include
   manifest-list entries for build attestations (SBOM/provenance) whose
   *content* Docker's pull client deliberately never downloads locally —
   only their digests. `kind load`'s default `--all-platforms` import then
   fails trying to import those absent blobs. This does **not** affect
   locally *built* images (`agent-relay:local`), whose attestation content
   is fully generated during `docker build`, only pulled ones. Confirmed by
   reproducing, then working around it: `docker save postgres:16-alpine -o
   pg.tar` → `docker cp` into the kind node → `docker exec ... ctr
   --namespace=k8s.io images import --digests --snapshotter=overlayfs
   pg.tar` (omitting `--all-platforms`) succeeded immediately.

   Along the way, removed the leftover `03-agent-relay-postgres-1` Compose
   container from session 4 (it was pinning the old image, blocking
   `docker rmi`, and was already flagged there as cleanup debt) via
   `docker compose down`.

3. **Stale image, unrelated to networking:** `agent-relay:local` (built in
   session 3) predated session 4's `psycopg2-binary` addition, so the first
   `agent-relay` pod crash-looped with `ModuleNotFoundError: No module
   named 'psycopg2'`. Rebuilt the image (`docker build -t agent-relay:local
   .`), reloaded it via `kind load docker-image` (worked cleanly — locally
   built, no missing-attestation-content issue), and `kubectl rollout
   restart deployment/agent-relay`.

## Result

```
kubectl get pods
agent-relay-5f9b4f5d84-nghw7   1/1   Running
postgres-6d87468d76-82hk2      1/1   Running
```

`kubectl port-forward svc/agent-relay 8000:8000` (backgrounded), then
verified:
- `GET /` → `200`, real dashboard HTML (`<title>Agent Relay</title>`).
- `GET /health` → `{"status":"ok"}`.
- `GET /ready` → `{"status":"ready"}` (queries real Postgres-backed tables,
  same as sessions 1/4 — not just a socket check).

## Answered: which resource keeps replica count up and manages updates?

**Deployment** — via its managed ReplicaSet it maintains desired replica
count and drives rolling updates. (Service = network routing/load
balancing; ConfigMap/Secret = non-secret/secret config data; neither
manages replica count or rollouts.) Matches what's in
`k8s/agent-relay-deployment.yaml` and `k8s/postgres-deployment.yaml`.

## Open items / next steps

- The `agent-relay` kind cluster and its `kubectl port-forward` (host port
  8000) are **still running** at the end of this session. Tear down with
  `kind delete cluster --name agent-relay` when no longer needed — this
  also removes its Docker containers/network, distinct from the plain
  Compose `postgres` container removed earlier in this session (session
  4's leftover is now gone; this is a new, separate kind-managed
  container).
- `postgres-deployment.yaml`'s image is loaded manually into this
  particular kind node and isn't in any registry; a fresh `kind create
  cluster` in a future session would need the same manual
  `docker save`/`ctr import --digests` workaround repeated (or the
  sandbox's containerd-image-store attestation issue fixed upstream)
  before `postgres` could start.
- No `Ingress` or `NodePort`/`LoadBalancer` was set up — access is only via
  `kubectl port-forward`, consistent with what was actually asked for.
