"""plan_v5 report (topic 3): 5-seed TEST results vs GDAE Table 5 (literature/gdae_table5.csv) and vs our reproduced baselines.
Writes results/t3_test_table.csv, results/t3_stats.json, results/t3_RESULTS.md."""
import glob, json, os
import numpy as np, pandas as pd
from scipy.stats import ttest_1samp, ttest_ind_from_stats, ttest_rel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
R = pd.DataFrame([json.load(open(f)) for f in glob.glob("results_t3/*/*.json")])
R = R[(R.method.str.contains("r200000")) | (~R.method.str.match(r"^(kn|ck|hc)"))]
M = ["pr_auc", "macro_f1", "acc", "roc_auc", "fpr_test", "fit_s", "score_s"]
T = R.groupby(["data", "method"])[M].agg(["mean", "std", "count"]); T.to_csv("results/t3_test_table.csv")
G = pd.read_csv("literature/gdae_table5.csv"); P = "hc1_s_r200000"; out = {}; pv = []
for ds in sorted(R.data.unique()):
    r = R[R.data == ds].set_index(["method", "seed"]); o = {}
    if P not in r.index.get_level_values(0): continue
    ours = r.loc[P]
    for met in ["pr_auc", "macro_f1"]:
        x = ours[met].values
        for _, g in G[G.dataset == ds].iterrows():
            t1 = ttest_1samp(x, g[met]); t2 = ttest_ind_from_stats(x.mean(), x.std(ddof=1), len(x), g[met], g[met + "_sd"], 5, equal_var=False)
            o[f"{met} vs {g.method} (reported)"] = {"ours": round(x.mean(), 4), "ours_sd": round(x.std(ddof=1), 4), "theirs": g[met],
                                                    "diff": round(x.mean() - g[met], 4), "p_1samp": float(t1.pvalue), "p_welch": float(t2.pvalue)}
            pv.append((ds, f"{met} vs {g.method} (reported)", float(t2.pvalue)))
        for b in sorted(set(r.index.get_level_values(0)) - {P}):
            y = r.loc[b][met].reindex(ours.index).values
            if np.isnan(y).any() or len(y) < 2: continue
            t = ttest_rel(x, y); o[f"{met} vs {b} (ours)"] = {"ours": round(x.mean(), 4), "theirs": round(np.mean(y), 4), "diff": round(np.mean(x - y), 4), "p_paired": float(t.pvalue)}
            pv.append((ds, f"{met} vs {b} (ours)", float(t.pvalue)))
    out[ds] = o
# Holm over every comparison of the primary method in this plan
pv.sort(key=lambda t: t[2]); m = len(pv); run = 0.0
for i, (ds, k, p) in enumerate(pv):
    run = max(run, min(1.0, (m - i) * p)); out[ds][k]["p_holm"] = run
json.dump(out, open("results/t3_stats.json", "w"), indent=1)
with open("results/t3_RESULTS.md", "w") as f:
    for ds in out:
        f.write(f"## {ds}\n| comparison | ours | theirs | diff | Holm p |\n|---|---|---|---|---|\n")
        for k, v in out[ds].items(): f.write(f"| {k} | {v['ours']} | {v['theirs']} | {v['diff']:+.4f} | {v['p_holm']:.2g} |\n")
print(open("results/t3_RESULTS.md").read())
print(T.xs("mean", axis=1, level=1)[["pr_auc", "macro_f1", "acc", "fpr_test"]].round(4).to_string())
