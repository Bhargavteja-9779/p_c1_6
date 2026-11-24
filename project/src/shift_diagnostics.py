#!/usr/bin/env python3
"""H2 diagnostic (journal entry 07): per-feature-group domain separability, measured separately on BENIGN and on ATTACK flows.
For each target t: target flows (t random_train) vs pooled source flows (other 3 random_train), using only the group's
features; LightGBM 2-fold CV AUC, reported as Gini=|2AUC-1|. Uses train pools only; no target VAL/TEST data.
Output: results/diagnostics/shift_by_group.json. Idempotent (overwrites its own output only)."""
import os, sys, json
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nids
N, SEED = 20000, 0
GROUPS = dict(nids.GROUPS)

def gini(X, y):
    p = np.zeros(len(y))
    for tr, te in StratifiedKFold(2, shuffle=True, random_state=SEED).split(X, y):
        m = lgb.LGBMClassifier(n_estimators=200, num_leaves=31, learning_rate=0.1, verbose=-1, n_jobs=2, random_state=SEED)
        m.fit(X[tr], y[tr]); p[te] = m.predict_proba(X[te])[:, 1]
    return float(abs(2 * roc_auc_score(y, p) - 1))

def main():
    pools = {d: nids.load(d, "random", "train") for d in nids.DATASETS}
    fc = nids.feature_cols(pools["UNSW"])
    GROUPS["all"] = fc
    out = {"note": __doc__, "n_per_side": N, "results": {}}
    for t in nids.DATASETS:
        for cls, lab in (("benign", 0), ("attack", 1)):
            tgt = pools[t][pools[t].Label == lab]
            src = pd.concat([pools[s][pools[s].Label == lab] for s in nids.DATASETS if s != t])
            tgt, src = nids.subsample(tgt, N, SEED), nids.subsample(src, N, SEED)
            for g, cols in GROUPS.items():
                X = np.r_[tgt[cols].to_numpy(np.float32), src[cols].to_numpy(np.float32)]
                y = np.r_[np.ones(len(tgt)), np.zeros(len(src))]
                v = gini(X, y)
                out["results"].setdefault(t, {}).setdefault(cls, {})[g] = {"gini": v, "n_target": len(tgt), "n_source": len(src)}
                print(t, cls, g, round(v, 4), len(tgt), len(src), flush=True)
    json.dump(out, open(os.path.join(nids.ROOT, "results/diagnostics/shift_by_group.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
