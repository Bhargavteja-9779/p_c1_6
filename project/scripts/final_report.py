#!/usr/bin/env python3
"""Section 12 automatic report. Reads results/<job_id>.json (written by src/run_job.py) and writes:
  results/metrics.json      per (exp, protocol, method, target): mean, std, 95% t-CI over seeds, n
  results/statistics.json   paired tests (method vs reference) on the primary metric, effect sizes, Holm correction
  tables/*.md               main LODO table, ablation table, in-distribution table
  results/RESULTS_SUMMARY.md
Primary metric (pre-registered, D11): macro-F1 at the source-val threshold, mean over targets UNSW, TON, CIC.
Pairing unit for tests: (target, seed) for targets in PRIMARY_TARGETS -> n = 3 targets x n seeds.
Idempotent; overwrites only its own derived outputs. Usage: python scripts/final_report.py [--dir results] [--split val]
"""
import os, sys, json, glob, math, argparse, collections
import numpy as np
from scipy import stats

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARY_TARGETS = ["UNSW", "TON", "CIC"]
TARGETS = ["UNSW", "TON", "CIC", "BOT"]
BASELINES = ["lr", "rf", "lgbm", "xgb", "mlp", "coral", "dann"]


def ci95(v):
    v = np.asarray(v, float)
    if len(v) < 2:
        return [float(v.mean()), float("nan"), float("nan")] if len(v) else [float("nan")] * 3
    h = stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / math.sqrt(len(v))
    return [float(v.mean()), float(v.mean() - h), float(v.mean() + h)]


def holm(pvals):
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i]); m = len(pvals); adj = [0.0] * m; run = 0.0
    for r, i in enumerate(idx):
        run = max(run, min(1.0, (m - r) * pvals[i])); adj[i] = run
    return adj


def mname(spec):
    m = spec["method"]
    return f"{m}_t{spec['tau']}" if "tau" in spec else m


def load(d, split):
    rows = []
    for p in glob.glob(os.path.join(R, d, "*.json")):
        if os.path.basename(p).startswith("tune_"):
            continue
        try:
            r = json.load(open(p))
        except Exception:
            continue
        s = r.get("spec", {})
        if "macro_f1" not in r or s.get("eval_split", "val") != split:
            continue
        rows.append(dict(exp=s.get("exp"), protocol=s.get("protocol"), method=mname(s), target=s.get("target"),
                         seed=s.get("seed"), n=s.get("n_per_source"), macro_f1=r["macro_f1"], auroc=r.get("auroc"),
                         prauc=r.get("prauc"), fpr=r.get("fpr"), tpr=r.get("tpr"), src=r.get("src_val_macro_f1"),
                         fit_s=r.get("fit_s"), pred=r.get("pred_ms_per_1k"), bytes=r.get("model_bytes"), job=s.get("job_id")))
    return rows


