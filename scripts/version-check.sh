#!/usr/bin/env bash
# tracer self-update check, run at the start of /tracer (SKILL.md Step 0).
#
# Safe by construction:
#   - never blocks the patrol (always exit 0, even with no network)
#   - throttled to once per 24h (cache stamp)
#   - auto-updates ONLY a clean consumer checkout (clean tree, not ahead);
#     a maintainer's working clone (dirty or ahead) is NEVER touched — notify only
#
# Output (stdout, at most one line) — the skill surfaces it in the brief report:
#   UPDATED: tracer <old> -> <new> (applies next /tracer)
#   UPDATE AVAILABLE: tracer is N commit(s) behind ... Update: git -C "<dir>" pull --ff-only
#   (no output = up to date / throttled / offline)
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # skill repo root
git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1 || exit 0   # not a git checkout

# --- throttle: once per 24h ---
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/tracer"
STAMP="$CACHE/last-update-check"
mkdir -p "$CACHE" 2>/dev/null || true
now=$(date +%s 2>/dev/null || echo 0)
if [ -f "$STAMP" ]; then
  last=$(cat "$STAMP" 2>/dev/null || echo 0)
  [ "$((now - last))" -lt 86400 ] 2>/dev/null && exit 0
fi
echo "$now" > "$STAMP" 2>/dev/null || true

# --- fetch (fail open) ---
git -C "$DIR" fetch --quiet --tags origin 2>/dev/null || exit 0

# default upstream = origin/main (or the tracked upstream if set)
upstream=$(git -C "$DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "origin/main")
behind=$(git -C "$DIR" rev-list --count "HEAD..$upstream" 2>/dev/null || echo 0)
[ "${behind:-0}" -eq 0 ] 2>/dev/null && exit 0   # up to date

local_v=$(cat "$DIR/VERSION" 2>/dev/null || echo "?")
dirty=$(git -C "$DIR" status --porcelain 2>/dev/null)
ahead=$(git -C "$DIR" rev-list --count "$upstream..HEAD" 2>/dev/null || echo 0)

if [ -z "$dirty" ] && [ "${ahead:-0}" -eq 0 ]; then
  # clean consumer checkout, strictly behind -> safe fast-forward
  if git -C "$DIR" pull --ff-only --quiet 2>/dev/null; then
    new_v=$(cat "$DIR/VERSION" 2>/dev/null || echo "?")
    echo "UPDATED: tracer $local_v -> $new_v (applies next /tracer)"
    exit 0
  fi
fi

# maintainer clone (dirty/ahead) or non-ff -> notify only, never mutate
echo "UPDATE AVAILABLE: tracer is $behind commit(s) behind $upstream (local VERSION $local_v). Update: git -C \"$DIR\" pull --ff-only"
exit 0
