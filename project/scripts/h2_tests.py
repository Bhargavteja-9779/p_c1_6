"""plan_v2 (cycle 2): tests of H2 (journal entry 12). TARGET VAL pools only; test pools stay locked.

E7  source-kNN detector (k=5 and k=25; one neighbour search with k=25, k=5 = its first 5 columns).
    Features: log1p(max(x,0)), z-scored with pooled-source TRAIN statistics. Score = distance-weighted share of
    attack neighbours. Threshold = best macro-F1 on pooled source val (20k/source). 20k train flows/source.
E8  LightGBM (cycle-1 tuned config of the same target, same seed, same data as E1) -> pred_contrib.
    For each target family with cycle-1 XGBoost AUROC < 0.5: per-feature diff = mean contrib(family flows)
    - mean contrib(pooled source-attack val flows). P2 statistic = share of the total NEGATIVE diff mass held by
    the 3 most negative features (decision D22).
E9  transplant (+ D23 benign control: same transplant on target benign flows, FPR before/after): set those top-3 features of the family's flows to the median of source-attack val flows; re-score.
    Control: 3 random features (rng 0). Report family recall at source threshold and family AUROC vs target benign.

Outputs: results/h2/<...>.json + results/h2/H2_SUMMARY.md. Idempotent (skips finished files).
Usage: python scripts/h2_tests.py [e7|e8|all]
"""
import json, os, sys, time
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import nids  # noqa: E402
from run_job import assemble  # noqa: E402

OUT = os.path.join(ROOT, "results", "h2"); os.makedirs(OUT, exist_ok=True)
TARGETS, SEEDS = ["UNSW", "TON", "CIC", "BOT"], [0, 1, 2]
INVERTED = {"CIC": ["DDOS_attack-HOIC", "Bot", "Infilteration"], "TON": ["scanning"],
            "BOT": ["Reconnaissance"], "UNSW": ["Fuzzers"]}  # cycle-1 XGBoost AUROC < 0.5 (results/diag_v2)


def lg(X):
    return np.log1p(np.maximum(X, 0.0))


def family_auroc(p, fam, a):
    b, m = fam == "Benign", fam == a
    if m.sum() < 5 or b.sum() < 5:
        return None
    return float(roc_auc_score(np.r_[np.zeros(b.sum()), np.ones(m.sum())], np.r_[p[b], p[m]]))


def e7():
    for t in TARGETS:
        for s in SEEDS:
            f = os.path.join(OUT, f"E7_knn_{t}_s{s}.json")
            if os.path.exists(f):
                continue
            t0 = time.time()
            spec = {"protocol": "lodo", "target": t, "n_per_source": 20000, "n_val_per_source": 20000, "eval_split": "val"}
            tr, va, te = assemble(spec, s)
            cols = [c for c in nids.feature_cols(te) if c != "_env"]
            Xtr = lg(tr[cols].to_numpy(np.float64)); mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
            Z = lambda d: (lg(d[cols].to_numpy(np.float64)) - mu) / sd  # noqa: E731
            nn = NearestNeighbors(n_neighbors=25, n_jobs=-1).fit((Xtr - mu) / sd)
            ytr = tr.Label.to_numpy()
            out = {"target": t, "seed": s}
            dv, iv = nn.kneighbors(Z(va)); de, ie = nn.kneighbors(Z(te))
            yva, yte, fam = va.Label.to_numpy(), te.Label.to_numpy(), te.Attack.to_numpy()
            for k in (5, 25):
                def score(d, i):
                    w = 1.0 / (d[:, :k] + 1e-6)
                    return (w * ytr[i[:, :k]]).sum(1) / w.sum(1)
                pva, pte = score(dv, iv), score(de, ie)
                thr, fva = nids.best_threshold(yva, pva)
                r = nids.metrics(yte, pte, thr)
                r.update(src_val_macro_f1=fva, family_auroc={a: family_auroc(pte, fam, a) for a in np.unique(fam) if a != "Benign"},
                         family_recall={a: float((pte[fam == a] >= thr).mean()) for a in np.unique(fam) if a != "Benign"})
                out[f"k{k}"] = r
            out["wall_s"] = time.time() - t0
            json.dump(out, open(f + ".tmp", "w"), indent=1); os.replace(f + ".tmp", f)
            print(f"E7 {t} s{s} k5 F1={out['k5']['macro_f1']:.4f} AUROC={out['k5']['auroc']:.4f} | "
                  f"k25 F1={out['k25']['macro_f1']:.4f} AUROC={out['k25']['auroc']:.4f} ({out['wall_s']:.0f}s)", flush=True)


