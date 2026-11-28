# HoCo-kNN: training-free host-context nearest neighbours for benign-only NetFlow intrusion detection

**Authors:** [to be completed by the authors] · **Affiliations:** [to be completed by the authors] · **Corresponding author:** [to be completed by the authors]

## Abstract
Anomaly-based network intrusion detectors are trained on benign traffic so that they can flag attacks they have never seen. The
strongest recent one-class detectors for NetFlow records build traffic graphs, train graph neural networks (GNNs) on GPUs, and choose
their final model with a validation metric that needs attack labels. We asked how much of their accuracy really requires graph
learning. A plain nearest-neighbour detector already competes with them on NF-UNSW-NB15-v2 but fails on NF-CSE-CIC-IDS2018-v2, where
it misses most of the largest attack. Two causes explained the failure: min–max scaling hides the heavy-tailed byte, packet and
duration counters, and many attacks are visible only in the behaviour of the host that sends them. We propose HoCo-kNN, which
log-rescales flow features and appends, in closed form, the mean behaviour of all flows from the same source host — the one-hop
aggregation that E-GraphSAGE-based detectors learn — and then scores flows by their distance to benign training flows. No parameter is
trained, no attack label is used at any stage, and the alarm threshold is set from benign validation flows at a 0.3 % false-positive
budget. Under the exact protocol of the recent GDAE detector (random 8:1:1 splits, five seeds), HoCo-kNN reaches PR-AUC 0.9299 on
NF-UNSW-NB15-v2 and 0.9809 on NF-CSE-CIC-IDS2018-v2, against 0.8591 and 0.9486 reported for GDAE, and runs on a 4-core CPU. Its
Macro-F1 is higher than GDAE's on NF-CSE-CIC-IDS2018-v2 (0.9718 vs 0.9571) but lower on NF-UNSW-NB15-v2 (0.8783 vs 0.9491). We also show
that much of the host-context gain on NF-CSE-CIC-IDS2018-v2 comes from dedicated attacker machines in the testbed, a property that
graph-based detectors exploit as well.

**Keywords:** network intrusion detection; one-class anomaly detection; NetFlow; nearest neighbours; graph neural networks; reproducibility

## 1 Introduction
Intrusion detection systems that match known signatures cannot recognise new attacks. Anomaly detectors take the opposite route: they
learn what normal traffic looks like and raise an alarm for anything that does not fit. In an operational network this only helps if
false alarms stay rare — an analyst who receives thousands of alerts per hour stops reading them — so a detector must be judged at a
low false-positive rate, and its threshold must be chosen without knowing which future flows are attacks.

The standardised NetFlow-v2 datasets of the University of Queensland (Sarhan et al. 2022) made it possible to compare such detectors
on common flow features. On these datasets, the best recent one-class detectors are graph-based: Anomal-E (Caville et al. 2022),
GraphIDS (Guerra et al. 2026) and GDAE (JKSU-CIS, 2026) turn hosts into nodes and flows into edges, learn E-GraphSAGE edge embeddings
from benign traffic, and score test flows by reconstruction or discrimination losses. Two aspects of this line of work motivated our
study. First, the classical baselines reported next to these models are weak — isolation forest reaches PR-AUC 0.1888 on
NF-UNSW-NB15-v2 in GDAE's comparison — and no nearest-neighbour baseline is reported, although nearest neighbours are among the
strongest one-class detectors on tabular data. Second, GraphIDS and GDAE stop training at the epoch with the best validation PR-AUC,
which requires labelled attacks in the validation set; a benign-only detector should not need them.

Our first attempt was therefore the simplest one: a nearest-neighbour detector on the 41 flow features after the same min–max scaling.
On the validation split of NF-UNSW-NB15-v2 it already matched the graph models' reconstruction baselines, but on NF-CSE-CIC-IDS2018-v2
it let most of the largest attack, DDoS-HOIC, pass undetected at a 0.3 % false-positive budget. Examining these misses taught us two
things. The counters that describe a flow (bytes, packets, durations, throughput) span several orders of magnitude, so after min–max
scaling almost every benign and malicious flow sits near zero and the distance ignores them. And a single HOIC request looks like an
ordinary HTTP flow; what gives it away is the host that sends thousands of near-identical requests to the same server.

The second observation is exactly what graph-based detectors encode with their first message-passing layer: E-GraphSAGE averages the
features of the edges incident to a node. That average does not need to be learned. Computing it directly, and placing it next to the
flow's own (log-rescaled) features, turned the failed nearest-neighbour detector into the most accurate detector we evaluated.

Our contributions are:
1. **HoCo-kNN**, a training-free, CPU-only one-class detector that combines log-rescaled flow features with closed-form source-host
   context and scores flows by nearest-neighbour distance to benign traffic (Section 4).
2. **A strictly benign-only protocol**: no attack labels for training, model selection or threshold setting; all design choices were
   made on the validation split of one seed and the test splits were used once (Section 5).
3. **Results under GDAE's exact protocol** with five seeds, a comparison with all eight methods of GDAE's Table 5, and an ablation of
   every component (Tables 2–4).
4. **An analysis of where host context helps and where the testbed inflates it**, including per-attack detection rates and the share of
   attack traffic that comes from dedicated attacker machines (Section 7).

## 2 Related work
**One-class flow-based detection.** Isolation forest, HBOS, one-class SVM, autoencoders and Deep SVDD are the usual benign-only
detectors for flow records; on NetFlow-v2 they are typically reported as weak baselines (GDAE, Table 5).
**Graph-based detection on NetFlow.** E-GraphSAGE (Lo et al. 2022) introduced edge-level graph learning for NetFlow; Anomal-E adapted it
to self-supervised training with Deep Graph Infomax; GraphIDS adds a masked transformer autoencoder; GDAE combines local and global
autoencoders with pseudo-anomaly discrimination and an extreme-value threshold.
**Critiques of complex detectors.** FlowGuard (2026) found that PCA and an autoencoder match a graph autoencoder on NF-UNSW-NB15-v2;
GIDS-Eval (2026) reported that a control without a learned encoder can rival GNNs on other datasets; Iqbal (2026) reached a similar
conclusion in the supervised setting. None of these compares nearest-neighbour detectors with GNN one-class models on both NetFlow-v2
datasets under the GDAE protocol, and none builds host context without a graph.

| Claim | Closest prior work | Difference |
|---|---|---|
| Host-level context improves one-class NetFlow detection | Anomal-E, GraphIDS, GDAE (learned E-GraphSAGE aggregation) | Same one-hop aggregation, computed in closed form; no training, no GPU |
| Simple detectors can rival graph models | FlowGuard 2026 (UNSW-v2 only, PCA/AE) | Both NetFlow-v2 datasets, GDAE protocol, five seeds, nearest neighbours, ablation |
| Label-free operation | GDAE (EVT threshold on benign validation, but labelled early stopping) | No attack label anywhere, including model selection |

## 3 Problem formulation and the failed first attempt
Each flow is a vector x of 41 NetFlow-v2 features (IP addresses and timestamps are removed). A detector is fitted on benign training
flows only and outputs a score s(x); a flow is flagged when s(x) exceeds the 99.7 % quantile of the scores of benign validation flows,
i.e. at a target false-positive rate of 0.3 %, the same target GDAE uses for its extreme-value threshold.

The raw nearest-neighbour detector (distance to the closest of 200 000 unique benign training flows) reaches test PR-AUC 0.7808 on
NF-UNSW-NB15-v2 and 0.8914 on NF-CSE-CIC-IDS2018-v2 (Table 3). At the 0.3 % budget it flags 5.8 % of DDoS-HOIC flows and 5.6 % of
DDoS-LOIC-HTTP flows (Table 5) — the largest and third-largest attack classes of NF-CSE-CIC-IDS2018-v2. Its Macro-F1 on that dataset,
0.7352, is far below the graph models.

## 4 Method: HoCo-kNN
**Log rescaling.** With x ∈ [0,1]^41 after min–max scaling fitted on benign training flows, each feature is mapped to
φ(x) = log(1 + c·x) / log(1 + c) with c = 10^4, which stretches the lower range where nearly all flows lie.
**Source-host context.** For a set of flows F (one set per split, as the graph-based detectors build one graph per split) and a flow i
with source host u(i), h(i) = mean over j ∈ F with u(j) = u(i) of φ(x_j). The representation is z(i) = [φ(x_i), h(i)] ∈ R^82.
IP addresses are used only to group flows; they never enter the representation.
**Scoring and threshold.** s(i) is the Euclidean distance from z(i) to its nearest neighbour among R = 200 000 unique benign training
representations (sampled with the run seed). The threshold is the 99.7 % quantile of s over benign validation flows.
**Why each part exists.** Log rescaling addresses the scale failure of Section 3; source-host context addresses the per-flow blindness
to host-level attacks; the nearest-neighbour rule keeps the detector free of trained parameters.
**Cost.** The context costs one pass over F. Scoring is brute force over R; approximate nearest-neighbour indexes would reduce it further.

## 5 Experimental setup
**Data.** NF-UNSW-NB15-v2 (2 390 275 flows, 3.98 % attacks, all used) and NF-CSE-CIC-IDS2018-v2 (18 893 708 flows, 11.95 % attacks;
10 % stratified sample by attack type, as in GDAE), official open-access release of the University of Queensland.
**Protocol (replicating GDAE Section 3.2.2).** IP addresses removed as features; missing and infinite values set to 0; random 8:1:1 split
stratified by attack type; attacks removed from the training part; min–max scaling fitted on the training part; seeds 42, 123, 456,
789 and 1234.
**Design hygiene.** All design decisions (log constant, context type, k, reference size) were taken on the validation split of seed 42,
with the threshold set on one half of the benign validation flows and metrics computed on the other half. The final configuration and
the predictions to be tested were written down before the test splits were used (plan_v5).
**Baselines.** We re-ran isolation forest, HBOS, PCA and raw nearest neighbours on the same splits, and compare with all methods of
GDAE's Table 5 using the means and standard deviations reported there (GDAE's code is not available).
**Statistics.** Five-seed mean ± standard deviation; Welch tests against reported results (n = 5 on both sides); paired t-tests against
our own baselines; Holm correction over all comparisons of the plan.
**Hardware and software.** 4 CPU cores, 15 GB RAM, no GPU; Python 3.13, scikit-learn, PyOD 3.6.9.

## 6 Results
**Table 2. Comparison with the methods of GDAE's Table 5 (test sets, mean ± sd over five seeds).**

{{TABLE_MAIN}}

HoCo-kNN has the highest PR-AUC on both datasets. On NF-CSE-CIC-IDS2018-v2 it also has the highest Macro-F1 (0.9718; GDAE 0.9571). On
NF-UNSW-NB15-v2 its Macro-F1 (0.8783) is lower than that of GDAE (0.9491), GraphIDS (0.9410), the autoencoder (0.9256) and Anomal-E
(0.9214): it ranks attacks better, but at our label-free 0.3 % operating point it recovers fewer of them. Our re-runs of isolation forest
and HBOS land close to, but not exactly at, GDAE's numbers (Table 2), which we attribute to implementation details we cannot check.

**Table 3. Ablation (test sets, mean ± sd over five seeds).**

{{TABLE_ABL}}

Each component helps on both datasets: log rescaling raises PR-AUC from 0.7808 to 0.8691 on NF-UNSW-NB15-v2 and from 0.8914 to 0.9191
on NF-CSE-CIC-IDS2018-v2, and source-host context raises it further to 0.9299 and 0.9809. Adding destination-host context does not
help on average. Source context alone, without the flow's own features, already reaches 0.9784 on NF-CSE-CIC-IDS2018-v2 — a warning we
return to in Section 7.

**Table 4. Statistical comparison with reported results (Welch tests, Holm-adjusted over all comparisons of the plan).**

{{TABLE_STATS}}

**Runtime (mean over five seeds, 4-core CPU, one core per job).**

{{TABLE_RUNTIME}}

## 7 Analysis
**Table 5. Share of each attack class flagged at the benign-only 0.3 % false-positive threshold (%, mean over five seeds).**

{{TABLE_ATTACK}}

