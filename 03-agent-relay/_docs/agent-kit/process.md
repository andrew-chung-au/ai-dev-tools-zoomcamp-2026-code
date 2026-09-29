# Development process

How work moves from idea to done, with any AI coding tool. Project-specific values (commands, branching, summary naming) are in `AGENTS.md`; this file refers to them by their bold labels, such as **Verify**.

## Start of every session

Before picking up work, the orchestrator checks the spec:

1. **No `_docs/specs.md`:** the project is in planning. See Planning.
2. **The spec changed since the last session:** take the spec version recorded in the latest session summary and run `git log --oneline <version>..HEAD -- _docs/specs.md`. If that lists any commits, run a backlog review (see Backlog) before starting an issue. If no summary records a version yet, skip this check.
3. **Otherwise:** continue with the lifecycle.

## Planning

Planning produces or revises `_docs/specs.md`. The human may write it outside the repo, or draft it with an agent (for example in a planning mode).

- An agent helping with planning proposes spec text; the human approves it before it's written.
- No issues are created and no product code is written until the spec exists.
- Spec changes are committed on their own, with a message saying what changed.

Mid-project changes and new versions (v2) work the same way: revise the spec, then review the backlog.

## Backlog

- Tasks are GitHub issues, worked one at a time.
- **Building the backlog:** when there are no open issues and the spec has parts not yet built, the PM proposes new issues from the spec.
- **Reviewing the backlog:** when the spec has changed, the PM compares the change with existing issues and proposes new issues, edits to open issues, and open issues to close as not planned.
- The human approves the proposal before any issue is created, edited or closed.
- After grooming, every issue follows `_docs/agent-kit/templates/task-template.md`.

## Roles

Each role follows its file in `_docs/agent-kit/team/`:

- **PM** (`pm.md`) builds and reviews the backlog, and grooms an issue before anyone implements it.
- **Engineer** (`software-engineer.md`) implements one groomed issue.
- **QA** (`qa-engineer.md`) checks the result against the acceptance criteria and changes nothing.

How to run a role depends on the tool:

- **If your tool can launch subagents,** the orchestrator launches each role as a subagent, tells it to read `AGENTS.md` and then its role file, and gives it the issue number. Subagents don't always receive the project's instructions automatically, so always say this explicitly.
- **Otherwise,** run each role in a fresh session: "You are the QA engineer. Read `_docs/agent-kit/team/qa-engineer.md` and check issue #N." A fresh session is the point: the reviewer shouldn't share the context of the author.

## Orchestrator

The main session is the orchestrator. It launches the roles and passes work between them. It does not plan the backlog, groom, implement or test itself.

## Lifecycle

1. Pick the next open issue. If there are none, build the backlog (see Backlog).
2. The PM grooms it. Never skip this step.
3. The Engineer implements it, commits, and runs **Verify** following `_docs/agent-kit/procedures/verify.md`.
4. The orchestrator notes the current commit (`git rev-parse --short HEAD`), then the QA engineer checks the issue.
5. After QA, the orchestrator runs **Assert clean** and confirms HEAD hasn't moved. If either fails, QA changed something: discard QA's verdict and run QA again.
6. On FAIL, go back to step 3 with the QA comment as input.
7. On PASS, if the Engineer proposed AGENTS.md changes, show them to the human as a diff. Apply them only after approval, in their own commit.
8. Write the session summary following `_docs/agent-kit/procedures/session-summary.md`.
9. Close the issue. Only the orchestrator closes issues: after QA posts PASS, or as not planned after the human approves a backlog review.
10. The human reviews the diff and pushes (see Commits).
11. Repeat until the backlog is empty and every part of the spec is built.

## Commits and pushes

- Small, focused commits at logical milestones; messages say what changed and why.
- Staging, protected files and hooks follow the Conventions in `AGENTS.md`.
- **Only the human pushes.** Before pushing, the human reads `git diff origin/main --stat -- .`, then the full diff, and asks about any changed file outside the issue's Constraints. A clean QA report is not proof of a clean diff. The pre-push hook then runs **Verify**.

## Keeping the setup current

`_docs/agent-kit/blueprints.md` lists what the project should have and when. When the project gains a capability listed there (a test framework, e2e tests, migrations, a linter), propose the matching blueprint, following the same approval rule as other AGENTS.md changes. To check everything at once, re-run `_docs/agent-kit/setup.md` in review mode.

## Definition of done

An issue is done when:

- **Verify** passes and QA has posted PASS, so every acceptance criterion is met.
- The changes are committed.
- Docs affected by the change are updated, and any AGENTS.md change has human approval.
- The session summary is written.
- The orchestrator has closed the issue.

The human's diff review and push come after this, outside the agent's definition of done.
