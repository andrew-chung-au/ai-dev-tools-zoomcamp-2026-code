# Agent kit Makefile blueprint. Setup merges these targets into the project's
# Makefile: add what's missing, never replace existing targets. Recipe lines
# must start with a TAB. See blueprints.md for when each target applies.

# --- Always (added at setup) ---------------------------------------------

help: ## List targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_ -]+:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

verify: ## Run the verification gate: make verify [BASE=<commit>]
	@bash _docs/agent-kit/scripts/verify.sh $(BASE)

assert-clean: ## Fail if this folder has uncommitted changes (used after QA)
	@bash _docs/agent-kit/scripts/assert-clean.sh

hooks: ## Install the repo's git hooks (once per clone or codespace)
	@bash _docs/agent-kit/scripts/install-hooks.sh

# --- When the stack is known (wrap the project's own commands) -------------

install: ## Install dependencies
	<the project's install command(s)>

test: ## Run all unit tests
	<the project's test command(s)>

# --- Only when the project has the capability --------------------------------

test-one: ## Run one test file: make test-one FILE=path
	@test -n "$(FILE)" || { echo "Usage: make test-one FILE=path/to/test_file"; exit 1; }
	<the project's single-file test command> "$(FILE)"

e2e: ## Run end-to-end tests
	<the project's e2e command, including any stack start and teardown>

migration: ## Create a database migration: make migration MSG="what changed"
	@test -n "$(MSG)" || { echo 'Usage: make migration MSG="what changed"'; exit 1; }
	<the project's migration command> "$(MSG)"

lint: ## Run the linter
	<the project's lint command>

typecheck: ## Run the type checker
	<the project's type-check command>
