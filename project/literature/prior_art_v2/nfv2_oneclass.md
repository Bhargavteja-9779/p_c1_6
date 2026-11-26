# Prior-art check: benign-only ("one-class") NetFlow IDS on NF-UNSW-NB15-v2 and NF-CSE-CIC-IDS2018-v2

Date: 2026-11-26. Comparator: GDAE (Zhao et al., JKSU-CIS 38:779, 2026, DOI 10.1007/s44443-026-01241-0).

## Method

Sources: WebSearch (11 phrasings), the arXiv API (6 queries), OpenAlex search (6 queries) with abstracts rebuilt from `abstract_inverted_index`, and Semantic Scholar citation lists for GraphIDS (22 citing papers) and Anomal-E (200 citing papers). Semantic Scholar batch lookups returned HTTP 429, so OpenAlex was used for abstracts. Public git and raw README were used for GitHub.

Phrasings used (selection): "GraphIDS self-supervised … masked autoencoder E-GraphSAGE"; "Anomal-E … NF-UNSW-NB15-v2"; "do graph neural networks help network intrusion detection simple baselines NetFlow"; "one-class NetFlow v2 kNN anomaly detection benign-only"; "unsupervised NIDS NF-UNSW-NB15-v2 NF-CSE-CIC-IDS2018-v2 PR-AUC autoencoder isolation forest"; "benign-only flow anomaly detection nearest neighbour isolation forest benchmark"; "E-GraphSAGE unsupervised benign-only edge embeddings"; "NF-CSE-CIC-IDS2018-v2 anomaly detection autoencoder benign"; "GDAE … Kendall uncertainty EVT github"; "NetFlow v2 duplicate flows random split deduplication"; "one-class intrusion detection threshold extreme value theory"; arXiv `all:"benign-only" AND intrusion`, `E-GraphSAGE AND self-supervised`, `netflow AND "one-class"`.

Depth of reading. Full text was read for: GDAE (local copy `literature/fulltext/gdae_page.txt`), GraphIDS (arXiv v5), the leakage-free R-GCN paper (arXiv 2611.04660), FlowGuard (Comdem PDF), DOC-NAD, the GIDS-Eval paper (arXiv 2609.12263), "Are We There Yet?" (arXiv 2503.20281) and AutoGraphAD (dataset check only). Everything else was read at abstract level only. The ACM DL full text of the "Controlled Study" paper is blocked by Cloudflare, so only its abstract was read.

## Key facts about the comparator (GDAE), from its full text

- Protocol: random split stratified by attack type, 8:1:1; attacks removed from training; validation and test are mixed; seeds {42, 123, 456, 789, 1234}. Source IP, destination IP and timestamps are dropped. On CIC-2018-v2 the 10% sample is as stated in the task (not re-checked here).
- **Early stopping uses validation PR-AUC** (patience 20; "the best-performing model parameters were retained", §3.x line 343). That needs attack labels in validation. So the "label-free" claim covers optimisation only, not model selection.
- EVT/POT threshold: u = 95th percentile of "normal validation anomaly scores", GPD fit, FPR_target = 0.003 (Eq. 17). Picking the *normal* validation flows also needs labels. Table 11 compares EVT only with the 90th, 95th and 99th percentiles, and on one seed only (42).
- The "AE" baseline is an autoencoder on **E-GraphSAGE edge embeddings, not raw flows**. No raw-flow AE, kNN or LOF baseline is reported. Whether OC-SVM and Deep SVDD ran on raw flows is not stated clearly (UNVERIFIED).
- Data/code availability statement: "No datasets were generated or analysed". No code link was found (web search for a GDAE repository found nothing).
- Observation: GDAE's UNSW-v2 baseline numbers almost equal GraphIDS Table 6/8 numbers. iForest 0.1888 vs GraphIDS-paper IF 0.1914; HBOS 0.3214 vs 0.3197; Anomal-E 0.714 vs Anomal-E-PCA 0.7133; GraphIDS 0.818 vs 0.8116. On CIC-2018-v2 they differ more (GraphIDS 0.898 vs 0.9201; Anomal-E 0.956 vs best 0.9287). Whether GDAE re-ran these baselines or partly reused them is UNVERIFIED. A paper should not assert either; it can simply note the agreement.

## Paper-by-paper record

