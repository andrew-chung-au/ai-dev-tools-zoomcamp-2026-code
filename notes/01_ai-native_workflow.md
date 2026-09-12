# Master Revision Notes: AI-Native Development (Module 1)

## 1. The Core Problem: Why change how we develop?
* **The AI Bottleneck**: Agents write code faster than developers can read it. We no longer spend our time typing; we spend it specifying what we want and checking the results.
* **The Danger of Assumptions**: If a task is vague, an AI agent fills the gaps with its own assumptions. A strong agent doesn't just fail; it builds an entire, perfectly functioning application that is entirely the *wrong* thing (e.g., building a command-line tool when a web-based retrospective app was needed).
* **The Illusion of Progress**: You see a working app with perfect documentation and passing tests, only to realize you can't use a single line of it for your actual business need.
* **Wasted Resources**: The agent spends time and compute tokens generating code, storage logic, and formatting files for an interface the developer never wanted.
* **The Unsalvageable Pivot**: Asking an AI to pivot a completed command-line tracking tool into a real-time web voting app is nearly impossible; you essentially have to throw the entire thing away and start over.

## 2. The End-to-End Workflow Pipeline
To prevent the AI bottleneck and wrong assumptions, the workflow outlines a strict 6-step project lifecycle:
1. **Chat Brainstorming**: Start in a chat assistant (e.g., ChatGPT in dictation mode) using a constrained prompt instructing the AI to ask *one question at a time*. Export the final scoping session into a `plan.md` file.
2. **Repository Bootstrap**: Initialize a Git repository (`git init`), place `plan.md` inside `_docs/plan.md`, and commit it.
3. **Tech Stack Selection**: Ask the coding agent to read `plan.md`, propose multiple tech stack options with tradeoffs (without writing code yet), and select a stack you can review (e.g., Django).
4. **Backlog Generation**: Ask the agent to decompose specs into `_docs/tasks.md` using a strict template (Goal and Description). Review, adjust for MVP scope, and push them to GitHub Issues using the `gh` CLI tool.
5. **Context Engineering Setup**: Establish global rules in `AGENTS.md` (and a `@AGENTS.md` pointer in `CLAUDE.md`), along with process and domain docs in `_docs/`.
6. **Execution & Orchestration**: Implement via simple prompts, loops (`/goal`), or a graph orchestrator.

## 3. Engineering Concepts & The "Why"
* **Spec-Driven Development**: Defining exact scope and specifications before writing any code to prevent agent guessing and ensure alignment with the vision.
* **Context Engineering (Setup)**: Creating files in the project root (`AGENTS.md`) to give agents durable project knowledge across sessions. **[Claude-Specific Note: Claude Code reads `CLAUDE.md` by default, which can contain a single line `@AGENTS.md` to keep configurations tool-agnostic.]**
* **Context Engineering (Rules & Notation)**: Split rules to keep prompt contexts short. Short, global rules (e.g., dependency restrictions) live directly under a "Rules" heading in `AGENTS.md`. Larger rule sets (testing guidelines, design systems) live in separate files inside `_docs/` and are linked via plain-text sentences in bullet points (e.g., `- Before writing tests, read _docs/testing-guidelines.md`).
* **Loop Engineering**: A command (like `/goal groom all issues`) typed directly into the agent's harness (CLI) during an active session. It gives the agent a checkable stop condition, forcing it to execute a batch of repetitive tasks automatically without manual hand-holding.
* **Graph Engineering**: Automating the handoff of work via an orchestrator by defining a workflow graph. Specialized agents act as **nodes**, and rules describing how work moves between them act as **edges**. It mimics a real-world team workflow autonomously, though it uses significantly more time and tokens than simple loops.

## 4. The Multi-Agent Team: Roles & Rationale
* **The Product Manager (PM) Agent**: 
    * *Action*: "Grooms" backlog tasks before implementation by turning vague issues into structured templates containing a project **Goal** (written text heading explaining what should be true when done, *not* the CLI `/goal` command), checkable **Acceptance Criteria**, **Out of Scope** items (linked to follow-up issues), and **Constraints**. Follows rules defined in `_docs/team/pm.md`.
    * *Why*: Misunderstandings are cheapest to catch in text; correcting a paragraph costs one sentence, whereas correcting code requires a rewrite.
* **The Software Engineer Agent**: 
    * *Action*: Implements one groomed task at a time strictly against the acceptance criteria, stays within constraints, writes tests, and commits regularly. Follows rules in `_docs/team/software-engineer.md`.
    * *Why*: Keeps the issue open for iterative feedback loops. Preventing the engineer from altering criteria to make faulty code pass ensures they don't move goalposts; if a criterion is impossible, they must comment on the issue instead.
* **The QA Engineer Agent**: 
    * *Action*: Checks finished work against the acceptance criteria and running code, explicitly ignoring what the implementation claims to do. Runs tests, looks for uncovered edge cases, and outputs a strict **PASS** or **FAIL** verdict via an issue comment. Follows rules in `_docs/team/qa-engineer.md`.
    * *Why*: Independent validation catches regressions. Forcing QA to only report (never fix code) prevents the agent from spiraling into an endless loop of breaking and fixing its own code.

## 5. Background Context: Tool Categories (2025–2026 Landscape)
* **Chat Applications (e.g., ChatGPT, Claude, DeepSeek)**: Best for brainstorming and scoping out initial ideas before touching code.
* **Coding Assistants / IDE Integrations (e.g., Cursor, GitHub Copilot, Windsurf, Claude Code)**: Integrated directly into the IDE or CLI to help write, refactor, and test seamlessly. Cursor leads multi-file IDE editing, while Claude Code provides a robust terminal interface.
* **Project Bootstrappers (e.g., Bolt.new, v0 by Vercel, Lovable.dev)**: Generates full projects from prompts for instant prototyping (Bolt.new for full-stack apps, v0 for React/Next.js frontend components). Often associated with rapid "vibe-coded" deployments on Vercel.
* **Agents (e.g., Devin, Anthropic Computer Use, Vellum)**: Autonomous systems designed to operate across files, use tools, and automate entire project workflows in cloud environments.