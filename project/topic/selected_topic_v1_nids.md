# Topic selection (cycle 1, 2026-11-24)

## Constraints that drove the choice
- Journal: JKSU-CIS (broad CS; 2025–26 titles include IDS, cross-domain IDS such as QuCAD-IDS 10.1007/s44443-026-00688-5, FedAware 10.1007/s44443-025-00153-9; see literature/jksu_titles_2025_2026.json).
- Machine: 4 CPU cores, 15 GB RAM, no GPU, ephemeral container → tabular / small models only.
- Public data only, standard or easily-defined leakage-safe splits.

## Candidates considered (≥10)
| # | Candidate | Verdict | Reason |
|---|---|---|---|
| 1 | Cross-network (leave-one-dataset-out) generalization of flow-based NIDS on the four UQ NetFlow-V3 datasets, with a shift-robust feature/normalization method | **SELECTED** | Real deployment problem; public data with shared 53-feature schema + timestamps; CPU-feasible; journal publishes on it; testable gap |
| 2 | Random vs chronological split inflation in NIDS benchmarks | folded into #1 as E3/E4 evaluation lens | Alone it may already be done (temporal NetFlow-V3 analysis papers) — to be checked in prior art |
| 3 | GNN over-smoothing / heterophily on citation graphs | rejected | Overcrowded; incremental |
| 4 | Federated learning for IoT IDS | rejected | Buzzy, crowded, results mostly simulation artefacts |
| 5 | LLM-based phishing detection | rejected | "LLM for X"; no GPU |
| 6 | Software defect prediction (cross-project) | rejected | Small, old datasets (NASA/PROMISE) with known quality problems; crowded |
| 7 | Concept-drift Android malware detection | rejected | AndroZoo needs an API key (non-public access) |
| 8 | Time-series forecasting linear vs transformer | rejected | Overcrowded since DLinear (2023) |
| 9 | Calibration of tabular classifiers under shift | partially folded into #1 (threshold transfer is a calibration problem) | Generic alone |
| 10 | Sentiment analysis with transformers for low-resource language | rejected | Needs GPU; crowded |
| 11 | Image segmentation for medical data | rejected | Needs GPU; many dataset licences restrict |
| 12 | Recommendation with graph models | rejected | Crowded; benchmark protocol issues already well documented |

## Selected topic
**Problem.** Flow-based network intrusion detectors are trained on one network's captured traffic and deployed on another. Papers routinely report ≈99 % accuracy on random splits of a single dataset, but a detector moved to a new network faces different benign traffic (hosts, OS TCP stacks, TTLs, services) and different attack tooling. Operators who deploy such models get floods of false alarms or missed attacks. Existing evaluations mostly hide this because train and test come from the same capture.

**Gap.**
- WHAT EXISTS: standard-feature NetFlow datasets (UQ NetFlow V2/V3) that allow cross-dataset tests; studies showing cross-dataset performance drops; domain-adaptation/generalization NIDS methods (e.g., domain-adversarial, contrastive cross-domain models).
- WHAT IS MISSING (to be verified by prior-art search, state/novelty_ledger.json): (i) a mechanistic account of *which* features cause the collapse and *why* (testbed-identifying "environment signatures" in benign traffic vs genuine attack semantics), demonstrated with controlled ablations across all four V3 datasets; (ii) a simple, CPU-cheap remedy targeted at that mechanism and compared fairly against tuned GBDT and domain-adaptation baselines under leave-one-dataset-out with source-only threshold selection.
- WHY IT MATTERS: the realistic deployment setting is a network the detector has never seen; thresholds cannot be re-tuned with target labels.

**Hypothesis (H1, written before any experiment).** Under leave-one-dataset-out evaluation, pooled-source detectors lose most of their in-distribution performance; a large share of that loss is attributable to features whose *benign* distributions differ strongly across networks (environment signatures, e.g., TTL, TCP window, DNS/FTP fields, ports). Removing or re-expressing those features (benign-relative, per-environment normalization) improves cross-network macro-F1 without hurting in-distribution performance by more than 1 point.

## Research questions
- RQ1: How large is the gap between in-distribution (random and chronological splits) and cross-network performance for standard detectors on NetFlow V3?
- RQ2: Which features carry environment signatures, and does their presence explain the cross-network collapse (diagnostic ablation)?
- RQ3: Does a shift-targeted feature treatment improve cross-network detection over tuned baselines (GBDT, MLP, domain-adversarial/CORAL), with Holm-corrected statistics?
- RQ4: How sensitive is cross-network performance to the decision threshold chosen on source data (threshold transfer)?
- RQ5: What is the cost (training time, inference latency, memory)?

## Data
UQ NetFlow V3: NF-UNSW-NB15-v3 (DOI 10.48610/6E0EDA1), NF-BoT-IoT-v3 (10.48610/73C4EBC), NF-ToN-IoT-v3 (10.48610/44D7C5E), NF-CSE-CIC-IDS2018-v3 (10.48610/ECE9B83). Obtained through the Hugging Face parquet mirror keys-i/netFlow (mirror states BagIt SHA-1 checks passed and no filtering). Licence: "UQ open access data terms" per mirror card (exact licence text UNVERIFIED — to check on UQ RDM record). Row counts are re-verified locally (scripts/prepare_data.py).

## Baselines
Logistic regression, Random Forest, LightGBM, XGBoost, MLP (all with equal random-search budget on validation), MLP+CORAL, MLP+DANN (domain-adversarial).

## Metrics
Primary (pre-registered): macro-F1 on the held-out network, threshold chosen on pooled-source validation, averaged over the 4 leave-one-out targets. Secondary: AUROC, PR-AUC (attack), FPR at source threshold, in-distribution macro-F1.

## Compute estimate
Subsampled data (≤ 300k flows per dataset). Each model fit ≤ 5 CPU-min; ~4 targets × ~8 methods × 3 seeds × tuning ≈ 6–10 CPU-h per cycle. Within the 15 h cycle budget.
