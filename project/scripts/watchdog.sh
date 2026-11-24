#!/usr/bin/env bash
# Run every 5 min (cron): if heartbeat older than 20 min, kill runner and relaunch (resumes from queue/checkpoints)
cd "$(dirname "$0")/.."
[ -f state/heartbeat ] || exit 0
age=$(( $(date +%s) - $(stat -c %Y state/heartbeat) ))
if [ $age -gt 1200 ] && grep -qv '"FINISHED"' state/agent_state.json; then
  pkill -f "run_all.py --mode full"; pkill -f run_job.py; sleep 5; bash scripts/launch_full.sh
  echo "$(date) watchdog restart (age $age)" >> logs/watchdog.log
fi
