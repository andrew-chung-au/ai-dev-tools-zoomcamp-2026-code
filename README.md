# AI Dev Tools Zoomcamp (2026 Cohort)

Coursework and practical projects for the **AI Dev Tools Zoomcamp** by [DataTalks.Club](https://datatalks.club/). This repository documents a specification-driven, AI-assisted development workflow spanning rapid prototyping, contract-driven architecture, containerization, end-to-end testing, observability, and automated incident response.

A major outcome of the course is the **agent kit**: a reusable, tool-agnostic process for running AI coding agents as a PM, Engineer and QA team, with verification gates and git hooks around their work. It grew out of the Module 1 team roles and was refined across the later modules.

---

## Repository Structure

```text
ai-dev-tools-zoomcamp-2026-code/
├── .githooks/                 # Repo-wide git hooks installed by the agent kit (`make hooks`)
├── .local/                    # Scratchpad, quick links, and personal workflow notes
├── 01-django-chores/          # Module 1: Household chores manager (my own app, Django)
├── 02-restaurant-waitlist/    # Module 2: Table Ready (my own full-stack app)
├── 03-agent-relay/            # Module 3: CI/CD and containerization (course-provided starter)
├── 04-order-tracker/          # Module 4: Observability and automated incident response (course-provided starter)
├── notes/                     # Markdown revision notes per module
├── submissions/               # Homework quiz submissions and course FAQ PRs
├── README.md
└── LICENSE
```

---

## The Agent Kit

A single folder, `_docs/agent-kit/`, copied into each project that uses it. It works with any AI coding tool that reads `AGENTS.md` and runs shell commands. It's currently set up and used in `04-order-tracker/`. Full documentation: [`04-order-tracker/_docs/agent-kit/README.md`](04-order-tracker/_docs/agent-kit/README.md).

**The problem it addresses.** AI coding agents work fast, but left alone they can report their own work as done, weaken a test to get a green run, change files outside the task, or rewrite their own instructions. The kit makes the process explicit: who does what, what counts as done, what needs a human, and what gets checked automatically.

**What it provides:**
* **An agent team.** Work is organized as GitHub issues, handled by three roles defined in plain Markdown (`team/`):
  * a **PM** grooms each issue into checkable acceptance criteria;
  * an **Engineer** implements it;
  * a **QA** agent verifies it separately from the Engineer and posts a PASS or FAIL verdict against each criterion. `make assert-clean` then confirms QA changed nothing, or its verdict is discarded.

  The main session only orchestrates, and brings every decision that needs a human to one point after QA passes.
* **A verification gate.** `make verify` runs the tests, a whitespace check, and a scan for weakened tests. Deleted test files and new skip or focus markers fail the gate. Removed assertions and changed fixtures are flagged, and each one needs a stated reason. Nothing is done until it passes.
* **Git hooks as a safety net.** Installed once at the repo root, they act only on folders that have adopted the kit:
  * **Pre-commit** blocks `.env` files, keys, local databases and other generated files. It also blocks changes to protected files (the spec, the agent instructions, the kit itself) unless a human has approved them.
  * **Pre-push** runs the verification gate.
  * **Git LFS** keeps working through pass-through hooks.
* **Blueprints and a setup procedure.** An agent reviews a project folder, maps what already exists, and proposes the project's `AGENTS.md`, Makefile targets and settings from templates, each applied only when it becomes relevant. Review mode reports drift as the project grows.
* **Human control points.** A human approves the spec, the backlog and any change to the agent instructions, reads every diff, and does every push. When an agent needs approval, it explains what it wants to do and why, the exact command, the risk and how to undo it, the alternatives, and its recommendation. Destructive steps, such as deleting data, are done by the human.

**Controls are layered, and their limits are stated plainly.**
* **Instructions come first:** every tool reads `AGENTS.md`.
* **Git hooks catch mistakes, but can be bypassed.** Any agent can skip them with `--no-verify`, which the rules forbid.
* **Human review is the real control.**
* **CI (continuous integration) is the only layer an agent can't bypass.** It's available as an optional template.

The kit's README documents what each layer does and doesn't guarantee.

**Results on Order Tracker.** Module 4 questions 2 to 6 were each built as GitHub issues, run through PM grooming, implementation, QA and human review:
* **End-to-end automated fix.** In the final run, a real Grafana alert reached the responder by webhook and started a headless coding agent as on-call engineer. Working from the saved traces and logs, the agent traced the failure to a month-end date bug, fixed it, added a regression test, passed the verification gate and committed the fix, all in one 86-second run. The fix then waited for human review before being pushed.
* **QA found real defects before any human review.** On the incident responder, it failed two criteria: the on-call agent's permission rules blocked the HTTP requests it needed, and the queue cap dropped an alert it should have queued. Both were fixed and re-checked.
* **QA reported risks no criterion covered.** For example, a Makefile expansion that could run arbitrary commands through the on-call agent's request wrapper. Each became a follow-up issue instead of passing unnoticed.
* **The controls held under pressure.** When the coding tool's safety checks blocked a QA run's attempt to delete a Docker volume, the run was stopped and checked (nothing had been deleted), then discarded and repeated, with the destructive step done by the human.
* **Protected changes needed a human.** Changes to the agent instructions, the spec, and the on-call agent's task and URL check were committed only after explicit human approval.

**How it evolved:** Module 1 role files → a Claude Code–specific version with hooks and subagents (in the separate Table Ready repository) → this tool-agnostic kit, now at version 1.7. Each version fixed problems found in real use, recorded in session summaries and issue comments:

| Problem found in use | Change to the kit |
|---|---|
| The repo's existing Git LFS hooks blocked installation | The kit's hooks call Git LFS themselves, so both work |
| Agents' shell habits (scratch files in `/tmp`, complex or chained commands, editing files from the shell) caused constant approval prompts | Shared conventions with simpler command forms and their replacements, a project `.scratch/` folder, and `make` targets |
| One role overwrote another role's issue comment | Comments are never edited, and each is labelled with its role |
| Agents started servers and stopped processes by hand | Start and stop targets that only stop the process they started |
| Decisions interrupted the human throughout an issue | One decision point after QA passes, each item with a recommendation |
| A usage limit cut off an agent mid-task | A procedure for checking what an interrupted role left behind before relaunching it |
| Approval prompts didn't say what an agent was doing, why, or what the alternatives were | Structured approval requests and decision questions; subagents route them through the orchestrator, because the human can't see a subagent's messages |
| A QA agent tried to delete data that the clean-tree check can't see | Agents never delete data they didn't create; destructive checks are planned at grooming and done by the human; a blocked agent stops and reports |
| The same environment fix had to be worked out twice | A "known environment issues" runbook entry (symptom, check, fix, undo) that later requests point to |
| Projects already using the kit needed upgrading | A documented upgrade path, and a review mode that reports drift |

---

## Projects Overview

Each module uses a different app. The Module 1 and 2 apps are my own, specified by me and built with AI coding tools, mostly Claude Code. Modules 3 and 4 start from apps provided by the course, which I extended: CI/CD in Module 3, and observability and automated incident response in Module 4.

### 1. Household Chores Manager (`01-django-chores/`)
My own app, built during Module 1 to establish the AI-native developer loop:
* **Workflow:** Conversational spec generation, task decomposition into a structured backlog, and execution via coding agents.
* **Stack:** Python, Django, SQLite, managed with `uv`.

### 2. Table Ready — Restaurant Waitlist Manager (`02-restaurant-waitlist/`)
My own full-stack app for Module 2. The frontend was generated with Lovable, and the rest was built with Claude Code. I kept extending it after the module, before Module 3 moved to a course-provided app:
* **Architecture:** Full-stack web application featuring an OpenAPI contract as the single source of truth between frontend and backend.
* **Frontend:** React, TypeScript, TanStack Start (configured for static SPA export), Tailwind CSS.
* **Backend:** Python 3.12+ managed via `uv`, FastAPI, SQLAlchemy ORM.
* **Persistence:** Database-agnostic layer supporting local SQLite development and PostgreSQL in containerized environments.
* **Production Packaging:** Multi-stage `Dockerfile` compiling the SPA frontend and serving static assets directly via FastAPI from a single production container.
* **Testing & Automation:**
  * Unit and endpoint tests via `pytest`.
  * Database integration tests against a live `postgres:16-alpine` service managed with Docker Compose.
  * Multi-role end-to-end (E2E) browser testing using Playwright (simulating simultaneous staff and guest sessions).

### 3. Agent Relay (`03-agent-relay/`)
A course-provided starter for Module 3, which I extended with CI/CD and containerization:
* **Architecture:** Task-claiming messaging system where agents poll and claim work through an HTTP API without external message brokers.
* **Focus:** CI/CD, local containerization, PostgreSQL migration, and deployment to a local Kubernetes cluster using `kind` (Kubernetes in Docker).

### 4. Order Tracker (`04-order-tracker/`)
A course-provided starter for Module 4, which I extended with observability and automated incident response, entirely through the agent kit's issue workflow. All six questions are complete, ending with an alert-to-fix run in which the on-call agent diagnosed and fixed a real bug on its own.
* **Observability:** OpenTelemetry metrics, logs and traces exported over OTLP (the OpenTelemetry protocol) to a Collector. From there, metrics go to Prometheus, logs to Loki and traces to Tempo, with Grafana data sources and a dashboard provisioned from files. Logs link to their traces.
* **Alerting:** A provisioned Grafana alert on 5xx responses from the order lookup endpoint, delivered to the responder through a provisioned webhook contact point with a bearer token.
* **Automated incident response:** A responder service receives Grafana webhook alerts, saves a bounded, read-only evidence packet (logs and traces), and launches a headless coding agent as on-call engineer. The agent works under the same `AGENTS.md` rules and verification gate as the rest of the team, with a restricted tool list: no push, no web access, and HTTP requests only through a `make probe` wrapper that accepts localhost URLs. The README states plainly that these limits keep an honest agent on track but aren't a sandbox.

---

## Tech Stack & Tooling

| Domain | Tools & Technologies |
|---|---|
| **AI Assistants & Agents** | Claude Code, ChatGPT (Dictation/Spec Scoping), Lovable |
| **Agent Steering** | `AGENTS.md`, `CLAUDE.md`, the agent kit (role files, blueprints, verification gate, git hooks), spec-driven context engineering |
| **Languages & Runtimes** | Python 3.12+ (`uv`), TypeScript, Node.js / Bun |
| **Frameworks & Libraries** | FastAPI, Django, React, SQLAlchemy, Pydantic |
| **Databases** | SQLite (development), PostgreSQL 16 (containers & production) |
| **Testing** | `pytest`, `pytest-anyio`, Playwright (multi-session E2E) |
| **Observability** | OpenTelemetry, OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana |
| **DevOps & Containers** | Docker (multi-stage builds), Docker Compose, `kind` (Kubernetes), Make, Git hooks (Bash), GitHub Issues and the GitHub CLI |

---

## Quickstart Guide

### Using the agent kit in a project folder

```bash
git config core.hooksPath   # should print .githooks; if not, run `make hooks` in an adopted project
cd 04-order-tracker
make help                   # lists the project's targets, including verify and assert-clean
make verify                 # the verification gate
```

To adopt the kit in another folder, copy `_docs/agent-kit/` into it and ask your AI coding tool: "Set up this project using `_docs/agent-kit/setup.md`." Full instructions are in `04-order-tracker/_docs/agent-kit/README.md`.

### Table Ready (`02-restaurant-waitlist/`)

#### 1. Local Development (Separate Services)
```bash
cd 02-restaurant-waitlist

# Run backend (port 8091)
make run

# Run frontend (port 8080)
cd frontend && bun run dev
```

#### 2. Run with Docker Compose (Full Stack + PostgreSQL)
```bash
cd 02-restaurant-waitlist
docker compose up --build
```
* Access the unified application at `http://localhost:8091`.
* API documentation is available at `http://localhost:8091/docs`.

#### 3. Running the Test Suites
```bash
cd 02-restaurant-waitlist

# Unit and API tests
uv run pytest

# Integration tests (requires Docker Compose stack)
uv run pytest tests/integration -m integration

# Playwright E2E tests (two-session staff/guest flow)
make e2e
```

### Order Tracker (`04-order-tracker/`)

```bash
cd 04-order-tracker
make run    # app plus the observability stack; waits until healthy
make stop   # stops the stack, keeping data volumes
```
Ports and the local Grafana login are in `04-order-tracker/README.md`.

---

## Core Engineering Principles Applied

* **Context Engineering:** Centralizing project rules, tool conventions (`uv`, `bun`), and testing standards inside `AGENTS.md` to prevent agent regression and maintain reproducible sessions.
* **Verification Over Trust:** Agents' work counts as done only when the gates have run and been observed. QA runs separately from the Engineer and must leave the code unchanged, weakened tests are caught by the gate, and a human reads every diff before pushing.
* **Humans Authorize, Agents Execute:** Specs, backlogs and agent instructions change only with human approval. Enforcement is layered (instructions, git hooks, human review, optional CI), with each layer's limits documented.
* **Improve the Process from Evidence:** Friction and failures in real agent runs are recorded, then fixed in the next version of the agent kit rather than worked around each time.
* **Contract-Driven Development:** Defining `openapi.yaml` before backend implementation to decouple frontend design from API implementation.
* **Database Agnosticism:** Leveraging SQLAlchemy ORM models and environment-injected `DATABASE_URL` configurations to transition seamlessly between local SQLite and containerized PostgreSQL.
* **Single-Container Production Model:** Converting SSR frameworks to static Single Page Applications (SPA), allowing a Python/FastAPI container to serve frontend static bundles without needing a separate Node runtime in production.

---

## Attribution

* The `03-agent-relay` directory contains a starter template provided by Alexey Grigorev and DataTalks.Club for Module 3 local Kubernetes and containerization exercises ([alexeygrigorev/agent-relay](https://github.com/alexeygrigorev/agent-relay)).
* The `04-order-tracker` directory is based on the Module 4 Order Tracker starter provided by DataTalks.Club. <!-- TODO: add the starter repository link -->
* Course materials and curriculum reference: [DataTalksClub/ai-dev-tools-zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp).