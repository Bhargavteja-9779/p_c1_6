"""Why did H6 (MinimaxCore) fail? DEV, contaminated (unsup), seeds 0-2. Training labels used ONLY diagnostically.
Tests the two risks pre-registered in journal 24:
  R1 bridging  : share of TRAINING anomalies that end up inside the core (m_j == 0) -> they shield like in kNN.
  R2 multimodal: share of TRAINING normals OUTSIDE the core (m_j > 0) -> normal clusters get false alarms.
Also: AUROC of m_j against training labels (does the minimax path cost rank training anomalies at all?),
and the per-dataset test AUROC difference mmc_a - knn from results_t2. Writes results_t2/diag_h6.csv"""
import json, os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split
from methods_t2 import MinimaxCore
D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]; rows = []
for name in dev:
    for s in range(3):
        d = np.load(D[name], allow_pickle=True); Xtr, ytr, _, _ = split(d["X"], d["y"].astype(int), "unsup", s, 10000)
        if ytr.sum() == 0: continue
        m = MinimaxCore(seed=s, frac=0.5).fit(Xtr).m
        r = {"dataset": name, "seed": s, "n": len(ytr), "contam": ytr.mean(),
             "anom_in_core": float((m[ytr == 1] == 0).mean()), "norm_out_core": float((m[ytr == 0] > 0).mean()),
             "auc_m_train": roc_auc_score(ytr, m) if np.ptp(m) > 0 else 0.5}
        for meth in ("mmc_a", "knn"):
            p = os.path.join(ROOT, "results_t2", "unsup", name, f"{meth}_s{s}.json")
            r[f"test_auc_{meth}"] = json.load(open(p))["auc_roc"] if os.path.exists(p) else np.nan
        rows.append(r)
g = pd.DataFrame(rows); g["delta_test"] = g.test_auc_mmc_a - g.test_auc_knn
g.to_csv(os.path.join(ROOT, "results_t2", "diag_h6.csv"), index=False)
pd.set_option("display.width", 200)
print(g.groupby("dataset").mean(numeric_only=True).drop(columns="seed").round(3).to_string())
print(g.mean(numeric_only=True).round(3).to_string())
from scipy.stats import spearmanr
gd = g.groupby("dataset").mean(numeric_only=True)
for c in ("anom_in_core", "norm_out_core", "contam"):
    print(f"spearman(delta_test, {c}) = {spearmanr(gd.delta_test, gd[c]).statistic:.3f}")
