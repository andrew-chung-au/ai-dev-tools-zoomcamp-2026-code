help: ## List targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_ -]+:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

verify: ## Run the verification gate: make verify [BASE=<commit>]
	@bash _docs/agent-kit/scripts/verify.sh $(BASE)

assert-clean: ## Fail if this folder has uncommitted changes (used after QA)
	@bash _docs/agent-kit/scripts/assert-clean.sh

hooks: ## Install the repo's git hooks (once per clone or codespace)
	@bash _docs/agent-kit/scripts/install-hooks.sh

install: ## Install dependencies
	uv sync

test: ## Run all unit tests
	uv run --frozen pytest -q

test-one: ## Run one test file: make test-one FILE=path
	@test -n "$(FILE)" || { echo "Usage: make test-one FILE=path/to/test_file"; exit 1; }
	uv run --frozen pytest -q "$(FILE)"

run: ## Start the app and the observability stack (Collector, Prometheus, Loki, Tempo, Grafana)
	docker compose up --build -d --wait

stop: ## Stop the app and the observability stack (keeps order and telemetry data volumes)
	docker compose down

logs: ## Follow the app's logs (Ctrl-C to stop)
	docker compose logs -f app

logs-all: ## Follow the logs of the app and the observability services (Ctrl-C to stop)
	docker compose logs -f

responder: ## Run the incident responder on port 8001 as a host process (Ctrl-C to stop)
	uv run --frozen python incident-response/responder.py