**Where host context helps.** Attacks carried out by one host against one service — DDoS-HOIC (5.8 % flagged by raw nearest neighbours,
100.0 % by HoCo-kNN), DDoS-LOIC-HTTP (5.6 % → 100.0 %), SQL injection and web brute force — become trivially separable once the
host's behaviour is visible.
**Where it does not.** Infiltration, in which an internal machine is compromised and keeps producing normal traffic, stays at 25.1 %.
Bot traffic drops from 100.0 % to 67.0 %, because the bots' hosts also carry flows that dilute their context.
**How much is testbed design.** In NF-CSE-CIC-IDS2018-v2, only 11.5 % of test attack flows come from source hosts that also appear in
benign training, and an attacker's test flows are on average 93.1 % attacks. Dedicated attacker machines make host context easy, which
is why source context alone already scores 0.9784. In NF-UNSW-NB15-v2, every attack flow comes from a host that also sends benign flows
and attackers' flows are 84.0 % attacks; there, context adds less (Table 3) and the flow's own features matter more. We regard the
NF-UNSW-NB15-v2 results as the more realistic estimate. The graph-based detectors aggregate exactly the same host neighbourhood, so the
comparison with them remains like for like.

## 8 Threats to validity and limitations
- **Random splits.** Following GDAE, flows of the same host appear in training and test. NetFlow-v2 carries no timestamps, so a
  temporal split cannot be built on these datasets.
- **Transductive context.** Host context is computed over the evaluated split, like the graph built by the GNN detectors. A deployed
  system would compute it over a sliding time window; we have not evaluated that setting.
- **Testbed inflation.** On NF-CSE-CIC-IDS2018-v2 most attack traffic comes from dedicated machines (Section 7).
- **Reported baselines.** GDAE, GraphIDS and Anomal-E numbers are taken from GDAE's Table 5 (means and standard deviations), not
  re-run; GDAE's code is not public, and its baseline numbers were not produced on our exact splits.
- **Operating point.** Our Macro-F1 depends on the fixed 0.3 % budget; GDAE's threshold procedure differs, and on NF-UNSW-NB15-v2 our
  Macro-F1 is lower.
- **Two datasets.** Both are testbed captures; results on production traffic may differ.

## 9 Conclusion
On both NetFlow-v2 benchmarks used by the recent one-class GNN detectors, a nearest-neighbour detector with log-rescaled features and
closed-form source-host context ranks attacks better than the published graph models, without training, without a GPU and without
attack labels. Most of what the graph contributes on these benchmarks can be computed with one averaging step. At the same time, the
size of the gain on NF-CSE-CIC-IDS2018-v2 owes much to dedicated attacker machines, and on NF-UNSW-NB15-v2 our label-free operating
point yields a lower Macro-F1 than GDAE. Future work should evaluate host context over time windows on traffic with timestamps.

## Declarations
**Data availability.** NF-UNSW-NB15-v2 and NF-CSE-CIC-IDS2018-v2 are openly available from the University of Queensland research data
manager. **Code availability.** [repository link to be added by the authors]. **Funding, conflicts of interest, ethics, author
contributions, use of AI assistance:** [to be completed by the authors].

## References
[To be formatted in the journal style by the authors; sources opened during this work:]
- GDAE: Dual-autoencoder multi-task self-supervised one-class graph anomaly detection for network traffic, J. King Saud Univ. Comput. Inf. Sci., 2026, doi:10.1007/s44443-026-01241-0.
- Sarhan M, Layeghy S, Portmann M (2022) Towards a standard feature set for network intrusion detection system datasets. Mobile Networks and Applications.
- Caville E, Lo WW, Layeghy S, Portmann M (2022) Anomal-E: a self-supervised network intrusion detection system based on graph neural networks. Knowledge-Based Systems.
- Lo WW, Layeghy S, Sarhan M, Gallagher M, Portmann M (2022) E-GraphSAGE: a graph neural network based intrusion detection system for IoT. NOMS.
- Guerra et al. (2026) GraphIDS (details: literature/prior_art_v2/nfv2_oneclass.md).
- FlowGuard (2026), doi:10.1922/comdem.v3i3s.18688; GIDS-Eval (CCS 2026); Iqbal (2026), arXiv 2611.04660 (details: literature/prior_art_v2/nfv2_oneclass.md).
- Liu FT, Ting KM, Zhou ZH (2008) Isolation forest. ICDM. · Goldstein M, Dengel A (2012) HBOS. KI.
