# 22 RESULT — scale-aware kNN sweep on DEV (27 sets, seed 0, max_n 20 000; logs/t2_dev_v4.log)
Mean AUC-ROC / AUC-PR: kNN k = 10 % of n 83.5 / 44.5 (best so far); multi-scale max-rank (k grid up to 10 % n) 83.2 / 37.4;
kNN k=100 82.8 / 41.8; k = 5 % n 82.4; k = 2 % n 81.5; subsampled kNN ensemble (Zimek-style, m=256, k=5, B=20) 82.0 / 40.2;
iForest 81.5 / 47.1 (still best AUC-PR).
Reading: the masking/scale effect holds (+2.0 AUC-ROC over iForest at k = 10 % n) and a fixed fraction beats the Zimek-style prior
art by 1.5 points, but iForest keeps the best AUC-PR. The gain is far smaller than the 13.5-point gap between iForest and HF-DIF's
claimed 82.6 on EVAL, so a scale fix alone is unlikely to beat HF-DIF. Next: a label-free rule that chooses the scale per dataset
(or per point), and fusion with isolation (AUC-PR); every variant stays on DEV (D35).
