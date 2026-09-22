.PHONY: run run-frontend dev test test-frontend test-backend e2e

run:
	uv run alembic upgrade head
	uv run uvicorn backend.main:app --reload --port 8091

run-frontend dev:
	cd frontend && bun run dev

test: test-frontend test-backend

test-frontend:
	cd frontend && bun test

test-backend:
	uv run pytest

# Builds and starts the docker-compose.yml stack, waits for the app to
# accept requests, runs the Playwright suite in e2e/ against it, then tears
# the stack back down (even if the tests fail, so it doesn't leak containers).
e2e:
	docker compose up -d --build
	@echo "Waiting for the app to become ready on http://localhost:8091..."
	@i=0; until curl -sf http://localhost:8091/api/venue > /dev/null 2>&1; do \
		i=$$((i + 1)); \
		if [ $$i -ge 60 ]; then \
			echo "Timed out waiting for the app to become ready"; \
			docker compose down; \
			exit 1; \
		fi; \
		sleep 2; \
	done
	(cd e2e && npm install && npx playwright install --with-deps chromium && npm test); \
	status=$$?; \
	docker compose down; \
	exit $$status