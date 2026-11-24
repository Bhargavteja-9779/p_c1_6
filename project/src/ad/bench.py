"""Topic 2 benchmark harness: tabular anomaly detection on ADBench Classical datasets.

Protocols (fixed before any result is seen; the one matching HF-DIF is chosen in plan_v4):
  semi  : one-class / semi-supervised (Livernoche et al. 2024 / ADBench "semi" style): a random 50 % of the NORMAL
          samples (per seed) form the training set; test = remaining normals + ALL anomalies.
  unsup : unsupervised (ADBench style): stratified 70/30 split per seed; detector fitted on the 70 % (labels unused,
          anomalies included), evaluated on the 30 %.
Preprocessing: min-max scaling fitted on the training part only (no test statistics).
Metrics: AUC-ROC, AUC-PR (average precision), P@K (K = #anomalies in test), fit/predict seconds.
Results: results_t2/<protocol>/<dataset>/<method>_s<seed>.json (atomic write; skipped if present).

Usage: python src/ad/bench.py --protocol semi --methods knn,iforest --seeds 0-9 [--datasets all|name,...] [--max_n 50000]
"""
import argparse, glob, json, os, sys, time, warnings
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "adbench", "repo", "adbench", "datasets", "Classical")
OUT = os.path.join(ROOT, "results_t2")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def datasets():
    fs = glob.glob(os.path.join(DATA, "*.npz"))
    return {os.path.basename(f)[:-4].split("_", 1)[1]: f for f in sorted(fs, key=lambda p: int(os.path.basename(p).split("_")[0]))}


def split(X, y, protocol, seed, max_n=None):
    rng = np.random.default_rng(seed)
    if max_n and len(y) > max_n:  # documented cap for very large sets (stratified subsample, per seed)
        idx = np.concatenate([rng.choice(np.flatnonzero(y == c), max(1, int(round(max_n * (y == c).mean()))), replace=False) for c in (0, 1)])
        X, y = X[idx], y[idx]
    if protocol == "semi":
        n = np.flatnonzero(y == 0); a = np.flatnonzero(y == 1); rng.shuffle(n)
        tr = n[: len(n) // 2]; te = np.concatenate([n[len(n) // 2:], a])
    elif protocol == "unsup":
        tr, te = [], []
        for c in (0, 1):
            i = np.flatnonzero(y == c); rng.shuffle(i); k = int(round(0.7 * len(i))); tr.append(i[:k]); te.append(i[k:])
        tr, te = np.concatenate(tr), np.concatenate(te)
    else:
        raise ValueError(protocol)
    Xtr, Xte = X[tr].astype(np.float64), X[te].astype(np.float64)
    lo, hi = Xtr.min(0), Xtr.max(0); rngw = np.where(hi - lo > 0, hi - lo, 1.0)
    return (Xtr - lo) / rngw, y[tr], (Xte - lo) / rngw, y[te]


def make(method, seed, n_train):
    from pyod.models.knn import KNN
    from pyod.models.iforest import IForest
    from pyod.models.ecod import ECOD
    from pyod.models.copod import COPOD
    from pyod.models.lof import LOF
    from pyod.models.ocsvm import OCSVM
    from pyod.models.pca import PCA
    from pyod.models.hbos import HBOS
    k = min(5, max(1, n_train - 1))
    M = {"knn": lambda: KNN(n_neighbors=k, method="largest"), "iforest": lambda: IForest(random_state=seed, n_jobs=1),
         "ecod": lambda: ECOD(), "copod": lambda: COPOD(), "lof": lambda: LOF(n_neighbors=min(20, max(2, n_train - 1))),
         "ocsvm": lambda: OCSVM(), "pca": lambda: PCA(random_state=seed), "hbos": lambda: HBOS()}
    if method in M:
        return M[method]()
    if method == "dif":
        from pyod.models.dif import DIF
        return DIF(random_state=seed, device="cpu")
    import methods_t2  # our methods live in src/ad/methods_t2.py
    return methods_t2.make(method, seed, n_train)


def run_one(protocol, name, path, method, seed, max_n):
    f = os.path.join(OUT, protocol, name, f"{method}_s{seed}.json")
    if os.path.exists(f):
        return None
    d = np.load(path, allow_pickle=True)
    Xtr, ytr, Xte, yte = split(d["X"], d["y"].astype(int), protocol, seed, max_n)
    m = make(method, seed, len(Xtr))
    np.random.seed(seed)
    t0 = time.time(); m.fit(Xtr); t1 = time.time(); s = m.decision_function(Xte); t2 = time.time()
    s = np.nan_to_num(np.asarray(s, float), nan=0.0, posinf=1e12, neginf=-1e12)
    k = int(yte.sum()); top = np.argsort(-s)[:k]
    r = {"dataset": name, "method": method, "seed": seed, "protocol": protocol, "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
         "anom_test": k, "auc_roc": float(roc_auc_score(yte, s)), "auc_pr": float(average_precision_score(yte, s)),
         "p_at_k": float(yte[top].mean()), "fit_s": t1 - t0, "pred_s": t2 - t1, "max_n": max_n}
    os.makedirs(os.path.dirname(f), exist_ok=True)
    json.dump(r, open(f + ".tmp", "w")); os.replace(f + ".tmp", f)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", default="semi"); ap.add_argument("--methods", default="knn")
    ap.add_argument("--seeds", default="0-9"); ap.add_argument("--datasets", default="all"); ap.add_argument("--max_n", type=int, default=50000)
    a = ap.parse_args()
    lo, hi = (a.seeds.split("-") + [None])[:2]; seeds = range(int(lo), int(hi or lo) + 1)
    D = datasets(); names = list(D) if a.datasets == "all" else a.datasets.split(",")
    for name in names:
        for method in a.methods.split(","):
            for s in seeds:
                try:
                    r = run_one(a.protocol, name, D[name], method, s, a.max_n)
                    if r:
                        print(f"{name:18s} {method:10s} s{s} AUCROC={r['auc_roc']:.4f} AUCPR={r['auc_pr']:.4f} fit={r['fit_s']:.1f}s", flush=True)
                except Exception as e:  # logged, never hidden
                    print(f"FAIL {name} {method} s{s}: {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    main()