def e8_e9():
    for t in TARGETS:
        cfg = json.load(open(os.path.join(ROOT, "results", f"tune_lodo_lgbm_{t}.json")))["best_cfg"]
        for s in SEEDS:
            f = os.path.join(OUT, f"E8_lgbm_{t}_s{s}.json")
            if os.path.exists(f) and "benign_control" in open(f).read():
                continue
            spec = {"protocol": "lodo", "target": t, "n_per_source": 100000, "n_val_per_source": 60000, "eval_split": "val"}
            tr, va, te = assemble(spec, s)
            cols = [c for c in nids.feature_cols(te) if c != "_env"]
            m = nids.make_model("lgbm", cfg, s); m.fit(tr[cols].to_numpy(np.float32), tr.Label.to_numpy())
            Xva, Xte = va[cols].to_numpy(np.float32), te[cols].to_numpy(np.float32)
            pva = m.predict_proba(Xva)[:, 1]; thr, _ = nids.best_threshold(va.Label.to_numpy(), pva)
            pte = m.predict_proba(Xte)[:, 1]
            auroc = float(roc_auc_score(te.Label.to_numpy(), pte))
            c1 = json.load(open(os.path.join(ROOT, "results", f"E1_lodo_lgbm_{t}_s{s}.json")))
            out = {"target": t, "seed": s, "auroc": auroc, "auroc_cycle1": c1["auroc"],
                   "reproduces_cycle1": abs(auroc - c1["auroc"]) < 1e-6, "threshold": thr, "families": {}}
            src_att = Xva[va.Label.to_numpy() == 1]
            ca = m.predict_proba(src_att, pred_contrib=True) if False else m.booster_.predict(src_att, pred_contrib=True)
            med_att = np.median(src_att, 0)
            fam = te.Attack.to_numpy(); rng = np.random.default_rng(0)
            for a in INVERTED[t]:
                idx = fam == a
                if idx.sum() < 5:
                    continue
                cf = m.booster_.predict(Xte[idx], pred_contrib=True)
                diff = cf[:, :-1].mean(0) - ca[:, :-1].mean(0)
                neg = np.clip(-diff, 0, None); order = np.argsort(diff)
                top3 = [cols[i] for i in order[:3]]
                share = float(neg[order[:3]].sum() / max(neg.sum(), 1e-12))
                absneg = np.clip(-cf[:, :-1].mean(0), 0, None); ao = np.argsort(-absneg)
                fr = {"n": int(idx.sum()), "auroc_vs_benign": family_auroc(pte, fam, a),
                      "recall": float((pte[idx] >= thr).mean()), "top3_diff": top3,
                      "top3_diff_values": [float(diff[i]) for i in order[:3]], "p2_share_top3_neg_diff": share,
                      "top3_abs_neg": [cols[i] for i in ao[:3]],
                      "p2_share_top3_abs_neg": float(absneg[ao[:3]].sum() / max(absneg.sum(), 1e-12))}
                for name, feats in (("transplant_top3", list(order[:3])),
                                    ("control_random3", list(rng.choice(len(cols), 3, replace=False)))):
                    X2 = Xte.copy(); X2[np.ix_(np.flatnonzero(idx), feats)] = med_att[feats]
                    p2 = m.predict_proba(X2)[:, 1]
                    fr[name] = {"features": [cols[i] for i in feats], "recall": float((p2[idx] >= thr).mean()),
                                "auroc_vs_benign": family_auroc(p2, fam, a)}
                    # D23 benign control: same transplant applied to target BENIGN flows -> FPR at source threshold
                    b = np.flatnonzero(fam == "Benign"); Xb = Xte[b].copy(); Xb[:, feats] = med_att[feats]
                    fr[name]["benign_control"] = {"fpr_before": float((pte[b] >= thr).mean()),
                                                  "fpr_after": float((m.predict_proba(Xb)[:, 1] >= thr).mean())}
                out["families"][a] = fr
                print(f"E8 {t} s{s} {a}: auroc={fr['auroc_vs_benign']:.3f} rec={fr['recall']:.3f} top3={top3} share={share:.2f} "
                      f"-> transplant rec={fr['transplant_top3']['recall']:.3f} / control rec={fr['control_random3']['recall']:.3f}", flush=True)
            json.dump(out, open(f + ".tmp", "w"), indent=1); os.replace(f + ".tmp", f)


