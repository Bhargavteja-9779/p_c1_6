# JKSU-CIS profile (G0 journal-fit gate) — started 2026-11-24
Source: 800 article titles 2025–2026 (literature/jksu_titles_2025_2026.json, Crossref). Keyword categories (overlapping; "other" = no keyword hit):
vision/image 197 · IoT/edge/network systems 128 · crypto/privacy/blockchain 103 · graph/GNN 97 · optimization/metaheuristic 89 · LLM/NLP 86 · medical/health 63 · federated 26 · recommendation 26 · time series/forecast 20 · intrusion/IDS/anomaly (network) 19 · education/social 14 · malware/phishing/fraud 4 · other 209.

## First conclusions
- Dominant paper type: a METHOD paper proposing a NAMED model/framework ("XXX: a … framework/method for …"), evaluated on several public benchmarks against many baselines, with ablation. Audits, replications and negative-result papers are rare → topic 1-style contributions fit poorly (consistent with the user's feedback, D29).
- Anomaly detection appears in several forms: tabular (HF-DIF), time series (TFD-CAD), zero-shot industrial (vision, GPU), network traffic (DDIM-based), few-shot (CRAD-HOPE).
- Detailed profile of ≥40 papers (abstracts, datasets, metrics, numbers, structure): see sections below (sub-agent + own reading).

## In-depth profile (sub-agent, 2026-11-24): 1,427 JKSU-CIS articles 2025–26 (Crossref), 54 CPU-feasible abstracts (OpenAlex), 7 full texts (Springer HTML via WebFetch; table bodies NOT visible → table-only values UNVERIFIED)
Title counts: vision 263 · GNN/graph 72 · LLM 60 · federated 51 · metaheuristics 49 · surveys 49 · recommendation 39 · intrusion/malware/traffic 26 · anomaly/outlier 21 · feature selection 20 · forecasting 18 · imbalance 14.

### Full-text audit (7)
| Paper (DOI 10.1007/s44443-) | Structure / size | Data / baselines | Rigour |
|---|---|---|---|
| HF-DIF 026-00706-6 (tabular unsup. AD) | Intro, Related, Prelim, Method 4.1–4.7, Discussion (complexity, theorem, limitations), Experiments, Conclusion; 18 tables, 15 figs | 20 ADBench datasets; 12 baselines | 10 seeds, paired t + Holm, ablation, runtime; GPU; no code; split ambiguous |
| SIGMA-AD 026-01284-3 (MTS AD) | Method 3.1–3.7, results 5.1–5.9; 8 tables 4 figs | MSL, SMAP, SWaT, PSM, SMD; 10 baselines | 5 seeds for 4 models, Holm; code on acceptance |
| GAMP 025-00021-6 (tabular AD) | 11 tables 10 figs | 12 (CWRU+ODDS); "six"/"nine" baselines inconsistent | no seeds/stats/ablation |
| GDAE 026-01241-0 (NetFlow graph AD) | ≥5 tables ≥9 figs | NF-UNSW-NB15-v2, NF-CSE-CIC-IDS2018-v2; 7 baselines (+4 copied) | 5 seeds, no stats, no full ablation |
| TransFraudGNN 026-00950-w | 6 tables 6 figs | IEEE-CIS, Amazon, Yelp; 5 baselines | 5 seeds, no stats, 4×A100 |
| ARO-GNN 025-00198-w | 5 tables 6 figs | Cora, Citeseer, Photo, Computer, Squirrel, Chameleon; 11 baselines | 5 runs, no stats, code |
| LTG 025-00024-3 | 7 tables 10 figs | WADI, SMD; 6 baselines | ablation; no seeds/stats/code |

### House style
Problem-driven intro ("existing methods suffer from (1)(2)(3)") → 3–5 bolded contribution bullets → named model with acronym'd components, equation-heavy method → many baselines, % improvement over strongest baseline → ablation + parameter sensitivity (+ complexity/runtime) → limitations. Long papers (≈100–330k chars page text). 2026 papers increasingly add seeds, paired tests, limitations.

### Common weaknesses we can fix while keeping the style
No seeds/statistics; inconsistent or copied baselines; random splits on temporal data; saturated numbers (AUC 1.000); point-adjusted F1 in MTS AD; missing strong simple baselines (kNN/iForest/ECOD, GBDT, DLinear); no AUC-PR; no code; heavy GPU use.

### Candidate directions with JKSU comparators (abstract-level numbers)
1. Unsupervised tabular AD on ADBench — HF-DIF (026-00706-6): 20-dataset avg AUC-ROC 82.6 (DNE 76.4, Disent-AD 73.6, DIF 73.5, iForest 68.7), AUC-PR 34.90 (DTE-C 31.43), P@K 39.20 (DIF 34.14); training 111.16 s avg (GPU). GAMP (025-00021-6): "+10.7 % AUC" on CWRU+ODDS.
2. Graph fraud (Amazon/Yelp/IEEE-CIS) — TransFraudGNN AUC 0.9361/0.9218/0.9487.
3. Benign-only NetFlow (graph) IDS — GDAE: NF-UNSW-v2 PR-AUC 0.8591, Macro-F1 0.9491; NF-CIC-2018-v2 PR-AUC 0.9486 (Anomal-E 0.9555), Macro-F1 0.9571; GraphINR-IDS (026-01260-x) F1 99.06±0.12.
4. MTS AD with honest metrics — SIGMA-AD PA-F1 avg 92.20, raw F1 31.60 (Autoformer 34.17); LTG SMD ROC-AUC 0.8506.
5. Imbalanced tabular — TSP-SMOTE, VRIF-VPSVM, MARS++ (numbers UNVERIFIED).
