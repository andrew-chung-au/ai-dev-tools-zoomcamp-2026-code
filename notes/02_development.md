# Master Revision Notes: Build and Ship an AI-Assisted Full-Stack App (Module 2)

## 1. The Core Philosophy
* **Controlled AI Workflow**: The goal is not to let an AI tool build everything unchecked, but rather to practice a controlled workflow where AI accelerates development while you verify every single step.
* **Incremental Verification**: At the end of each step, you must produce a concrete, testable component before moving on to the next layer of the stack.
* **Local End-to-End Goal**: The module concludes with a locally running application featuring a frontend, a backend, an OpenAPI contract, and data persisted in a SQLite database.

## 2. The Step-by-Step AI Development Pipeline
* **Step 1: Product Specification**: Write a small product spec containing user stories, acceptance criteria, and non-goals before generating any code. This is often done using ChatGPT in dictation mode to describe the system explicitly.
* **Step 2: Frontend Prototype (Mocked)**: Draft a frontend prototype using an AI tool like Lovable, Bolt, or Cursor. Crucially, you must prompt the AI to centralize every backend call into one service layer and create a mock implementation so the app runs without a real backend.
* **Step 3: OpenAPI Contract**: Generate an `openapi.yaml` specification directly from the frontend's API client. This defines the explicit agreement (endpoints, methods, request/response bodies, authentication) between the frontend and backend.
* **Step 4: Backend Implementation (Mocked Store)**: Ask an AI assistant to build a FastAPI backend that implements the OpenAPI spec. Start with an in-memory store and seeded data to ensure the frontend-backend connection works smoothly before worrying about database persistence.
* **Step 5: Connecting the Stack**: Switch the frontend to use the real backend client instead of the mock service. You will likely need to fix CORS errors and test the application manually using multiple browser windows to verify data flows.
* **Step 6: Database Persistence**: Replace the in-memory store with a real database like SQLite using SQLAlchemy. Ensure the setup is configured via environment variables and remains database-agnostic so it can easily be swapped for Postgres later without a code rewrite.

## 3. Key Engineering Concepts & Best Practices
* **Frontend-First Approach**: For simple solo projects, starting with the frontend allows you to quickly judge if the application solves your problem and validates your specification visually.
* **Mocking as a Safety Net**: By mocking backend calls in the frontend phase and using an in-memory store in the early backend phase, you isolate errors and verify interactions incrementally.
* **Contract-Driven Development**: Using an OpenAPI file provides a precise target for the backend agent rather than forcing it to infer requirements from frontend code. This saves compute tokens and creates a clear picture of exact backend needs.
* **Tool-Specific Context (`AGENTS.md`)**: Because AI agents may not know how to properly use newer tools like `uv` (a Python dependency manager), you must document specific commands (`uv sync`, `uv run`) explicitly inside `AGENTS.md`.
* **Makefiles for Simplicity**: Ask the AI to generate a `Makefile` to simplify complex backend startup commands (like `uv run uvicorn backend.main:app --reload`) into simple commands like `make run`.

## 4. Target Architecture & Deliverables
* **Repository Structure**: The final repository must include specific files and folders to be considered complete.
* **Documentation**: `product-spec.md` for project scope, and `docs/ai-usage-report.md` for tracking AI assistance.
* **Agent Context**: `AGENTS.md` (or equivalent) to provide baseline instructions for coding agents.
* **Application Code**: `frontend/` and `backend/` directories containing the respective system components.
* **Integration Rules**: `openapi.yaml` acting as the strict API source of truth between the frontend and backend.
* **Validation**: `tests/` containing unit and frontend tests that cover behaviors described in both the spec and the contract.

## 5. Background Context: Tooling & Examples (2025–2026)
* **Project Examples**: The course uses interactive, visual apps like a multiplayer Snake Arena or a collaborative System-Design Canvas to practice real-time integrations like WebSockets.
* **Frontend Generators**: Tools like Lovable, v0, Bolt, Claude Design, and Replit are highlighted for generating React apps from single prompts, often making strong UI design choices automatically.
* **Backend Stack**: Python, FastAPI, and `uv` (for dependency management) are utilized alongside SQLAlchemy and SQLite for lightweight local development.
* **Legacy Context (2025 Archive)**: Older archived workflows highlight utilizing Google Antigravity, GitHub Codespaces for cloud environments, and Docker Compose for containerization before deploying to platforms like Render.