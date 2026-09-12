# Development process


This document describes how work is organised and executed for the Table Ready project in Module 2.


## Backlog and tasks


- Tasks are GitHub issues, one at a time.
- Each issue has a clear title, description, and acceptance criteria.
- Everyone involved reads the acceptance criteria:
  - before starting work, and
  - before closing the issue.


The backlog lives in the GitHub Issues tab of the repository.


## Agent team workflow


### Roles


- **PM** – grooms a task before anyone implements it, follows `_docs/team/pm.md`.
- **Engineer** – implements one groomed task, follows `_docs/team/software-engineer.md`.
- **QA** – checks the result against the acceptance criteria, follows `_docs/team/qa-engineer.md`.


### Orchestrator


The main session is the orchestrator. It launches the PM, the Engineer, and QA as subagents. It does not groom, implement, or test itself.


### Lifecycle


1. Pick the next open issue from the backlog.
2. PM grooms it.
3. Engineer implements it.
4. QA verifies it.
5. On FAIL, go back to step 3 with the QA comment as input.
6. On PASS, close the issue.
7. Repeat until the backlog is empty.


### Rules


- Do not skip step 2 (PM grooming).
- The Engineer does not close the issue.
- QA does not fix the code; QA only outputs PASS or FAIL.
- The orchestrator closes the issue only after QA outputs PASS.


## Git workflow


- Use small, focused commits that correspond to logical milestones.
- Commit regularly, not only at the end of a large change.
- Prefer descriptive commit messages that explain *what* changed and *why*.
- Do not use `git add .` or `git add -A` blindly; review paths before staging.
- Before proposing a commit, always run:
  - `git status --short`
  - `git diff --check`
  - and inspect the exact paths that would be staged.


Branching:

- For Module 2, working directly on `main` is acceptable.
- For larger, riskier changes, use a short-lived feature branch (e.g. `feat/...`) and merge via a pull request.


## Session summaries


Each main orchestrator session writes a summary file into:

```text
_session-summaries/
```

### Naming convention


Use the following pattern:

```text
_session-summaries/issue-<number>_step-<label>-<short-name>.md
```

Examples:

- `_session-summaries/issue-001_step-03b_table-management.md`
- `_session-summaries/issue-002_step-04_fastapi-in-memory.md`
- `_session-summaries/issue-003_step-05_connect-frontend.md`
- `_session-summaries/issue-004_step-06_sqlite-persistence.md`


Where:

- `<number>` is the GitHub issue number (zero-padded to three digits).
- `<label>` is the Module 2 step label (e.g. `03b`, `04`, `05`, `06`).
- `<short-name>` is a concise, hyphen-separated description of the task.


### Content expectations


Each summary should include:

- What changed in this session.
- Files created or modified.
- Any mismatches with `_docs/specs.md` or other design docs.
- Commands to validate (tests, builds, lint, OpenAPI validation, etc.).
- Any follow-up notes or decisions for the next session.


The summary is a lightweight audit trail and handover note between sessions.


## Definition of done for a task


A task (GitHub issue) is considered done when:

- All acceptance criteria are met.
- Code changes are committed and pushed.
- Relevant documentation (specs, process, README, etc.) is updated if needed.
- Session summary is written to `_session-summaries/` using the naming convention above.
- QA has verified the result and the orchestrator has closed the issue.