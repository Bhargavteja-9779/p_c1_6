# Beat-the-journal benchmark (G0/D30) — topic 2: unsupervised tabular anomaly detection

## Target paper
HF-DIF: Hierarchical feature-selection deep isolation forest, JKSU-CIS 38(6), 2026, DOI 10.1007/s44443-026-00706-6
(received 26 Oct 2025, accepted 25 Mar 2026; CC BY-NC-ND 4.0). Full text read: literature/fulltext/hfdif_2026_page.txt.
Exact per-dataset numbers (Tables 2–4, all 13 methods, mean ± std over 10 runs): literature/hfdif_tables.csv.

## Their protocol (as written, Sec. 6.1)
- 20 ADBench sets (Table 1): SpamBase, Waveform, Satellite, Cardiotocography, InternetAds, Optdigits, Speech, Wilt, Magic.gamma,
  Mammography, Landsat, Fault, Smtp, Yeast, Celeba, Donors, Vowels, Backdoor, Pageblocks, Fraud.
- z-score on the dataset; "each model ... trained with bootstrapping on the entire dataset, and anomaly scores are evaluated for all
  samples" (transductive, contaminated). The paper ALSO says "50 % of the normal samples are used for training" — contradictory.
  **Resolved empirically (D34, journal 19):** deterministic ECOD under our `transd` protocol matches their ECOD column on 19/20 sets
  within 1.1 points. Backdoor exception: their ECOD 50.0 / COPOD 51.0 vs our 84.6 / 78.9 (their baselines look broken there).
- 10 seeds (0–9); metrics AUC-ROC, AUC-PR, P@K (K = #anomalies); two-sided paired t-test over 20 per-dataset means, Holm.
- HF-DIF: DIF settings (50 representations, d = 40, 6 trees each, ψ = 256), GPU RTX 4090; no code released.

## Numbers to beat (average over the 20 sets, %)
| Method | AUC-ROC | AUC-PR | P@K |
|---|---|---|---|
| HF-DIF (theirs) | 82.6 | 34.90 | 39.20 |
| DNE | 76.4 | 30.52 | — |
| Disent-AD | 73.6 | 30.50 | — |
| DIF | 73.5 | — | 34.14 |
| DTE-C | 70.9 | 31.43 | — |
| iForest | 68.7 | — | — |
(dashes: see hfdif_tables.csv for the full table.)

## Weaknesses we can address fairly
1. GPU and no code → we release CPU code and report runtime on 4 CPU cores.
2. Contradictory split description → we state one protocol and show it reproduces their baselines.
3. Broken Backdoor baselines inflate their win count; we report with and without Backdoor.
4. Only parametric t-test on 20 points → we add Wilcoxon signed-rank + Holm and per-dataset win/tie/loss.
5. Their method design used the same 20 sets they evaluate on; we design on 27 disjoint ADBench sets (D35) and evaluate the frozen method once.

## Fairness rule for the comparison
Our method vs HF-DIF uses THEIR reported per-dataset means (cannot rerun, no code). Our method vs reproduced baselines uses
identical data and seeds. Both comparisons are reported; the second is the primary statistical claim (G5).
