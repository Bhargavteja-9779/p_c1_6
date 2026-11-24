#!/usr/bin/env bash
# Topic 2 baseline suite under the primary protocol (transd), HF-DIF's 20 datasets. Resumable (bench.py skips finished files).
cd "$(dirname "$0")/.." && mkdir -p logs
P=${P:-transd}; S=${S:-0-4}
python3 src/ad/bench.py --protocol $P --methods ecod,copod,hbos,pca --seeds 0 --datasets hfdif20 --max_n 1000000 > logs/t2_${P}_det.log 2>&1 &
python3 src/ad/bench.py --protocol $P --methods iforest,loda --seeds $S --datasets hfdif20 --max_n 1000000 > logs/t2_${P}_rand.log 2>&1 &
python3 src/ad/bench.py --protocol $P --methods knn,lof --seeds 0 --datasets hfdif20 --max_n 1000000 > logs/t2_${P}_nn.log 2>&1 &
wait
