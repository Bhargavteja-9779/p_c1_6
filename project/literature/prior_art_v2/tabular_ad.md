# Tabular AD state of the art (sub-agent survey, 2026-11-24; numbers as reported by the cited papers, abstract/README level unless stated)
## Protocol warnings
- ADBench's own "semi-supervised" = a few LABELED anomalies; the one-class protocol (DTE/TCCM) trains on 50 % of normals, tests on other normals + all anomalies; ZEN/FOCUS use 70 %.
- LEAK in official ADBench data_generator.py: datasets < 1000 rows are resampled to 1000 WITH replacement before splitting (Bershtman & Cohen arXiv 2610.06693: 12/47 sets affected; 91.5 % of clean-regime test normals have a train twin). Our harness loads the .npz directly (no resampling) — must still check exact duplicates.
## Reported numbers
- Bershtman & Cohen 2610.06693 (leak fixed, 47 sets, 10k subsample, 5 seeds): clean (70 % normals) AUROC: FOCUS 85.9, ZEN 85.2, kNN 85.1 (best mean rank 4.4), LOF 82.9, CBLOF 81.7, DTE 81.5, TCCM 80.8, IForest 79.6, HBOS 77.4, PCA 76.7, OCSVM 75.6, DeepSVDD 74.7, COPOD 74.5, ECOD 74.2. Contaminated (stratified 70/30): FOCUS 80.0, ZEN 79.7, IForest 76.4, kNN 73.9, LOF 65.4. FOCUS vs kNN clean p = 0.52. GPU (A100).
- PRISM-T 2611.08136 (50 % normals, z-score, 47 sets, 5 seeds; leak handling not stated): AUROC/AUPRC PRISM-T 86.4/65.9, DTE-NP 86.3/65.5, DenoiserAD 86.3/64.5, LUNAR 85.9/68.0, AnoDDAE 85.9/65.6, TCCM 84.7/64.5, KDE 84.2/62.3, IForest 79.8/49.3, DIF 76.2/48.2. CPU.
- OutFormer ICML 2026 (2602.03018; 57 sets, inlier-only): avg rank / rAUC: OutFormer 4.02/0.956, TabPFN-OD 4.74/0.945, kNN 5.05/0.938, DTE-NP 5.12/0.939, ICL 5.63/0.925, FoMo-0D 6.00/0.928, LOF 6.04/0.913, IForest 8.46/0.879; OutFormer vs kNN p = 0.06. GPU.
- TCCM NeurIPS 2025 (2510.18328): best avg rank AUROC 5.7 over 44 baselines (DTE-NP 2nd, LUNAR 3rd, KDE 4th).
- DTE ICLR 2024: "DTE outperforms all baselines for the semi-supervised setting apart from kNN".
- Others: FoMo-0D (2409.05672), ICL (ICLR 2022), MCM (ICLR 2024), DRL (ICLR 2025), NPT-AD, DIF (TKDE 2023), SLAD (ICML 2023), AnoLLM (ICLR 2025), uLEAD-TabPFN (2604.20255), TACTIC (2603.14171), ICLAD (2603.19497), OFA-TAD, TaskBridge (2609.36968), DIFFINT (2609.03878), UCF (2606.12483), KCM (2610.02345), RIFT (2610.12244), Vendi score (2611.12871).
## Findings
kNN top in normal-only setting (DTE, MacrOData, ZEN/FOCUS, OutFormer); contamination flips rankings (kNN −11, LOF −17; IForest best classical); MacrOData 2602.09329 critiques ADBench (low power, global outliers, near-duplicate datasets, trivial sets); Mai et al. 2309.08374 (SSL reps add irrelevant features); AUPRC means dominated by high-anomaly-rate sets → report ranks + Wilcoxon/Holm.
## Gaps (CPU) and who touches them
Irrelevant features (uLEAD-TabPFN, ZEN — GPU); mixed scales/local correlation (PRISM global Mahalanobis; local whitening not found 2024–26); local density (LOF, RIFT); clustered anomalies/masking (RIFT); contaminated reference set (ZEN/FOCUS trust weighting — GPU, TACTIC); over-extrapolation (KCM).
## Suggested ideas
(1) conditional-residual kNN; (2) locally whitened kNN; (3) trust-weighted contamination-robust raw kNN.
