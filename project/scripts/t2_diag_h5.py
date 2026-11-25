"""Why did H5 fail? DEV, contaminated, seeds 0-2: how well do the trust scores rank TRAINING anomalies (AUROC vs training labels,
diagnostic only), and what share of training anomalies the 20 % cut removes. Writes results_t2/diag_h5.csv"""
import json, os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split
from methods_t2 import _subsample_knn_scores
D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]; rows = []
for name in dev:
    for s in range(3):
        d = np.load(D[name], allow_pickle=True); Xtr, ytr, _, _ = split(d["X"], d["y"].astype(int), "unsup", s, 10000)
        if ytr.sum() == 0: continue
        t_if = -IsolationForest(max_samples=min(256, len(Xtr)), random_state=s).fit(Xtr).score_samples(Xtr)
        t_sk = _subsample_knn_scores(Xtr, Xtr, 50, 256, 1, np.random.default_rng(s), exclude_self=True)
        loo = NearestNeighbors(n_neighbors=6).fit(Xtr).kneighbors(Xtr)[0][:, -1]
        r = {"dataset": name, "seed": s, "contam": ytr.mean()}
        for k, t in (("iforest", t_if), ("subknn", t_sk), ("loo_knn5", loo)):
            r[f"auc_{k}"] = roc_auc_score(ytr, t); r[f"removed20_{k}"] = float(ytr[t >= np.quantile(t, 0.8)].sum() / ytr.sum())
        rows.append(r)
g = pd.DataFrame(rows); g.to_csv(os.path.join(ROOT, "results_t2", "diag_h5.csv"), index=False)
print(g.groupby("dataset").mean(numeric_only=True).drop(columns="seed").round(3).to_string()); print(g.mean(numeric_only=True).round(3).to_string())
