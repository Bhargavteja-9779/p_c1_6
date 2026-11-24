"""Summarise results_t2/<protocol> over a dataset list: mean AUC-ROC / AUC-PR per method (seed-averaged first), mean rank, n sets."""
import glob, json, os, sys
import pandas as pd
proto = sys.argv[1]; sets = sys.argv[2]; methods = sys.argv[3].split(",") if len(sys.argv) > 3 else None
root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results_t2", proto)
sys.path.insert(0, os.path.join(os.path.dirname(root), "..", "src", "ad"))
if sets == "dev": names = open(os.path.join(root, "..", "..", "state", "dev_sets.txt")).read().strip().split(",")
elif sets == "hfdif20":
    import bench; names = bench.HFDIF20
else: names = sets.split(",")
R = [json.load(open(f)) for n in names for f in glob.glob(os.path.join(root, n, "*.json"))]
d = pd.DataFrame(R)
if methods: d = d[d.method.isin(methods)]
g = d.groupby(["dataset", "method"])[["auc_roc", "auc_pr"]].mean().reset_index()
full = g.groupby("method").dataset.nunique(); keep = full[full == len(names)].index
g = g[g.method.isin(keep)]
roc = g.pivot(index="dataset", columns="method", values="auc_roc")
pr = g.pivot(index="dataset", columns="method", values="auc_pr")
out = pd.DataFrame({"AUCROC": roc.mean() * 100, "AUCPR": pr.mean() * 100, "rankROC": roc.rank(axis=1, ascending=False).mean(), "n": roc.count()})
print(out.sort_values("AUCROC", ascending=False).round(2).to_string())
if "-v" in sys.argv: print((roc * 100).round(1).to_string())
