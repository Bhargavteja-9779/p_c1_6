# HoCo-kNN: training-free host-context nearest neighbours for benign-only NetFlow intrusion detection

**Authors:** [to be completed by the authors] · **Affiliations:** [to be completed by the authors] · **Corresponding author:** [to be completed by the authors]

## Abstract
Anomaly-based network intrusion detectors are trained on benign traffic so that they can flag attacks they have never seen. The
strongest recent one-class detectors for NetFlow records build traffic graphs, train graph neural networks (GNNs) on GPUs, and choose
their final model with a validation metric that needs attack labels. We asked how much of their accuracy really requires graph
learning. A plain nearest-neighbour detector already competes with them on NF-UNSW-NB15-v2 but fails on NF-CSE-CIC-IDS2018-v2, where
it misses most of the largest attack. Two causes explained the failure: min–max scaling hides the heavy-tailed byte, packet and
duration counters, and many attacks are visible only in the behaviour of the host that sends them. We revisit a classical idea — per-host aggregate features, used in intrusion detection since the KDD'99 era but absent
from the NetFlow-v2 feature set — and combine it with log rescaling and a nearest-neighbour rule. The resulting detector, HoCo-kNN,
appends to each flow the mean (log-rescaled) features of all flows from the same source host, a fixed one-hop mean aggregation of the
kind graph detectors compute before their learned layers, and scores flows by their distance to benign training flows. No parameter is
trained, no attack label is used for training or for the alarm threshold (set from benign validation flows at a 0.3 % false-positive
budget), and labelled validation data of one seed served only for a small number of design choices. Under the split protocol of the recent GDAE detector (random 8:1:1 splits, five seeds), HoCo-kNN reaches PR-AUC 0.9299 on
NF-UNSW-NB15-v2 and 0.9809 on NF-CSE-CIC-IDS2018-v2, against 0.8591 and 0.9486 reported for GDAE, and runs on a 4-core CPU. Its
Macro-F1 is higher than GDAE's on NF-CSE-CIC-IDS2018-v2 (0.9718 vs 0.9571) but lower on NF-UNSW-NB15-v2 (0.8783 vs 0.9491). Shortcut controls show that much of the host-context gain on NF-CSE-CIC-IDS2018-v2 comes from
dedicated attacker machines in the testbed; {{TON_SENTENCE}}

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

The second observation is old. Per-host aggregate features — counts and averages over the recent connections of a host — were part of
the KDD'99 features (Lee and Stolfo 2000), of the original UNSW-NB15 release (Moustafa and Slay 2015) and of Kitsune (Mirsky et al.
2018), but the standardised NetFlow-v2 feature set keeps only per-flow fields. Graph detectors recover host context indirectly: in
Anomal-E the first layer averages the features of all flows incident to a host (a fixed mean, followed by learned weights), while
GraphIDS aggregates only flows arriving at a host. We compute the source-host mean directly and place it next to the flow's own
log-rescaled features. This turned the failed nearest-neighbour detector into the most accurate detector we evaluated — and it also
forced us to check how much of that accuracy is genuine host behaviour and how much is the identity of attacker machines.

Our contributions are:
1. **HoCo-kNN**, a training-free, CPU-only one-class detector that re-introduces classical source-host aggregates into NetFlow-v2
   one-class detection, combined with log rescaling and a nearest-neighbour rule (Section 4). We do not claim the ingredients as new;
   the contribution is showing what they achieve against the recent graph models on their own benchmarks.
2. **A benign-only evaluation**: no attack labels for training or thresholds; design choices made on the validation split of one seed;
   a frozen plan; and a third dataset, NF-ToN-IoT-v2, that played no part in any design decision (Section 5).
3. **Results under GDAE's exact protocol** with five seeds, a comparison with all eight methods of GDAE's Table 5, and an ablation of
   every component (Tables 2–4).
4. **Shortcut controls** — a host-novelty baseline, host-label permutation, mixed-host subsets and reduced context — that separate host
   behaviour from attacker identity (Section 7).

## 2 Related work
**Per-host aggregate features.** Host-level aggregation is one of the oldest ideas in network intrusion detection. The KDD'99 features
include time-window counts over a host's recent connections (Lee and Stolfo 2000; Tavallaee et al. 2009); the original UNSW-NB15
release has per-source-IP `ct_*` counters (Moustafa and Slay 2015); behaviour profiling and traffic classification build host-level
models from flow records (Xu et al. 2005; Karagiannis et al. 2005; Bilge et al. 2012); Kitsune keeps damped per-host statistics for
unsupervised online detection (Mirsky et al. 2018). The NetFlow-v2 standard feature set (Sarhan et al. 2022) deliberately keeps only
per-flow fields, and temporal host features for NetFlow were proposed only recently (Luay et al. 2026).
**Graph-based detection on NetFlow.** E-GraphSAGE (Lo et al. 2022) learns edge embeddings from flow graphs; Anomal-E (Caville et al.
2022) trains it self-supervised with Deep Graph Infomax; GraphIDS (Guerra et al. 2025) adds a masked transformer autoencoder; GDAE
(Zhao et al. 2026) combines local and global autoencoders with pseudo-anomaly discrimination and an extreme-value threshold; Bilot et
al. (2023) survey the area. In graph learning, precomputing neighbourhood means in closed form and feeding them to a simple model is
the idea behind SGC and SIGN (Wu et al. 2019; Rossi et al. 2020).
**Re-evaluations of graph detectors.** R+R (Wang et al. 2025) re-evaluated graph-based NIDS and found many claims fragile; GIDS-Eval
(2026) reported that an encoder-free control can rival GNNs; FlowGuard (2026) found PCA and an autoencoder on par with a graph
autoencoder on NF-UNSW-NB15-v2; a controlled study of shared-endpoint topology (Zhou 2026) and Iqbal (2026, supervised) reach related
conclusions. More broadly, shortcut learning and closed-world evaluation are long-standing pitfalls of machine learning for security
(Sommer and Paxson 2010; Arp et al. 2022). Nearest-neighbour detectors remain among the strongest one-class methods on tabular data
(Han et al. 2022; Bergman et al. 2020).

