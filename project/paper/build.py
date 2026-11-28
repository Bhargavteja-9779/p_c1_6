"""Builds paper/manuscript.md from paper/manuscript_src.md by replacing {{TABLE_*}} tokens with tables generated from result files."""
import json, os
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = pd.read_csv("results/t3_test_table.csv", header=[0, 1], index_col=[0, 1]); G = pd.read_csv("literature/gdae_table5.csv")
DS = [("NF-UNSW-NB15-v2", "UNSW-v2"), ("NF-CSE-CIC-IDS2018-v2", "CIC-2018-v2")]
def ms(ds, m, met):
    try: return f"{T.loc[(ds, m), (met, 'mean')]:.4f} ± {T.loc[(ds, m), (met, 'std')]:.4f}"
    except KeyError: return "—"
def main():
    h = "| Method | Source | " + " | ".join(f"{n} PR-AUC | {n} Macro-F1 | {n} ACC" for _, n in DS) + " |\n|" + "---|" * 8 + "\n"
    for meth in ["IF", "HBOS", "OC-SVM", "Deep SVDD", "AE", "Anomal-E", "GraphIDS", "GDAE"]:
        cells = []
        for ds, _ in DS:
            g = G[(G.method == meth) & (G.dataset == ds)].iloc[0]
            cells += [f"{g.pr_auc:.4f} ± {g.pr_auc_sd:.4f}", f"{g.macro_f1:.4f} ± {g.macro_f1_sd:.4f}", f"{g.acc:.4f} ± {g.acc_sd:.4f}"]
        h += f"| {meth} | GDAE Table 5 | " + " | ".join(cells) + " |\n"
    for m, n in [("iforest", "iForest (ours)"), ("hbos", "HBOS (ours)"), ("pca", "PCA (ours)"), ("knn1_r200000", "kNN, raw (ours)"), ("hc1_s_r200000", "**HoCo-kNN (ours)**")]:
        h += f"| {n} | this work | " + " | ".join(ms(ds, m, x) for ds, _ in DS for x in ["pr_auc", "macro_f1", "acc"]) + " |\n"
    return h
def abl():
    rows = [("knn1_r200000", "raw features (min–max)"), ("knn5_r200000", "raw features, k = 5"), ("ck1_L_r200000", "+ log rescaling"),
            ("hc1_s_r200000", "+ source-host context (HoCo-kNN)"), ("hc1_sd_r200000", "+ source and destination context"),
            ("hc1_d_r200000", "log + destination context only"), ("hc1_os_r200000", "source context only (no own features)")]
    h = "| Variant | " + " | ".join(f"{n} PR-AUC | {n} Macro-F1" for _, n in DS) + " |\n|" + "---|" * 5 + "\n"
    for m, n in rows: h += f"| {n} | " + " | ".join(ms(ds, m, x) for ds, _ in DS for x in ["pr_auc", "macro_f1"]) + " |\n"
    return h
def stats():
    S = json.load(open("results/t3_stats.json")); h = "| Dataset | Comparison | Ours | Theirs | Difference | Holm-adjusted p |\n|---|---|---|---|---|---|\n"
    for ds, n in DS:
        for k, v in S[ds].items():
            if "(reported)" in k and any(x in k for x in ("GDAE", "Anomal-E", "GraphIDS", "AE")):
                h += f"| {n} | {k.replace('pr_auc', 'PR-AUC').replace('macro_f1', 'Macro-F1')} | {v['ours']:.4f} | {v['theirs']:.4f} | {v['diff']:+.4f} | {v['p_holm']:.2g} |\n"
    return h
def per_attack():
    P = pd.read_csv("results/t3_per_attack.csv", index_col=[0, 1]) * 100
    h = "| Dataset | Attack | iForest | HBOS | kNN raw | + log | HoCo-kNN |\n|---|---|---|---|---|---|---|\n"
    for (ds, a), r in P.iterrows():
        if a == "Benign": continue
        h += f"| {dict(DS)[ds]} | {a} | " + " | ".join(f"{r[c]:.1f}" for c in ["iforest", "hbos", "knn1_r200000", "ck1_L_r200000", "hc1_s_r200000"]) + " |\n"
    return h
def runtime():
    h = "| Dataset | Method | fit (s) | scoring val+test (s) |\n|---|---|---|---|\n"
    for ds, n in DS:
        for m, nm in [("iforest", "iForest"), ("knn1_r200000", "kNN raw"), ("hc1_s_r200000", "HoCo-kNN")]:
            h += f"| {n} | {nm} | {T.loc[(ds, m), ('fit_s', 'mean')]:.1f} | {T.loc[(ds, m), ('score_s', 'mean')]:.1f} |\n"
    return h
src = open("paper/manuscript_src.md").read()
for k, f in {"MAIN": main, "ABL": abl, "STATS": stats, "ATTACK": per_attack, "RUNTIME": runtime}.items(): src = src.replace("{{TABLE_" + k + "}}", f())
open("paper/manuscript.md", "w").write(src); print("built paper/manuscript.md", len(src))
