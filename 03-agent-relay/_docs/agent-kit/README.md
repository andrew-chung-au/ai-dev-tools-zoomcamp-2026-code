# Agent kit

**Version 1.3 (2026-09-29).** A tool-agnostic way to run a project with AI coding agents: a PM, Engineer and QA team working from GitHub issues, a verification gate that catches weakened tests, and git hooks as a safety net. It works with any agent that can read `AGENTS.md` and run shell commands.

The kit is one folder, `_docs/agent-kit/`, copied unchanged into each project. It holds three kinds of material:

- **Shared process:** the lifecycle, team roles and procedures, used as is.
- **Blueprints:** templates plus rules for *when* each applies, for the parts that must be tailored to a project, such as `AGENTS.md`, Makefile targets, settings, hooks and CI.
- **A setup procedure:** an agent reviews the project folder, maps what's already there, and proposes how to build the kit around it.

## How the controls work

No tool-agnostic equivalent of an AI tool's own hooks or permission system exists, so the kit layers four controls:

1. **Instructions (primary).** `AGENTS.md` and the role files carry the rules: stage explicit paths only, don't push, don't edit protected files without approval, never skip hooks. Every tool reads these, so they do most of the work.
2. **Git hooks (safety net).** They run whichever tool commits or pushes:
   - **Pre-commit** refuses secrets and generated files, whitespace errors, and changes to protected files unless `HUMAN_APPROVED=1` is set.
   - **Pre-push** runs `make verify`, and blocks the push if tests fail or have been weakened.
3. **Your review (the real control).** You approve protected changes, read the diff, and do every push yourself.
4. **CI (optional backstop).** A GitHub Actions workflow running `make verify` is the only layer an agent can't bypass.

**Limits, stated plainly:**
- Any agent can skip git hooks with `--no-verify`, or set `HUMAN_APPROVED=1` itself. The instructions forbid both, which makes a breach a visible rule violation rather than an accident.
- The QA check (`make assert-clean`) detects changes after the fact; it doesn't prevent them.
- Hooks don't run for commits made on the GitHub website.
- All roles usually share one GitHub login, so GitHub can't stop one role editing another's comments or closing an issue. The rules forbid it, and GitHub's edit history shows if it happened.

## What's in the kit

```
_docs/agent-kit/
  README.md          this file (for humans)
  setup.md           setup and review procedure (for agents)
  blueprints.md      what a project needs, and when
  process.md         lifecycle: planning, backlog, roles, verification, handover
  team/              pm.md, software-engineer.md, qa-engineer.md
  procedures/        verify.md, session-summary.md
  templates/         AGENTS.md, agent-kit.conf, Makefile, task, session-summary and CI templates
  scripts/           verify.sh, check-staged.sh, assert-clean.sh, install-hooks.sh, lib.sh
  githooks/          pre-commit, pre-push and a Git LFS pass-through, installed at the repo root
```

## Adding the kit to a project folder

You need `git`, `make` and `bash`: WSL, macOS, Linux or Codespaces.

1. Copy `_docs/agent-kit/` from your newest project into `<project>/_docs/agent-kit/`.
2. Optional: put a product spec at `<project>/_docs/specs.md`. Without one, the project starts in planning.
3. Start your AI coding tool in the project folder and say: "Set up this project using `_docs/agent-kit/setup.md`."
4. Review what it proposes, approve or correct it, then approve the setup commit.
5. In every clone or new codespace, run `make hooks` once.

In a monorepo, the hooks go at the repository root and only act on folders that contain `agent-kit.conf`, so projects without the kit are unaffected.

If the repo already has hooks, `make hooks` checks them first. Standard Git LFS hooks are replaced automatically, because the kit's hooks call Git LFS themselves. Any other hook stops the install, so you can merge it by hand.

## Day to day

- **Work:** "Work the next issue following `_docs/agent-kit/process.md`."
- **Approving a protected change:** once you've read the diff, tell the agent "approved, commit it with `HUMAN_APPROVED=1`", or commit it yourself.
- **Pushing:** read `git diff origin/main --stat -- .` and the diff, then push. If the pre-push hook blocks you, its output says why.
- **Checking the setup later:** "Review this project using `_docs/agent-kit/setup.md`." Review mode reports blueprints that now apply, such as a new linter, and any drift.

## Fewer approval prompts

Agents trigger most approval prompts in two ways: working outside the project folder (scratch files in `/tmp`), and shell commands too complex for the tool to check. The shared conventions tell agents to use a `.scratch/` folder in the project, prefer built-in file tools and `make` targets, and write simple commands, retrying once in simpler form before asking. When you do decline a prompt, say why in your reply. The agent is told never to pursue a declined goal another way, so a reason like "use a literal path" tells it what to fix. To pre-approve routine commands in your tool, see Tool permissions in `blueprints.md`.

## Updating the kit

The kit's files are protected in every project, so changes need your approval. Improve the kit in the project you're working on, then copy the folder to other projects you're still actively working on; finished homework can keep the version it was built with. Bump the version at the top of this file when you change it.

The git hooks carry their own version number. `make hooks` upgrades an older installed version and leaves an equal or newer one alone, so projects with different kit versions can share one repository.

## Optional: tool-native enforcement

Tools with their own hooks or permission systems can add harder enforcement on top by calling the same scripts. For example, a Claude Code Stop hook can run `make verify` so the agent can't finish while it fails. Keep that configuration in the tool's own folder, and keep `AGENTS.md` and this kit as the source of truth.
