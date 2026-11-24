#!/usr/bin/env bash
# Commit + push results/ and state/ every 20 min while the run is alive (ephemeral container safety).
cd "$(dirname "$0")/.."
while pgrep -f "run_all.py" >/dev/null; do
  sleep 1200
  git add results state journal >/dev/null 2>&1
  git commit -qm "auto: run progress $(python3 -c "import json,collections;q=json.load(open('state/queue.json'))['jobs'];print(dict(collections.Counter(x['status'] for x in q.values())))")" && \
  for i in 1 2 3 4; do git push -q origin HEAD && break; sleep $((i*10)); done
done
