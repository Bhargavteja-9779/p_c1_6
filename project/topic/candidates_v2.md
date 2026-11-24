# Topic candidates after pivot #1 (2026-11-24) — JKSU-CIS scope, CPU only (4 cores, 15 GB, no GPU), public data
Lesson from topic 1: the prior-art check (incl. code deposits / preprints) happens BEFORE any code.

| # | Candidate | First-pass view |
|---|---|---|
| 1 | Shortcut/leakage audit of popular **phishing-website/URL feature datasets** (e.g., PhiUSIIL 2024 with ~100 % reported accuracy; UCI phishing websites) — find features that trivially encode the label, show what accuracy remains without them, cross-dataset tests | cheap; many papers report ~99.9 %; possible Type A/D; must check if PhiUSIIL leakage is already documented |
| 2 | **Underspecification (Rashomon) in flow-based NIDS**: models indistinguishable in-distribution diverge on new networks; which design choices control the spread | reuses topic-1 infrastructure + data; risk of overlap with Gazi/Rayamajhi |
| 3 | **Temporal failure on the Elliptic / Elliptic++ bitcoin AML graph** (known collapse after the dark-market shutdown, t≥43): mechanism + remedy | public (GitHub/Kaggle); crowded by many GNN papers; mechanism angle may be open |
| 4 | **Label errors in NetFlow-V3 / CIC-2018** via confident learning: how many, which families, effect on reported results | Engelen 2021 / Lanvin 2022 did CIC-IDS2017 manual relabelling; NF-v3 maybe open |
| 5 | Log anomaly detection (HDFS/BGL) — simple baselines suffice | already shown (Le & Zhang 2022; Landauer 2023) → reject |
| 6 | Time-series anomaly detection benchmark flaws | already shown (Wu & Keogh 2021; Kim et al. 2022) → reject |
| 7 | Encrypted traffic classification shortcut learning (ISCX VPN, ET-BERT) | crowded since 2023 critiques; GPU for transformers → reject |
| 8 | IEEE-CIS fraud temporal drift | Kaggle-crowded; licence restricts redistribution → reject |
| 9 | SMS/email spam detection | crowded → reject |
| 10 | Explanation (SHAP) instability across seeds for tabular security models | generic; exists for tabular ML → weak |
| 11 | Android malware drift with public feature sets (e.g., KronoDroid 2021, timestamped) | KronoDroid is public; drift papers exist (TESSERACT 2019, Chen 2023 continuous learning) → check |
| 12 | Credit-scoring fairness under shift | off-scope for security; crowded |

Shortlist for prior-art check (in parallel): 1, 2, 3, 11.