def summary():
    import glob
    L = ["# H2 tests (auto-generated by scripts/h2_tests.py; target VAL; seeds 0-2)", ""]
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "E7_knn_*.json"))):
        r = json.load(open(f))
        for k in ("k5", "k25"):
            rows.append({"target": r["target"], "seed": r["seed"], "arm": f"knn_{k}", "macro_f1": r[k]["macro_f1"], "auroc": r[k]["auroc"],
                         "fpr": r[k]["fpr"], "HOIC_auroc": r[k]["family_auroc"].get("DDOS_attack-HOIC")})
    for f in sorted(glob.glob(os.path.join(ROOT, "results", "E1_lodo_xgb_*_s*.json"))):
        r = json.load(open(f)); sp = r["spec"]
        rows.append({"target": sp["target"], "seed": sp["seed"], "arm": "xgb(cycle1)", "macro_f1": r["macro_f1"], "auroc": r["auroc"], "fpr": r["fpr"], "HOIC_auroc": None})
    d = pd.DataFrame(rows)
    if len(d):
        g = d.groupby(["arm", "target"])[["macro_f1", "auroc", "fpr", "HOIC_auroc"]].mean().round(4).reset_index()
        L += ["## E7 source-kNN vs XGBoost (mean over seeds)", "", g.to_markdown(index=False), ""]
        p = d[d.target.isin(["UNSW", "TON", "CIC"])].groupby(["arm", "seed"]).macro_f1.mean().groupby("arm").agg(["mean", "std"]).round(4)
        L += ["Primary metric (mean macro-F1 UNSW/TON/CIC):", "", p.reset_index().to_markdown(index=False), ""]
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "E8_lgbm_*.json"))):
        r = json.load(open(f))
        for a, x in r["families"].items():
            rows.append({"target": r["target"], "seed": r["seed"], "family": a, "reproduces_c1": r["reproduces_cycle1"],
                         "auroc": x["auroc_vs_benign"], "recall": x["recall"], "top3": ",".join(x["top3_diff"]),
                         "P2_share": x["p2_share_top3_neg_diff"], "P3_recall_transplant": x["transplant_top3"]["recall"],
                         "auroc_transplant": x["transplant_top3"]["auroc_vs_benign"], "recall_control": x["control_random3"]["recall"],
                         "benign_fpr_before": x["transplant_top3"]["benign_control"]["fpr_before"],
                         "benign_fpr_after_transplant": x["transplant_top3"]["benign_control"]["fpr_after"]})
    if rows:
        L += ["## E8/E9 attribution and transplant (LightGBM)", "", pd.DataFrame(rows).round(3).to_markdown(index=False), ""]
    open(os.path.join(OUT, "H2_SUMMARY.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("e8", "all"):
        e8_e9()
    if what in ("e7", "all"):
        e7()
    summary()
