# HoCo-kNN: Training-free host-context nearest neighbours for benign-only NetFlow intrusion detection

**Authors:** [to be completed by the authors] · **Affiliations:** [to be completed] · **Corresponding author:** [to be completed]

## Abstract
Network intrusion detectors that are trained only on benign traffic can, in principle, recognise attacks they have never seen.
Recent one-class detectors for NetFlow data build traffic graphs and train graph neural networks (GNNs) on GPUs, and select their
models with validation metrics that require attack labels. We ask how much of their accuracy actually needs graph learning.
Starting from a plain nearest-neighbour detector, we found two causes of its weakness: min–max scaling hides the heavy-tailed
byte, packet and duration counters, and a single flow does not reveal attacks whose signature is the behaviour of the host that
sends them. We propose HoCo-kNN, which (i) log-rescales flow features and (ii) appends, in closed form, the mean behaviour of the
flows that share the source host — the one-hop aggregation a GNN learns, without training. Thresholds are set from benign validation
flows only, at a 0.3 % false-positive budget. Following the protocol of the strongest recent one-class GNN (GDAE) on NF-UNSW-NB15-v2
and NF-CSE-CIC-IDS2018-v2 (five seeds), HoCo-kNN reaches PR-AUC {{pr_unsw}} and {{pr_cic}} (GDAE: 0.859 and 0.949), runs on a
CPU, and needs no attack labels at any stage. We also show where the gain comes from and where it is inflated by testbed design.

**Keywords:** network intrusion detection; one-class anomaly detection; NetFlow; nearest neighbours; graph neural networks; reproducibility

## 1 Introduction
(a) Problem. Signature-based NIDS miss new attacks; anomaly detectors trained on benign traffic are the standard answer, but in
practice they must keep false alarms below a fraction of a percent.
(b) Current practice and where it falls short. The best recent one-class NetFlow detectors (Anomal-E, GraphIDS, GDAE) learn
E-GraphSAGE edge embeddings on GPUs and stop training at the epoch with the best validation PR-AUC — which uses attack labels.
Their classical baselines (iForest PR-AUC 0.189 on NF-UNSW-NB15-v2) are weak, and no nearest-neighbour baseline is reported.
(c) Our first idea, and why it was not enough. A nearest-neighbour detector on the raw 41 flow features already reaches PR-AUC
{{pr_unsw_knn1}} on NF-UNSW-NB15-v2 — above Anomal-E — but only {{pr_cic_knn1}} on NF-CSE-CIC-IDS2018-v2, where it lets the largest
attack (DDoS-HOIC) pass almost entirely at a 0.3 % false-positive budget.
(d) What the failure taught us. Two things: the scaling hides most of the counters' range, and HOIC flows look like ordinary HTTP flows
one at a time — what gives them away is the host that sends thousands of them.
(e) The insight. The one-hop mean aggregation that E-GraphSAGE learns can be computed directly, without training.
(f) Contributions.
1. HoCo-kNN, a training-free, CPU-only one-class detector: log-rescaled flow features plus closed-form source-host context (Sect. 4).
2. A strict benign-only protocol: no attack labels for training, model selection or thresholds (Sect. 5).
3. Results on GDAE's exact protocol, five seeds, with ablations (Tables 2–4).
4. An analysis of where host context helps and where testbed design inflates it (Sect. 7).

## 2 Related work
[organised by gap: one-class NIDS on NetFlow; GNN-based NIDS (E-GraphSAGE, Anomal-E, GraphIDS, GDAE); simple-baseline critiques
(FlowGuard 2026; GIDS-Eval 2026; Iqbal 2026); label use in model selection. CLAIM → CLOSEST PRIOR WORK → DIFFERENCE table. See
literature/prior_art_v2/nfv2_oneclass.md for sources.]

## 3 Problem formulation and the failed first attempt
[from journal entries 29–30: raw kNN numbers per attack class; HOIC 7 % flagged.]

## 4 Method: HoCo-kNN
x ∈ [0,1]^41 (min–max on benign training flows). Log rescaling: φ(x) = log(1 + c·x)/log(1 + c), c = 10^4.
Host context within a set of flows F (one graph per split, as in the GNN baselines): for flow i with source host s(i),
h(i) = mean_{j ∈ F : s(j) = s(i)} φ(x_j). Representation z(i) = [φ(x_i), h(i)] ∈ R^82.
Score: Euclidean distance to the nearest of R benign training representations (R = 200 000 unique rows, sampled).
Threshold: the 99.7 % quantile of scores of benign validation flows (target FPR 0.3 %, as GDAE's EVT target).
Complexity: O(|F|·d) for the context; O(|R|·d) per scored flow (brute force; tree/ANN indexes apply).

## 5 Experimental setup
Datasets: NF-UNSW-NB15-v2 (2 390 275 flows, 3.98 % attacks) and a 10 % stratified sample of NF-CSE-CIC-IDS2018-v2, official UQ release.
Protocol (GDAE Sect. 3.2.2): IPs and timestamps removed as features, NaN/Inf→0, random 8:1:1 split stratified by attack type,
benign-only training, min–max fitted on training data; seeds 42, 123, 456, 789, 1234.
Design hygiene: every design choice was made on the validation split of seed 42; the test split was used once, after freezing
(plan_v5, written before the test run).
Hardware: 4 CPU cores, 15 GB RAM, no GPU. Software: Python 3.13, scikit-learn, PyOD 3.6.9.

## 6 Results
Table 2 — comparison with GDAE's Table 5 (PR-AUC, Macro-F1, mean ± sd over 5 seeds): {{table_main}}
Table 3 — ablation (raw kNN → log → + source context; + destination context; context only): {{table_ablation}}
Table 4 — statistics (Welch tests vs reported numbers; paired tests vs our baselines; Holm-corrected): {{table_stats}}
Runtime: {{runtime}}

## 7 Analysis
[per-attack flag rates; mixed-host vs dedicated-attacker analysis (journal 32); why UNSW Macro-F1 stays below GDAE's.]

## 8 Threats to validity and limitations
- Random splits (as in GDAE) put flows of the same host in train and test; NetFlow-v2 has no timestamps, so a temporal split is not possible.
- On NF-CSE-CIC-IDS2018-v2, 88.5 % of attack flows come from hosts never seen in benign training and attacker hosts emit 93 % attacks:
  host context partly recognises dedicated attack machines (journal 32). The GNN baselines rely on the same structure.
- Comparison with GDAE uses their reported means and standard deviations (no code available).
- Host context is computed over the evaluated partition (transductive, like the GNN baselines); streaming deployment needs a time window.

## 9 Conclusion
[to be written from final numbers]

## Declarations
Data availability: UQ NetFlow-v2 (open access, UQ RDM). Code: [repository link to be added by the authors].
Funding, conflicts of interest, ethics: [to be completed by the authors]. Use of AI assistance: [to be completed by the authors].

## References
[only papers actually opened; see literature/]
