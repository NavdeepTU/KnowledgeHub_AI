#!/bin/bash
# Stop hook: push already-committed work to origin after each turn.
# Never commits anything itself - only pushes commits that already exist.
set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/Users/navdeep/Downloads/Interview Prep/Projects/KnowledgeHub_AI}"
cd "$PROJECT_DIR" || exit 0

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -z "$branch" ] && exit 0

git rev-parse --abbrev-ref "${branch}@{upstream}" >/dev/null 2>&1 || exit 0

ahead=$(git rev-list --count "${branch}@{upstream}..${branch}" 2>/dev/null || echo 0)
[ "$ahead" = "0" ] && exit 0

if git push origin "$branch" >/tmp/knowledgehub_ai_push.log 2>&1; then
    echo "{\"systemMessage\": \"Auto-pushed $ahead commit(s) to origin/$branch.\"}"
else
    echo "{\"systemMessage\": \"Auto-push to origin/$branch failed - see /tmp/knowledgehub_ai_push.log.\"}"
fi
