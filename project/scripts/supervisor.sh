#!/usr/bin/env bash
# Layer B: restart the agent CLI headlessly until state says FINISHED. Stop: touch state/STOP
cd "$(dirname "$0")/.."; mkdir -p logs; delays=(300 900 1800 3600); i=0
CLI=$(command -v claude || true); [ -z "$CLI" ] && { echo "no agent CLI found; paste BOOTSTRAP_PROMPT.txt manually" | tee -a logs/supervisor.log; exit 1; }
while true; do
  grep -q '"FINISHED"' state/agent_state.json 2>/dev/null && { echo "$(date) FINISHED" >> logs/supervisor.log; exit 0; }
  [ -f state/STOP ] && { echo "$(date) STOP file" >> logs/supervisor.log; exit 0; }
  echo "$(date) starting agent" >> logs/supervisor.log
  "$CLI" -p "$(cat BOOTSTRAP_PROMPT.txt)" --permission-mode acceptEdits >> logs/agent_run.log 2>&1; rc=$?
  d=${delays[$((i<3?i:3))]}; i=$((i+1))
  echo "$(date) agent exited rc=$rc; sleeping $d s" >> logs/supervisor.log; sleep $d
done
