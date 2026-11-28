"""Shortcut controls for host context (review R1 concern 1), seed 42 TEST split, frozen settings.
(1) host-novelty baseline: score = [source IP never seen in benign training] + tiny tie-break by the log-kNN score;
(2) host-label permutation: source-host labels shuffled within each partition (same group sizes, random membership), context recomputed;
(3) mixed-host subset: PR-AUC / flag rate on benign flows + attack flows whose source IP also appears in benign training.
Uses results/t3_scores_<data>_s42.npz. Output results/t3_controls_<data>.json"""
import json, os, sys
import numpy as np
from sklearn.metrics import average_precision_score, f1_score
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import nfv2_prep, nfv2_bench as B, nfv2_methods as M
data = sys.argv[1]; seed = 42
S = dict(np.load(f"results/t3_scores_{data}_s42.npz")); d = dict(np.load(nfv2_prep.make(data, seed))); y = S["y"]
seen_tr = set(np.unique(d["str_"])); seen = np.array([s in seen_tr for s in S["src"]])
res = {}
def ev(name, s, mask=None, thr=None):
    m = np.ones(len(y), bool) if mask is None else mask
    r = {"pr_auc": float(average_precision_score(y[m], s[m]))}
    if thr is not None: p = s[m] > thr; r["macro_f1"] = float(f1_score(y[m], p, average="macro")); r["attack_flag_rate"] = float(p[y[m] == 1].mean()); r["benign_fpr"] = float(p[y[m] == 0].mean())
    res[name] = r; print(name, r, flush=True)
for k in ["knn1", "ck1_L", "hoco", "hoco_halfctx"]: ev(k, S[k], thr=float(S[k + "_thr"]))
rk = (np.argsort(np.argsort(S["ck1_L"])) / len(y)); ev("host_novelty", (~seen).astype(float) + 1e-3 * rk)
mixed = (y == 0) | seen
for k in ["knn1", "ck1_L", "hoco"]: ev(k + "@mixed_hosts", S[k], mixed, float(S[k + "_thr"]))
res["n_attack_mixed_hosts"] = int((mixed & (y == 1)).sum()); res["n_attack_all"] = int((y == 1).sum())
# permutation control: shuffle host labels within each partition
rng = np.random.default_rng(7); P = lambda s: rng.permutation(s)
C = lambda X, s: M.context(X.astype(np.float64), s, s, parts="s"); vb = d["yva"] == 0
R = B.ref_subsample(C(d["Xtr"], P(d["str_"])), 200000, seed)
thr = float(np.quantile(B.knn_scores(R, C(d["Xva"], P(d["sva"]))[vb], 1), 1 - B.FPR))
ev("hoco_permuted_hosts", B.knn_scores(R, C(d["Xte"], P(d["ste"])), 1), thr=thr)
json.dump(res, open(f"results/t3_controls_{data}.json", "w"), indent=1)
