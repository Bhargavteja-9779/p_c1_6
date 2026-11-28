"""Revision experiments (review round 1), seed 42, TEST split, frozen settings (ref 200k, k=1, c=1e4):
saves per-flow scores of knn1 (raw), ck1_L (log) and HoCo-kNN, with honest end-to-end timing (context + reference + index + scoring),
plus 'HoCo-kNN, half context': test-flow context computed from a random 50 % of test flows only (split-size dependence).
Output: results/t3_scores_<data>_s42.npz and results/t3_timing_<data>_s42.json. Usage: python scripts/t3_scores.py DATA"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import nfv2_prep, nfv2_bench as B, nfv2_methods as M
data = sys.argv[1]; seed = 42; ref = 200000
d = dict(np.load(nfv2_prep.make(data, seed))); vb = d["yva"] == 0
L = lambda X: np.log1p(1e4 * X.astype(np.float64)) / np.log1p(1e4)
out, timing = {"y": d["yte"], "att": d["ate"], "src": d["ste"]}, {}
def go(name, build_tr, build_va, build_te):
    t0 = time.time(); Ztr = build_tr(); R = B.ref_subsample(Ztr, ref, seed); t1 = time.time()
    sv = B.knn_scores(R, build_va(), 1); thr = float(np.quantile(sv, 1 - B.FPR)); t2 = time.time()
    Zte = build_te(); st = B.knn_scores(R, Zte, 1); t3 = time.time()
    out[name] = st; out[name + "_thr"] = thr
    timing[name] = {"build_s": t1 - t0, "threshold_s": t2 - t1, "test_score_s": t3 - t2, "n_test": int(len(st)), "us_per_test_flow": 1e6 * (t3 - t2) / len(st)}
    print(name, timing[name], flush=True)
go("knn1", lambda: d["Xtr"].astype(np.float64), lambda: d["Xva"][vb].astype(np.float64), lambda: d["Xte"].astype(np.float64))
go("ck1_L", lambda: L(d["Xtr"]), lambda: L(d["Xva"][vb]), lambda: L(d["Xte"]))
C = lambda X, s: M.context(X.astype(np.float64), s, s, parts="s")
Cva = C(d["Xva"], d["sva"])[vb]
go("hoco", lambda: C(d["Xtr"], d["str_"]), lambda: Cva, lambda: C(d["Xte"], d["ste"]))
def half_ctx():  # context of every test flow from a random half H of the test flows (own flow excluded unless in H)
    rng = np.random.default_rng(seed + 1); H = rng.random(len(d["ste"])) < 0.5; Lx = L(d["Xte"]); s = d["ste"]
    n = s.max() + 1; S = np.zeros((n, Lx.shape[1])); np.add.at(S, s[H], Lx[H]); cnt = np.bincount(s[H], minlength=n).astype(float)
    ctx = np.where(cnt[s][:, None] > 0, S[s] / np.maximum(cnt[s], 1)[:, None], Lx)
    return np.hstack([Lx, ctx])
go("hoco_halfctx", lambda: C(d["Xtr"], d["str_"]), lambda: Cva, half_ctx)
np.savez_compressed(f"results/t3_scores_{data}_s42.npz", **out); json.dump(timing, open(f"results/t3_timing_{data}_s42.json", "w"), indent=1)
