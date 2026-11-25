#!/usr/bin/env bash
# Commit + push project state every 15 min while running (ephemeral container protection). Stop: pkill -f autocommit.sh
cd "$(dirname "$0")/../.."
while true; do
  git add -A project >/dev/null 2>&1
  git diff --cached --quiet || git commit -qm "auto: progress snapshot $(date -u +%Y-%m-%dT%H:%MZ)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Hw1gvGYXnvkdXFNtv4R5P1"
  for i in 1 2 3 4; do git push -q origin claude/cool-ptolemy-6dtl6w && break; sleep $((i*10)); done
  sleep 900
done
