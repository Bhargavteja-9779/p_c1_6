#!/usr/bin/env python3
"""Section 12 report: results/metrics.json, results/statistics.json, tables/*.md, figures/*.png, results/RESULTS_SUMMARY.md.
Reads results/raw_results.csv (full mode only). Idempotent: regenerates outputs from the CSV each time.
Primary metric (pre-registered, D11): target macro-F1 at source-val threshold, mean over targets UNSW, TON, CIC.
Statistics: for each method vs the reference (best baseline by primary mean), paired over (target, seed) units on
the primary targets; paired t-test + Wilcoxon signed-rank; Cohen's dz; bootstrap 95% CI of mean diff; Holm over all
comparisons in the same family (exp)."""
import os, json, sys
import numpy as np, pandas as pd
from scipy import stats
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARY_T = ["UNSW", "TON", "CIC"]
BASELINES = ["lgbm", "xgb", "rf", "lr", "mlp", "dann", "coral"]
METRICS = ["macro_f1", "auroc", "prauc", "f1_attack", "fpr", "tpr", "bal_acc"]

def ci95(x):
    x = np.asarray(x, float)
    if len(x) < 2: return [float("nan")] * 2
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return [float(x.mean() - h), float(x.mean() + h)]

def boot_ci(d, B=10000, seed=0):
    rng = np.random.default_rng(seed); d = np.asarray(d, float)
    m = rng.choice(d, (B, len(d))).mean(1)
    return [float(np.quantile(m, .025)), float(np.quantile(m, .975))]

def holm(ps):
    ps = np.asarray(ps, float); o = np.argsort(ps); adj = np.empty_like(ps); run = 0
    for r, i in enumerate(o):
        run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1.0, run)
    return adj

