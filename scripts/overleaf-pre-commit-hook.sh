#!/bin/sh
# pre-commit hook for the Overleaf clone (paper/): refuse to commit on a stale base.
#
# Colleagues edit through the Overleaf UI, which turns their edits into commits
# continuously; building local commits on an old base invites conflicts at push
# time. This hook fetches from Overleaf and rejects the commit if upstream has
# anything not yet incorporated locally.
#
# Install (from the repository root):
#   cp scripts/overleaf-pre-commit-hook.sh paper/.git/hooks/pre-commit
#   chmod +x paper/.git/hooks/pre-commit

# Detached HEAD or a branch with no upstream: nothing to compare against, skip.
git symbolic-ref --quiet HEAD >/dev/null || exit 0
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null) || exit 0

if ! git fetch --quiet origin; then
    echo "pre-commit: cannot reach Overleaf to check freshness (offline?) — allowing commit." >&2
    exit 0
fi

behind=$(git rev-list --count "HEAD..$upstream")
if [ "$behind" -gt 0 ]; then
    echo "pre-commit: $upstream has $behind new commit(s) from Overleaf that you haven't incorporated." >&2
    echo "Incorporate them first:   git pull --rebase" >&2
    echo "Bypass once (discouraged): git commit --no-verify" >&2
    exit 1
fi
exit 0
