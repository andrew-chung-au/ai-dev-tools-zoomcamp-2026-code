#!/usr/bin/env bash
# Installs the kit's git hooks at <repo root>/.githooks and points git at them.
# Safe to re-run. Run once per clone or new codespace: `make hooks`.
# FORCE=1 replaces a different hooks setup after you've checked it.
set -uo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd)"
root="$(git rev-parse --show-toplevel)"
target="$root/.githooks"

current="$(git config --get core.hooksPath || true)"
if [ -n "$current" ] && [ "$current" != ".githooks" ] && [ "${FORCE:-}" != "1" ]; then
  echo "agent-kit: git already uses hooks from '$current'. Not changing that." >&2
  echo "  Merge the kit's hooks ($kit/githooks) into it, or re-run with FORCE=1." >&2
  exit 1
fi
if [ -z "$current" ] && [ "${FORCE:-}" != "1" ]; then
  gitdir="$(git rev-parse --git-common-dir)"
  existing="$(find "$gitdir/hooks" -maxdepth 1 -type f ! -name '*.sample' 2>/dev/null)"
  if [ -n "$existing" ]; then
    echo "agent-kit: existing hooks in $gitdir/hooks would stop running:" >&2
    echo "$existing" >&2
    echo "  Move them into .githooks yourself, or re-run with FORCE=1." >&2
    exit 1
  fi
fi

version_of() { sed -n 's/^# agent-kit-hooks-version: *//p' "$1" 2>/dev/null | head -1; }

mkdir -p "$target"
for hook in pre-commit pre-push; do
  src="$kit/githooks/$hook"
  dst="$target/$hook"
  if [ ! -f "$dst" ]; then
    cp "$src" "$dst"
    echo "installed .githooks/$hook"
  elif cmp -s "$src" "$dst"; then
    echo ".githooks/$hook is up to date"
  elif [ "$(version_of "$src")" -gt "$(version_of "$dst" || echo 0)" ] 2>/dev/null; then
    cp "$src" "$dst"
    echo "updated .githooks/$hook to version $(version_of "$src")"
  else
    echo ".githooks/$hook differs but isn't older than the kit's; left as is"
  fi
  chmod +x "$dst"
done

git config core.hooksPath .githooks
echo "git now runs hooks from .githooks (core.hooksPath)."
echo "Commit .githooks/ at the repo root so other clones get it; each clone still needs 'make hooks' once."