### 1. GraphIDS: Guerra, Chapuis, Duc, Mozharovskyi, Nguyen, "Self-Supervised Learning of Graph Representations for Network Intrusion Detection", NeurIPS 2025 (DOI 10.52202/085713-3653; arXiv 2509.16625). Full text read.
- Setting: benign-only training; 80/10/10 split stratified by attack type; Min-Max scaler fit on benign training data; **early stopping on validation PR-AUC**; Bayesian HPO on validation PR-AUC; threshold = maximise macro-F1 on a *labelled* validation set. The authors say this openly and name "fully unsupervised thresholding" as future work.
- Datasets: NF-UNSW-NB15-v2/v3 and NF-CSE-CIC-IDS2018-v2/v3. Anomal-E needed a downsampled CIC graph; GraphIDS used the full graph.
- PR-AUC / Macro-F1 on v2 (Table 3, 6, 8; mean ± sd over seeds):

| Model | UNSW-v2 PR-AUC | UNSW-v2 F1 | CIC18-v2 PR-AUC | CIC18-v2 F1 |
|---|---|---|---|---|
| CBLOF (raw) | 0.2102 | 0.7046 | 0.7822 | 0.8889 |
| HBOS (raw) | 0.3197 | 0.7032 | 0.6662 | 0.8578 |
| IF (raw) | 0.1914 | 0.6844 | 0.6124 | 0.8321 |
| PCA (raw) | 0.2840 | 0.6975 | 0.5911 | 0.6128 |
| SAFE (MAE+LOF) | 0.2044 | 0.5815 | 0.5222 | 0.4684 |
| Anomal-E best (HBOS / CBLOF) | 0.7489 | 0.9156 | 0.9287 | 0.9410 |
| T-MAE (raw flows, no GNN) | 0.5995 | 0.8039 | 0.7375 | 0.8453 |
| SimpleAE (E-GraphSAGE + MLP-AE) | 0.7864 | 0.8680 | **0.9310** | **0.9450** |
| GraphIDS | **0.8116** | **0.9264** | 0.9201 | 0.9431 |

- Relevant points: (a) on CIC18-v2 the MLP-AE variant (SimpleAE) is equal to or better than GraphIDS; (b) **Anomal-E's public code target-encodes categorical features with the attack label (label leakage)**, which GraphIDS removed before re-running it; (c) **no kNN, LOF on raw flows, or raw-flow MLP-AE baseline**. The best raw-flow detector on UNSW-v2 reaches PR-AUC 0.32.
- Code: yes, github.com/lorenzo9uerra/GraphIDS (Apache-2.0, PyG; `main` and `dgl` branches exist, confirmed via git ls-remote).
- Does it show simple ≥ GNN? No. It shows the reverse for classical raw-flow detectors.

### 2. Anomal-E: Caville, Lo, Layeghy, Portmann, Knowledge-Based Systems 258:110030 (2022), arXiv 2207.06819. Abstract and search summary read.
- E-GraphSAGE + DGI, then IF / PCA / CBLOF / HBOS run on the embeddings. Evaluated on NF-UNSW-NB15-v2 and NF-CSE-CIC-IDS2018-v2, with a contamination study.
- Reported (search-extracted, Table 7, 0% contamination, UNSW-v2): Anomal-E-PCA accuracy ~98.63%, macro-F1 ~92.18%. No PR-AUC is reported. Exact column alignment is UNVERIFIED.
- Code: github.com/waimorris/Anomal-E (confirmed). GraphIDS reports that this code leaks labels through target encoding.

### 3. GDAE (comparator). See above. DOI 10.1007/s44443-026-01241-0.

### 4. FlowGuard: Iskandarova et al., "Leakage-Controlled Cross-Dataset Evaluation of Self-Supervised Graph-Based NIDS", *Computer and Decision Making* 3(3s):139-167 (2026), DOI 10.1922/comdem.v3i3s.18688. Full text read.
- Setting: benign-only graph autoencoder; IPs removed; ports reduced to 3 categories. **Disjoint sampling: 200k stratified test flows, then 100k benign training flows drawn from records not in the test set.** 5 seeds. **Label-free threshold** set at a target FPR on benign *training* scores. Achieved FPR 0.0098 / 0.0247 / 0.0495 / 0.0987 for targets 0.01 / 0.025 / 0.05 / 0.10.
- Datasets: NF-UNSW-NB15-v2 and NF-BoT-IoT-v2. **No CIC-2018-v2.**
- Results on UNSW-v2 (base rate 0.038; Table 5):

| Detector | ROC-AUC | PR-AUC | Macro-F1 |
|---|---|---|---|
| IF | 0.915 | 0.314 | 0.663 |
| PCA reconstruction | 0.975 | 0.578 | 0.752 |
| MLP autoencoder | 0.969 | 0.639 | 0.754 |
| FlowGuard (graph AE) | 0.968 | 0.564 | 0.748 |

The authors state plainly that the graph model does not lead and that "part of the advantage reported for graph models may … belong to evaluation regimes in which those shortcuts were still open."
- Code: "release the complete pipeline" is claimed; no URL was verified (UNVERIFIED).
- **This is the closest prior statement of "simple ≥ graph, one-class, NF-UNSW-v2".** Its limits: small venue; one NF-v2 dataset of the two; its own sanitized feature policy (not the GraphIDS/GDAE protocol); no kNN or LOF; it does not re-run GraphIDS or GDAE; absolute PR-AUC (~0.56-0.64) is not comparable to the GDAE/GraphIDS ~0.8.

### 5. Zhou, "A Controlled Study of Shared-Endpoint Flow Topology for Self-Supervised Network Intrusion Detection", AIIIP 2026, ACM, DOI 10.1145/3856389.3856511. Abstract only (ACM full text blocked).
- Benign-only; **benign-only calibration**; separate train / calibration / dev / test splits; 5% stratified subset of NF-UNSW-NB15-v2; 5 seeds.
- PR-AUC: real topology 0.7536; degree-preserving random graph 0.6054; no edges 0.6537. Against PCA, the graph encoder has higher ROC-AUC and PR-AUC but **lower thresholded Macro-F1 and attack F1**. Includes "non-graph baseline" experiments (details UNVERIFIED) and a timestamped CSE-CIC-IDS2018 check (which version is UNVERIFIED).
- Shows that topology adds ranking signal on a 5% subset. Partly against the "simple wins" claim (for PR-AUC), partly for it (for F1).

### 6. Iqbal, "Leakage-free evaluation of residual graph convolutional networks for NIDS", arXiv 2611.04660 (2026). Full text read.
- **Supervised**, not one-class. Uses CICIDS2017 and NF-UNSW-NB15-v2.
- **Label-aware exact de-duplication removes 69% of NF-UNSW-NB15-v2.** After dropping src port, DNS query id and labels, and setting IPs aside, 2,390,275 flows become 731,810: benign 690,559, attacks ~41k (Exploits 23,565, Fuzzers 7,405, ...).
- 60/20/20 stratified split, 3 seeds. R-GCN binary F1 on UNSW-v2 is 90.57 ± 0.38, no better than an MLP. A kNN vote and tree ensembles are competitive or better; the trees lead on PR-AUC.
- Relevance: direct evidence that random splits of NF-UNSW-v2 put the same flow vectors in both train and test. It does not cover benign-only or CIC-2018-v2.

### 7. Zhao & Ul Hassan, "A First-Principles Evaluation of Graph-Based NIDS" (GIDS-Eval / GIDS-Lite), ACM CCS 2026, DOI 10.1145/3830454.3846576, arXiv 2609.12263. Full text skimmed.
- Encoder-free GIDS-Lite ranks first by AP on 2 of 4 datasets at up to 575× lower runtime. Aligning preprocessing moves AP by up to 61.8 pp; the snapshot window gives a 38.3% relative swing.
- Datasets: Campus, corrected CIC-IDS2017, LANL, OpTC. **No NF-v2.** Temporal splits.
- Strong top-venue precedent for "simple control ≈ GNN" in graph NIDS generally, but not on NF-v2 and not with GraphIDS or GDAE.

### 8. Wang, Zheng, Gui, Hua, Ul Hassan, "R+R: From Claims to Crashes: A Systematic Re-evaluation of Graph-Based NIDS", ACSAC 2025 (DOI 10.1109/ACSAC67867.2025.00050; preprint arXiv 2503.20281 "Are We There Yet?").
- Reproduces 5 GIDS, including Anomal-E, on LANL, OpTC, CIC-IDS-2017 and an enterprise dataset. Metrics vary by up to 40%. Threshold-setting strategy is a key, poorly documented factor.
- It lists NF-UNSW-NB15-v2 / NF-CSE-CIC-IDS2018-v2 only as Anomal-E's original datasets and **does not evaluate on NF-v2**.

### 9. DOC-NAD: Sarhan, Kulatilleke, Lo, Layeghy, Portmann, CCGridW 2023, arXiv 2212.07558. Full text read.
- Benign-only; benign data split 70/30; the test set appears roughly balanced (UNVERIFIED). Metrics: Acc / F1 / ROC-AUC / DR / FAR. **No PR-AUC.**
- NF-UNSW-NB15-v2 AUC: IF 89.45, PCA 85.22, VAE 85.54, DeepSVDD 95.03, HBOS 95.01, DOC 98.89. NF-CSE-CIC-IDS2018-v2 AUC: IF 74.90, PCA 85.41, VAE 76.87, DeepSVDD 83.59, HBOS 82.91, DOC 85.52. Most baselines use a ~10% FAR operating point.
- No graph model; no kNN.

### 10. Other one-class / self-supervised NetFlow work (abstract level)
- Lee, Ran, Lee, "Topology-aware unsupervised intrusion detection from network flows in encrypted traffic", *Computer Networks* (2027 issue), DOI 10.1016/j.comnet.2026.112940. Graph AE compared with GraphIDS, Anomal-E, KitNET and VAE across 6 datasets / 8 conditions; mean ROC-AUC 0.986; CPU timing. Whether it uses NF-v2 is UNVERIFIED.
- Miguel-Diez et al., arXiv 2509.01375 (2025): online OC-SVM (River) on NF-UNSW-NB15 and v2. Accuracy > 98%, FPR < 3.1%, recall 100%. No PR-AUC.
- Xu et al., *Computer Networks* 2024, DOI 10.1016/j.comnet.2024.110495 (arXiv 2403.01501): graph SSL using NF-BoT-IoT(-v2) and NF-CSE-CIC-IDS2018(-v2). Not benign-only one-class in the GDAE sense (UNVERIFIED in detail).
- AutoGraphAD (Anyfantis & Barlet-Ros, NetSoft 2026, arXiv 2511.17113): heterogeneous VGAE, matches Anomal-E on raw UNSW-NB15 (not NF-v2).
- OPTIMAL (*Computer Networks* 2026, 10.1016/j.comnet.2026.112169), SSGMHAN (*J. Cloud Computing* 2026), Semantic-guided edge enhancement (*Sci. Rep.* 2026), MFNID (IEEE IoT-J 2026): further graph SSL NIDS papers, mostly with supervised or partly supervised evaluation. No abstract reports NF-v2 PR-AUC against kNN or LOF.
- Butt, Hotho, Schlör, "Evaluating Tabular Representation Learning for NIDS", IEEE CSR 2026 (arXiv 2605.02519): representation learning plus unsupervised detectors on NetFlow data. "No single combination consistently dominates". Datasets include CIDDS; NF-v2 use is UNVERIFIED.
- Albluwi et al., Research Square 2026 (10.21203/rs.3.rs-10707774/v1): a label-free topology-validity framework. On NF-CSE-CIC-IDS2018-v2, Hybrid Precision = 0.000 under gap-based selection, i.e. topology there is "structurally degenerate" for attack-selective reasoning. This is a useful citation for "GNN topology may add little on CIC-2018-v2".
- GESR (arXiv 2605.07536): benign-only graph edge reconstruction with MAD calibration, on CTU-13 and CICIDS2017 (not NF-v2).

### 11. Evaluation-hygiene background
- Flood, Engelen, Aspinall, Desmet, "Bad Design Smells in Benchmark NIDS Datasets", EuroS&P 2024. Near-duplicate flows and label leakage in features across 7 datasets. No NF-v2 mention in the full text (grep).
- "When Simple Model Just Works: Is Network Traffic Classification in Crisis?", arXiv 2506.08655. A k-NN baseline matches complex models because >50% of samples are redundant and spill across splits. This is the analogous argument in traffic classification.
- Filali, Zenodo 10.5281/zenodo.22966955: "leakaudit" (duplicates, train-test overlap under random and chronological splits, label-host coupling) on CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15 and NF-v3. Not NF-v2.
- El Mahdaouy et al., arXiv 2602.05594 (survey): lists random splitting, temporal leakage and duplicates as inflating factors.
- See also `literature/prior_art.md` P04 (Valencia Vélez record-level audit of NF-v2/v3, Zenodo, abstract only).

## Answers

### (1) Has "simple CPU detectors beat GNN one-class NIDS on NF-v2" already been published?

**Not in the specific form planned, but it is partly anticipated.**
- No paper found runs kNN or LOF (raw, standardized NF-v2 features) against GraphIDS, GDAE or Anomal-E under the GDAE/GraphIDS 8:1:1 benign-only protocol on **both** NF-UNSW-NB15-v2 and NF-CSE-CIC-IDS2018-v2.
- In the published record, raw-flow classical detectors look weak on UNSW-v2: IF 0.19, HBOS 0.32, PCA 0.28, CBLOF 0.21 (GraphIDS Table 8; GDAE Table 5). So a strong kNN or LOF result would be new evidence that contradicts these tables.
- Partial precedents a reviewer will cite:
  - **FlowGuard (Comdem 2026)**: PCA and an MLP-AE ≥ a graph AE on NF-UNSW-v2 under a sanitized, label-free-threshold protocol. One NF-v2 dataset only, no kNN, no GraphIDS/GDAE.
  - **GraphIDS's own SimpleAE**: an MLP-AE head on E-GraphSAGE ≥ GraphIDS on CIC18-v2. Still uses a GNN.
  - **GDAE's own Table 5**: the embedding-AE (0.942) and Anomal-E (0.956) are within about 0.01 of GDAE (0.949) on CIC18-v2.
  - **Iqbal 2026**: supervised; kNN, MLP and trees ≥ GCN on de-duplicated NF-UNSW-v2.
  - **GIDS-Eval (CCS 2026)**: an encoder-free control ≥ GNNs, but on non-NF-v2 data.
