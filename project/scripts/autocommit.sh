#!/usr/bin/env bash
# Commit + push new result files every 20 min while the run is active (cloud container is ephemeral).
cd "$(dirname "$0")/.."
while pgrep -f run_all.py >/dev/null; do
  sleep 1200
  git add results state/variants_tried.csv state/budget.json state/queue.json logs 2>/dev/null
  git commit -qm "cycle1: auto-commit of finished results ($(python3 -c 'import json,collections;q=json.load(open("state/queue.json"))["jobs"];print(dict(collections.Counter(j["status"] for j in q.values())))'))" && \
    for i in 1 2 3 4; do git push -q && break || sleep $((i*5)); done
done
