# JKSU-CIS literature matrix — reported results & evaluation practice (summary)
Built 2026-11-24 by a literature sub-agent from 19 Springer-era JKSU-CIS papers opened in full text (tables opened at /article/<DOI>/tables/N). Matrix: literature/journal_papers_matrix.csv (P01–P19; all DOIs resolved on Crossref). Elsevier-era papers not opened (ScienceDirect 403).

## Key verified numbers
- Only true zero-shot cross-dataset test: P05 eBPF/ML IDS (10.1007/s44443-026-01098-3), Table 10: CIC-IDS2018→2017 F1 0.1708 (ROC-AUC 0.7582) vs in-dist 0.9083; 2017→2018 F1 0.4052 (ROC-AUC 0.7516) vs in-dist 0.9942.
- P01 QuCAD-IDS (10.1007/s44443-026-00688-5): "cross-domain" F1 99.55–99.88 (Tables 5–8) but after fine-tuning on 70 % labelled target data.
- P07 GraphINR-IDS (10.1007/s44443-026-01260-x): F1 99.06 random split (Table 7) vs 61.78 cross-day CIC-IDS2017 (Table 16); FPR 5.13 → ~32 cross-session (Table 14).
- P10 ADHS-EL (10.1007/s44443-025-00015-4): ~0.998 random split (Table 5) vs 0.75–0.81 on KDDTest+ (Table 11).
- P15 GDAE (10.1007/s44443-026-01241-0), only NetFlow-V2 user: NF-UNSW-NB15-v2 macro-F1 0.9491 ± 0.0081, NF-CSE-CIC-IDS2018-v2 0.9571 ± 0.0034 (Table 5), random 8:1:1 split. NetFlow V3: used by none.

## Evaluation practice (n=19)
Random/holdout split 7; temporal/capture-disjoint 4; unclear 5; true cross-dataset 1; dispersion over runs 11; significance tests 5; public code 2; duplicate removal stated 0; internally inconsistent metrics 5 (P04, P08, P09, P12, P13).
