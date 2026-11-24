#!/usr/bin/env python3
"""Pre-registered analysis of plan_v2 / E7 (written 2026-11-24 before any full E7 result existed).

Decides H2a-H2d exactly as stated in experiments/plan_v2.yaml, on target VAL, seeds 0-2.
  H2a: LightGBM, mean over targets UNSW/TON/CIC and seeds of effect(all|benign) - effect(all|attack) on macro-F1 > 0,
       one-sided paired t-test over (target, seed) pairs, alpha 0.05.
  H2b: LightGBM, per-group benign-side macro-F1 effect averaged over UNSW/TON/CIC and seeds, for the 6 coarse groups;
       positive parts only; H2b holds if the top-2 groups carry >= 50 % of the summed positive effect.
  H2c: rank order (Kendall tau) of the 6 coarse benign-side effects across lgbm/xgb/rf/mlp; holds if mean pairwise tau > 0.5.
  H2d: Spearman correlation between transplant benign-side effect and plan_v1 E2 drop-one effect
       (E2 macro-F1 minus E1 lgbm macro-F1, same target+seed) over the 5 groups that exist in both, per target; descriptive.
Outputs results/e7_analysis.json and tables/E7_effects.md. BOT is reported but excluded from H2a-H2c (0.3 % benign).
"""
import os, json, glob, itertools, collections
import numpy as np
from scipy import stats

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PT = ["UNSW", "TON", "CIC"]; COARSE = ["ttl", "tcpwin", "port_proto", "app_fields", "flags", "rest"]
FINE = ["rest_volume", "rest_timing", "rest_rates", "rest_pktsize"]
METHODS = ["lgbm", "xgb", "rf", "mlp"]


def load():
    out = {}
    for p in glob.glob(os.path.join(R, "results", "E7_lodo_transplant_*.json")):
        r = json.load(open(p)); s = r["spec"]
        out[(s["method"], s["target"], s["seed"])] = r
    return out


def eff(r, key, m="macro_f1"):
    e = r["transplant"]["effects"].get(key)
    return None if e is None else e["effect"][m]


def main():
    E = load()
    if not E:
        print("no E7 results"); return
    res = {"n_jobs": len(E)}
    # per-method, per-target mean effects
    table = collections.defaultdict(dict)
    for meth in METHODS:
        for t in PT + ["BOT"]:
            rs = [E[k] for k in E if k[0] == meth and k[1] == t]
            if not rs:
                continue
            row = {"base_macro_f1": float(np.mean([r["transplant"]["base"]["macro_f1"] for r in rs])), "n_seeds": len(rs)}
            for g in COARSE + FINE + ["all"]:
                for c in ("benign", "attack"):
                    v = [eff(r, f"{g}|{c}") for r in rs]; v = [x for x in v if x is not None]
                    if v:
                        row[f"{g}|{c}"] = float(np.mean(v))
            table[meth][t] = row
    res["mean_effects"] = table
    # H2a
    pairs = [(E[k]) for k in E if k[0] == "lgbm" and k[1] in PT]
    d = np.array([eff(r, "all|benign") - eff(r, "all|attack") for r in pairs if eff(r, "all|benign") is not None and eff(r, "all|attack") is not None])
    if len(d) >= 3:
        t = stats.ttest_1samp(d, 0.0, alternative="greater")
        res["H2a"] = {"n_pairs": int(len(d)), "mean_diff": float(d.mean()), "p_one_sided": float(t.pvalue), "holds": bool(t.pvalue < 0.05 and d.mean() > 0)}
    # H2b
    def coarse_vec(meth):
        v = []
        for g in COARSE:
            x = [table[meth][t].get(f"{g}|benign") for t in PT if t in table[meth]]
            x = [y for y in x if y is not None]
            v.append(float(np.mean(x)) if x else np.nan)
        return np.array(v)
    if "lgbm" in table:
        v = coarse_vec("lgbm"); pos = np.clip(np.nan_to_num(v), 0, None)
        top2 = np.sort(pos)[-2:].sum(); tot = pos.sum()
        res["H2b"] = {"benign_effects": dict(zip(COARSE, map(float, v))), "top2_share": float(top2 / tot) if tot > 0 else None,
                      "holds": bool(tot > 0 and top2 / tot >= 0.5)}
    # H2c
    vecs = {m: coarse_vec(m) for m in METHODS if m in table}
    taus = {f"{a}-{b}": float(stats.kendalltau(vecs[a], vecs[b]).statistic) for a, b in itertools.combinations(vecs, 2)}
    if taus:
        mt = float(np.nanmean(list(taus.values())))
        res["H2c"] = {"pairwise_tau": taus, "mean_tau": mt, "holds": bool(mt > 0.5), "n_methods": len(vecs)}
    # H2d
    h2d = {}
    for t in PT + ["BOT"]:
        xs, ys = [], []
        for g in ["ttl", "tcpwin", "port_proto", "app_fields", "flags"]:
            tr, dr = [], []
            for s in (0, 1, 2):
                k = ("lgbm", t, s); p2 = os.path.join(R, "results", f"E2_lodo_drop_{g}-lgbm_{t}_s{s}.json"); p1 = os.path.join(R, "results", f"E1_lodo_lgbm_{t}_s{s}.json")
                if k in E and os.path.exists(p1) and os.path.exists(p2):
                    tr.append(eff(E[k], f"{g}|benign")); dr.append(json.load(open(p2))["macro_f1"] - json.load(open(p1))["macro_f1"])
            if tr:
                xs.append(np.mean(tr)); ys.append(np.mean(dr))
        if len(xs) >= 4:
            h2d[t] = {"spearman": float(stats.spearmanr(xs, ys).statistic), "transplant": list(map(float, xs)), "drop_one": list(map(float, ys))}
    res["H2d"] = h2d
    json.dump(res, open(os.path.join(R, "results", "e7_analysis.json"), "w"), indent=1)
    os.makedirs(os.path.join(R, "tables"), exist_ok=True)
    s = "### E7 transplant effects on macro-F1 (SRC − CTRL; mean over seeds; target VAL)\n\n"
    cols = [f"{g}|{c}" for g in COARSE + FINE + ["all"] for c in ("benign", "attack")]
    s += "| method | target | base | " + " | ".join(cols) + " |\n|---|---|---|" + "---|" * len(cols) + "\n"
    for m in table:
        for t, row in table[m].items():
            s += f"| {m} | {t} | {row['base_macro_f1']:.3f} | " + " | ".join(f"{row[c]:+.3f}" if c in row else "–" for c in cols) + " |\n"
    open(os.path.join(R, "tables", "E7_effects.md"), "w").write(s)
    print(json.dumps({k: v for k, v in res.items() if k.startswith("H2") or k == "n_jobs"}, indent=1))


if __name__ == "__main__":
    main()
