"""Diagnostic (DEV, seeds 0-2): kNN AUROC as a function of k in both regimes. Is there a k that breaks shielding without hurting clean?"""
import json, os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split
D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]; K = [1, 5, 10, 20, 50, 100, 200, 500]; rows = []
for name in dev:
    for p in ("semi", "unsup"):
        for s in range(3):
            d = np.load(D[name], allow_pickle=True); Xtr, ytr, Xte, yte = split(d["X"], d["y"].astype(int), p, s, 10000)
            kk = min(max(K), len(Xtr)); dist = NearestNeighbors(n_neighbors=kk).fit(Xtr).kneighbors(Xte)[0]
            for k in K:
                if k <= kk: rows.append({"dataset": name, "protocol": p, "seed": s, "k": k, "auc": roc_auc_score(yte, dist[:, k - 1]), "auc_mean": roc_auc_score(yte, dist[:, :k].mean(1))})
r = pd.DataFrame(rows); r.to_csv(os.path.join(ROOT, "results_t2", "diag_ksweep.csv"), index=False)
print((r.groupby(["protocol", "k"])[["auc", "auc_mean"]].mean() * 100).round(2).unstack(0).to_string())
