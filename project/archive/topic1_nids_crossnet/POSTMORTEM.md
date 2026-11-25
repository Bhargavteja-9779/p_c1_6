# Post-mortem — topic 1: cross-network generalization of flow-based NIDS (NetFlow V3), cycles 1–3

Files stay in place (moving them would break result paths): topic/selected_topic.md, experiments/plan_v1–v3.yaml,
results/ (cycle 1), results/diag_v2, results/h2, results/h3, journal entries 00–17, literature/prior_art.md.

| Cycle | Idea | Outcome (target VAL, seeds 0–2) | Evidence |
|---|---|---|---|
| 1 | H1: environment-signature features cause LODO collapse; ESF / PEN fix it | ESF 0.58–0.60 vs XGBoost 0.6114 (n.s.); PEN 0.4337 (−0.178) | results/RESULTS_SUMMARY.md, journal 10 |
| 1→2 | Diagnosis | Inverted ranking of large families: CIC DDoS-HOIC (40 % of CIC attacks) AUROC ≈ 0.12 | results/diag_v2, journal 11 |
| 2 | H2: few-feature shortcuts in trees | P1 ✓ (kNN HOIC AUROC 0.66–0.89), P2 ✗ (top-3 share 0.34–0.38), P3 ✓ on CIC only (recall 0 → 1.0) | results/h2, journal 13–14 |
| 3 | H3: XGBoost + kNN ensemble | −0.0563, Holm p 0.156 | results/h3, journal 16 |

Why it failed: the topic was already covered by a thorough benchmark released two weeks earlier (Gazi et al., Zenodo 10.5281/zenodo.24172401) and by Rayamajhi 2026; and in our data no simple, general mechanism explains the cross-network loss.
Novelty: 9/25 (cycle 1), 9/25 (cycle 2). Compute: see state/budget.json.
Lessons carried over: (1) read the closest prior work's code before building; (2) every counterfactual needs a benign control; (3) sample sizes near hard thresholds; (4) keep the session awake during long runs.
