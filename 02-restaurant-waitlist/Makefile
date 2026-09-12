.PHONY: run run-frontend dev test test-frontend test-backend

run:
	uv run uvicorn backend.main:app --reload --port 8091

run-frontend dev:
	cd frontend && bun run dev

test: test-frontend test-backend

test-frontend:
	cd frontend && bun test

test-backend:
	uv run pytest