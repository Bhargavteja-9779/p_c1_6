# Frontiers in AI — Phase 2 literature (session 2, 2026-11-24)

20 papers opened in full on frontiersin.org by a sub-agent (Crossref ISSN 2624-8212, 18 query sets, 2024-11 … 2026-11).
Matrix: frontiers_ai_matrix.csv (exact headline numbers with table references). Not opened (not counted): 1526221, 1929727,
1900815, 1928178, 1651516, 1738152, 1701944, 1832131, 1878587.

- **No paper in the journal evaluates on NetFlow-v2/v3**, none does leave-one-dataset-out zero-shot cross-network evaluation,
  and none does interventional/feature-group attribution (attribution in the journal = SHAP / importance ranking).
- **Closest:** Ahmed et al. 2026 (10.3389/frai.2026.1928858): zero-label cross-testbed transfer CIC-IDS2017↔CSE-CIC-IDS2018,
  16 TTA/monitoring variants, all collapse (macro-F1 ≈ 0.06–0.42, Table 5); label-free selectors pick the wrong model in 10–12/12
  trials. Must be cited and contrasted. TL-CRANN (1934604) uses 5–50 % target labels (not zero-shot).
- "Cross-dataset" is often used for per-dataset retraining (1950536, 1857306, 1934767, 1685376) → we must define the protocol precisely.
- Evaluation norms: most papers random splits with 95–100 % accuracy; 6/20 multi-seed (3–10 seeds); strongest papers use Wilcoxon /
  paired t / Friedman + Holm and bootstrap CIs (1957727, 1932015, 1903112, 1928858); 6/20 release code.
- Supporting: temporal split collapses F1 to 0.483 (1755696); LOEO vs random (1811692); null-result paper accepted (1957727) —
  the journal publishes rigorous negative results.
