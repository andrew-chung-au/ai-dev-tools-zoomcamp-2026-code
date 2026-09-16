# AI Dev Tools Zoomcamp (2026 Cohort)

Coursework and practical projects for the **AI Dev Tools Zoomcamp** by [DataTalks.Club](https://datatalks.club/). This repository documents a specification-driven, AI-assisted development workflow spanning rapid prototyping, contract-driven architecture, containerization, end-to-end testing, and deployment.

---

## Repository Structure

```text
ai-dev-tools-zoomcamp-2026-code/
├── .local/                    # Scratchpad, quick links, and personal workflow notes
├── 01-django-chores/          # Module 1: Household chores manager (Django)
├── 02-restaurant-waitlist/    # Modules 2–4: Table Ready (Core full-stack project)
├── 03-agent-relay/            # Module 3: Local Kubernetes & containerization starter
├── notes/                     # Markdown revision notes per module
├── submissions/               # Homework quiz submissions and course FAQ PRs
├── README.md
└── LICENSE
```

---

## Projects Overview

### 1. Table Ready — Restaurant Waitlist Manager (`02-restaurant-waitlist/`)
The primary capstone project developed across Modules 2 and 3:
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

---

## Tech Stack & Tooling

| Domain | Tools & Technologies |
|---|---|
| **AI Assistants & Agents** | Claude Code, ChatGPT (Dictation/Spec Scoping), Lovable |
| **Agent Steering** | `AGENTS.md`, `CLAUDE.md`, Spec-driven context engineering |
| **Languages & Runtimes** | Python 3.12+ (`uv`), TypeScript, Node.js / Bun |
| **Frameworks & Libraries** | FastAPI, Django, React, SQLAlchemy, Pydantic |
| **Databases** | SQLite (development), PostgreSQL 16 (containers & production) |
| **Testing** | `pytest`, `pytest-anyio`, Playwright (multi-session E2E) |
| **DevOps & Containers** | Docker (multi-stage builds), Docker Compose, `kind` (Kubernetes) |

---

## Quickstart Guide

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

---

## Core Engineering Principles Applied

* **Context Engineering:** Centralizing project rules, tool conventions (`uv`, `bun`), and testing standards inside `AGENTS.md` to prevent agent regression and maintain reproducible sessions.
* **Contract-Driven Development:** Defining `openapi.yaml` before backend implementation to decouple frontend design from API implementation.
* **Database Agnosticism:** Leveraging SQLAlchemy ORM models and environment-injected `DATABASE_URL` configurations to transition seamlessly between local SQLite and containerized PostgreSQL.
* **Single-Container Production Model:** Converting SSR frameworks to static Single Page Applications (SPA), allowing a Python/FastAPI container to serve frontend static bundles without needing a separate Node runtime in production.

---

## Attribution

* The `03-agent-relay` directory contains a starter template provided by Alexey Grigorev and DataTalks.Club for Module 3 local Kubernetes and containerization exercises ([alexeygrigorev/agent-relay](https://github.com/alexeygrigorev/agent-relay)).
* Course materials and curriculum reference: [DataTalksClub/ai-dev-tools-zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp).