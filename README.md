# AI Dev Tools Zoomcamp (2026 Cohort)

Coursework and practical projects for the **AI Dev Tools Zoomcamp** by [DataTalks.Club](https://datatalks.club/). This repository documents a specification-driven, AI-assisted development workflow spanning rapid prototyping, contract-driven architecture, containerization, end-to-end testing, observability, and automated incident response.

A major outcome of the course is the **agent kit**: a reusable, tool-agnostic process for running AI coding agents as a PM, Engineer and QA team, with verification gates and git hooks around their work. It grew out of the Module 1 team roles and was refined across the later modules.

---

## Repository Structure

```text
ai-dev-tools-zoomcamp-2026-code/
├── .githooks/                 # Repo-wide git hooks installed by the agent kit (`make hooks`)
├── .local/                    # Scratchpad, quick links, and personal workflow notes
├── 01-django-chores/          # Module 1: Household chores manager (Django)
├── 02-restaurant-waitlist/    # Modules 2–3: Table Ready (core full-stack project)
├── 03-agent-relay/            # Module 3: Local Kubernetes & containerization starter
├── 04-order-tracker/          # Module 4: Observability and automated incident response
├── notes/                     # Markdown revision notes per module
├── submissions/               # Homework quiz submissions and course FAQ PRs
├── README.md
└── LICENSE
```

---

## The Agent Kit

A single folder, `_docs/agent-kit/`, copied into each project that uses it. It works with any AI coding tool that reads `AGENTS.md` and runs shell commands. It's currently setup and used in `04-order-tracker/`.

**What it provides:**
* **An agent team.** Work is organized as GitHub issues, handled by three roles defined in plain Markdown (`team/`):
  * a **PM** grooms each issue into checkable acceptance criteria;
  * an **Engineer** implements it;
  * a **QA** agent verifies it in a fresh session and posts a PASS or FAIL verdict against each criterion.

  The main session only orchestrates.
* **A verification gate.** `make verify` runs the tests, a whitespace check, and a scan for weakened tests: deleted test files, new skip or focus markers, and removed assertions. Nothing is done until it passes.
* **Git hooks as a safety net.** Installed once at the repo root, they act only on folders that have adopted the kit:
  * **Pre-commit** blocks secrets, local databases and changes to protected files (the spec and the agent instructions) unless a human has approved them.
  * **Pre-push** runs the verification gate.
  * **Git LFS** keeps working through pass-through hooks.
* **Blueprints and a setup procedure.** An agent reviews a project folder, maps what already exists, and proposes the project's `AGENTS.md`, Makefile targets and settings from templates, each applied only when it becomes relevant.
* **Human control points.** A human approves the spec, the backlog and any change to the agent instructions, reads every diff, and does every push.

**Controls are layered, and their limits are stated plainly.**
* **Instructions come first:** every tool reads `AGENTS.md`.
* **Git hooks catch mistakes, but can be bypassed.** Any agent can skip them with `--no-verify`, which the rules forbid.
* **Human review is the real control.**
* **CI (continuous integration) is the only layer an agent can't bypass.** It's available as an optional template.

The kit's README documents what each layer does and doesn't guarantee.

**How it evolved:** Module 1 role files → a Claude Code–specific version with hooks and subagents (in the separate Table Ready repository) → this tool-agnostic kit. Each version since has fixed problems found in real use, recorded in session summaries and issue comments.

---

## Projects Overview

### 1. Table Ready — Restaurant Waitlist Manager (`02-restaurant-waitlist/`)
The primary capstone project, developed across Modules 2 and 3:
* **Architecture:** Full-stack web application featuring an OpenAPI contract as the single source of truth between frontend and backend.
* **Frontend:** React, TypeScript, TanStack Start (configured for static SPA export), Tailwind CSS.
* **Backend:** Python 3.12+ managed via `uv`, FastAPI, SQLAlchemy ORM.
* **Persistence:** Database-agnostic layer supporting local SQLite development and PostgreSQL in containerized environments.
* **Production Packaging:** Multi-stage `Dockerfile` compiling the SPA frontend and serving static assets directly via FastAPI from a single production container.
* **Testing & Automation:**
  * Unit and endpoint tests via `pytest`.
  * Database integration tests against a live `postgres:16-alpine` service managed with Docker Compose.
  * Multi-role end-to-end (E2E) browser testing using Playwright (simulating simultaneous staff and guest sessions).

### 2. Household Chores Manager (`01-django-chores/`)
Built during Module 1 to establish the AI-native developer loop:
* **Workflow:** Conversational spec generation, task decomposition into a structured backlog, and execution via coding agents.
* **Stack:** Python, Django, SQLite, managed with `uv`.

### 3. Agent Relay (`03-agent-relay/`)
The standardized exercise for Module 3 homework:
* **Architecture:** Task-claiming messaging system where agents poll and claim work through an HTTP API without external message brokers.
* **Focus:** Local containerization, PostgreSQL migration, and deployment to a local Kubernetes cluster using `kind` (Kubernetes in Docker).

### 4. Order Tracker (`04-order-tracker/`)
The Module 4 homework, built entirely through the agent kit's issue workflow. In progress:
* **Observability:** OpenTelemetry metrics, logs and traces exported over OTLP (the OpenTelemetry protocol) to a Collector. From there, metrics go to Prometheus, logs to Loki and traces to Tempo, with Grafana data sources and a dashboard provisioned from files. Logs link to their traces.
* **Alerting:** A provisioned Grafana alert on 5xx responses from the order lookup endpoint.
* **Automated incident response:** A responder service receives Grafana webhook alerts, saves a bounded, read-only evidence packet (logs and traces), and launches a headless coding agent as on-call engineer. The agent works under the same `AGENTS.md` rules and verification gate as the rest of the team.

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
| **DevOps & Containers** | Docker (multi-stage builds), Docker Compose, `kind` (Kubernetes), Make |

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

### Core Project: Table Ready (`02-restaurant-waitlist/`)

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
* **Verification Over Trust:** Agents' work counts as done only when the gates have run and been observed. QA runs in a fresh session, weakened tests fail the gate, and a human reads every diff before pushing.
* **Humans Authorize, Agents Execute:** Specs, backlogs and agent instructions change only with human approval. Enforcement is layered (instructions, git hooks, human review, optional CI), with each layer's limits documented.
* **Contract-Driven Development:** Defining `openapi.yaml` before backend implementation to decouple frontend design from API implementation.
* **Database Agnosticism:** Leveraging SQLAlchemy ORM models and environment-injected `DATABASE_URL` configurations to transition seamlessly between local SQLite and containerized PostgreSQL.
* **Single-Container Production Model:** Converting SSR frameworks to static Single Page Applications (SPA), allowing a Python/FastAPI container to serve frontend static bundles without needing a separate Node runtime in production.

---

## Attribution

* The `03-agent-relay` directory contains a starter template provided by Alexey Grigorev and DataTalks.Club for Module 3 local Kubernetes and containerization exercises ([alexeygrigorev/agent-relay](https://github.com/alexeygrigorev/agent-relay)).
* The `04-order-tracker` directory is based on the Module 4 Order Tracker starter provided by DataTalks.Club. <!-- TODO: add the starter repository link -->
* Course materials and curriculum reference: [DataTalksClub/ai-dev-tools-zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp).