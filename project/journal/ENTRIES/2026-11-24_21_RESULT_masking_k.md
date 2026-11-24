# 21 RESULT / SURPRISE — kNN in the contaminated setting improves monotonically with k (DEV, seed 0, max_n 20 000)
Mean AUC-ROC over 27 DEV sets: k=1 68.9, k=5 73.1, k=10 74.6, k=20 77.9, k=50 79.0, k=100 82.8 (iForest 81.5, 200-tree IF 81.6).
Trimmed reference (k=10, 2 rounds) only reached 76.0; trimmed iForest 82.2 (+0.6 over its 200-tree control 81.6) — H4 P1 holds but weakly.
Reading: masking is real, but the lever is the neighbourhood SCALE, not cleaning the reference: once k exceeds the size of an anomaly
cluster, anomalies stop vouching for each other. A fixed k cannot be right for every set (cluster sizes differ by orders of magnitude).
Prior art to beat on this exact idea: subsampled kNN ensembles (Zimek et al., KDD 2013; Aggarwal & Sathe variable subsampling 2015)
— subsampling at rate r turns the k-th neighbour into roughly the (k/r)-th, i.e. it also enlarges the effective scale. They go in as baselines.
