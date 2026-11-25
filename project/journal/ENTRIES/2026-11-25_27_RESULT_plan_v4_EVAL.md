# 27 RESULT — plan_v4 frozen EVAL run (HF-DIF's 20 sets; 18/20 complete at writing, Backdoor/Fraud still running)
Numbers: results/t2_eval_stats.json, results/t2_eval_auc_roc.csv (scripts/t2_eval_report.py).
- P1 FAILED: kNN k=10 % n vs reproduced iForest: 69.14 vs 66.49 AUC-ROC (+2.65, 11 W / 7 L, Wilcoxon p = 0.26) — not significant.
- P2 FAILED: vs default kNN (k=5): +4.29, p = 0.17.
- P3 HELD (as predicted): 12.1 points below HF-DIF's reported numbers, 0 wins on 18 sets.
- AUC-PR: kNN-10 % 30.0 vs iForest 24.4 (+5.6, p = 0.21) vs HF-DIF reported 33.7 (−3.7, 5 W / 12 L, p = 0.21).
- Reproduction check: iForest +0.4 and ECOD +1.7 vs HF-DIF's columns (match); PyOD-DIF (CPU) 60.6 vs their DIF 69.1 on 15 sets
  (−8.5, p = 0.008) — their DIF numbers do NOT reproduce with PyOD's implementation (they used DeepOD; difference unexplained).
Reading: the DEV gain from neighbourhood scale (+2.0) transferred only in direction (+2.7, n.s.). The method is not a contribution
that beats the journal. G5 FAILS. Combined with the parallel session line (admiring-archimedes: H4–H7 failed, cycle 5), the
"reference set / scale" family for topic 2 is exhausted on two independent protocols.
