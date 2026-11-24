#!/usr/bin/env bash
# Re-download NetFlow V3 parquet mirror (~1.4 GB) and rebuild pools. Idempotent.
cd "$(dirname "$0")/.." && mkdir -p data/raw logs
for f in NF-UNSW-NB15-v3 NF-BoT-IoT-v3 NF-ToN-IoT-v3 NF-CICIDS2018-v3; do
  [ -s data/raw/$f.parquet ] || curl -L --retry 5 -C - -o data/raw/$f.parquet https://huggingface.co/datasets/keys-i/netFlow/resolve/main/data/$f.parquet
done
curl -sL -o data/raw/NetFlow_v3_Features.csv https://huggingface.co/datasets/keys-i/netFlow/resolve/main/metadata/NetFlow_v3_Features.csv
pip install -q pyarrow lightgbm xgboost scikit-learn scipy statsmodels matplotlib pyyaml
python3 -c "import torch" 2>/dev/null || pip install -q torch --index-url https://download.pytorch.org/whl/cpu
python3 src/prepare_data.py
