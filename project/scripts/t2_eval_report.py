"""plan_v4 EVAL report: our frozen methods + reproduced baselines vs HF-DIF's reported per-dataset numbers (literature/hfdif_tables.csv).
Writes results/t2_eval_table.csv and results/t2_eval_stats.json. Only datasets where every compared column exists are averaged."""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, ttest_rel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sys.path.insert(0, "src/ad"); import bench
R = pd.DataFrame([json.load(open(f)) for n in bench.HFDIF20 for f in glob.glob(f"results_t2/transd/{n}/*.json")])
R["ds"] = R.dataset.str.lower()
ours = ["scknn_F0.1", "fuse_F0.1_w0.5", "iforest", "knn", "lof", "ecod", "copod", "hbos", "pca", "loda", "dif"]
out = {}
H = pd.read_csv("literature/hfdif_tables.csv"); H["ds"] = H.dataset.str.lower(); H = H[H.ds != "average"]
for met in ["auc_roc", "auc_pr"]:
    g = R.groupby(["ds", "method"])[met].mean().unstack() * 100
    h = H[H.metric == met].pivot(index="ds", columns="method", values="mean").astype(float).add_prefix("paper:")
    T = g[[c for c in ours if c in g]].join(h, how="inner")
    T.to_csv(f"results/t2_eval_{met}.csv")
    S = {}
    for cols in [["scknn_F0.1", "iforest"], ["scknn_F0.1", "knn"], ["scknn_F0.1", "paper:HF-DIF"], ["fuse_F0.1_w0.5", "iforest"],
                 ["fuse_F0.1_w0.5", "paper:HF-DIF"], ["iforest", "paper:iForest"], ["ecod", "paper:ECOD"], ["dif", "paper:DIF"]]:
        if not all(c in T for c in cols): continue
        d = T[cols].dropna(); diff = d[cols[0]] - d[cols[1]]
        S[f"{cols[0]} vs {cols[1]}"] = {"n_sets": int(len(d)), "mean_a": round(d[cols[0]].mean(), 2), "mean_b": round(d[cols[1]].mean(), 2),
            "diff": round(diff.mean(), 2), "wins": int((diff > 0.5).sum()), "losses": int((diff < -0.5).sum()),
            "wilcoxon_p": float(wilcoxon(diff).pvalue) if len(d) > 5 and diff.abs().sum() > 0 else None,
            "ttest_p": float(ttest_rel(d[cols[0]], d[cols[1]]).pvalue) if len(d) > 2 else None}
    out[met] = S
json.dump(out, open("results/t2_eval_stats.json", "w"), indent=1)
for met, S in out.items():
    print("==", met)
    for k, v in S.items(): print(f"{k:34s} n={v['n_sets']:2d} {v['mean_a']:6.2f} vs {v['mean_b']:6.2f} diff={v['diff']:+6.2f} W/L={v['wins']}/{v['losses']} pW={v['wilcoxon_p'] and round(v['wilcoxon_p'],4)}")
