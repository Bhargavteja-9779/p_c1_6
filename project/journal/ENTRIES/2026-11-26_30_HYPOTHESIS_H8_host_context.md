# 30 HYPOTHESIS — H8 host-context kNN (written before any result)
Observation (VAL, CIC-v2 seed 42, ck1_L): PR-AUC 0.869 vs GDAE 0.949 / Anomal-E 0.956. At the benign-only 0.3 % FPR threshold the
largest attack, DDOS-HOIC (10.8k val flows), is flagged 7 %, LOIC-HTTP 5 %, Bot 6 %, Infiltration 3 %: per-flow they look like benign HTTP.
What the GNN baselines have and we lack is one-hop host context (E-GraphSAGE mean-aggregates the edges at the source and destination IP).
H8: appending, to each flow's log-rescaled features, the MEAN log-rescaled features of all flows in the same split partition that share
its source IP, and those that share its destination IP (closed-form one-hop mean aggregation, no training), lets benign-only kNN
separate host-level attacks. Context is computed inside each partition (train-benign / val / test) separately, as the GNN papers build
one graph per split. Counts/degrees are NOT used (partition sizes differ 8:1:1), only means.
Predictions (VAL only): P1 CIC PR-AUC rises above 0.90; P2 HOIC/LOIC flag rates rise substantially; P3 UNSW does not drop > 0.01.
