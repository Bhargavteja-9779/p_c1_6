# Prior art for H7 angle selection (2026-11-25, session 3)
Sub-agent search: 61 queries (OpenAlex with abstracts + arXiv; Semantic Scholar HTTP 429 throughout), 28 papers opened (abstract
level), 6 located by title only (UNVERIFIED). Query log per angle kept in the sub-agent report summarised here.

| Angle | Verdict | Closest work |
|---|---|---|
| (a) reverse-neighbour / hubness scores (ODIN 10.1109/icpr.2004.1334558; AntiHub 10.1109/tkde.2014.2365790; RDOS arXiv 1606.08538; CFOF arXiv 1901.04992) | done as scores; none targets masking. Our diagnostic (journal 26): in-degree AUROC 60.3 < kNN5 72.8 → dropped | Hierarchical Reference Sets arXiv 2603.12847; Cluster Catch Digraphs arXiv 2409.11596 |
| (b) cross-fitting / sample splitting (SRR arXiv 2106.06115; Zimek et al. 10.1145/2487575.2487676; LOO influence arXiv 2607.14335) | partly done (random folds / point-level). Per-query leave-OWN-CLUSTER-out at test time not found | D.MCA 10.1109/icdm54844.2022.00119 (global, iterative micro-cluster pruning) |
| (c) adaptive k / distance profile | largely done; our diagnostic: profile-jump AUROC 44.5 → dropped | McCatch 10.1109/icde60146.2024.00116 (1NN vs group-1NN "oracle plot") |
| (d) subsampling isolation (iNNE 10.1111/coin.12156; IDK 10.1145/3394486.3403062) | done as mechanism; iNNE claims masking robustness → **mandatory baseline** | iNNE |
| (e) clustered anomalies / contamination-robust (D.MCA, McCatch, Gen2Out 10.1109/bigdata52589.2021.9671550, LOE arXiv 2202.08088, AAR arXiv 2511.21378, TabADM arXiv 2307.12336, mean-shift OD 10.1016/j.patcog.2021.107874) | done; all filter/reweight the training set (circular family, cf. H5) or are transductive | D.MCA, McCatch |
To read before any novelty claim: Tabasi & Gupta 2026 "Contaminated by Construction" (10.2139/ssrn.7415960, title only); D.MCA full
pruning procedure; McCatch scoring.

## CLAIM → CLOSEST PRIOR WORK → EXACT DIFFERENCE (H7)
Leave-own-cluster-out kNN (LOCO-kNN): score a test point by its kNN distance to the contaminated training set after removing the
small mutual-kNN component(s) its nearest training neighbours belong to → D.MCA (global iterative pruning of micro-clusters from the
training set) and McCatch (group-1NN distance over detected micro-clusters) → exclusion is per query, at scoring time, non-iterative,
needs no contamination ratio, and is tested against an oracle-clean reference in an inductive contaminated-train protocol.
