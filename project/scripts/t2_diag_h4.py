"""H4 diagnostic (journal 19). DEV datasets, seeds 0-2, CONTAMINATED regime. Writes results_t2/diag_h4.csv + summary print.
Oracle removal uses training labels ONLY as a diagnostic, never in a method."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split
D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]
rows = []
def kscore(Xtr, Xte, k=5):
    nn = NearestNeighbors(n_neighbors=min(k, len(Xtr))).fit(Xtr); d, i = nn.kneighbors(Xte); return d[:, -1], i
for name in dev:
    for s in range(3):
        d = np.load(D[name], allow_pickle=True); X, y = d["X"], d["y"].astype(int)
        Xtr, ytr, Xte, yte = split(X, y, "unsup", s, 10000)
        sc, idx = kscore(Xtr, Xte)
        a = yte == 1
        shield = float((ytr[idx[a, 0]] == 1).mean()) if a.any() else np.nan
        sc_or, _ = kscore(Xtr[ytr == 0], Xte)
        Xc, yc, Xtc, ytc = split(X, y, "semi", s, 10000)
        sc_cl, _ = kscore(Xc, Xtc)
        rows.append({"dataset": name, "seed": s, "anom_rate_train": float(ytr.mean()), "shield_rate": shield,
                     "auc_contam": roc_auc_score(yte, sc), "auc_contam_oracle_clean_ref": roc_auc_score(yte, sc_or),
                     "auc_clean": roc_auc_score(ytc, sc_cl)})
r = pd.DataFrame(rows); r.to_csv(os.path.join(ROOT, "results_t2", "diag_h4.csv"), index=False)
g = r.groupby("dataset").mean(numeric_only=True)
g["drop"] = g.auc_clean - g.auc_contam; g["recovered"] = g.auc_contam_oracle_clean_ref - g.auc_contam
print(g[["anom_rate_train", "shield_rate", "auc_clean", "auc_contam", "auc_contam_oracle_clean_ref", "drop", "recovered"]].round(3).to_string())
print("P1 shield_rate > 2x anomaly rate in", int((g.shield_rate > 2 * g.anom_rate_train).sum()), "of", len(g))
rho = spearmanr(g["drop"], g.shield_rate); print(f"P2 Spearman(drop, shield_rate) = {rho.statistic:.3f} (p={rho.pvalue:.3g})")
print(f"P3 mean drop {g['drop'].mean():.4f}, mean oracle recovery {g.recovered.mean():.4f}, share {g.recovered.mean()/g['drop'].mean():.2f}")
