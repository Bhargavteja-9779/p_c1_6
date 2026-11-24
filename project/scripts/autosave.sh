#!/usr/bin/env bash
# Periodically commit+push results/state to the session branch (container is ephemeral). Stop: touch state/STOP_AUTOSAVE
cd "$(dirname "$0")/.."
BR=$(git rev-parse --abbrev-ref HEAD)
while [ ! -f state/STOP_AUTOSAVE ]; do
  sleep "${AUTOSAVE_S:-1200}"
  git add -A results state journal 2>/dev/null
  if ! git diff --cached --quiet; then
    git commit -qm "autosave: $(python3 scripts/status.py 2>/dev/null | grep queue.json | head -1)" && \
    for i in 1 2 3 4; do git push -q origin "$BR" && break; sleep $((2**i)); done
  fi
done
