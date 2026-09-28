# Master Revision Notes: DevOps and Observability for an AI-Built App (Module 4)

## 1. The Core Problem: What Module 4 tackles
* **Starting Point**: The Interview Canvas / System Design Canvas app (React frontend → FastAPI backend → Postgres) is containerized, tested (integration + end-to-end), deployed to AWS via CloudFormation, and auto-deployed by GitHub Actions on every push to `main`.
* **Push-to-Live Is Risky**: Auto-deploying every push straight to users is fine early on. Once real users exist, you need a chance to catch regressions before they reach them.
* **Rebuilding on Promotion Is Unsafe**: If the image is rebuilt when promoting to production, dependencies or base images may have changed, so prod doesn't run exactly what was tested in dev.
* **Bugs Will Still Escape**: Two environments reduce accidents but don't eliminate them. You need to *detect* failures quickly and *understand* them.
* **Nobody Watches Dashboards 24/7**: Detection has to be automatic (alerts), and alerts need someone (or something) to respond (on-call).
* **Goal of the Module**: Make the existing deployment production-ready: environments, controlled promotion, telemetry, dashboards, alerts, and an AI on-call responder.

## 2. The End-to-End Workflow Pipeline (Module 4 Focus)
1. **Split Environments**: Reuse the infrastructure-as-code to create an independent **prod** copy; the existing stack becomes **dev**. Expect small differences (e.g., machine size), but most resources stay identical.
2. **Manual Promotion Workflow**: Dev deploys on every push; prod only via a manually triggered GitHub Actions workflow (confirmation checkbox + optional release tag).
3. **Build Once, Deploy Many**: Split the old "deploy" stage into:
   * **Build**: build the Docker image, tag it, push to a container registry (Amazon ECR).
   * **Deploy**: pull the tagged image from the registry and run it on dev.
   * **Prod Release**: take the tag currently running in dev and pull that *same* image into prod.
   * Tag format: `YYYYMMDD-HHMMSS-shortsha` (e.g., `20260818-163457-83242da`).
4. **Instrument the Backend**: Add OpenTelemetry to FastAPI, attaching **service name**, **environment**, and **deployed version** to all telemetry.
5. **Add a Collector + Storage**: Create `observability/` as a *separate* Docker Compose project containing the OTel Collector, Prometheus, Loki, Tempo, and Grafana.
6. **Define App Metrics + Dashboard**: Track product-specific metrics and build a Grafana panel filterable by environment and version. Verify locally: create a room, add an element, confirm it shows up in Grafana.
7. **Deploy the Observability Stack**: Deploy it separately from the app stack and connect *both* dev and prod to it. Repeat the local test against the deployed Grafana.
8. **Alerting**: Add an actionable alert for repeated canvas component-creation failures.
9. **AI On-Call Engineer**: Add `on-call-engineer/` with a script that polls the alert API every minute and hands firing alerts to a headless coding agent.
10. **Test the Loop with a Deliberate Bug**: Have an agent introduce a realistic, reproducible bug that the existing tests *don't* catch, then confirm the alert fires and the on-call agent responds.
11. **Clean Up**: Delete the CloudFormation stacks and independently verify nothing is still running (AWS console or a second agent scanning the account).

## 3. Engineering Concepts & The "Why"
* **Dev vs Prod Environments**:
  * *Dev*: internal, always runs the latest code, auto-deployed on push. Where you check things work.
  * *Prod*: what users see. Changes arrive deliberately, with more control.
* **Deploy vs Promote**: Deploying puts a new build somewhere; promoting moves an *already tested* build forward. Promotion should never involve a new build.
* **Build/Deploy Separation (Immutable Artifacts)**:
  * *Anti-pattern*: building the image on the EC2 host during deploy.
  * *Why it's bad*: build and deploy are two jobs; a failed build should stop deployment before it starts. Rebuilding for prod means prod may differ from what was tested.
  * *Fix*: build once, store in a registry, deploy the same artifact everywhere.
