#!/usr/bin/env bash
# Installs the kit's git hooks at <repo root>/.githooks and points git at them.
# Safe to re-run. Run once per clone or new codespace: `make hooks`.
#
# Standard Git LFS hooks are recognised and replaced by the kit's hooks, which
# keep LFS working. Any other existing hook stops the install; FORCE=1 replaces
# it after you've checked it.
set -uo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd)"
root="$(git rev-parse --show-toplevel)"
target="$root/.githooks"
lfs_hooks="pre-push post-checkout post-commit post-merge"

# is_lfs_hook FILE: true only for the exact hooks `git lfs install` writes: a
# git-lfs presence check plus `git lfs <hook> "$@"`, and nothing else.
is_lfs_hook() {
  local name extra
  name="$(basename "$1")"
  case " $lfs_hooks " in *" $name "*) ;; *) return 1 ;; esac
  grep -qE "^git lfs $name \"\\\$@\"\$" "$1" || return 1
  extra="$(grep -vE '^[[:space:]]*(#|$)' "$1" | grep -vE "^command -v git-lfs |^git lfs $name \"\\\$@\"\$")"
  [ -z "$extra" ]
}
version_of() { sed -n 's/^# agent-kit-hooks-version: *//p' "$1" 2>/dev/null | head -1; }

# 1. Which hooks folder git uses now.
current="$(git config --get core.hooksPath || true)"
if [ -n "$current" ] && [ "$current" != ".githooks" ] && [ "${FORCE:-}" != "1" ]; then
  echo "agent-kit: git already uses hooks from '$current'. Not changing that." >&2
  echo "  Merge the kit's hooks ($kit/githooks) into it, or re-run with FORCE=1." >&2
  exit 1
fi

# 2. Hooks in .git/hooks stop running once core.hooksPath is set.
if [ -z "$current" ]; then
  gitdir="$(git rev-parse --git-common-dir)"
  lfs_found=""
  other_found=""
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if is_lfs_hook "$f"; then lfs_found="$lfs_found $(basename "$f")"; else other_found="$other_found $f"; fi
  done < <(find "$gitdir/hooks" -maxdepth 1 -type f ! -name '*.sample' 2>/dev/null)
  if [ -n "$other_found" ] && [ "${FORCE:-}" != "1" ]; then
    echo "agent-kit: these hooks in $gitdir/hooks would stop running:" >&2
    printf '  %s\n' $other_found >&2
    echo "  Move them into .githooks yourself, or re-run with FORCE=1." >&2
    exit 1
  fi
  if [ -n "$lfs_found" ]; then
    echo "Found standard Git LFS hooks (${lfs_found# }); the kit's hooks include LFS support, so LFS keeps working."
  fi
fi

# 3. Install or upgrade each hook.
mkdir -p "$target"
conflicts=0
for hook in pre-commit pre-push post-checkout post-commit post-merge; do
  case "$hook" in
    post-*) src="$kit/githooks/lfs-passthrough" ;;
    *) src="$kit/githooks/$hook" ;;
  esac
  dst="$target/$hook"
  if [ ! -f "$dst" ]; then
    cp "$src" "$dst" && echo "installed .githooks/$hook"
  elif cmp -s "$src" "$dst"; then
    echo ".githooks/$hook is up to date"
  elif [ -n "$(version_of "$dst")" ]; then
    if [ "$(version_of "$src")" -gt "$(version_of "$dst")" ]; then
      cp "$src" "$dst" && echo "updated .githooks/$hook to version $(version_of "$src")"
    else
      echo ".githooks/$hook is the same or a newer kit version; left as is"
    fi
  elif is_lfs_hook "$dst"; then
    cp "$src" "$dst" && echo "replaced the Git LFS .githooks/$hook with the kit's (LFS still runs)"
  elif [ "${FORCE:-}" = "1" ]; then
    cp "$src" "$dst" && echo "replaced .githooks/$hook (FORCE=1)"
  else
    echo "agent-kit: .githooks/$hook exists and isn't a kit or Git LFS hook; left as is." >&2
    conflicts=1
  fi
  chmod +x "$dst"
done

if [ "$conflicts" -ne 0 ]; then
  echo "  Merge those hooks by hand, or re-run with FORCE=1 to replace them." >&2
  exit 1
fi

git config core.hooksPath .githooks
echo "git now runs hooks from .githooks (core.hooksPath)."
echo "Commit .githooks/ at the repo root so other clones get it; each clone still needs 'make hooks' once."
