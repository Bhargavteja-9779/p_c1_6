# 33 RESULT — plan_v5 frozen TEST run, primary method (5 seeds each; results/t3_stats.json, Holm over all plan comparisons)
HoCo-kNN (hc1_s, ref 200k, k=1, benign-only threshold at 0.3 % FPR):
- NF-CSE-CIC-IDS2018-v2: PR-AUC 0.9809 vs GDAE 0.9486 (+0.032, Holm p = 2.3e-5), vs Anomal-E 0.9555 (+0.025, p = 0.0033);
  Macro-F1 0.9718 vs GDAE 0.9571 (+0.015, p = 0.017).  P1 and P2 HOLD.
- NF-UNSW-NB15-v2: PR-AUC 0.9299 vs GDAE 0.8591 (+0.071, p = 0.0033) — P1 HOLDS;
  Macro-F1 0.8783 vs GDAE 0.9491 (−0.071, p = 0.0016) — LOWER, as predicted in plan_v5 (val 0.895). Also below AE / Anomal-E /
  GraphIDS F1 there. Possible reasons (to analyse, not assume): our threshold is label-free at 0.3 % FPR; theirs is EVT-calibrated on
  validation with early stopping on labelled PR-AUC. Ranking (PR-AUC) is better, the operating point is not.
Baselines reproduced (5 seeds): iForest 0.237 / 0.518, HBOS 0.533 / 0.568, PCA 0.264 / 0.113 PR-AUC (UNSW / CIC).
Ablations (log-only, src+dst, dst, context-only, raw kNN) still running.
