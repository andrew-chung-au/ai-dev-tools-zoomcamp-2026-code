## Scope

- Work only within `02-restaurant-waitlist/`.
- Do not modify, stage, move, delete, or commit any file outside this directory.
- Do not use `git add .` or `git add -A`.
- Before proposing a commit, show `git status --short`, `git diff --check`, and the exact paths that would be staged.

Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking

Documents
- `_docs/process.md` - how work is organized
- Before writing tests, read `_docs/testing-guidelines.md`
- For anything touching the UI, read `_docs/design-system.md`