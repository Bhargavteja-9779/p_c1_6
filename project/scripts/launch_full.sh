#!/usr/bin/env bash
# Layer A: detached full run in tmux (resume-safe). Status: python3 scripts/status.py ; logs: tail -f logs/run_all_full.log
cd "$(dirname "$0")/.."
tmux new-session -d -s nids "python3 run_all.py --mode full --resume" 2>/dev/null || setsid nohup python3 run_all.py --mode full --resume > logs/run_all_full.out 2>&1 &
echo "launched"
