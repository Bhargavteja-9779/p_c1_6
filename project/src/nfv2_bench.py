"""Topic 3 benchmark: one-class NetFlow-v2 detectors (D39). Score = higher is more anomalous.
Threshold: (1 - FPR_target) quantile of scores on BENIGN validation flows (no attack labels; FPR_target = 0.003 as GDAE's EVT target).
Metrics on test: PR-AUC (average precision), ROC-AUC, Macro-F1 and ACC at that threshold, plus per-attack recall.
Results: results_t3/<dataset>/<method>_s<seed>.json (atomic; skipped if present).
Usage: python src/nfv2_bench.py --data NF-UNSW-NB15-v2 --methods knn1,iforest --seeds 42,123,456,789,1234 [--ref 200000]"""
import argparse, json, os, sys, time
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, accuracy_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nfv2_prep
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "results_t3")
FPR = 0.003


def ref_subsample(X, m, seed):
    U = np.unique(X, axis=0)  # duplicates add nothing to a nearest-neighbour reference
    if len(U) > m: U = U[np.random.default_rng(seed).choice(len(U), m, replace=False)]
    return U


def knn_scores(R, Q, k):
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=k, algorithm="brute", n_jobs=1).fit(R)
    out = np.empty(len(Q))
    for b in range(0, len(Q), 20000):
        d, _ = nn.kneighbors(Q[b:b + 20000]); out[b:b + 20000] = d.mean(1)
    return out


def detector(method, Xtr, seed, ref):
    if method.startswith("knn"):
        k = int(method[3:] or 1); R = ref_subsample(Xtr, ref, seed); return lambda Q: knn_scores(R, Q, k)
    if method == "iforest":
        from sklearn.ensemble import IsolationForest
        m = IsolationForest(n_estimators=200, max_samples=256, random_state=seed, n_jobs=1).fit(Xtr); return lambda Q: -m.score_samples(Q)
    if method == "hbos":
        from pyod.models.hbos import HBOS
        m = HBOS().fit(Xtr); return m.decision_function
    if method == "pca":
        from sklearn.decomposition import PCA
        p = PCA(0.99, random_state=seed).fit(Xtr); return lambda Q: ((Q - p.inverse_transform(p.transform(Q))) ** 2).sum(1)
    if method == "ae":
        from sklearn.neural_network import MLPRegressor
        S = Xtr[np.random.default_rng(seed).choice(len(Xtr), min(200000, len(Xtr)), replace=False)]
        m = MLPRegressor((64, 16, 64), max_iter=30, random_state=seed).fit(S, S); return lambda Q: ((Q - m.predict(Q)) ** 2).sum(1)
    import nfv2_methods
    return nfv2_methods.make(method, Xtr, seed, ref)


def run(data, method, seed, ref, ev="test"):
    tag = f"{method}_r{ref}" if method.startswith("knn") or method.startswith("ck") else method
    f = os.path.join(OUT + ("_val" if ev == "val" else ""), data, f"{tag}_s{seed}.json")
    if os.path.exists(f): return None
    d = np.load(nfv2_prep.make(data, seed)); Xtr = d["Xtr"].astype(np.float64)
    import nfv2_methods; nfv2_methods.FEATS = [str(x) for x in d["feats"]]
    t0 = time.time(); score = detector(method, Xtr, seed, ref); t1 = time.time()
    if ev == "val":  # DESIGN mode (D40): split validation in two halves; threshold from benign half A, metrics on half B
        h = np.random.default_rng(seed + 7).random(len(d["yva"])) < 0.5
        va_b = d["Xva"][h & (d["yva"] == 0)].astype(np.float64); XE, y, att = d["Xva"][~h], d["yva"][~h], d["ava"][~h]
    else:
        va_b = d["Xva"][d["yva"] == 0].astype(np.float64); XE, y, att = d["Xte"], d["yte"], d["ate"]
    sv = score(va_b); thr = np.quantile(sv, 1 - FPR)
    st = score(XE.astype(np.float64)); t2 = time.time(); pred = (st > thr).astype(int)
    rec = {a: float(pred[att == a].mean()) for a in np.unique(att)}
    r = {"data": data, "method": tag, "seed": seed, "ref": ref, "pr_auc": float(average_precision_score(y, st)), "roc_auc": float(roc_auc_score(y, st)),
         "macro_f1": float(f1_score(y, pred, average="macro")), "acc": float(accuracy_score(y, pred)), "fpr_test": float(pred[y == 0].mean()),
         "eval": ev, "recall_attack": float(pred[y == 1].mean()), "per_class_flag_rate": rec, "fit_s": t1 - t0, "score_s": t2 - t1, "n_test": int(len(y))}
    os.makedirs(os.path.dirname(f), exist_ok=True); json.dump(r, open(f + ".tmp", "w"), indent=1); os.replace(f + ".tmp", f)
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data"); ap.add_argument("--methods"); ap.add_argument("--seeds", default="42")
    ap.add_argument("--ref", type=int, default=200000); ap.add_argument("--eval", default="test"); a = ap.parse_args()
    for m in a.methods.split(","):
        for s in map(int, a.seeds.split(",")):
            try:
                r = run(a.data, m, s, a.ref, a.eval)
                if r: print(f"{a.data} {m:10s} s{s} PR-AUC={r['pr_auc']:.4f} ROC={r['roc_auc']:.4f} F1={r['macro_f1']:.4f} ACC={r['acc']:.4f} FPR={r['fpr_test']:.4f} t={r['fit_s']+r['score_s']:.0f}s", flush=True)
            except Exception as e:
                print(f"FAIL {a.data} {m} s{s}: {type(e).__name__}: {e}", flush=True)
