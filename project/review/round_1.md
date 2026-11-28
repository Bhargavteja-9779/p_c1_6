# Review round 1 — merged triage (R1 4/10 major, R2 5/10 major, R3 5/10 major)
Full reviews: review/round_1_R1.md, round_1_R2.md, round_1_R3.md.

| # | Concern (source) | Type | Action |
|---|---|---|---|
| 1 | Host context = source-IP shortcut on CIC; context-only 0.9784 (R1-1, R2-3) | evidence | host-novelty baseline, host-label permutation, mixed-host subset (scripts/t3_controls.py); untouched NF-ToN-IoT-v2; reframe CIC claim |
| 2 | "Closed form of what E-GraphSAGE learns" inaccurate: aggregation is fixed in GNNs; GraphIDS uses in-flows only; "like for like" unsupported (R2-1) | writing | rewrite Sect. 1/4/7: same *kind* of one-hop mean aggregation (Anomal-E, all incident flows); GraphIDS differs; remove "like for like" |
| 3 | Not novel as a method: classical per-host aggregates (KDD'99, UNSW-NB15 original, Kitsune, BLINC), SGC/SIGN (R2-2) | writing | reposition: re-introducing classical host aggregates into one-class NetFlow-v2 benchmarking; related-work section rewritten with R2's verified refs; novelty claim weakened |
| 4 | Not GDAE's exact protocol (no one-hot, different CIC sample, quantile vs EVT, graph-per-split unverified); iForest/HBOS gaps called "close" (R1-2) | writing+evidence | say "GDAE's split protocol"; list differences in a table; re-run raw-flow AE on our splits; Anomal-E/GraphIDS/GDAE not re-run (state why) |
| 5 | Attack labels used for design on seed-42 val, which overlaps other seeds' test (R1-3) | writing+evidence | correct wording; NF-ToN-IoT-v2 = zero design contact |
| 6 | Stats: Welch vs reported mixes protocol differences; one-sample tests dropped; UNSW leads over GraphIDS/AE n.s. (R1-4, R3) | writing | report both tests, interpret as descriptive; claim only Holm-significant differences |
| 7 | Runtime "fit 0.0 s" wrong (R3) | bug | end-to-end timing (scripts/t3_scores.py) |
| 8 | Log constant "tuned" claim false (R3) | writing+evidence | state c fixed a priori; add sensitivity of c, R, k on validation |
| 9 | No figures, short, no equations/algorithm/complexity/discussion (R3) | writing | PR curves, F1-vs-FPR budget, per-attack heatmap, sensitivity, method diagram; numbered equations, Algorithm 1, complexity, Discussion |
| 10 | README/requirements, references incomplete, declarations (R3) | writing | README with exact commands, requirements.txt, references completed from R2's verified list |
