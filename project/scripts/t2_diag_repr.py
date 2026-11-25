"""Cycle-5 angle selection (EXPLORATORY diagnostic, DEV only, both regimes, seeds 0-2). Does any feature REPRESENTATION
make kNN robust to contaminated training data? Labels used only to evaluate. Every representation is a logged variant.
Representations (fit on TRAINING data only):
  raw     : the benchmark's min-max scaling (as in bench.py)
  rank    : per-feature empirical CDF of the training data (rank transform)
  pcaw    : PCA whitening (all components with variance > 1e-9)
  fbag    : feature bagging — mean over 25 random subspaces of size ceil(d/2) of the kNN score (rank-normalised)
  rproj   : mean over 25 Gaussian random projections to max(2, ceil(d/2)) dims (rank-normalised)
Scores: kNN5 and kNN50 in each representation. Writes results_t2/diag_repr.csv"""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, os.path.join(ROOT, "src", "ad"))
from bench import datasets, split


def knn(Xtr, Xte, k):
    k = min(k, len(Xtr)); return NearestNeighbors(n_neighbors=k).fit(Xtr).kneighbors(Xte)[0][:, -1]


def ecdf(Xtr, X):
    Z = np.empty_like(X)
    for j in range(X.shape[1]):
        r = np.sort(Xtr[:, j]); Z[:, j] = (np.searchsorted(r, X[:, j], "left") + np.searchsorted(r, X[:, j], "right")) / (2 * len(r))
    return Z


D = datasets(); dev = json.load(open(os.path.join(ROOT, "experiments", "t2_dataset_split.json")))["dev"]; rows = []
for name in dev:
    for proto in ("unsup", "semi"):
        for s in range(3):
            d = np.load(D[name], allow_pickle=True); Xtr, ytr, Xte, yte = split(d["X"], d["y"].astype(int), proto, s, 10000)
            rng = np.random.default_rng(s); dd = Xtr.shape[1]; r = {"dataset": name, "protocol": proto, "seed": s}
            reps = {"raw": (Xtr, Xte), "rank": (ecdf(Xtr, Xtr), ecdf(Xtr, Xte))}
            mu = Xtr.mean(0); U, S, Vt = np.linalg.svd(Xtr - mu, full_matrices=False); keep = S ** 2 / len(Xtr) > 1e-9
            W = Vt[keep].T / (S[keep] / np.sqrt(len(Xtr))); reps["pcaw"] = ((Xtr - mu) @ W, (Xte - mu) @ W)
            for nm, (A, B) in reps.items():
                for k in (5, 50):
                    r[f"{nm}_k{k}"] = roc_auc_score(yte, knn(A, B, k))
            for k in (5, 50):
                fb, rp = [], []
                for _ in range(25):
                    f = rng.choice(dd, max(1, int(np.ceil(dd / 2))), replace=False); fb.append(rankdata(knn(Xtr[:, f], Xte[:, f], k)))
                    P = rng.normal(size=(dd, max(2, int(np.ceil(dd / 2))))); rp.append(rankdata(knn(Xtr @ P, Xte @ P, k)))
                r[f"fbag_k{k}"] = roc_auc_score(yte, np.mean(fb, 0)); r[f"rproj_k{k}"] = roc_auc_score(yte, np.mean(rp, 0))
            rows.append(r)
g = pd.DataFrame(rows); g.to_csv(os.path.join(ROOT, "results_t2", "diag_repr.csv"), index=False)
m = g.groupby(["protocol", "dataset"]).mean(numeric_only=True).drop(columns="seed").groupby("protocol").mean()
pd.set_option("display.width", 250); print((100 * m).round(2).T.to_string())
