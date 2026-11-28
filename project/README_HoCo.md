# HoCo-kNN — reproduction guide (topic 3 of this repository)

Training-free host-context nearest neighbours for benign-only NetFlow intrusion detection. Everything below runs on a 4-core CPU
with 15 GB RAM; no GPU. Files of earlier, abandoned topics (NetFlow-v3 cross-network, tabular AD) live elsewhere in this repository
and are not needed here (see FINAL_REPORT.md and archive/).

## 1. Environment
```bash
pip install -r requirements_t3.txt
```
Python 3.13 was used. Set `OMP_NUM_THREADS=1` when running several jobs in parallel.

## 2. Data (official University of Queensland release, open access for academic use with citation)
```bash
bash scripts/get_data_nfv2.sh
```
Downloads NF-UNSW-NB15-v2, NF-CSE-CIC-IDS2018-v2 and NF-ToN-IoT-v2 into data/nfv2/ (sha256 of each zip saved next to it).

## 3. Splits (random 8:1:1 stratified by attack type, benign-only training; 10 % stratified sample for CIC and ToN)
```bash
for s in 42 123 456 789 1234; do for d in NF-UNSW-NB15-v2 NF-CSE-CIC-IDS2018-v2 NF-ToN-IoT-v2; do python3 src/nfv2_prep.py $d $s; done; done
```

## 4. Main results (Tables 2–4)
```bash
S=42,123,456,789,1234
for d in NF-UNSW-NB15-v2 NF-CSE-CIC-IDS2018-v2 NF-ToN-IoT-v2; do
  python3 src/nfv2_bench.py --data $d --methods hc1_s,ck1_L,knn1 --seeds $S --ref 200000
  python3 src/nfv2_bench.py --data $d --methods iforest,hbos,pca,ae --seeds $S
done
python3 src/nfv2_bench.py --data NF-UNSW-NB15-v2 --methods hc1_sd,hc1_d,hc1_os,knn5 --seeds $S --ref 200000   # ablations (same for CIC)
python3 scripts/t3_report.py && python3 scripts/t3_per_attack.py && python3 scripts/t3_host_purity.py
```
Method names: `hc1_s` = HoCo-kNN (log rescaling + source-host context, k = 1); `ck1_L` = log rescaling only; `knn1` = raw features.

## 5. Analyses, figures, manuscript
```bash
python3 scripts/t3_scores.py NF-UNSW-NB15-v2; python3 scripts/t3_scores.py NF-CSE-CIC-IDS2018-v2     # per-flow scores, timing
python3 scripts/t3_controls.py NF-UNSW-NB15-v2; python3 scripts/t3_controls.py NF-CSE-CIC-IDS2018-v2  # shortcut controls
python3 scripts/t3_figures.py
python3 paper/build.py && python3 scripts/t3_audit.py    # manuscript tables from result files + number audit
```
Design-mode runs (validation split only) use `--eval val` and write to results_t3_val/.

## Pre-registration and logs
experiments/plan_v5.yaml (frozen before the test runs), state/decisions.md (D38–D42), journal/ENTRIES/28–… (research log),
review/ (simulated review rounds).
