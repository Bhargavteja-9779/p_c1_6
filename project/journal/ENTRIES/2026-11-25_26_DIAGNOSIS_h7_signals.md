# DIAGNOSIS — 2026-11-25 — which label-free signals see shielded anomalies? (H7 angle selection, DEV only)
scripts/t2_diag_h7.py → results_t2/diag_h7.csv. Contaminated regime, 23 DEV datasets × seeds 0–2. Labels used only to evaluate.
"Shielded" = a test anomaly whose 5 nearest training neighbours are mostly training anomalies.
- Shielding is the common case: on average 61.5 % of test anomalies are shielded (≥ 0.97 on breastw, donors, optdigits, wine).
- Mean AUROC (×100), all anomalies / shielded-only: kNN1 66.94 / 65.57; kNN5 72.83 / 75.02; kNN50 74.53 / 78.94;
  neighbours' own d50 ("nbr_escape") 72.04 / 76.68; mean over k-grid 73.75 / 76.04;
  ODIN-style reverse-neighbour in-degree 60.30 / 57.72; distance-profile jump log(d50/d5) 44.48 / 47.17.
- So two of my candidate angles are dead before building anything: reverse-neighbour evidence (angle a) and the
  per-point distance-profile jump (angle c) are WORSE than plain kNN. Larger neighbourhoods help a little (+1.7) but no
  single label-free distance signal comes near the bar (83).
- Surprise: shielded anomalies are not harder for kNN5 than unshielded ones (75.0 vs 72.8 overall). The shielding cluster
  lowers their scores, but it also lowers the scores of the normals that border it... What is lost is the margin, not the order.
