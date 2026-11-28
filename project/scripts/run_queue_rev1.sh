#!/usr/bin/env bash
# Review-round-1 experiment queue: waits for ToN prep and the running jobs to free memory, then runs state/queue_rev1.txt with 3 workers.
cd "$(dirname "$0")/.."; export OMP_NUM_THREADS=1
while pgrep -f "nfv2_prep.py NF-ToN" >/dev/null || [ $(ls data/nfv2/NF-ToN-IoT-v2_s*.npz 2>/dev/null | wc -l) -lt 5 ]; do sleep 30; done
while pgrep -f "t3_scores.py NF-CSE" >/dev/null; do sleep 30; done
python3 scripts/t3_controls.py NF-CSE-CIC-IDS2018-v2 > logs/t3_controls_cic.log 2>&1
grep -v '^#' state/queue_rev1.txt | xargs -P 3 -I{} sh -c '{} >> logs/t3_rev1_queue.log 2>&1'
python3 scripts/t3_controls.py NF-UNSW-NB15-v2 > logs/t3_controls_unsw.log 2>&1
echo QUEUE_DONE >> logs/t3_rev1_queue.log