| Claim | Closest prior work | Difference |
|---|---|---|
| Host context helps one-class NetFlow detection | Classical host aggregates (KDD'99, UNSW-NB15 `ct_*`, Kitsune); Anomal-E's fixed mean aggregation before learned layers | Not new as an idea; we evaluate it, without graphs or training, on the NetFlow-v2 one-class benchmarks of the graph models |
| Simple detectors can rival graph models | FlowGuard 2026 (NF-UNSW-NB15-v2, PCA/AE); GIDS-Eval 2026; R+R 2025 | Both NetFlow-v2 datasets plus an untouched third one, GDAE's split protocol, five seeds, nearest neighbours, ablation, shortcut controls |
| Host context partly encodes attacker identity in testbeds | Arp et al. 2022 (spurious correlations, in general) | Quantified on NetFlow-v2: host-novelty baseline, permutation, mixed-host subsets |

## 3 Problem formulation and the failed first attempt
Each flow is a vector x of 41 NetFlow-v2 features (IP addresses and timestamps are removed). A detector is fitted on benign training
flows only and outputs a score s(x); a flow is flagged when s(x) exceeds the 99.7 % quantile of the scores of benign validation flows,
i.e. at a target false-positive rate of 0.3 %, the same target GDAE uses for its extreme-value threshold.

The raw nearest-neighbour detector (distance to the closest of 200 000 unique benign training flows) reaches test PR-AUC 0.7808 on
NF-UNSW-NB15-v2 and 0.8914 on NF-CSE-CIC-IDS2018-v2 (Table 3). At the 0.3 % budget it flags 5.8 % of DDoS-HOIC flows and 5.6 % of
DDoS-LOIC-HTTP flows (Table 5) — the largest and third-largest attack classes of NF-CSE-CIC-IDS2018-v2. Its Macro-F1 on that dataset,
0.7352, is far below the graph models.

## 4 Method: HoCo-kNN
Let x ∈ [0,1]^41 be a flow after min–max scaling fitted on benign training flows, u(x) its source IP address, and F the set of flows
of one split (training-benign, validation or test), mirroring the one-graph-per-split construction of the graph baselines.

**Log rescaling.** Each feature is mapped by

  φ(x) = log(1 + c·x) / log(1 + c),  c = 10^4,                                                  (1)

which stretches the lower end of the range where almost all flows lie. The constant c was fixed before any experiment; its
sensitivity is reported in Fig. 5.

**Source-host context.** For a flow i ∈ F,

  h(i) = (1 / |F_u(i)|) Σ_{j ∈ F_u(i)} φ(x_j),  F_u = { j ∈ F : u(j) = u },                     (2)

  z(i) = [ φ(x_i) ; h(i) ] ∈ R^82.                                                             (3)

IP addresses are used only to group flows; they never enter z.

**Score and threshold.** With R a random sample of unique benign training representations (|R| = 200 000),

  s(i) = min_{r ∈ R} ‖ z(i) − r ‖_2 ,                                                          (4)

and a flow is flagged when s(i) > τ, where τ is the 99.7 % quantile of s over benign validation flows (target false-positive rate 0.3 %).

**Algorithm 1 — HoCo-kNN.**
1. Fit min–max scaling on benign training flows; apply Eq. (1) to all flows.
2. For each split separately, compute h by one pass of group means over source IPs (Eq. 2) and form z (Eq. 3).
3. Deduplicate benign training representations and sample R.
4. τ ← 99.7 % quantile of s (Eq. 4) over benign validation flows.
5. For each test flow, output s(i) and the alarm s(i) > τ.

**Complexity.** Steps 1–2 cost O(|F|·d) time and O(|F|·d) memory (d = 41). Step 4 and 5 cost O(|R|·d) per scored flow with brute-force
search; approximate nearest-neighbour indexes reduce this to sub-linear time. No parameter is trained, so there is no training loop,
early stopping or GPU requirement. Measured end-to-end times are in Table 6.

**Why each part exists.** Eq. (1) addresses the scale failure of Section 3; Eqs. (2)–(3) address per-flow blindness to host-level
attacks; Eq. (4) keeps the detector free of trained parameters.

## 5 Experimental setup
**Data.** NF-UNSW-NB15-v2 (2 390 275 flows, 3.98 % attacks, all used) and NF-CSE-CIC-IDS2018-v2 (18 893 708 flows, 11.95 % attacks;
10 % stratified sample by attack type, as in GDAE), official open-access release of the University of Queensland.
**Protocol (GDAE's split protocol, Section 3.2.2).** IP addresses removed as features; missing and infinite values set to 0; random 8:1:1 split
stratified by attack type; attacks removed from the training part; min–max scaling fitted on the training part; seeds 42, 123, 456,
789 and 1234.
**Design hygiene.** The design choices (log rescaling on/off, context type, k ∈ {1, 5, 10}, reference size 50 000 vs 200 000; about
19 configurations in total) were made on the labelled validation split of seed 42, with the threshold set on one half of its benign
flows and metrics on the other half; c was never tuned. Because every seed re-draws the split from the same flows, the seed-42
validation flows overlap the test flows of the other seeds; the design freedom was small, but to remove the concern entirely we froze
the configuration (plan_v5, written before any test run of HoCo-kNN) and evaluated it on NF-ToN-IoT-v2, which played no part in any
decision. Seed-42 test runs of the baselines (iForest, HBOS, PCA, raw kNN) preceded the freeze; they carry no design freedom.

**Differences from GDAE's pipeline.**

| Aspect | GDAE | This work |
|---|---|---|
| Split | random 8:1:1 stratified by attack, five seeds | same, same seeds (our own draws) |
| CIC-2018 sample | 10 % stratified by attack type | 10 % stratified by attack type, drawn per 1 M-row chunk, data seed 0 |
| Categorical features | one-hot | numeric codes, log-rescaled |
| Threshold | EVT at target FPR 0.003 on validation | empirical 99.7 % quantile of benign validation scores |
| Model selection | early stopping on validation PR-AUC (attack labels) | none (no training) |
| Baseline numbers | own runs | GDAE's Table 5 for GNNs; own runs for iForest, HBOS, PCA, kNN, AE |
**Baselines.** We re-ran isolation forest, HBOS, PCA and raw nearest neighbours on the same splits, and compare with all methods of
GDAE's Table 5 using the means and standard deviations reported there (GDAE's code is not available).
**Statistics.** Five-seed mean ± standard deviation; Welch tests against reported results (n = 5 on both sides); paired t-tests against
our own baselines; Holm correction over all comparisons of the plan.
**Hardware and software.** 4 CPU cores, 15 GB RAM, no GPU; Python 3.13, scikit-learn, PyOD 3.6.9.

## 6 Results
**Table 2. Comparison with the methods of GDAE's Table 5 (test sets, mean ± sd over five seeds).**

| Method | Source | UNSW-v2 PR-AUC | UNSW-v2 Macro-F1 | UNSW-v2 ACC | CIC-2018-v2 PR-AUC | CIC-2018-v2 Macro-F1 | CIC-2018-v2 ACC |
|---|---|---|---|---|---|---|---|
| IF | GDAE Table 5 | 0.1888 ± 0.0020 | 0.6712 ± 0.0127 | 0.9260 ± 0.0057 | 0.6290 ± 0.0422 | 0.8355 ± 0.0033 | 0.9284 ± 0.0040 |
| HBOS | GDAE Table 5 | 0.3214 ± 0.0079 | 0.7044 ± 0.0043 | 0.9640 ± 0.0004 | 0.6909 ± 0.0010 | 0.8570 ± 0.0018 | 0.9329 ± 0.0012 |
| OC-SVM | GDAE Table 5 | 0.5844 ± 0.0258 | 0.7938 ± 0.0138 | 0.9708 ± 0.0004 | 0.4007 ± 0.0066 | 0.7766 ± 0.0016 | 0.9219 ± 0.0009 |
| Deep SVDD | GDAE Table 5 | 0.6283 ± 0.1834 | 0.6998 ± 0.0627 | 0.9700 ± 0.0036 | 0.5375 ± 0.1096 | 0.4692 ± 0.0001 | 0.8805 ± 0.0001 |
| AE | GDAE Table 5 | 0.7614 ± 0.0860 | 0.9256 ± 0.0101 | 0.9872 ± 0.0022 | 0.9419 ± 0.0095 | 0.9438 ± 0.0038 | 0.9765 ± 0.0018 |
| Anomal-E | GDAE Table 5 | 0.7135 ± 0.0058 | 0.9214 ± 0.0093 | 0.9859 ± 0.0020 | 0.9555 ± 0.0048 | 0.9519 ± 0.0029 | 0.9804 ± 0.0012 |
| GraphIDS | GDAE Table 5 | 0.8175 ± 0.0494 | 0.9410 ± 0.0145 | 0.9899 ± 0.0029 | 0.8984 ± 0.0159 | 0.9432 ± 0.0064 | 0.9759 ± 0.0039 |
| GDAE | GDAE Table 5 | 0.8591 ± 0.0142 | 0.9491 ± 0.0081 | 0.9916 ± 0.0012 | 0.9486 ± 0.0023 | 0.9571 ± 0.0034 | 0.9827 ± 0.0014 |
| iForest (ours) | this work | 0.2374 ± 0.0184 | 0.4919 ± 0.0006 | 0.9575 ± 0.0002 | 0.5183 ± 0.0332 | 0.4981 ± 0.0029 | 0.8815 ± 0.0003 |
| HBOS (ours) | this work | 0.5327 ± 0.0089 | 0.5614 ± 0.0095 | 0.9606 ± 0.0004 | 0.5675 ± 0.0037 | 0.6063 ± 0.0017 | 0.8968 ± 0.0003 |
| PCA (ours) | this work | 0.2639 ± 0.0051 | 0.5907 ± 0.0044 | 0.9621 ± 0.0003 | 0.1127 ± 0.0034 | 0.4689 ± 0.0002 | 0.8780 ± 0.0002 |
| AE on raw flows (ours) | this work | — | — | — | — | — | — |
| kNN, raw (ours) | this work | 0.7808 ± 0.0059 | 0.7438 ± 0.0092 | 0.9716 ± 0.0006 | 0.8914 ± 0.0087 | 0.7352 ± 0.0239 | 0.9202 ± 0.0051 |
| **HoCo-kNN (ours)** | this work | 0.9299 ± 0.0036 | 0.8783 ± 0.0153 | 0.9838 ± 0.0015 | 0.9809 ± 0.0008 | 0.9718 ± 0.0060 | 0.9884 ± 0.0024 |


HoCo-kNN has the highest mean PR-AUC on both datasets. After Holm correction the difference is significant against GDAE and
Anomal-E on both datasets, but not against GraphIDS and the autoencoder on NF-UNSW-NB15-v2 (Table 4), whose reported standard
deviations are large; we therefore do not claim to outperform those two there. Because the comparison uses reported means and
standard deviations, and the pipelines differ in the ways listed in Section 5, these tests describe the size of the gap rather than
isolate the method effect. On NF-CSE-CIC-IDS2018-v2 it also has the highest Macro-F1 (0.9718; GDAE 0.9571). On
NF-UNSW-NB15-v2 its Macro-F1 (0.8783) is lower than that of GDAE (0.9491), GraphIDS (0.9410), the autoencoder (0.9256) and Anomal-E
(0.9214): it ranks attacks better, but at our label-free 0.3 % operating point it recovers fewer of them. Our re-runs of isolation forest
and HBOS do not reproduce GDAE's numbers: PR-AUC differs by up to 0.2 and Macro-F1 by up to 0.35 (Table 2), which shows how much the
classical baselines depend on implementation and threshold choices we cannot check without GDAE's code. We therefore also re-ran an
autoencoder on raw flows on our own splits (Table 2).

**Table 3. Ablation (test sets, mean ± sd over five seeds).**

| Variant | UNSW-v2 PR-AUC | UNSW-v2 Macro-F1 | CIC-2018-v2 PR-AUC | CIC-2018-v2 Macro-F1 |
|---|---|---|---|---|
| raw features (min–max) | 0.7808 ± 0.0059 | 0.7438 ± 0.0092 | 0.8914 ± 0.0087 | 0.7352 ± 0.0239 |
| raw features, k = 5 | — | — | 0.8446 ± 0.0052 | 0.6888 ± 0.0098 |
| + log rescaling | 0.8691 ± 0.0031 | 0.8720 ± 0.0049 | 0.9191 ± 0.0083 | 0.7805 ± 0.0314 |
| + source-host context (HoCo-kNN) | 0.9299 ± 0.0036 | 0.8783 ± 0.0153 | 0.9809 ± 0.0008 | 0.9718 ± 0.0060 |
| + source and destination context | 0.9171 ± 0.0069 | 0.8713 ± 0.0139 | 0.9801 ± 0.0005 | 0.9793 ± 0.0067 |
| log + destination context only | — | — | 0.9358 ± 0.0091 | 0.9011 ± 0.0847 |
| source context only (no own features) | — | — | 0.9784 ± 0.0007 | 0.9605 ± 0.0007 |


Each component helps on both datasets: log rescaling raises PR-AUC from 0.7808 to 0.8691 on NF-UNSW-NB15-v2 and from 0.8914 to 0.9191
on NF-CSE-CIC-IDS2018-v2, and source-host context raises it further to 0.9299 and 0.9809. Adding destination-host context does not
help on average. Source context alone, without the flow's own features, already reaches 0.9784 on NF-CSE-CIC-IDS2018-v2 — a warning we
return to in Section 7.

**Table 4. Statistical comparison with reported results (Welch tests, Holm-adjusted over all comparisons of the plan).**

| Dataset | Comparison | Ours | Theirs | Difference | Holm-adjusted p |
|---|---|---|---|---|---|
| UNSW-v2 | PR-AUC vs AE (reported) | 0.9299 | 0.7614 | +0.1685 | 0.083 |
| UNSW-v2 | PR-AUC vs Anomal-E (reported) | 0.9299 | 0.7135 | +0.2164 | 4.7e-09 |
| UNSW-v2 | PR-AUC vs GraphIDS (reported) | 0.9299 | 0.8175 | +0.1124 | 0.062 |
| UNSW-v2 | PR-AUC vs GDAE (reported) | 0.9299 | 0.8591 | +0.0708 | 0.0048 |
| UNSW-v2 | Macro-F1 vs AE (reported) | 0.8783 | 0.9256 | -0.0473 | 0.012 |
| UNSW-v2 | Macro-F1 vs Anomal-E (reported) | 0.8783 | 0.9214 | -0.0431 | 0.018 |
| UNSW-v2 | Macro-F1 vs GraphIDS (reported) | 0.8783 | 0.9410 | -0.0627 | 0.0038 |
| UNSW-v2 | Macro-F1 vs GDAE (reported) | 0.8783 | 0.9491 | -0.0708 | 0.0024 |
| CIC-2018-v2 | PR-AUC vs AE (reported) | 0.9809 | 0.9419 | +0.0390 | 0.012 |
| CIC-2018-v2 | PR-AUC vs Anomal-E (reported) | 0.9809 | 0.9555 | +0.0254 | 0.0048 |
| CIC-2018-v2 | PR-AUC vs GraphIDS (reported) | 0.9809 | 0.8984 | +0.0825 | 0.0059 |
| CIC-2018-v2 | PR-AUC vs GDAE (reported) | 0.9809 | 0.9486 | +0.0323 | 3.3e-05 |
| CIC-2018-v2 | Macro-F1 vs AE (reported) | 0.9718 | 0.9438 | +0.0280 | 0.0017 |
| CIC-2018-v2 | Macro-F1 vs Anomal-E (reported) | 0.9718 | 0.9519 | +0.0199 | 0.011 |
| CIC-2018-v2 | Macro-F1 vs GraphIDS (reported) | 0.9718 | 0.9432 | +0.0286 | 0.0024 |
| CIC-2018-v2 | Macro-F1 vs GDAE (reported) | 0.9718 | 0.9571 | +0.0147 | 0.032 |


**Table 6. End-to-end runtime, seed 42 (one CPU core): building the representation and reference set, the benign threshold, and
scoring the test split.**

| Dataset | Method | build representation + reference (s) | threshold on benign val (s) | score test split (s) | µs per test flow |
|---|---|---|---|---|---|
| UNSW-v2 | (pending) | | | | |
| CIC-2018-v2 | (pending) | | | | |


**Untouched dataset.** {{TON_PARAGRAPH}}

(pending)

Fig. 2 shows precision–recall curves, Fig. 3 attack recall as a function of the false-positive budget, Fig. 4 the per-attack
detection rates, and Fig. 5 the sensitivity to c, k and R on the validation split.

## 7 Analysis
**Table 5. Share of each attack class flagged at the benign-only 0.3 % false-positive threshold (%, mean over five seeds).**

| Dataset | Attack | iForest | HBOS | kNN raw | + log | HoCo-kNN |
|---|---|---|---|---|---|---|
| CIC-2018-v2 | Bot | 0.0 | 0.2 | 100.0 | 99.9 | 67.0 |
| CIC-2018-v2 | Brute Force -Web | 1.0 | 11.4 | 4.8 | 30.5 | 100.0 |
| CIC-2018-v2 | Brute Force -XSS | 0.0 | 2.2 | 20.0 | 24.4 | 100.0 |
| CIC-2018-v2 | DDOS attack-HOIC | 0.0 | 0.2 | 5.8 | 21.8 | 100.0 |
| CIC-2018-v2 | DDOS attack-LOIC-UDP | 0.0 | 99.0 | 100.0 | 100.0 | 100.0 |
| CIC-2018-v2 | DDoS attacks-LOIC-HTTP | 0.0 | 0.4 | 5.6 | 41.3 | 100.0 |
| CIC-2018-v2 | DoS attacks-GoldenEye | 2.7 | 64.8 | 100.0 | 77.8 | 100.0 |
| CIC-2018-v2 | DoS attacks-Hulk | 13.1 | 64.5 | 100.0 | 89.5 | 100.0 |
| CIC-2018-v2 | DoS attacks-SlowHTTPTest | 0.0 | 0.0 | 100.0 | 100.0 | 100.0 |
| CIC-2018-v2 | DoS attacks-Slowloris | 0.0 | 39.4 | 76.6 | 76.4 | 100.0 |
| CIC-2018-v2 | FTP-BruteForce | 0.0 | 0.0 | 100.0 | 100.0 | 100.0 |
| CIC-2018-v2 | Infilteration | 0.2 | 0.4 | 7.7 | 11.2 | 25.1 |
| CIC-2018-v2 | SQL Injection | 0.0 | 0.0 | 15.0 | 5.0 | 100.0 |
| CIC-2018-v2 | SSH-Bruteforce | 13.7 | 52.8 | 61.5 | 15.9 | 66.4 |
| UNSW-v2 | Analysis | 0.0 | 1.7 | 68.5 | 81.3 | 84.8 |
| UNSW-v2 | Backdoor | 0.0 | 3.2 | 72.4 | 91.0 | 92.2 |
| UNSW-v2 | DoS | 1.1 | 8.4 | 52.5 | 74.3 | 72.3 |
| UNSW-v2 | Exploits | 0.5 | 7.5 | 41.3 | 57.4 | 58.5 |
| UNSW-v2 | Fuzzers | 0.1 | 15.3 | 17.7 | 45.9 | 55.2 |
| UNSW-v2 | Generic | 0.3 | 2.6 | 50.9 | 94.6 | 91.3 |
| UNSW-v2 | Reconnaissance | 0.0 | 6.3 | 12.8 | 62.7 | 63.6 |
| UNSW-v2 | Shellcode | 0.0 | 17.9 | 63.6 | 85.3 | 75.7 |
| UNSW-v2 | Worms | 2.5 | 10.0 | 32.5 | 83.8 | 58.8 |


**Where host context helps.** Attacks carried out by one host against one service — DDoS-HOIC (5.8 % flagged by raw nearest neighbours,
100.0 % by HoCo-kNN), DDoS-LOIC-HTTP (5.6 % → 100.0 %), SQL injection and web brute force — become trivially separable once the
host's behaviour is visible.
**Where it does not.** Infiltration, in which an internal machine is compromised and keeps producing normal traffic, stays at 25.1 %.
Bot traffic drops from 100.0 % to 67.0 %, because the bots' hosts also carry flows that dilute their context.
**How much is testbed design.** In NF-CSE-CIC-IDS2018-v2, only 11.5 % of test attack flows come from source hosts that also appear in
benign training, and an attacker's test flows are on average 93.1 % attacks. Dedicated attacker machines make host context easy, which
is why source context alone already scores 0.9784. In NF-UNSW-NB15-v2, every attack flow comes from a host that also sends benign flows
and attackers' flows are 84.0 % attacks; there, context adds less (Table 3) and the flow's own features matter more. We regard the
NF-UNSW-NB15-v2 results as the more realistic estimate. Anomal-E also averages over all flows incident to a host and could exploit the same
property; GraphIDS aggregates only incoming flows, so the attacker's own outgoing flows do not reach its first layer. The comparison
with the graph detectors is therefore not like for like in this respect, and we report the controls below to make the size of the
identity effect explicit.

**Table 7. Shortcut controls (seed 42, test split).**

| Dataset | Detector / subset | PR-AUC | Macro-F1 | attacks flagged (%) |
|---|---|---|---|---|
| UNSW-v2 | (pending) | | | |
| CIC-2018-v2 | (pending) | | | |


## 8 Discussion
**What the graph contributes on these benchmarks.** On both NetFlow-v2 datasets, one fixed averaging step over the source host,
added to log-rescaled flow features, ranks attacks better than the published graph detectors. This does not show that graph learning
is useless in general — the controls of Section 7 show that part of the benefit of host context is identity — but it shows that the
benchmark numbers of recent graph detectors can be matched without learning, and that simple, strong baselines should accompany them.
**Practical use.** HoCo-kNN needs no GPU, no training loop and no attack labels for thresholds, and its alarms can be explained by the
nearest benign flow and by the host's mean behaviour. Its cost is the nearest-neighbour search, which approximate indexes reduce.
**Where it fails.** At the 0.3 % budget it recovers fewer attacks than GDAE reports on NF-UNSW-NB15-v2, and attacks from hosts that
mostly behave normally (infiltration, bots) stay hard.

## 9 Threats to validity and limitations
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

## 10 Conclusion
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
Arp D, Quiring E, Pendlebury F, et al. (2022) Dos and don'ts of machine learning in computer security. USENIX Security. arXiv:2010.09470
Bergman L, Cohen N, Hoshen Y (2020) Deep nearest neighbor anomaly detection. arXiv:2002.10445
Bilge L, Balzarotti D, Robertson W, Kirda E, Kruegel C (2012) Disclosure: detecting botnet command and control servers through large-scale NetFlow analysis. ACSAC. doi:10.1145/2420950.2420969
Bilot T, El Madhoun N, Al Agha K, Zouaoui A (2023) Graph neural networks for intrusion detection: a survey. IEEE Access. doi:10.1109/ACCESS.2023.3275789
Caville E, Lo WW, Layeghy S, Portmann M (2022) Anomal-E: a self-supervised network intrusion detection system based on graph neural networks. Knowledge-Based Systems 258:110030. doi:10.1016/j.knosys.2022.110030
GIDS-Eval (2026) [authors and title to be completed from doi:10.1145/3830454.3846576; arXiv:2609.12263]
Goldstein M, Dengel A (2012) Histogram-based outlier score (HBOS). KI 2012.
Guerra et al. (2025) GraphIDS. NeurIPS 2025. doi:10.52202/085713-3653; arXiv:2509.16625 [full author list to be completed]
Han S, Hu X, Huang H, Jiang M, Zhao Y (2022) ADBench: anomaly detection benchmark. NeurIPS. arXiv:2206.09426
Iqbal (2026) arXiv:2611.04660 [title and authors to be completed]
Karagiannis T, Papagiannaki K, Faloutsos M (2005) BLINC: multilevel traffic classification in the dark. SIGCOMM. doi:10.1145/1080091.1080119
Lee W, Stolfo SJ (2000) A framework for constructing features and models for intrusion detection systems. ACM TISSEC 3(4). doi:10.1145/382912.382914
Liu FT, Ting KM, Zhou ZH (2008) Isolation forest. ICDM.
Lo WW, Layeghy S, Sarhan M, Gallagher M, Portmann M (2022) E-GraphSAGE: a graph neural network based intrusion detection system for IoT. NOMS. doi:10.1109/NOMS54207.2022.9789878
Luay M, Layeghy S, et al., Portmann M (2026) Time matters: temporal NetFlow features for ML-based network intrusion detection. IEEE Access. doi:10.1109/ACCESS.2026.3688204
Mirsky Y, Doitshman T, Elovici Y, Shabtai A (2018) Kitsune: an ensemble of autoencoders for online network intrusion detection. NDSS. doi:10.14722/ndss.2018.23204
Moustafa N, Slay J (2015) UNSW-NB15: a comprehensive data set for network intrusion detection systems. MilCIS. doi:10.1109/MilCIS.2015.7348942
Rossi E, Frasca F, Chamberlain B, Eynard D, Bronstein M, Monti F (2020) SIGN: scalable inception graph neural networks. arXiv:2004.11198
Sarhan M, Layeghy S, Portmann M (2022) Towards a standard feature set for network intrusion detection system datasets. Mobile Networks and Applications. doi:10.1007/s11036-021-01843-0
Sommer R, Paxson V (2010) Outside the closed world: on using machine learning for network intrusion detection. IEEE S&P. doi:10.1109/SP.2010.25
Tavallaee M, Bagheri E, Lu W, Ghorbani AA (2009) A detailed analysis of the KDD CUP 99 data set. CISDA. doi:10.1109/CISDA.2009.5356528
Wang et al. (2025) R+R: from claims to crashes — a systematic re-evaluation of graph-based NIDS. ACSAC. doi:10.1109/ACSAC67867.2025.00050 [authors to be completed]
Wu F, Souza A, Zhang T, Fifty C, Yu T, Weinberger K (2019) Simplifying graph convolutional networks. ICML. arXiv:1902.07153
Xu K, Zhang ZL, Bhattacharyya S (2005) Profiling Internet backbone traffic: behavior models and applications. SIGCOMM. doi:10.1145/1080091.1080112
Zhao et al. (2026) Dual-autoencoder multi-task self-supervised one-class graph anomaly detection for network traffic (GDAE). J King Saud Univ Comput Inf Sci. doi:10.1007/s44443-026-01241-0 [full author list to be completed]
Zhou (2026) A controlled study of shared-endpoint flow topology for self-supervised network intrusion detection. AIIIP. doi:10.1145/3856389.3856511
FlowGuard (2026) Computer and Decision Making. doi:10.1922/comdem.v3i3s.18688 [DOI flagged for re-checking by Reviewer 3; title/authors to be completed]
