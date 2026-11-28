# Review — Reviewer 2 (novelty and related work), Round 1

**Manuscript:** "HoCo-kNN: training-free host-context nearest neighbours for benign-only NetFlow intrusion detection"
**Journal:** J. King Saud Univ. – Computer and Information Sciences
**Score:** 5 / 10
**Recommendation:** Major revision

## Summary of the submission
The authors put a 1-nearest-neighbour detector on log-rescaled NetFlow-v2 features and add, for each flow, the mean feature vector of all flows from the same source IP in the same split ("host context"). No parameters are trained and no attack labels are used; the threshold is the 99.7 % quantile of benign validation scores. Under GDAE's 8:1:1 protocol over five seeds, they report higher PR-AUC than every method in GDAE's Table 5 on NF-UNSW-NB15-v2 and NF-CSE-CIC-IDS2018-v2. Macro-F1 is higher on CIC-2018-v2 but clearly lower on UNSW-v2. They argue that the host mean is "the one-hop aggregation that E-GraphSAGE-based detectors learn", so most of what the graph contributes can be computed in closed form.

## Overall assessment of novelty and significance
The empirical finding is useful for JKSU-CIS readers. Under the GNN papers' own protocol, a training-free CPU detector matches or beats them on PR-AUC on both NetFlow-v2 benchmarks. No published work reports a kNN baseline there; I checked GraphIDS, GDAE, Anomal-E, FlowGuard, Iqbal 2026, GIDS-Eval and R+R. The benign-only selection protocol is also a fair point against GraphIDS and GDAE, which both early-stop on validation PR-AUC.

The *methodological* novelty is much smaller than the paper implies, for two reasons.

1. Per-source-host aggregate features are one of the oldest ideas in network intrusion detection, and the paper cites none of that work. Examples:
   - KDD'99 / Lee–Stolfo "time-based traffic features" (same-host counts over 2 s windows and the last 100 connections);
   - the UNSW-NB15 `ct_*` features (`ct_src_ltm`, `ct_srv_src`, `ct_dst_src_ltm`, …), which are per-source-IP statistics over the last 100 connections in the *parent dataset* of NF-UNSW-NB15-v2;
   - Kitsune's damped-window per-source-IP, per-channel and per-socket statistics;
   - host and behaviour profiling (Xu et al. 2005, BLINC) and NetFlow server profiling (Disclosure).
2. "Precompute the neighbourhood mean in closed form, then use a simple model" is exactly SGC/SIGN in the graph-learning literature.

The contribution should be repositioned. It is not a new representation. It is a controlled demonstration that the classical host-aggregate idea, when re-introduced into the NetFlow-v2 benchmark (which removed it), accounts for most of the published GNN gain. That framing is honest and still publishable.

The central mechanistic claim is also inaccurate as stated (Concern 1). Combined with the attacker-host shortcut the authors themselves document (Concern 3), the significance of the CIC-2018-v2 result is uncertain.

## Numbered concerns

### 1. [MAJOR] "Closed-form host context = what E-GraphSAGE's first layer learns" is inaccurate.
I read the public implementations: github.com/waimorris/Anomal-E (notebook `Anomal_E_cicids2017.ipynb`) and github.com/lorenzo9uerra/GraphIDS (`models/graphids.py`, `utils/dataloaders.py`, `configs/NF-*-v2.yaml`). They show four differences from HoCo-kNN.
- **(a) Aggregation is not learned.** In E-GraphSAGE the mean over incident edges is a fixed operator. What is learned is the linear map plus ReLU applied after it (`W_apply` / `fc_neigh`), and a second linear map over the *concatenation of both endpoint embeddings* (`W_edge` / `fc_edge`). HoCo removes the learned maps, not the aggregation. "Learned" should become "computes and then transforms with learned weights".
- **(b) Wrong neighbourhood.** HoCo averages the *outgoing* flows of the *source* host.
  - Anomal-E builds an undirected `nx.MultiGraph` and calls `to_directed()`, so every node averages *all incident flows, in and out*.
  - GraphIDS builds a directed graph and aggregates to the *destination* node (scatter-mean over incoming edges, "mean of incoming edges" in the docstring). The source endpoint's embedding therefore summarises flows *received by* the attacker, which is often empty, so the vector is zero. The source-out mean that drives HoCo's gains (Table 3) is not available to GraphIDS's first layer at all.
  - Both models then concatenate *source and destination* node embeddings. The nearest analogue in the ablation is "source + destination context", and even that ablation uses directed out/in means rather than the all-incident mean.
- **(c) Different inputs and sampling.** The GNNs average min–max features, not log-rescaled ones. GraphIDS also uses `LinkNeighborLoader` with fanout 32 768, so its mean is sampled for high-degree nodes.
- **(d) GDAE's code is unavailable,** so its aggregation cannot be verified at all.

The sentence in Section 7, "The graph-based detectors aggregate exactly the same host neighbourhood, so the comparison remains like for like", is not supported.

*What would resolve this:*
- Rewrite the claim as "inspired by the one-hop mean aggregation used by E-GraphSAGE".
- State precisely how each detector's neighbourhood is defined: incident vs. out vs. in, which endpoints are used, and the sampling.
- Add an ablation that reproduces the E-GraphSAGE neighbourhood exactly. That means the all-incident mean for both endpoints, concatenated, on min–max features without log. This shows how much of the gain comes from the neighbourhood definition and how much from the log transform.
- Ideally, add one sanity run: GraphIDS's public code with a reversed or symmetrised edge index.

### 2. [MAJOR] The classical host-aggregation literature is missing, so the novelty claim is overstated.
The related-work table says that no prior work "builds host context without a graph". That holds only inside the GNN-on-NetFlow-v2 niche. Per-host and time-window aggregates are standard NIDS features (references R1–R6 below). NF-UNSW-NB15-v2 was derived from UNSW-NB15, whose original CSV ships per-source-IP connection-count features (`ct_src_ltm`, `ct_srv_src`, `ct_dst_src_ltm`, etc.). NetFlow-v2 dropped them. Kitsune's incremental per-source statistics are the canonical *unsupervised*, closed-form host context. Related NetFlow-v2 work on temporal/window features exists from the dataset authors' own group (R8).

*What would resolve this:*
- Add a related-work paragraph on host and time-window aggregate features (R1–R6, R8).
- Add one on precomputed graph aggregation (SGC/SIGN, R9–R10).
- Re-state contribution 1 as "re-introducing classical per-host aggregate features into the one-class NetFlow-v2 benchmark and showing they account for the reported GNN gain", not as a new detector design.
- Ideally, add a Kitsune-style baseline: damped per-source-IP statistics plus kNN, or KitNET. This would show whether the plain mean matters or any host aggregate would do.

### 3. [MAJOR] Host context on CIC-2018-v2 is largely an attacker-identity shortcut, and that limits significance.
The authors' own numbers support this reading:
- source context *without the flow's own features* reaches PR-AUC 0.9784;
- 88.5 % of test attack flows come from hosts never seen in benign training;
- attacker hosts send 93.1 % attack flows.

The per-split mean is therefore close to a lookup of "is this one of the attacker machines". The statement that "IP addresses never enter the representation" is formally true, but the host mean is a fingerprint of the IP, which is the shortcut that Arp et al. (R11) and Sommer & Paxson (R12) warn about. Saying that GNNs exploit the same shortcut does not make it a scientific contribution. It shows that the benchmark, not the method, decides the result. On UNSW-v2, which the authors call the more realistic dataset, the context gain is +0.06 PR-AUC and Macro-F1 is significantly worse than all four learned baselines.

*What would resolve this:*
- Move this analysis forward into the abstract and conclusion as a primary finding.
- Report a host-disjoint evaluation (group split by source IP), or at least results restricted to attack flows from hosts that also send benign flows.
- Report a mixed-host control: dilute attacker hosts with benign flows, or evaluate only on "mixed" hosts.
- Without this evidence, the claim that HoCo-kNN is "the most accurate detector" should be limited to these testbeds.

### 4. [MAJOR] Positioning against "simple beats GNN" critiques must be sharper.
FlowGuard (UNSW-v2, PCA/AE ≥ graph AE), GIDS-Eval (an encoder-free control ranks first on 2 of 4 datasets, CCS 2026), R+R (ACSAC 2025) and Iqbal 2026 (kNN ≥ R-GCN, supervised) together already establish the general message. The Zhou 2026 controlled topology study (DOI 10.1145/3856389.3856511) is directly relevant and absent: it finds that real topology beats randomised graphs on PR-AUC, but the GNN loses to PCA on thresholded F1. That mirrors this paper's PR-AUC/F1 split on UNSW-v2. Literature on kNN as a strong tabular one-class detector (ADBench, DN2) is also uncited, though it is used as motivation.

*What would resolve this:*
- Cite and discuss Zhou 2026, R+R, ADBench and DN2 (R13–R16).
- State explicitly that the incremental novelty over these works is (i) both NF-v2 datasets under the GDAE protocol, (ii) a fully label-free protocol, and (iii) identifying *which* GNN component (the host mean) carries the signal.

### 5. [MAJOR] PR-AUC superiority mixes re-implemented and copied numbers, and the operating-point comparison is not like for like.
All GNN numbers are copied from GDAE's Table 5. The prior-art notes record that GDAE's UNSW-v2 baseline values nearly coincide with GraphIDS's own paper. GDAE's splits are not the authors' splits, and their own IF/HBOS re-runs deviate strongly from GDAE's (UNSW HBOS PR-AUC 0.53 vs 0.32; CIC Macro-F1 0.50 vs 0.84). A Welch test with n = 5 against copied means is weak evidence of superiority. GraphIDS has public code (Apache-2.0), so at least one GNN can be re-run on identical splits.

*What would resolve this:*
- Re-run GraphIDS on the same five splits. Report it both with its labelled early stopping and with a benign-only selection rule, which also quantifies the label-selection advantage the paper criticises.
- Compare at matched operating points: Macro-F1 at the same achieved FPR, and report the achieved test FPR for HoCo-kNN.

### 6. [MINOR] Transductive context.
h(i) for a test flow is the mean over *all test-split flows* of that host, including future flows and the other attack flows. This is as transductive as the GNN graphs, but it is not deployable as-is. The limitations section already says so.

*What would resolve this:* A simple causal variant, e.g. a running mean over each host's previous flows in file order. A Kitsune-style damped mean is the natural choice (see Concern 2).

### 7. [MINOR] Duplicates.
Iqbal 2026 reports 69 % exact duplicates in NF-UNSW-NB15-v2. A 1-NN detector benefits disproportionately from exact train/test matches of benign flows, which lowers benign scores. The "200 000 unique benign" reference set partly addresses this, but train–test overlap is not reported.

*What would resolve this:* Report the share of benign and attack test vectors with an exact match in training, and the PR-AUC after de-duplication.

### 8. [MINOR] Wording and references.
- "the most accurate detector we evaluated" and "Most of what the graph contributes … can be computed with one averaging step" should be qualified by dataset and metric (not Macro-F1 on UNSW-v2).
- The reference list is incomplete: GDAE has no authors (Zhao et al.); GraphIDS is NeurIPS 2025, DOI 10.52202/085713-3653, arXiv 2509.16625; GIDS-Eval is DOI 10.1145/3830454.3846576, arXiv 2609.12263.
- The manuscript cites internal files ("plan_v5", "literature/prior_art_v2/…"). These must be removed or replaced by a public pre-registration or repository link.

### 9. [MINOR] Log constant and bot dilution.
The log constant c = 10^4 was selected on seed-42 validation. A sensitivity plot (c ∈ {10, 10², …, 10⁶}) would show that the gain is not tuned. The drop in Bot detection (100 % → 67 %) shows that mean aggregation dilutes mixed hosts. Discuss max/variance or count-type aggregates, as in Kitsune and UNSW `ct_*` features.

## Missing references (each verified via Crossref or the arXiv API on 2026-11-28)
| # | Reference | Identifier |
|---|---|---|
| R1 | Lee W., Stolfo S. J., "A framework for constructing features and models for intrusion detection systems", ACM TISSEC 3(4), 2000 (KDD'99 time-based host features) | doi:10.1145/382912.382914 |
| R2 | Tavallaee M. et al., "A detailed analysis of the KDD CUP 99 data set", CISDA 2009 | doi:10.1109/CISDA.2009.5356528 |
| R3 | Moustafa N., Slay J., "UNSW-NB15: a comprehensive data set for network intrusion detection systems", MilCIS 2015 (per-source-IP `ct_*` features) | doi:10.1109/MilCIS.2015.7348942 |
| R4 | Mirsky Y. et al., "Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection", NDSS 2018 (damped per-host statistics, unsupervised) | doi:10.14722/ndss.2018.23204; arXiv:1802.09089 |
| R5 | Xu K., Zhang Z.-L., Bhattacharyya S., "Profiling Internet backbone traffic: behavior models and applications", SIGCOMM 2005 | doi:10.1145/1080091.1080112 |
| R6 | Karagiannis T. et al., "BLINC: multilevel traffic classification in the dark", SIGCOMM 2005 | doi:10.1145/1080091.1080119 |
| R7 | Bilge L. et al., "Disclosure: detecting botnet C&C servers through large-scale NetFlow analysis", ACSAC 2012 (per-server NetFlow aggregates) | doi:10.1145/2420950.2420969 |
| R8 | Luay M., Layeghy S., …, Portmann M., "Time Matters: Temporal NetFlow Features for ML-Based Network Intrusion Detection", IEEE Access 2026 (existence and authors verified; content not read) | doi:10.1109/ACCESS.2026.3688204 |
| R9 | Wu F. et al., "Simplifying Graph Convolutional Networks", ICML 2019 (closed-form precomputed aggregation) | arXiv:1902.07153 |
| R10 | Rossi E. et al., "SIGN: Scalable Inception Graph Neural Networks", 2020 | arXiv:2004.11198 |
| R11 | Arp D. et al., "Dos and Don'ts of Machine Learning in Computer Security", USENIX Security 2022 (spurious correlations / shortcuts) | arXiv:2010.09470 |
| R12 | Sommer R., Paxson V., "Outside the Closed World: On Using Machine Learning for Network Intrusion Detection", IEEE S&P 2010 | doi:10.1109/SP.2010.25 |
| R13 | Zhou, "A Controlled Study of Shared-Endpoint Flow Topology for Self-Supervised Network Intrusion Detection", AIIIP 2026 | doi:10.1145/3856389.3856511 |
| R14 | Wang et al., "R+R: From Claims to Crashes: A Systematic Re-evaluation of Graph-Based NIDS", ACSAC 2025 | doi:10.1109/ACSAC67867.2025.00050; arXiv:2503.20281 |
| R15 | Han S. et al., "ADBench: Anomaly Detection Benchmark", NeurIPS 2022 (kNN among the strongest tabular detectors) | arXiv:2206.09426 |
| R16 | Bergman L., Cohen N., Hoshen Y., "Deep Nearest Neighbor Anomaly Detection", 2020 | arXiv:2002.10445 |
| R17 | Bilot T. et al., "Graph Neural Networks for Intrusion Detection: A Survey", IEEE Access 2023 | doi:10.1109/ACCESS.2023.3275789 |
| R18 | Lo W. W. et al., E-GraphSAGE, NOMS 2022 (add DOI) | doi:10.1109/NOMS54207.2022.9789878; arXiv:2103.16329 |
| R19 | Caville E. et al., Anomal-E, Knowledge-Based Systems 258:110030, 2022 (add DOI) | doi:10.1016/j.knosys.2022.110030; arXiv:2207.06819 |
| R20 | Sarhan M. et al., "Towards a Standard Feature Set for NIDS Datasets", MONET (online 2021) | doi:10.1007/s11036-021-01843-0 |

I found no paper that runs kNN with per-host aggregate features on NF-UNSW-NB15-v2 or NF-CSE-CIC-IDS2018-v2 in the one-class setting. The search covered OpenAlex, Crossref, arXiv and the web. The specific empirical combination therefore appears new; the ingredients do not.

## Confidential note to the editor
The empirical result is solid enough to deserve publication once it is repositioned. The two things that must change are the inaccurate "same aggregation as E-GraphSAGE" claim and the missing classical host-feature literature. A re-run of GraphIDS (public code) on identical splits would turn a suggestive comparison into a convincing one.