* **Traceable Image Tags**: The timestamp makes tags sortable; the short commit SHA links a running image back to exact source code. Combined with the "deployed version" telemetry attribute, you can tie an incident to a specific release.
* **Observability**: Collecting enough information about an application to understand its behavior and quickly find problems when something breaks.
  * *Baseline*: CPU, memory utilization, requests per second (RPS). Rising CPU/memory with falling RPS is a warning sign.
  * *Limitation*: baseline metrics say *that* something is wrong, not *why*. That requires richer telemetry.
* **The Three Kinds of Telemetry**:
  * **Metrics**: concrete numbers over time (RPS, latency, error counts).
  * **Logs**: timestamped records of individual events (an error message, a failed DB query). Provide detail.
  * **Traces**: the full path of one request through the system, broken into steps called **spans**.
* **OpenTelemetry (OTel)**: The industry standard for producing telemetry. **OTLP** is the protocol apps use to send it.
* **Instrumentation**: Adding telemetry collection to an app. **Auto-instrumentation** covers popular libraries like FastAPI without modifying their code; often only a few lines of setup.
* **OTel Collector**: Sits between the app and storage backends. The app just exports OTLP; the collector routes metrics, logs, and traces to the right systems, so backends can change without touching app code.
* **Application-Specific Metrics**: Infrastructure metrics aren't enough; measure what matters for *this* product.
  * *Current-value metrics* (e.g., active participants) vs *event counts per interval* (e.g., rooms created or errors in the last 5 minutes).
  * *Examples for the canvas*: total rooms, active rooms/participants, canvas elements across the app, change propagation delay (time for my edit to appear on your screen), error counts.
  * *Implemented*: rooms created, active participants, canvas elements created, component-creation failures, all labelled with environment and version.
* **Actionable Alerts**:
  * Threshold **and** duration should reflect real user impact (avoid firing on a single blip).
  * Alert payload should include service, environment, deployed version, owner, and dashboard URL, so the responder can act immediately.
* **On-Call**: The engineer who receives an alert, figures out what's happening, and stops the problem fast. In real setups, an AI on-call agent must also decide whether to **escalate** to a human (not implemented in the course).
* **Test Your Safety Net**: Deliberately inject a bug that passes existing tests to prove detection → alert → response actually works end to end.
* **Security Caveat**: The course exposes Grafana and friends publicly for simplicity. In practice: private networks, restricted network access, and authentication for observability tools and databases.

## 4. The Multi-Role Pipeline in Practice
* **The Release Owner**:
  * *Action*: Manually triggers promotion of a tested dev release to prod.
  * *Why*: A human gate between "works internally" and "users see it".
* **The Build & CI Engineer**:
  * *Action*: Builds, tags (`YYYYMMDD-HHMMSS-shortsha`), and pushes images to ECR; deploys the tag to dev.
  * *Why*: One immutable artifact flows through every environment.
* **The Infrastructure Engineer**:
  * *Action*: Duplicates the IaC into an independent prod stack; deploys the observability stack separately from the app stack.
  * *Why*: Environments stay consistent, and observability survives app-stack changes.
* **The Observability Engineer**:
  * *Action*: Instruments the backend, runs the collector, defines app metrics, builds dashboards filterable by env/version.
  * *Why*: Fast diagnosis, and the ability to isolate a problem to one environment or release.
* **The Alerting Engineer (SRE)**:
  * *Action*: Writes alerts with impact-based thresholds/durations and rich context.
  * *Why*: Alerts that are both trustworthy and immediately actionable.
* **The AI On-Call Agent**:
  * *Action*: On alert, investigates root cause, reads the code, reproduces the failure. If it's a real bug: smallest possible fix, run backend tests, commit with a clear message. If it's a false positive: explain why and change nothing.
  * *Why*: The narrow mandate (minimal fix, tests must pass, no edits on false positives) keeps an autonomous agent from making sweeping or unjustified changes, the same guardrail idea as the Module 1 QA/Engineer role rules.
