"""Automatic results report (Section 12). Reads ONLY result files; no training, no LLM.

Usage: python scripts/final_report.py [--results results] [--tag cycle1]
Writes results/metrics.json, results/statistics.json, tables/*.csv|md, figures/*.png,
results/RESULTS_SUMMARY.md. Safe to run any number of times (outputs are regenerated).

Definitions (pre-registered in plan_v1 / decisions D10-D11):
  arm      = job_id without the trailing _{TARGET}_s{SEED} (keeps tau / n variants apart)
  primary  = macro-F1 at the source-val threshold, averaged over targets UNSW, TON, CIC (per seed)
  tests    = paired over (target, seed) units of the PRIMARY targets: Wilcoxon signed-rank +
             paired t; effect = mean paired difference, Cohen's d_z, bootstrap 95% CI (10k, seed 0).
  Holm     = over every arm compared to the reference on the same evaluation data, plus the count
             of earlier variants in state/variants_tried.csv evaluated on the same data (rule 8).
"""
import argparse, json, os, re
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PRIMARY = ["UNSW", "TON", "CIC"]
METRICS = ["macro_f1", "auroc", "prauc", "f1_attack", "tpr", "fpr", "bal_acc", "src_val_macro_f1"]
ID = re.compile(r"^(?P<arm>.+)_(?P<t>UNSW|TON|CIC|BOT)_s(?P<s>\d+)$")


def ci95(x):
    x = np.asarray(x, float)
    if len(x) < 2:
        return [float(x.mean()) if len(x) else None] * 2
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return [float(x.mean() - h), float(x.mean() + h)]


def boot_ci(d, n=10000, seed=0):
    r = np.random.default_rng(seed)
    m = r.choice(d, (n, len(d)), replace=True).mean(1)
    return [float(np.quantile(m, .025)), float(np.quantile(m, .975))]


def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * ps[i])); adj[i] = run
    return adj


def load(results):
    p = os.path.join(ROOT, results, "raw_results.csv")
    df = pd.read_csv(p)
    df = df.drop_duplicates("job_id", keep="last")
    m = df.job_id.str.extract(ID)
    df["arm"] = m["arm"]
    return df[df.arm.notna()]


