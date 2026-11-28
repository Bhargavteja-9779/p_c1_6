"""Manuscript figures for topic 3 (written to figures/). Palette: validated categorical slots 1-4 (blue, orange, aqua, yellow);
identity is also carried by line style and direct labels (contrast WARN for slots 2-4). Each figure is skipped if its inputs are missing."""
import glob, json, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.makedirs("figures", exist_ok=True)
COL = {"knn1": "#257de0", "ck1_L": "#f47230", "hoco": "#00b894", "hoco_halfctx": "#f2a600"}
LS = {"knn1": ":", "ck1_L": "--", "hoco": "-", "hoco_halfctx": "-."}
NAME = {"knn1": "kNN, raw features", "ck1_L": "+ log rescaling", "hoco": "HoCo-kNN", "hoco_halfctx": "HoCo-kNN, half context"}
DS = [("NF-UNSW-NB15-v2", "NF-UNSW-NB15-v2"), ("NF-CSE-CIC-IDS2018-v2", "NF-CSE-CIC-IDS2018-v2")]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#666666",
                     "axes.labelcolor": "#191919", "xtick.color": "#666666", "ytick.color": "#666666", "axes.grid": True,
                     "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "savefig.dpi": 300, "figure.facecolor": "white"})

def fig_method():
    f, ax = plt.subplots(figsize=(8.0, 2.2)); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    boxes = [(0.0, "NetFlow record\n41 features, min–max\non benign training"), (0.26, "Log rescaling\nφ(x) = log(1+cx)\n/ log(1+c)"),
             (0.52, "Source-host context\nh = mean of φ over\nflows from same IP"), (0.78, "Distance to nearest\nbenign neighbour;\nthreshold 0.3 % FPR")]
    for x, t in boxes:
        ax.add_patch(plt.Rectangle((x, 0.25), 0.22, 0.55, fc="#f4f8fe", ec="#257de0", lw=1.2)); ax.text(x + 0.11, 0.525, t, ha="center", va="center", fontsize=7.5, color="#191919", linespacing=1.4)
    for x in (0.22, 0.48, 0.74): ax.annotate("", xy=(x + 0.04, 0.525), xytext=(x, 0.525), arrowprops=dict(arrowstyle="->", color="#666666"))
    ax.text(0.5, 0.08, "z = [φ(x), h] ∈ R^82   ·   no trained parameters · no attack labels in training or thresholds", ha="center", fontsize=8, color="#666666")
    f.savefig("figures/fig1_method.png", bbox_inches="tight"); plt.close(f)

def fig_pr():
    fs = [f"results/t3_scores_{d}_s42.npz" for d, _ in DS]
    if not all(os.path.exists(f) for f in fs): return print("skip PR")
    f, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for ax, (d, n), fn in zip(axs, DS, fs):
        S = np.load(fn); y = S["y"]
        for k in ["knn1", "ck1_L", "hoco"]:
            p, r, _ = precision_recall_curve(y, S[k]); ax.plot(r, p, color=COL[k], ls=LS[k], lw=2, label=NAME[k])
        ax.set_title(n, fontsize=9); ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.set_ylim(0, 1.02)
    axs[0].legend(frameon=False, fontsize=8, loc="lower left"); f.tight_layout(); f.savefig("figures/fig2_pr_curves.png"); plt.close(f)

