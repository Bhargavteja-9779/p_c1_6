#!/usr/bin/env bash
# Topic 2 data: ADBench "Classical" tabular AD datasets (47 .npz, ~83 MB). Repo licence BSD-2-Clause (Han et al., NeurIPS 2022).
# Idempotent. Uses a sparse, blobless clone (the GitHub API is not reachable from the cloud container; plain git is).
cd "$(dirname "$0")/.." && mkdir -p data/adbench
if [ ! -d data/adbench/repo/adbench/datasets/Classical ]; then
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/Minqi824/ADBench.git data/adbench/repo
  git -C data/adbench/repo sparse-checkout set adbench/datasets/Classical
fi
git -C data/adbench/repo rev-parse HEAD > data/adbench/COMMIT
ls data/adbench/repo/adbench/datasets/Classical/*.npz | wc -l
python3 -c "import pyod, hdbscan" 2>/dev/null || pip install -q pyod==3.6.9 hdbscan scikit-learn scipy