def md(df, floatfmt=4):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.{floatfmt}f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    a = ap.parse_args()
    R = os.path.join(ROOT, a.results); T = os.path.join(ROOT, "tables"); F = os.path.join(ROOT, "figures")
    for d in (T, F):
        os.makedirs(d, exist_ok=True)
    df = load(a.results)

    # ---------- per arm x target metrics
    metrics = {}
    rows = []
    for (arm, tgt), g in df.groupby(["arm", "target"]):
        e = {"n_seeds": int(len(g)), "seeds": sorted(int(s) for s in g.seed)}
        for k in METRICS:
            if k in g:
                v = g[k].astype(float).values
                e[k] = {"mean": float(v.mean()), "std": float(v.std(ddof=1)) if len(v) > 1 else 0.0, "ci95": ci95(v)}
        metrics.setdefault(arm, {})[tgt] = e
        rows.append({"arm": arm, "target": tgt, "n": len(g), "macro_f1": g.macro_f1.mean(),
                     "macro_f1_sd": g.macro_f1.std(ddof=1) if len(g) > 1 else 0.0,
                     "auroc": g.auroc.mean(), "fpr": g.fpr.mean(), "tpr": g.tpr.mean(),
                     "src_val_macro_f1": g.src_val_macro_f1.mean()})
    long = pd.DataFrame(rows)
    long.to_csv(os.path.join(T, "per_target.csv"), index=False)

    # ---------- primary metric per arm (only arms with all 3 primary targets for a seed)
    lodo = df[(df.protocol == "lodo") & (df.target.isin(PRIMARY))]
    piv = lodo.pivot_table(index=["arm", "seed"], columns="target", values="macro_f1")
    piv = piv.dropna(subset=[t for t in PRIMARY if t in piv.columns])
    prim = piv[PRIMARY].mean(axis=1).rename("primary").reset_index() if set(PRIMARY) <= set(piv.columns) else pd.DataFrame(columns=["arm", "seed", "primary"])
    summ = []
    for arm, g in prim.groupby("arm"):
        v = g.primary.values
        metrics.setdefault(arm, {})["PRIMARY_mean_UNSW_TON_CIC"] = {"n_seeds": len(v), "mean": float(v.mean()),
                                                                    "std": float(v.std(ddof=1)) if len(v) > 1 else 0.0, "ci95": ci95(v)}
        summ.append({"arm": arm, "n_seeds": len(v), "primary_macro_f1": v.mean(), "sd": v.std(ddof=1) if len(v) > 1 else 0.0})
    summ = pd.DataFrame(summ).sort_values("primary_macro_f1", ascending=False) if summ else pd.DataFrame()
    summ.to_csv(os.path.join(T, "primary.csv"), index=False)
    json.dump(metrics, open(os.path.join(R, "metrics.json"), "w"), indent=1)

    # ---------- paired tests: every LODO arm vs the best E1 baseline
    baselines = ["E1_lodo_" + m for m in ("lgbm", "xgb", "rf", "lr", "mlp", "dann", "coral")]
    st = {"definition": __doc__, "comparisons": []}
    units = lodo.set_index(["arm", "target", "seed"]).macro_f1
    bl = summ[summ.arm.isin(baselines)] if len(summ) else summ
    if len(bl):
        ref = bl.iloc[0].arm
        st["reference_best_baseline"] = ref
        n_prior = 0
        vt = os.path.join(ROOT, "state", "variants_tried.csv")
        if os.path.exists(vt):
            v = pd.read_csv(vt)
            n_prior = int((~v.outcome.astype(str).str.contains("smoke|pipeline", case=False)).sum())
        comps = []
        for arm in sorted(set(lodo.arm) - {ref}):
            try:
                a_ = units.loc[arm]; r_ = units.loc[ref]
            except KeyError:
                continue
            j = a_.to_frame("a").join(r_.to_frame("r"), how="inner")
            j = j[j.index.get_level_values(0).isin(PRIMARY)]
            if len(j) < 3:
                continue
            d = (j.a - j.r).values
            w = stats.wilcoxon(d) if np.any(d != 0) else None
            t = stats.ttest_rel(j.a, j.r)
            comps.append({"arm": arm, "vs": ref, "n_pairs": int(len(d)), "mean_diff": float(d.mean()),
                          "cohen_dz": float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else None,
                          "boot_ci95": boot_ci(d), "p_wilcoxon": float(w.pvalue) if w else 1.0,
                          "p_ttest": float(t.pvalue)})
        if comps:
            ps = np.array([c["p_wilcoxon"] for c in comps] + [1.0] * n_prior)  # prior variants as unknown (conservative)
            adj = holm(ps)
            for c, p in zip(comps, adj):
                c["p_holm"] = float(p)
        st["n_prior_variants_counted"] = n_prior
        st["comparisons"] = sorted(comps, key=lambda c: -c["mean_diff"])
    json.dump(st, open(os.path.join(R, "statistics.json"), "w"), indent=1)

    # ---------- tables
    tab_md = {}
    if len(long):
        w = long[long.arm.str.startswith("E1_lodo")].pivot_table(index="arm", columns="target", values="macro_f1")
        w.reset_index().to_csv(os.path.join(T, "E1_lodo_macro_f1.csv"), index=False)
        tab_md["E1 LODO macro-F1 (target val, mean over seeds)"] = md(w.reset_index())
        idd = long[long.arm.str.startswith("E4")].pivot_table(index="arm", columns="target", values="macro_f1")
        if len(idd):
            tab_md["E4 in-distribution macro-F1"] = md(idd.reset_index())
        e2 = long[long.arm.str.startswith("E2") | (long.arm == "E1_lodo_lgbm")].pivot_table(index="arm", columns="target", values="macro_f1")
        if len(e2):
            tab_md["E2 group ablation (LightGBM) macro-F1"] = md(e2.reset_index())
        e3 = long[long.arm.str.startswith("E3")].pivot_table(index="arm", columns="target", values="macro_f1")
        if len(e3):
            tab_md["E3 reduced source data macro-F1"] = md(e3.reset_index())
        for k, v in tab_md.items():
            open(os.path.join(T, re.sub(r"\W+", "_", k.split("(")[0].strip()) + ".md"), "w").write(f"## {k}\n\n{v}\n")

    # ---------- figure
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        if len(summ):
            s = summ.sort_values("primary_macro_f1")
            fig, ax = plt.subplots(figsize=(7, max(3, 0.28 * len(s))))
            ax.barh(s.arm, s.primary_macro_f1, xerr=s.sd, color="#4C72B0")
            ax.set_xlabel("macro-F1 (mean of UNSW/TON/CIC targets, target val)"); ax.set_xlim(0, 1)
            fig.tight_layout(); fig.savefig(os.path.join(F, "primary_by_arm.png"), dpi=150); plt.close(fig)
    except Exception as e:  # figure is optional
        print("figure skipped:", e)

    # ---------- summary
    q = {}
    qp = os.path.join(ROOT, "state", "queue.json")
    if os.path.exists(qp):
        for j in json.load(open(qp)).values():
            q[j.get("status")] = q.get(j.get("status"), 0) + 1
    L = ["# RESULTS SUMMARY (auto-generated by scripts/final_report.py — numbers from result files only)", "",
         f"Results dir: `{a.results}/` — {len(df)} result rows. Queue status: {q}", "",
         "Evaluation split for all exploration runs: TARGET **validation** pool (test pool untouched; D9).", "",
         "## Primary metric (macro-F1, mean over UNSW/TON/CIC targets)", "",
         md(summ) if len(summ) else "(no complete arms yet)", ""]
    if st.get("comparisons"):
        L += [f"## Paired comparisons vs best baseline `{st['reference_best_baseline']}` "
              f"(Holm over {len(st['comparisons'])} arms + {st['n_prior_variants_counted']} prior variants)", "",
              md(pd.DataFrame([{k: c[k] for k in ("arm", "n_pairs", "mean_diff", "cohen_dz", "p_wilcoxon", "p_holm")}
                               | {"ci_lo": c["boot_ci95"][0], "ci_hi": c["boot_ci95"][1]} for c in st["comparisons"]])), "",
              "Note: these are exploration (validation) statistics on seeds 0-2. They are NOT the G5 confirmation test.", ""]
    for k, v in tab_md.items():
        L += [f"## {k}", "", v, ""]
    open(os.path.join(R, "RESULTS_SUMMARY.md"), "w").write("\n".join(L))
    print(f"report written: {len(df)} rows, {len(summ)} arms with primary metric")


if __name__ == "__main__":
    main()
