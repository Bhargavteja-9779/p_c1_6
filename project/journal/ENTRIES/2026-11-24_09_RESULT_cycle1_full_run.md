# RESULT — 2026-11-24 12:22 UTC — cycle 1 full run (plan_v1) finished
376/376 jobs done, 4.18 CPU-h. One retry (the job killed by the worker restart). Numbers below are from results/RESULTS_SUMMARY.md (target VAL pools, seeds 0–2; not confirmation).
- Cross-network collapse is real: in-distribution random-split macro-F1 is 0.93–1.00 (E4) but LODO macro-F1 for the best detectors is 0.43–0.47 on CIC, 0.57–0.62 on UNSW, 0.77–0.78 on TON, 0.05–0.14 on BOT.
- Best baseline on the primary metric (mean of UNSW/TON/CIC): XGBoost 0.6114; LightGBM 0.6059; RF 0.6038; MLP 0.5285; CORAL 0.4917; DANN 0.4491; LR 0.4463.
- Chronological within-dataset split collapses CIC too (LightGBM 0.5930 chrono vs 0.9834 random).