def key(r):
    k = (r["exp"], r["protocol"], r["method"])
    return k + ((f"n{r['n']}",) if r["exp"] == "E3" else ())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="results"); ap.add_argument("--split", default="val")
    a = ap.parse_args()
    rows = load(a.dir, a.split)
    os.makedirs(os.path.join(R, "tables"), exist_ok=True)
    if not rows:
        print("no results found in", a.dir); return
    groups = collections.defaultdict(list)
    for r in rows:
        groups[key(r) + (r["target"],)].append(r)
    metrics = {}
    for k, rs in sorted(groups.items(), key=lambda x: str(x[0])):
        e = {"n": len(rs), "seeds": sorted(x["seed"] for x in rs), "jobs": sorted(x["job"] for x in rs)}
        for m in ("macro_f1", "auroc", "prauc", "fpr", "tpr", "src", "fit_s", "pred", "bytes"):
            v = [x[m] for x in rs if x[m] is not None and not (isinstance(x[m], float) and math.isnan(x[m]))]
            if v:
                c = ci95(v); e[m] = {"mean": c[0], "std": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0, "ci95": c[1:]}
        metrics["|".join(map(str, k))] = e
    json.dump(metrics, open(os.path.join(R, a.dir, "metrics.json"), "w"), indent=1)

    # primary metric per method (E1 + E2 + E3 lodo): per seed mean over PRIMARY_TARGETS; paired by (target, seed)
    by = collections.defaultdict(dict)
    for r in rows:
        if r["protocol"] == "lodo":
            by[key(r)][(r["target"], r["seed"])] = r["macro_f1"]
    prim = {}
    for k, d in by.items():
        seeds = sorted({s for (t, s) in d if t in PRIMARY_TARGETS})
        per_seed = [np.mean([d[(t, s)] for t in PRIMARY_TARGETS]) for s in seeds if all((t, s) in d for t in PRIMARY_TARGETS)]
        if per_seed:
            c = ci95(per_seed)
            prim["|".join(map(str, k))] = {"mean": c[0], "ci95": c[1:], "n_seeds": len(per_seed),
                                           "per_target": {t: float(np.mean([v for (tt, s), v in d.items() if tt == t]))
                                                          for t in TARGETS if any(tt == t for (tt, _) in d)}}
    e1 = {k: v for k, v in prim.items() if k.startswith("E1|")}
    base = {k: v for k, v in e1.items() if k.split("|")[2] in BASELINES}
    ref = max(base, key=lambda k: base[k]["mean"]) if base else None
    tests = []
    if ref:
        for k in prim:
            if k == ref:
                continue
            common = sorted(set(by[tuple(k.split("|"))]) & set(by[tuple(ref.split("|"))]))
            common = [c for c in common if c[0] in PRIMARY_TARGETS]
            if len(common) < 3:
                continue
            x = np.array([by[tuple(k.split("|"))][c] for c in common]); y = np.array([by[tuple(ref.split("|"))][c] for c in common])
            dlt = x - y
            try:
                pw = stats.wilcoxon(dlt).pvalue if np.any(dlt != 0) else 1.0
            except Exception:
                pw = float("nan")
            pt = stats.ttest_rel(x, y).pvalue if np.std(dlt) > 0 else 1.0
            c = ci95(dlt)
            dz = float(dlt.mean() / dlt.std(ddof=1)) if len(dlt) > 1 and dlt.std(ddof=1) > 0 else float("nan")
            tests.append({"method": k, "reference": ref, "n_pairs": len(common), "mean_diff": c[0], "ci95_diff": c[1:],
                          "cohen_dz": dz, "p_ttest": float(pt), "p_wilcoxon": float(pw)})
        adj = holm([t["p_ttest"] for t in tests])
        for t, p in zip(tests, adj):
            t["p_holm"] = p
    json.dump({"primary_metric": "macro-F1 @ source-val threshold, mean over " + ",".join(PRIMARY_TARGETS),
               "eval_split": a.split, "best_baseline": ref, "primary": prim, "tests_vs_best_baseline": tests,
               "note": "Holm over ALL methods/variants compared to the reference on the same data (Rule 8)."},
              open(os.path.join(R, a.dir, "statistics.json"), "w"), indent=1)

    # tables
    def tab(prefix, title):
        ks = sorted([k for k in prim if k.startswith(prefix)], key=lambda k: -prim[k]["mean"])
        if not ks:
            return ""
        s = f"### {title}\n\n| method | " + " | ".join(TARGETS) + " | primary mean [95% CI] | seeds |\n|---|" + "---|" * (len(TARGETS) + 2) + "\n"
        for k in ks:
            p = prim[k]
            s += f"| {k.split('|', 2)[2]} | " + " | ".join(f"{p['per_target'][t]:.3f}" if t in p["per_target"] else "–" for t in TARGETS)
            s += f" | {p['mean']:.3f} [{p['ci95'][0]:.3f}, {p['ci95'][1]:.3f}] | {p['n_seeds']} |\n"
        open(os.path.join(R, "tables", f"{prefix.strip('|').replace('|', '_')}_{a.split}.md"), "w").write(s)
        return s + "\n"
    out = f"# RESULTS SUMMARY (auto-generated by scripts/final_report.py; split={a.split}, dir={a.dir})\n\n"
    out += f"Rows: {len(rows)} result files. Primary metric: macro-F1 at source-val threshold, mean over {PRIMARY_TARGETS} (BOT shown, not in mean).\n\n"
    out += tab("E1|lodo|", "E1 LODO main comparison") + tab("E2|lodo|", "E2 feature-group removal (LightGBM)") + tab("E3|lodo|", "E3 reduced source data")
    idt = [(k, v) for k, v in metrics.items() if k.startswith("E4|")]
    if idt:
        s = "### E4 in-distribution macro-F1 (mean ± std over seeds)\n\n| protocol | method | target | macro-F1 |\n|---|---|---|---|\n"
        for k, v in sorted(idt):
            _, pr, me, tg = k.split("|")
            s += f"| {pr} | {me} | {tg} | {v['macro_f1']['mean']:.3f} ± {v['macro_f1']['std']:.3f} |\n"
        open(os.path.join(R, "tables", f"E4_{a.split}.md"), "w").write(s); out += s + "\n"
    if tests:
        out += f"### Paired tests vs best baseline `{ref}` (pairs = target×seed, Holm over {len(tests)} comparisons)\n\n"
        out += "| method | Δ mean [95% CI] | d_z | p (t) | p Holm |\n|---|---|---|---|---|\n"
        for t in sorted(tests, key=lambda t: -t["mean_diff"]):
            out += f"| {t['method']} | {t['mean_diff']:+.3f} [{t['ci95_diff'][0]:+.3f}, {t['ci95_diff'][1]:+.3f}] | {t['cohen_dz']:.2f} | {t['p_ttest']:.3g} | {t['p_holm']:.3g} |\n"
    open(os.path.join(R, a.dir, "RESULTS_SUMMARY.md"), "w").write(out)
    print(out)


if __name__ == "__main__":
    main()
