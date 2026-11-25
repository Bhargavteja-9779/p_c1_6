# Beat-the-journal benchmark (D30): HF-DIF, JKSU-CIS 2026
Tang, Chen, Zhang, "HF-DIF: Hierarchical feature-selected deep isolation forest for unsupervised anomaly detection on tabular data", JKSU-CIS, DOI 10.1007/s44443-026-00706-6. Extracted 2026-11-24 by sub-agent from Springer full text + "Full size table" pages (Tables 1–16 readable). Column averages recomputed from the per-dataset values match the printed averages (e.g. HF-DIF 82.65/34.90/39.19).

## Protocol (as printed; CONTRADICTORY → UNVERIFIED which was used)
- Text A: "50% of the normal samples are used for training and the remaining 50% is set aside for testing in each experiment" (one-class / clean).
- Text B (following DDAE): z-score standardisation; "In the unsupervised setting, each model … is trained with bootstrapping on the entire dataset, and anomaly scores are evaluated for all samples within the same dataset" (transductive, contaminated).
- 10 seeds (0–9); metrics AUC-ROC, AUC-PR, P@K (K = #anomalies in test, PyOD precision_n_scores). Paired t-tests on per-dataset means (n=20), Holm. Hardware: Xeon Silver 6133 + RTX4090. No code statement.
- HF-DIF settings: same as DIF (Γ=50 representations, d=40, K=6 trees each, ψ=256), hierarchical feature selection 25 % per subspace × 20 % global ≈ 5 %. Baselines: PyOD defaults for classical; DeepOD for DIF/DNE; packages for SLAD, DTE, Disent-AD, DDAE.
- Our response: run BOTH our CLEAN protocol (50 % normals) and a TRANSDUCTIVE-CONTAMINATED protocol (fit on all data, score all data), report against HF-DIF on its 20 datasets for both, clearly labelled "not identical protocol" where applicable.

## The 20 datasets (Table 1)
SpamBase, Waveform, Satellite, Cardiotocography, InternetAds, Optdigits, Speech, Wilt, Magic.gamma, Mammography, Landsat, Fault, Smtp, Yeast, Celeba, Donors, Vowels, Backdoor, Pageblocks, Fraud.

## Table 2 AUC-ROC (%; mean of 10 runs) — selected columns
| Dataset | iForest | DIF | DNE | DTE-C | Disent-AD | LUNAR | ECOD | HF-DIF |
|---|---|---|---|---|---|---|---|---|
| SpamBase | 63.7 | 64.6 | 66.4 | 51.5 | 66.2 | 55.9 | 65.6 | 68.3 |
| Waveform | 70.7 | 72.3 | 72.4 | 60.2 | 69.9 | 74.7 | 60.3 | 81.4 |
| Satellite | 69.5 | 73.7 | 74.1 | 71.1 | 70.2 | 63.8 | 58.3 | 82.5 |
| Cardiotocography | 68.1 | 70.9 | 73.0 | 51.0 | 69.0 | 52.7 | 78.4 | 78.2 |
| InternetAds | 68.6 | 69.0 | 85.5 | 65.6 | 78.5 | 67.5 | 67.7 | 83.2 |
| Optdigits | 69.6 | 76.5 | 79.4 | 50.8 | 79.5 | 41.5 | 61.5 | 89.9 |
| Speech | 47.6 | 49.3 | 54.1 | 49.5 | 58.2 | 49.3 | 47.0 | 60.6 |
| Wilt | 45.1 | 62.2 | 84.8 | 85.1 | 65.1 | 56.0 | 39.4 | 83.8 |
| Magic.gamma | 72.1 | 74.4 | 81.1 | 76.5 | 82.2 | 82.3 | 63.8 | 86.1 |
| Mammography | 86.0 | 86.2 | 87.3 | 81.0 | 87.4 | 83.5 | 90.6 | 89.5 |
| Landsat | 47.4 | 64.2 | 43.2 | 54.4 | 60.6 | 57.5 | 36.8 | 71.3 |
| Fault | 54.4 | 63.5 | 61.8 | 59.0 | 63.0 | 71.2 | 46.8 | 70.1 |
| Smtp | 90.5 | 92.0 | 92.4 | 95.1 | 90.3 | 85.6 | 88.2 | 94.2 |
| Yeast | 39.4 | 45.5 | 52.3 | 42.0 | 46.7 | 40.4 | 44.3 | 60.5 |
| Celeba | 70.7 | 72.1 | 59.1 | 81.2 | 72.6 | 57.2 | 76.3 | 83.2 |
| Donors | 77.1 | 81.5 | 86.6 | 78.5 | 83.1 | 63.4 | 88.8 | 91.5 |
| Vowels | 76.3 | 80.4 | 96.1 | 91.4 | 80.3 | 86.2 | 59.3 | 94.9 |
| Backdoor | 72.5 | 86.9 | 91.2 | 87.5 | 69.1 | 65.7 | 50.0 | 93.9 |
| Pageblocks | 89.7 | 90.3 | 92.6 | 92.4 | 86.7 | 77.6 | 91.4 | 94.6 |
| Fraud | 94.9 | 95.0 | 94.5 | 93.8 | 92.8 | 93.0 | 94.9 | 95.2 |
| **Average** | 68.7 | 73.5 | 76.4 | 70.9 | 73.6 | 66.3 | 65.5 | **82.6** |
Other averages (AUC-ROC): COPOD 64.4, SLAD 64.6, DDAE 68.4, LODA 59.3, HBOS 68.3.

## Table 3 AUC-PR (%) — HF-DIF per dataset and averages
HF-DIF: SpamBase 56.2, Waveform 9.5, Satellite 78.0, Cardiotocography 49.5, InternetAds 60.8, Optdigits 6.7, Speech 3.5, Wilt 9.3, Magic.gamma 78.1, Mammography 44.2, Landsat 34.8, Fault 49.2, Smtp 5.0, Yeast 45.3, Celeba 10.9, Donors 27.8, Vowels 22.0, Backdoor 16.5, Pageblocks 64.2, Fraud 26.5. Average 34.9.
Averages: COPOD 25.0, ECOD 28.9, DNE 30.5, SLAD 24.1, DTE-C 31.4, iForest 25.1, DIF 27.6, Disent-AD 30.5, DDAE 28.0, LODA 23.8, HBOS 24.7, LUNAR 26.5.
Notable: Smtp HF-DIF 5.0 vs ECOD 58.9; Backdoor DDAE 52.0 / DTE-C 48.1 vs 16.5; Fraud DTE-C 64.8 vs 26.5; Vowels DTE-C 41.7 vs 22.0.

## Table 4 P@K (%) averages
COPOD 29.8, ECOD 29.5, DNE 33.7, SLAD 27.4, DTE-C 31.8, iForest 29.6, DIF 34.1, Disent-AD 33.8, DDAE 28.2, LODA 23.4, HBOS 25.7, LUNAR 29.3, HF-DIF 39.2.
HF-DIF per dataset: SpamBase 55.3, Waveform 20.4, Satellite 68.5, Cardiotocography 53.6, InternetAds 54.2, Optdigits 12.9, Speech 3.9, Wilt 3.3, Magic.gamma 68.6, Mammography 30.5, Landsat 33.9, Fault 57.6, Smtp 72.3, Yeast 37.8, Celeba 16.5, Donors 20.6, Vowels 25.4, Backdoor 55.1, Pageblocks 49.8, Fraud 43.7.

## Statistics, runtime, oddities
Holm-adjusted AUC-PR: HF-DIF not significant vs ECOD, DNE, SLAD, DTE-C, Disent-AD, DDAE, LUNAR. Holm-adjusted P@K: n.s. vs COPOD, ECOD, DNE, DTE-C, Disent-AD, DDAE, LUNAR. Runtime Table 12: HF-DIF avg train 123.3 s (text says 111.16 s — inconsistent), DIF 104.5 s; inference HF-DIF 0.66 s vs DIF 16.77 s. Oddities: Table 9 prints DIF avg 64.6 vs 73.5 in Table 2; Smtp P@K 72.3 vs AUC-PR 5.0 with 30 anomalies; ADBench citation miscited; kNN NOT among the baselines (the strongest one-class baseline per the SOTA survey).
