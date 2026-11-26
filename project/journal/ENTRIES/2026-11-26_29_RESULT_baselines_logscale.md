# 29 RESULT — topic 3 first numbers (NF-UNSW-NB15-v2, seed 42)
TEST (baselines only, no design freedom): iForest PR-AUC 0.223 (GDAE table 0.189), HBOS 0.526 (0.321), PCA 0.261,
kNN k=1 (ref 50k unique benign) 0.763, kNN k=5 0.792. GDAE reports AE 0.761, Anomal-E 0.714, GraphIDS 0.818, GDAE 0.859.
VAL design mode (D40): kNN1 0.767 → log-rescaled kNN1 (ck1_L) 0.862 / Macro-F1 0.867 at benign-only threshold (FPR 0.3 %);
one-hot categoricals 0.791; L+C+drop src port 0.705 (worse).
Reading: min-max scaling of heavy-tailed NetFlow counters makes kNN blind to most of the byte/packet/duration range; a log
rescaling recovers ~0.10 PR-AUC. No graph needed so far. Prior-art agent (literature/prior_art_v2/nfv2_oneclass.md): no paper shows
simple detectors vs GNN one-class on both NF-v2 sets under this protocol; FlowGuard 2026 is the closest (UNSW-v2 only, no kNN).
PROBLEM: CIC-v2 prep OOM (18.9 M rows read at once) → chunked stratified sampling.
