# 31 BREAKTHROUGH (VAL only) — H8 host-context kNN
VAL, seed 42, ref 50k, k=1 (results_t3_val/):
- CIC-v2: log-kNN 0.869 → host context (src+dst) 0.973 PR-AUC, Macro-F1 0.964 at benign-only 0.3 % FPR threshold;
  src-only 0.975 / 0.958; dst-only 0.923 / 0.769. (GDAE test 0.949 / 0.957; Anomal-E 0.956 / 0.952.)  P1 HOLDS.
- UNSW-v2: log-kNN 0.862 → 0.909 PR-AUC, Macro-F1 0.879 (GDAE 0.859 / 0.949). P3 HOLDS (rises, not drops).
Evidence it is not luck: one seed only so far; the confirmation is the frozen 5-seed TEST run (plan_v5). Threat to validity to test
before claiming: host context is transductive within the evaluated partition (as in the GNN papers, which build a graph per split),
and attacker IPs in these testbeds may emit almost only attacks → we must show (a) context-only ablation, (b) per-attack gains,
(c) a stricter variant where context is computed from a SEPARATE time-free disjoint window (not possible: v2 has no timestamps —
stated as a limitation), (d) robustness when context uses only flows seen BEFORE in a random order (streaming approximation).
