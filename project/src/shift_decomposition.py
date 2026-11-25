"""E7 — Shift decomposition (diagnostic, exploration split only).

For each LODO target T and seed s, train the tuned LightGBM on the pooled sources and score:
  SB = source-val benign, SA = source-val attack, TB = target-val benign, TA = target-val attack.
  AUC_src  = AUC(SB vs SA)          in-distribution ranking quality
  AUC_tgt  = AUC(TB vs TA)          cross-network ranking quality (what LODO reports)
  AUC_benign_shift = AUC(TB vs SA)  can the model still separate NEW benign from KNOWN attacks?
  AUC_attack_shift = AUC(SB vs TA)  can the model still separate KNOWN benign from NEW attacks?
Plus at the source-val threshold: FPR on SB vs TB, TPR on SA vs TA.
If AUC_benign_shift << AUC_src while AUC_attack_shift stays high, the collapse is benign-side (new normal
traffic looks attack-like); and vice versa. Optionally repeats with feature groups removed (--groups).
Writes results/E7/<target>_s<seed>[_<variant>].json  (idempotent).
"""
import os, sys, json, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nids, run_job
from sklearn.metrics import roc_auc_score

R = nids.ROOT


def auc(neg, pos):
    if len(neg) < 5 or len(pos) < 5:
        return float("nan")
    return float(roc_auc_score(np.r_[np.zeros(len(neg)), np.ones(len(pos))], np.r_[neg, pos]))


def one(target, seed, method="lgbm", tau=None):
    tag = method.replace("+", "-") + (f"_t{tau}" if tau else "")
    out = os.path.join(R, "results", "E7", f"{target}_s{seed}_{tag}.json")
    if os.path.exists(out):
        return json.load(open(out))
    spec = {"job_id": f"E7_{target}_{seed}_{tag}", "protocol": "lodo", "target": target, "method": method, "seed": seed,
            "n_per_source": 100000, "n_val_per_source": 60000, "eval_split": "val"}
    if tau: spec["tau"] = tau
    cfg = json.load(open(os.path.join(R, "results", f"tune_lodo_lgbm_{target}.json")))["best_cfg"]
    tr, va, te = run_job.assemble(spec, seed)
    cols = [c for c in nids.feature_cols(tr) if c != "_env"]
    Xtr, Xva, Xte, use, info, order = run_job.treat(spec, cfg, tr, va, te, cols)
    ytr = tr.Label.to_numpy() if order is None else tr.Label.to_numpy()[order]
    m = nids.make_model(method, cfg, seed).fit(Xtr, ytr)
    pva, pte = m.predict_proba(Xva)[:, 1], m.predict_proba(Xte)[:, 1]
    yva, yte = va.Label.to_numpy(), te.Label.to_numpy()
    thr, _ = nids.best_threshold(yva, pva)
    SB, SA, TB, TA = pva[yva == 0], pva[yva == 1], pte[yte == 0], pte[yte == 1]
    res = {"target": target, "seed": seed, "method": method, "tau": tau, "n_features": len(use),
           "AUC_src": auc(SB, SA), "AUC_tgt": auc(TB, TA), "AUC_benign_shift": auc(TB, SA), "AUC_attack_shift": auc(SB, TA),
           "FPR_src": float((SB >= thr).mean()), "FPR_tgt": float((TB >= thr).mean()) if len(TB) else float("nan"),
           "TPR_src": float((SA >= thr).mean()), "TPR_tgt": float((TA >= thr).mean()) if len(TA) else float("nan"),
           "threshold": thr, "n": {"SB": len(SB), "SA": len(SA), "TB": len(TB), "TA": len(TA)},
           # per-source-environment benign FPR (does one source's benign dominate?)
           "FPR_src_by_env": {e: float((pva[(va._env.to_numpy() == e) & (yva == 0)] >= thr).mean()) for e in va._env.unique()}}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out + ".tmp", "w"), indent=1); os.replace(out + ".tmp", out)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", default="0,1,2"); ap.add_argument("--method", default="lgbm")
    ap.add_argument("--targets", default="UNSW,TON,CIC,BOT"); ap.add_argument("--tau", type=float, default=None)
    a = ap.parse_args()
    for t in a.targets.split(","):
        for s in map(int, a.seeds.split(",")):
            r = one(t, s, a.method, a.tau)
            print(t, s, {k: round(v, 4) for k, v in r.items() if k.startswith(("AUC", "FPR_s", "FPR_t", "TPR"))}, flush=True)
