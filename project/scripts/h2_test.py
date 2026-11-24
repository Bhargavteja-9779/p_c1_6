#!/usr/bin/env python3
"""Pre-registered H2 test (journal entry 07). Δ(g,t) = mean_seeds macro-F1(E2 drop_g+lgbm) − mean_seeds macro-F1(E1 lgbm)
on target val; S_benign/S_attack from results/diagnostics/shift_by_group.json. Spearman over the 20 (g,t) cells.
Writes results/diagnostics/h2_test.json."""
import os, json
import pandas as pd
from scipy.stats import spearmanr
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(R, "results/raw_results.csv"))
sh = json.load(open(os.path.join(R, "results/diagnostics/shift_by_group.json")))["results"]
base = df[df.job_id.str.match(r"E1_lodo_lgbm_")].groupby("target").macro_f1.mean()
rows = []
for g in ["ttl", "tcpwin", "port_proto", "app_fields", "flags"]:
    d = df[df.method == f"drop_{g}+lgbm"].groupby("target").macro_f1.mean()
    for t in d.index:
        rows.append({"group": g, "target": t, "delta_macro_f1": float(d[t] - base[t]), "n_seeds": int((df.method == f"drop_{g}+lgbm").sum() // 4),
                     "S_benign": sh[t]["benign"][g]["gini"], "S_attack": sh[t]["attack"][g]["gini"]})
T = pd.DataFrame(rows)
rb = spearmanr(T.delta_macro_f1, T.S_benign); ra = spearmanr(T.delta_macro_f1, T.S_attack)
rd = spearmanr(T.delta_macro_f1, T.S_benign - T.S_attack)
out = {"n_cells": len(T), "rho_benign": rb.statistic, "p_benign": rb.pvalue, "rho_attack": ra.statistic, "p_attack": ra.pvalue,
       "rho_benign_minus_attack": rd.statistic, "p_benign_minus_attack": rd.pvalue,
       "H2_supported": bool(rb.statistic > 0 and rb.statistic > ra.statistic), "cells": rows}
json.dump(out, open(os.path.join(R, "results/diagnostics/h2_test.json"), "w"), indent=1)
print(T.round(4).to_string()); print({k: v for k, v in out.items() if k != "cells"})
