"""H7 angle selection (diagnostic, DEV only, contaminated regime, seeds 0-2). Training/test labels are used ONLY to
evaluate label-free candidate signals; nothing here is a method result.
Shielded test anomaly := test anomaly whose 5 nearest TRAINING neighbours are majority anomalies.
Signals (all label-free, higher = more anomalous):
  knn1, knn5, knn50      : distance to the k-th training neighbour
  ratio50_5              : log d50 - log d5 (jump of the distance profile)
  odin_in                : -(# training points j with d(x, j) <= d5(j))  (reverse-neighbour in-degree, ODIN-style)
  nbr_escape             : mean over x's 5 NN j of d50(j) (how far x's own neighbours are from the bulk)
  kgrid                  : mean over k in {1,2,5,10,20,50} of rank-normalised d_k
Writes results_t2/diag_h7.csv (per dataset/seed AUROC of each signal on all anomalies and on shielded anomalies)."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split
D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]; rows = []
KS = [1, 2, 5, 10, 20, 50]
for name in dev:
    for s in range(3):
        d = np.load(D[name], allow_pickle=True); Xtr, ytr, Xte, yte = split(d["X"], d["y"].astype(int), "unsup", s, 10000)
        K = min(50, len(Xtr) - 1)
        nn = NearestNeighbors(n_neighbors=K).fit(Xtr)
        dte, ite = nn.kneighbors(Xte)                      # test -> train
        dtr, itr = nn.kneighbors(Xtr, n_neighbors=K + 1)   # train -> train (col 0 = self)
        dtr, itr = dtr[:, 1:], itr[:, 1:]
        k5 = min(5, K) - 1; kK = K - 1
        sig = {"knn1": dte[:, 0], "knn5": dte[:, k5], "knn50": dte[:, kK],
               "ratio50_5": np.log(dte[:, kK] + 1e-12) - np.log(dte[:, k5] + 1e-12),
               "nbr_escape": dtr[ite[:, :5], kK].mean(1)}
        r5 = dtr[:, k5]                                    # 5-NN radius of each training point
        indeg = np.zeros(len(Xte))
        for i in range(0, len(Xte), 512):                  # in-degree: training points that would have x in their 5-NN ball
            from sklearn.metrics import pairwise_distances
            indeg[i:i + 512] = (pairwise_distances(Xte[i:i + 512], Xtr) <= r5[None, :]).sum(1)
        sig["odin_in"] = -indeg
        sig["kgrid"] = np.mean([rankdata(dte[:, min(k, K) - 1]) for k in KS], 0)
        shield = (yte == 1) & (ytr[ite[:, :5]].mean(1) > 0.5)
        r = {"dataset": name, "seed": s, "contam": ytr.mean(), "n_anom_te": int(yte.sum()), "shielded_share": shield.sum() / max(1, yte.sum())}
        for k, v in sig.items():
            r[f"all_{k}"] = roc_auc_score(yte, v)
            sub = (yte == 0) | shield
            r[f"sh_{k}"] = roc_auc_score(yte[sub], v[sub]) if shield.sum() >= 2 else np.nan
        rows.append(r)
g = pd.DataFrame(rows); g.to_csv(os.path.join(ROOT, "results_t2", "diag_h7.csv"), index=False)
pd.set_option("display.width", 250)
gd = g.groupby("dataset").mean(numeric_only=True).drop(columns="seed")
print(gd[["contam", "shielded_share"] + [c for c in gd if c.startswith("all_")]].round(3).to_string())
print("\nMEAN over datasets (AUROC x100):")
print((100 * gd[[c for c in gd if c.startswith(("all_", "sh_"))]].mean()).round(2).to_string())
print("shielded share mean", round(gd.shielded_share.mean(), 3))
