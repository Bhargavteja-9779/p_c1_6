"""Per-attack flag rate (share of each attack class above the benign-only 0.3 % FPR threshold), mean over the 5 TEST seeds."""
import glob, json, os
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rows = []
for f in glob.glob("results_t3/*/*.json"):
    r = json.load(open(f))
    if r["method"] not in ("knn1_r200000", "ck1_L_r200000", "hc1_s_r200000", "iforest", "hbos"): continue
    for a, v in r["per_class_flag_rate"].items(): rows.append((r["data"], r["method"], a, v))
d = pd.DataFrame(rows, columns=["data", "method", "attack", "flag"]).groupby(["data", "attack", "method"]).flag.mean().unstack()
d.to_csv("results/t3_per_attack.csv"); print((d * 100).round(1).to_string())