* **The Chaos / Bug-Injection Agent**:
  * *Action*: Introduces a realistic, reproducible failure in component creation that slips past existing tests.
  * *Why*: Validates the whole detection and response chain.

## 5. Background Context: Tooling (Module 4)
* **Cloud & IaC**: AWS, CloudFormation, EC2. Principles are tool-agnostic.
* **CI/CD**: GitHub Actions (auto workflow for dev, manual workflow for prod promotion).
* **Container Registry**: Amazon ECR; Docker Hub or another registry outside AWS.
* **Telemetry**: OpenTelemetry SDK + FastAPI auto-instrumentation, exported over OTLP.
* **Self-Hosted Observability Stack**:
  * OTel Collector: receives and routes telemetry
  * Prometheus: metrics
  * Loki: logs
  * Tempo: traces
  * Grafana: dashboards and alerting UI
* **Managed Alternatives** (skip self-hosting): CloudWatch, Grafana Cloud, Datadog, Sentry.
* **Tool Discovery Tip**: The author asked for Prometheus + Grafana and the agent suggested adding Loki and Tempo. Ask your assistant for options and pick what fits.
* **Headless Coding Agents**: Codex or Claude running non-interactively for on-call sessions.

## 6. Target Architecture & Deliverables (Module 4)
* **Deployment Flow**:
  * Push to `main` → CI tests → **Build** (image → ECR with tag) → **Deploy** tag to dev
  * Manual trigger → **Prod Release** pulls the dev tag → prod
* **Telemetry Flow**:
  * Dev + prod apps → OTLP → OTel Collector → Prometheus / Loki / Tempo → Grafana dashboards → alerts
* **Repository Additions**:
  * GitHub Actions workflows: CI (test, build, push, deploy to dev) + manual prod promotion
  * Infrastructure templates for independent dev and prod stacks
  * `observability/`: separate Compose project for collector, Prometheus, Loki, Tempo, Grafana
  * `on-call-engineer/`: alert poller script + agent prompt
* **Backend Changes**: OTel instrumentation with service/environment/version attributes; custom app metrics.
* **Dashboards & Alerts**: Grafana panel for app metrics (env/version filters); alert on repeated component-creation failures.
* **Course PoC vs Production On-Call Architecture**:
  * *Course*: a script polls the alert API every minute and launches a local headless agent.
  * *Production*: Alert → SNS (or similar) → Lambda → isolated container job → headless agent with access to code, logs, metrics → session log saved → compute terminated.

## 7. Clean Up & Beyond Module 4 (Production Gaps)
* **Clean Up**: Delete CloudFormation stacks after the module and verify manually; forgotten resources mean a bigger bill.
* **Replace the EC2 Shell Script**: Use a container management system (ECS or alternative) instead of running scripts on the instance.
* **Rollback**: Make it easy to revert a bad prod promotion (the tagged images in the registry make this feasible).
* **Managed Database**: Prefer a managed DB service over self-hosting.
* **Backups**: Back up regularly, keep backups *outside* the IaC stack, keep multiple independent copies, and test that restores actually work.
* **Network Security**: Internal services on private subnets inside a VPC with restricted access.
* **Scaling**: Learn load balancing and scaling for high traffic; container orchestration makes this easier.
* **Security Audits**: Have strong models (the author suggests using more than one) audit the code for vulnerabilities, repeatedly.

## 8. Connecting to Earlier Modules
* **Module 1 (Roles & Rules)**: The on-call agent is another specialized role with explicit rules, like the PM/Engineer/QA agents. Its "don't change code on a false positive" rule mirrors QA's "report, don't fix".
* **Module 2 (Config via Env Vars)**: Environment-driven, database-agnostic configuration is what makes dev/prod copies and environment labels on telemetry straightforward.
* **Module 3 (Containers & CI/CD)**: Module 3 containerized the app and set up push-to-deploy. Module 4 refines it: separate build from deploy, version-tag images, and add a controlled path to prod. The basic "logs + metrics endpoint" idea from Module 3 grows into full OTel telemetry with metrics, logs, and traces.