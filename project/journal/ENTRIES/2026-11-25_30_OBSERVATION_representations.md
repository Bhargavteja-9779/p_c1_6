# OBSERVATION — 2026-11-25 — changing the feature space does not rescue kNN either (exploratory, DEV)
scripts/t2_diag_repr.py → results_t2/diag_repr.csv. kNN5 / kNN50 in five representations fit on training data only; 23 DEV datasets × 3 seeds.
Mean AUROC (×100), contaminated / clean:
raw kNN5 72.83 / 86.13; raw kNN50 74.53 / 82.16; rank(ECDF) kNN5 62.78 / 78.63, kNN50 68.62 / 76.67; PCA-whitened kNN5 72.70 / 84.43,
kNN50 74.47 / 83.09; feature bagging (25 half-subspaces) kNN5 73.16 / 84.73, kNN50 75.44 / 81.70; random projections kNN5 74.02 / 85.51,
kNN50 74.53 / 81.83. Best contaminated: feature-bagged kNN50, 75.44 (wins on 16/23 datasets, median +2.5 vs raw kNN5).
Every distance-based variant I have run (H5–H7 and these) lands at 72–76 in the contaminated regime. The bar (≥ 83) came from
HF-DIF's printed average (82.6). Before designing anything else I need to know whether that number is even comparable: DIF under
our inductive contaminated protocol scores 35.1 on SpamBase, where HF-DIF prints 64.6 for DIF. I am adding HF-DIF's transductive
protocol (fit and score the same contaminated data) to calibrate with baselines only (D39).