def fig_budget():
    fs = [f"results/t3_scores_{d}_s42.npz" for d, _ in DS]
    if not all(os.path.exists(f) for f in fs): return print("skip budget")
    budgets = np.array([0.0005, 0.001, 0.002, 0.003, 0.005, 0.01, 0.02, 0.05])
    f, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for ax, (d, n), fn in zip(axs, DS, fs):
        S = np.load(fn); y = S["y"]
        for k in ["knn1", "ck1_L", "hoco", "hoco_halfctx"]:
            s = S[k]; rec = [(s[y == 1] > np.quantile(s[y == 0], 1 - b)).mean() for b in budgets]
            ax.plot(budgets * 100, rec, color=COL[k], ls=LS[k], lw=2, marker="o", ms=4, label=NAME[k])
        ax.axvline(0.3, color="#9c9c9c", lw=1); ax.set_xscale("log"); ax.set_xlabel("False-positive budget on benign test flows (%)")
        ax.set_ylabel("Attack recall"); ax.set_title(n, fontsize=9); ax.set_ylim(0, 1.02)
    axs[1].legend(frameon=False, fontsize=8, loc="lower right"); f.tight_layout(); f.savefig("figures/fig3_recall_vs_budget.png"); plt.close(f)

def fig_attack():
    if not os.path.exists("results/t3_per_attack.csv"): return print("skip attack")
    P = pd.read_csv("results/t3_per_attack.csv", index_col=[0, 1]) * 100; P = P[P.index.get_level_values(1) != "Benign"]
    cols = ["iforest", "hbos", "knn1_r200000", "ck1_L_r200000", "hc1_s_r200000"]; lab = ["iForest", "HBOS", "kNN raw", "+ log", "HoCo-kNN"]
    M = P[cols].values; f, ax = plt.subplots(figsize=(5.6, 0.28 * len(P) + 1.0))
    im = ax.imshow(M, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f4f8fe", "#84b9f3", "#257de0", "#0e3d7e"]), vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(lab)), lab); ax.set_yticks(range(len(P)), [f"{'UNSW' if 'UNSW' in a else 'CIC'} · {b}" for a, b in P.index]); ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]): ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7, color="#191919" if M[i, j] < 60 else "white")
    f.colorbar(im, ax=ax, label="Flagged at 0.3 % FPR (%)", shrink=0.6); f.tight_layout(); f.savefig("figures/fig4_per_attack.png", bbox_inches="tight"); plt.close(f)

def fig_sensitivity():
    rows = []
    for fn in glob.glob("results_t3_val/*/hc*_s*.json"):
        r = json.load(open(fn)); m = r["method"]
        if not m.startswith("hc") or "_s" not in m: continue
        rows.append((r["data"], m, r["ref"], r["pr_auc"]))
    if not rows: return print("skip sensitivity")
    D = pd.DataFrame(rows, columns=["data", "method", "ref", "pr"]); f, axs = plt.subplots(1, 3, figsize=(7.2, 2.6))
    for (d, n), c, ls in zip(DS, ["#257de0", "#f47230"], ["-", "--"]):
        x = D[(D.data == d) & (D.ref == 200000) & D.method.str.match(r"^hc1_s(_c\d)?_r")]
        ce = x.method.str.extract(r"_c(\d)")[0].fillna(4).astype(int); x = x.assign(c=ce).sort_values("c")
        axs[0].plot(x.c, x.pr, color=c, ls=ls, marker="o", lw=2, label=n)
        k = D[(D.data == d) & (D.ref == 200000) & D.method.str.match(r"^hc\d+_s_r")]; k = k.assign(k=k.method.str.extract(r"^hc(\d+)")[0].astype(int)).sort_values("k")
        axs[1].plot(k.k, k.pr, color=c, ls=ls, marker="o", lw=2)
        R = D[(D.data == d) & D.method.str.match(r"^hc1_s_r")].sort_values("ref"); axs[2].plot(R.ref / 1000, R.pr, color=c, ls=ls, marker="o", lw=2)
    for ax, t in zip(axs, ["log10 c (log constant)", "k (neighbours)", "reference size R (thousands)"]): ax.set_xlabel(t); ax.set_ylabel("Validation PR-AUC")
    axs[0].legend(frameon=False, fontsize=7); f.tight_layout(); f.savefig("figures/fig5_sensitivity.png"); plt.close(f)

for fn in (fig_method, fig_pr, fig_budget, fig_attack, fig_sensitivity): fn()
print(sorted(os.listdir("figures")))