def main(csv=os.path.join(R, "results", "raw_results.csv")):
    df = pd.read_csv(csv)
    df = df[df.job_id.str.startswith("E")]
    df["variant"] = df.job_id.str.replace(r"_(UNSW|TON|CIC|BOT)_s\d+$", "", regex=True)
    metrics = {}
    for (exp, var, tgt), g in df.groupby(["exp", "variant", "target"]):
        metrics.setdefault(exp, {}).setdefault(var, {})[tgt] = {
            m: {"mean": float(g[m].mean()), "std": float(g[m].std(ddof=1)) if len(g) > 1 else 0.0,
                "ci95": ci95(g[m]), "n": int(len(g))} for m in METRICS if m in g}
    # primary per variant: mean over primary targets, per seed
    prim = df[df.target.isin(PRIMARY_T)].pivot_table(index=["variant", "seed"], columns="target", values="macro_f1")
    prim = prim.dropna()
    prim_mean = prim.mean(1).groupby("variant").agg(["mean", "std", "count"])
    for v, r in prim_mean.iterrows():
        e = v.split("_")[0]
        metrics.setdefault(e, {}).setdefault(v, {})["PRIMARY_mean_UNSW_TON_CIC"] = {
            "mean": float(r["mean"]), "std": float(r["std"]) if r["count"] > 1 else 0.0, "n_seeds": int(r["count"])}
    json.dump(metrics, open(os.path.join(R, "results", "metrics.json"), "w"), indent=1)

    # statistics: E1 lodo variants vs best baseline
    st = {}
    e1 = df[(df.exp == "E1") & df.target.isin(PRIMARY_T)]
    long = e1.set_index(["variant", "target", "seed"]).macro_f1
    base_vars = [f"E1_lodo_{b}" for b in BASELINES if f"E1_lodo_{b}" in prim_mean.index]
    if base_vars:
        ref = max(base_vars, key=lambda v: prim_mean.loc[v, "mean"])
        st["reference_best_baseline"] = ref
        comps = []
        for v in sorted(set(e1.variant)):
            if v == ref: continue
            a, b = long.xs(v, level=0), long.xs(ref, level=0)
            idx = a.index.intersection(b.index)
            if len(idx) < 3: continue
            d = (a[idx] - b[idx]).values
            t = stats.ttest_rel(a[idx], b[idx]).pvalue
            try: w = stats.wilcoxon(d).pvalue
            except Exception: w = float("nan")
            comps.append({"variant": v, "n_pairs": int(len(idx)), "mean_diff": float(d.mean()),
                          "dz": float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else float("nan"),
                          "boot_ci95": boot_ci(d), "p_t": float(t), "p_wilcoxon": float(w)})
        if comps:
            for c, a in zip(comps, holm([c["p_t"] for c in comps])): c["p_t_holm"] = float(a)
        st["E1_vs_reference"] = comps
        st["note"] = ("Exploration statistics on TARGET VAL with seeds 0-2; units = (target, seed) pairs over UNSW/TON/CIC. "
                      "Not confirmatory (Rule 5/8): confirmation needs frozen config on SEEDS_CONFIRM and target TEST.")
    json.dump(st, open(os.path.join(R, "results", "statistics.json"), "w"), indent=1)

    # tables
    os.makedirs(os.path.join(R, "tables"), exist_ok=True)
    lines = []
    for exp in sorted(set(df.exp)):
        sub = df[df.exp == exp]
        t = sub.groupby(["variant", "target"]).macro_f1.agg(["mean", "std"]).unstack("target")
        tab = t["mean"].round(3).astype(str) + " ± " + t["std"].round(3).astype(str)
        if exp == "E1" or exp in ("E2", "E3"):
            tab["PRIMARY(U/T/C)"] = [f'{prim_mean.loc[v,"mean"]:.3f} ± {prim_mean.loc[v,"std"]:.3f}' if v in prim_mean.index else "" for v in tab.index]
        md = tab.to_markdown()
        open(os.path.join(R, "tables", f"{exp}_macro_f1.md"), "w").write(f"# {exp}: macro-F1 (mean ± std over seeds)\n\n{md}\n")
        lines += [f"## {exp} macro-F1", "", md, ""]
    for m in ["auroc", "fpr"]:
        t = df[df.exp == "E1"].groupby(["variant", "target"])[m].mean().unstack("target").round(3)
        open(os.path.join(R, "tables", f"E1_{m}.md"), "w").write(f"# E1: {m} (mean over seeds)\n\n{t.to_markdown()}\n")
        lines += [f"## E1 {m}", "", t.to_markdown(), ""]
    # figure
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        os.makedirs(os.path.join(R, "figures"), exist_ok=True)
        e1m = prim_mean[prim_mean.index.str.startswith("E1_")].sort_values("mean")
        fig, ax = plt.subplots(figsize=(7, 0.35 * len(e1m) + 1))
        ax.barh([v.replace("E1_lodo_", "") for v in e1m.index], e1m["mean"], xerr=e1m["std"], color="#4C78A8")
        ax.set_xlabel("LODO macro-F1 (mean over UNSW/TON/CIC targets; ± std over seeds)")
        fig.tight_layout(); fig.savefig(os.path.join(R, "figures", "E1_primary.png"), dpi=150)
    except Exception as e:
        print("figure failed:", e)
    s = ["# RESULTS SUMMARY (auto-generated by scripts/final_report.py)", "",
         f"Source: results/raw_results.csv ({len(df)} E-rows). Exploration numbers on target VAL; not confirmatory.", "",
         "## Primary metric per variant (mean over UNSW/TON/CIC targets, ± std over seeds)", "",
         prim_mean.round(4).to_markdown(), "", "## Statistics vs best baseline", "",
         "```json", json.dumps(st, indent=1), "```", ""] + lines
    open(os.path.join(R, "results", "RESULTS_SUMMARY.md"), "w").write("\n".join(s))
    print("report written")

if __name__ == "__main__":
    main(*(sys.argv[1:2]))
