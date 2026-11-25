#!/usr/bin/env python3
"""Topic-2 DEV/HOLDOUT summary: mean AUROC/AUPR (x100) over datasets (each dataset = mean over seeds),
paired Wilcoxon over datasets vs a reference method, Holm over the compared methods.
Only datasets where BOTH methods have all requested seeds are paired (counts reported).
Usage: python scripts/t2_summary.py --split dev --seeds 0-2 --ref knn [--methods a,b,...] [--out results_t2/summary_dev.json]
"""
import os, json, argparse, glob
import numpy as np
from scipy import stats

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def holm(p):
    o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (m - r) * p[i])); adj[i] = run
    return adj


def table(proto, D, seeds, metric):
    out = {}
    for p in glob.glob(os.path.join(R, "results_t2", proto, "*", "*.json")):
        ds = p.split(os.sep)[-2]
        if ds not in D: continue
        r = json.load(open(p))
        if r["seed"] in seeds:
            out.setdefault(r["method"], {}).setdefault(ds, {})[r["seed"]] = r[metric]
    return {m: {d: 100 * np.mean(list(v.values())) for d, v in dd.items() if len(v) == len(seeds)} for m, dd in out.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--split", default="dev"); ap.add_argument("--seeds", default="0-2")
    ap.add_argument("--ref", default="knn"); ap.add_argument("--methods", default=None); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lo, hi = map(int, a.seeds.split("-")); seeds = set(range(lo, hi + 1))
    D = json.load(open(os.path.join(R, "experiments", "t2_dataset_split.json")))[a.split]
    res = {}
    for proto in ("semi", "unsup"):
        res[proto] = {}
        for metric in ("auc_roc", "auc_pr"):
            T = table(proto, D, seeds, metric)
            meths = a.methods.split(",") if a.methods else sorted(T)
            rows = []
            for m in meths:
                if m not in T: continue
                common = sorted(set(T[m]) & set(T.get(a.ref, {})))
                full = len(T[m]) == len(D)
                x = np.array([T[m][d] for d in common]); y = np.array([T[a.ref][d] for d in common])
                p = stats.wilcoxon(x, y).pvalue if m != a.ref and len(common) > 5 and np.any(x != y) else 1.0
                rows.append({"method": m, "n_datasets": len(T[m]), "complete": full, "mean": float(np.mean(list(T[m].values()))),
                             "paired_n": len(common), "diff_vs_ref": float((x - y).mean()) if len(common) else None, "p_wilcoxon": float(p)})
            adj = holm(np.array([r["p_wilcoxon"] for r in rows])) if rows else []
            for r, q in zip(rows, adj): r["p_holm"] = float(q)
            res[proto][metric] = sorted(rows, key=lambda r: -r["mean"])
            print(f"\n== {proto} {metric} ({a.split}, seeds {a.seeds}, ref {a.ref}, {len(D)} datasets)")
            for r in res[proto][metric]:
                print(f"{r['method']:10s} {r['mean']:6.2f}  n={r['n_datasets']:2d}{'' if r['complete'] else '*'}  Δref={r['diff_vs_ref'] if r['diff_vs_ref'] is not None else float('nan'):+6.2f}  p={r['p_wilcoxon']:.3g}  pHolm={r['p_holm']:.3g}")
    if a.out:
        json.dump(res, open(os.path.join(R, a.out), "w"), indent=1)


if __name__ == "__main__":
    main()
