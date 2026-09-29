# Blueprints

What a project using this kit should have, when each piece applies, and how to create it for the folder it's in. Setup (`setup.md`) works through this list; so does any later review. The templates are starting points: adapt every placeholder to the project, never copy one in unchanged.

## Rules for every blueprint

- **Build on what exists.** Merge into existing files; never replace or delete them. When an existing file does the same job as a blueprint, adapt the blueprint to it, or propose moving the old one to `_docs/archive/`. The human decides.
- **Only when it applies.** Each blueprint has a trigger. If it hasn't happened yet, record the blueprint as "later", not "not needed".
- **Propose first.** Show every new file or change as a diff, and create nothing until the human approves.
- **Don't loosen a gate to make existing code pass.** If existing code fails a new check, leave that check off in `agent-kit.conf` and propose an issue to fix the code.

## Catalog

| Blueprint | Applies when | Where | Source |
|---|---|---|---|
| Project instructions | Always, at setup | `AGENTS.md` in the project folder | `templates/AGENTS.md.template` |
| Tool pointer file | The human uses a tool that doesn't read `AGENTS.md` | Project folder | See Tool pointers below |
| Kit settings | Always, at setup | `agent-kit.conf` in the project folder | `templates/agent-kit.conf.template` |
| Core make targets: `help`, `verify`, `assert-clean`, `hooks` | Always, at setup | Project `Makefile` | `templates/Makefile.mk` |
| `install`, `test` targets | The stack is known: code or a spec naming it | Project `Makefile` | `templates/Makefile.mk` |
| `run`, `test-one`, `e2e`, `migration` targets | The project has that capability | Project `Makefile` | `templates/Makefile.mk` |
| Lint and type-check gates | A linter or type checker is installed **and** existing code passes it | `lint`/`typecheck` targets, then `LINT_CMD`/`TYPECHECK_CMD` in `agent-kit.conf` | `templates/Makefile.mk` |
| Git hooks | Always, at setup; once per repository | `.githooks/` at the repo root, activated per clone by `make hooks` | `githooks/`, via `scripts/install-hooks.sh` |
| Ignore rules | Always, at setup | Project `.gitignore` | See Ignore rules below |
| Product spec | Planning; written or approved by the human | `_docs/specs.md` | Human-owned; see `process.md` |
| Session summaries folder | The first session summary | `_session-summaries/` | `procedures/session-summary.md` |
| CI backstop | The human asks for it | `.github/workflows/` at the repo root | `templates/ci-verify.yml.template` |
| Tool-native enforcement | The human wants hard enforcement in one specific tool | That tool's own config folder | Not in the kit; see README |
| Tool permission allow-list | The human's tool asks for approval on routine commands | That tool's own settings file | See Tool permissions below |

## Notes on specific blueprints

**Project instructions.** Fill the project half from what the folder actually contains; write "none" for command slots the project doesn't have yet. Keep the shared Conventions block unchanged. Carry useful content from any existing instruction file into the project half, and say where each part went. In a monorepo, include the line that limits work to this folder. Leave nested instruction files that other tools generated (for example `frontend/AGENTS.md`) in place, and check they don't contradict the root file.

**Kit settings.** Set `TEST_CMD` to the test target. Adjust `TEST_FILES` to the project's test layout and `FORBIDDEN` to its secrets and generated files. Keep `PROTECTED` covering at least `AGENTS.md`, `agent-kit.conf`, the spec and the kit folder.

**Make targets.** Wrap the project's existing commands; don't introduce new tools. Add missing targets to an existing Makefile, and never rename or replace existing ones. Add a `## description` comment after each existing target's name so `make help` lists it. When a target is added, the Commands section of `AGENTS.md` gets the matching slot.

**Lint and type-check gates.** Order matters: add the targets, fix or suppress the existing errors (as an issue, through the normal process), and only then set `LINT_CMD`/`TYPECHECK_CMD`. Setting them earlier would block every push on errors nobody introduced.

**Git hooks.** Hooks are repository-wide, so they live at the repo root even when the project is a subfolder. They only act on folders containing `agent-kit.conf`, so other folders are unaffected. Once installed, git ignores `.git/hooks`, so `install-hooks.sh` checks what's there first. Standard Git LFS hooks are replaced automatically: the kit installs LFS pass-throughs, and its `pre-push` uploads LFS objects after verify passes. Any other existing hook stops the install until the human merges it or approves `FORCE=1`. The `.githooks/` folder is committed once, and each clone or new codespace runs `make hooks` once.

**Ignore rules.** Make sure the project's `.gitignore` covers `.env` and `.env.*` (but not `.env.example`), local databases, the agents' `.scratch/` folder, and build, cache and dependency folders for the stack. The pre-commit hook catches these too, but ignore rules keep them out of `git status`.

**Session summaries.** If the project already has summaries with a naming scheme, keep that scheme and record it in the **Session summaries** setting in `AGENTS.md`.

**CI backstop.** In a monorepo, the workflow must sit in `.github/workflows/` at the repo root, with a `paths:` filter for the project folder. A `.github/` folder inside a project folder is ignored by GitHub. Fill in the stack setup steps from the project's tooling.

## Tool pointers

Many AI coding tools read `AGENTS.md` directly. For a tool that reads its own file instead, add a short pointer file so every tool gets the same instructions. Check the tool's documentation for its file name and import syntax. For example:

- **Claude Code** reads `CLAUDE.md`, which can import other files: one line, `@AGENTS.md`.
- **Other tools:** a pointer file that says "Follow the instructions in AGENTS.md", if the tool can't import files.

Create pointer files only for tools the human actually uses.

## Tool permissions

Tools that ask before running commands can usually pre-approve safe ones. Allowing the project's `make` targets and read-only git commands (`git status`, `git diff`, `git log`) removes most routine prompts, while pushes and edits to protected files still ask. Only propose this for a tool the human uses, and show the settings change for approval. For example, in Claude Code, project settings live in `.claude/settings.json` under `permissions.allow`.