- Novelty therefore has to rest on: (i) both NF-v2 datasets under the comparator's exact protocol; (ii) kNN, LOF and raw-flow AE (none reported anywhere on NF-v2 with PR-AUC); (iii) the protocol-hygiene angles below. A pure "simple beats GNN" headline is weakened by FlowGuard and GIDS-Eval, which must be cited.

### (2) Which angles look OPEN

1. **Validation-label leakage in model selection (OPEN, strong).** Both GraphIDS and GDAE early-stop on validation PR-AUC. GraphIDS also tunes hyperparameters by Bayesian optimisation on validation PR-AUC and sets thresholds by validation macro-F1. GDAE fits EVT on "normal validation scores", which needs labels to pick the normal flows. No paper found quantifies how much of the GNN-vs-simple gap comes from attack-label-driven selection. The test is to re-run with benign-only selection criteria, such as benign reconstruction loss or a benign-holdout score. GraphIDS acknowledges the issue as future work; none of the papers found here measures it.
2. **Label-free threshold calibration (PARTLY OPEN).** FlowGuard (target-FPR quantiles on benign training scores; achieved FPR close to target), the Controlled-Study paper (benign-only calibration) and GESR (MAD) already do label-free calibration. GDAE's EVT is compared only with fixed validation percentiles, on one seed, and is fit on validation benign data. Still open on NF-v2: a target-FPR calibration study that compares EVT/POT with plain empirical quantiles and conformal (split-conformal p-values) on benign-only *training/calibration* data, across seeds and both datasets. It would report achieved FPR versus target and macro-F1 at that operating point. Novelty is moderate, so frame it as a protocol component rather than the headline.
3. **Near-duplicate and exact-duplicate flows across random splits (OPEN for one-class NF-v2).** Iqbal 2026 shows 69% exact duplicates in NF-UNSW-NB15-v2 (supervised, label-aware). Flood et al. and the traffic-classification kNN paper give the general argument. No paper found measures train-test duplicate overlap for **benign-only** splits on NF-v2, or for **NF-CSE-CIC-IDS2018-v2** at all. Nor has anyone shown how duplication inflates kNN/LOF versus GNN detectors (kNN benefits most from exact matches, so this is double-edged). A de-duplicated, or grouped-by-flow-signature, re-run is open.
4. **Per-host / per-service conditioning without GNNs (OPEN).** No paper found tests whether simple context features or conditioning reproduce the "topology" gain on NF-v2. Examples: per-destination-port or per-L7-protocol kNN, per-host benign profiles, or degree/fan-out counts as tabular features. The Controlled-Study paper's randomized-graph control (0.7536 vs 0.6054/0.6537) is the nearest work, and it uses a GNN encoder. Albluwi et al. report that CIC-2018-v2 topology is degenerate for attack-selective prominence, which supports this angle. Caveat: source and destination IPs are dropped as features in GDAE, so host conditioning must use them only for grouping, and the paper should discuss shortcut risk (cf. FlowGuard's IP probe).
5. Smaller open points:
   - (a) GDAE's CIC18-v2 numbers come from a 10% stratified sample, while GraphIDS used the full graph. Nobody has checked how sample size moves graph-based versus kNN detectors.
   - (b) Seed variance and significance: GDAE reports mean ± sd only, with no paired tests.
   - (c) CPU cost and latency of kNN (e.g. FAISS-CPU or sklearn BallTree on ~1.8M benign flows) against GNN inference has not been reported on NF-v2.

## Caveats and items not verified
- GDAE code availability: none found (UNVERIFIED that none exists).
- FlowGuard code URL: not verified.
- Controlled-Study paper: non-graph baseline details and its CIC-2018 version not verified (abstract only).
- Anomal-E Table 7 numbers come from a search-tool extraction, not a direct read.
- Topology-aware comnet paper, tabular-representation paper: NF-v2 use not verified.
- The search covered indexed literature to about 2026-11. Very recent JKSU-CIS or Springer items not yet in OpenAlex or Semantic Scholar could be missed.
