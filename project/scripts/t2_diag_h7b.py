"""Why did H7 fail? DEV, contaminated, seeds 0-2, LOCO-kNN variant b (k_m=10, cap=0.05). Labels used only diagnostically.
For each test point: was an exclusion triggered (a small group among its 5 NN)? Shares for shielded anomalies, unshielded
anomalies and normals; share of TRAINING anomalies that lie in small components (removable at all); AUROC of kNN5 and LOCO on
shielded-vs-normals and unshielded-vs-normals. Writes results_t2/diag_h7b.csv"""
import json, os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split
from methods_t2 import LocoKNN
D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]; rows = []
for name in dev:
    for s in range(3):
        d = np.load(D[name], allow_pickle=True); Xtr, ytr, Xte, yte = split(d["X"], d["y"].astype(int), "unsup", s, 10000)
        m = LocoKNN(s, k_m=10, cap=0.05).fit(Xtr); sl = m.decision_function(Xte)
        dd, ii = NearestNeighbors(n_neighbors=5).fit(Xtr).kneighbors(Xte); sk = dd[:, -1]
        trig = m.small[ii].any(1); shield = (yte == 1) & (ytr[ii].mean(1) > 0.5); unsh = (yte == 1) & ~shield
        r = {"dataset": name, "seed": s, "train_anom_in_small": m.small[ytr == 1].mean() if ytr.sum() else np.nan,
             "train_norm_in_small": m.small[ytr == 0].mean(), "trig_shielded": trig[shield].mean() if shield.any() else np.nan,
             "trig_unshielded": trig[unsh].mean() if unsh.any() else np.nan, "trig_normal": trig[yte == 0].mean()}
        for lab, mask in (("sh", shield), ("unsh", unsh)):
            sub = (yte == 0) | mask
            ok = mask.sum() >= 2
            r[f"knn5_{lab}"] = roc_auc_score(yte[sub], sk[sub]) if ok else np.nan
            r[f"loco_{lab}"] = roc_auc_score(yte[sub], sl[sub]) if ok else np.nan
        rows.append(r)
g = pd.DataFrame(rows); g.to_csv(os.path.join(ROOT, "results_t2", "diag_h7b.csv"), index=False)
gd = g.groupby("dataset").mean(numeric_only=True).drop(columns="seed")
pd.set_option("display.width", 250); print(gd.round(3).to_string()); print(gd.mean().round(3).to_string())
