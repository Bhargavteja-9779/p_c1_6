# Review — Reviewer 1 (methodology and statistics)

**Manuscript:** HoCo-kNN: training-free host-context nearest neighbours for benign-only NetFlow intrusion detection
**Journal:** J. King Saud Univ. – Computer and Information Sciences
**Overall score:** 4 / 10
**Recommendation:** Major revision

## Summary of the submission
The authors replace learned E-GraphSAGE aggregation with a closed-form mean over all flows that share a source IP, computed within each split. They append this mean to log-rescaled min–max features and score each flow by its 1-NN distance to 200 k unique benign training representations. The threshold is the 99.7 % quantile of benign validation scores. Over five seeds of a random 8:1:1 split, they report PR-AUC 0.9299 (UNSW-v2) and 0.9809 (CIC-2018-v2) and compare it with the means and standard deviations in GDAE's Table 5.

The paper is clearly written. The code is short and readable. The authors deserve credit for a pre-registration file and for reporting the Macro-F1 deficit on UNSW-v2 openly. I checked every number in the abstract and in Tables 2–5 against `results/t3_test_table.csv`, `t3_stats.json`, `t3_per_attack.csv` and `t3_host_purity.json`, and they match after rounding. I also recomputed the Holm adjustment over the 62 Welch and paired p-values and one Welch test (UNSW PR-AUC against GDAE, p = 2.2e-4), and both reproduce. My concerns are not about arithmetic. They are about what the numbers measure and whether the comparison with GDAE is a like-for-like comparison.

## Major concerns

**1. [MAJOR] The host context acts largely as a source-IP identity shortcut, which removes the effect of dropping IPs as features.**
In `nfv2_bench.run`, the context of every test flow is the mean over all *test* flows with the same source IP (`ste`), attacks included. On CIC-2018-v2, 88.5 % of test attack flows come from source IPs that never appear in benign training, and an attacker's test flows are 93.1 % attacks (`t3_host_purity.json`). The context of these flows is therefore the mean of an almost purely malicious host's traffic, and no benign training row resembles it.

The ablation confirms this directly. "Source context only", without the flow's own features (`hc1_os`), reaches PR-AUC 0.9784, which is within 0.0025 of the full method. In other words, nearly all of the CIC performance comes from asking which host sent the flow, not what the flow looks like. GDAE removes IP addresses precisely because they "may induce shortcut learning" (GDAE §3.2.2). Grouping by IP brings the same information back in through the context. On UNSW-v2, all attack sources also send benign flows, yet attackers' flows are still 84 % attacks, so the same mechanism is probably at work, only weaker.

The paper discusses this as "testbed inflation" (§7). It then concludes that the "comparison with [GNNs] remains like for like" and that the method "ranks attacks better than the published graph models". Neither conclusion is established (see concern 2).

*What would resolve this:*
- (a) A trivial host-novelty baseline: score each test flow by whether its source IP is absent from benign training, or by the distance of `hc1_os` alone. Report its PR-AUC and Macro-F1 on both datasets.
- (b) A host-disjoint evaluation, where attacker and benign source IPs in test are unseen in training, or a leave-attacker-host-out evaluation.
- (c) A permutation control that shuffles source-IP assignments within the test split and reports the drop.
- (d) An inductive variant that computes context only from flows preceding the scored flow, or from a fixed-size window. NF-UNSW-NB15-v3 and NF-CSE-CIC-IDS2018-v3 include flow timestamps, so the claim in §8 that "a temporal split cannot be built" holds only for v2. The authors should run the temporal and windowed variants on v3.
- (e) Narrower claims in the Abstract and Conclusion, unless (a)–(d) show that the gain survives.

**2. [MAJOR] Several statements about GDAE's protocol go beyond what GDAE reports, and the authors' own baseline re-runs disagree strongly with GDAE's numbers.**
The paper claims "the exact protocol of GDAE". Several differences or unknowns remain:
- (i) **Features.** GDAE one-hot encodes categorical features (protocol, service; 43 inputs after encoding). This work min–max scales all 41 raw columns, including ports and L7_PROTO, as if they were continuous.
- (ii) **CIC subsample.** The 10 % CIC subsample is drawn independently per 1 M-row chunk with `random_state=0`, so it is not GDAE's subsample. GDAE does not report its sampling seed, so the two evaluations use different data.
- (iii) **Splits.** The splits come from `numpy.default_rng(seed)` with the same seed values as GDAE. Equal seed values do not imply equal splits.
- (iv) **Graph construction.** The statement that graph detectors "build one graph per split" and therefore aggregate "exactly the same host neighbourhood" is not supported by GDAE's text. GDAE describes one directed graph built from the NetFlow records and fixed-size neighbour sampling with fanout 32 768. It never says whether test edges can draw neighbours from training edges.
- (v) **Thresholds.** GDAE fits an EVT/GPD tail with u_pct = 0.95. This work uses an empirical quantile. How GDAE thresholds its baselines is not reported at all.

Most importantly, the authors' re-runs do not "land close to" GDAE's numbers, as §6 states. Macro-F1 for iForest is 0.4919 against 0.6712 (UNSW) and 0.4981 against 0.8355 (CIC). Macro-F1 for HBOS is 0.5614 against 0.7044 and 0.6063 against 0.8570. PR-AUC for HBOS on UNSW is 0.5327 against 0.3214, a difference in the opposite direction. Gaps of 0.15–0.34 in Macro-F1 for deterministic, standard algorithms are direct evidence that the two pipelines differ, at least in the threshold rule and possibly in the features and data. Until this is explained, numbers from the two sources cannot share one table as if they were comparable, and they cannot be fed into a significance test.

*What would resolve this:*
- Re-run at least one graph detector on the authors' own splits. Anomal-E and E-GraphSAGE have public implementations, and GraphIDS may as well. Ideally, re-run a GNN with the same per-split graph construction.
- Re-run the AE baseline, which is already implemented in `nfv2_bench.py` (`ae`) but not reported, and OC-SVM.
- Use GDAE's one-hot encoding, or show that the encoding does not matter.
- Report Macro-F1 for the reproduced baselines both at your threshold and at an EVT threshold, to show whether the threshold rule explains the iForest and HBOS gap.
- Mark the reported and re-run rows of Table 2 explicitly as non-comparable.
- Rewrite "exact protocol" as "following GDAE's described protocol, with the following differences: …".

**3. [MAJOR] "No attack label is used at any stage" is not accurate. Model design used labelled validation metrics, and the design data overlap the test sets of the other seeds.**
`results_t3_val/` contains about 19 configurations evaluated on seed-42 validation by PR-AUC and Macro-F1, both of which need attack labels: log constant, k ∈ {1, 5, 10}, reference size, categorical encoding, port dropping, and s / d / sd context. The final method was selected from these. That is model selection with attack labels, the same practice the paper criticises in GraphIDS and GDAE (early stopping on validation PR-AUC), only done once instead of per epoch.

Two further points:
- The splits are re-drawn for every seed. About 10 % of the seed-42 validation rows used for design therefore fall into each of the other four seeds' test sets, and about 80 % into their (benign) training sets. The "test used once" hygiene therefore holds strictly only for seed 42.
- File timestamps show that seed-42 TEST results for iForest, HBOS, PCA and raw kNN (with r = 50 k and 300 k) were produced at 12:24–12:40 on 26 Nov, before plan_v5 was committed at 12:56. The plan's own wording ("before any TEST result of hc*/ck*") is consistent with this, but the manuscript's statement that "the test splits were used once" is not.

Finally, benign-only training and benign-only threshold estimation both use ground-truth labels to remove attacks. GDAE acknowledges this explicitly, and this paper should too.

*What would resolve this:*
- Replace the claim with an accurate one, for example: "no attack labels in fitting or thresholding; design choices were selected on labelled validation data of one seed."
- List every configuration that was tried, with its validation numbers, as a supplementary table.
- Disclose the pre-plan test runs of the baselines.
- Ideally, report a design-free variant (e.g. hc1_s with default c and r) to show that the selection did not drive the result.
- Remove or reword the "strictly benign-only" contrast with GDAE in the Introduction and in the contribution list.

**4. [MAJOR] The significance tests against reported results are not valid inference about method superiority.**
- (i) A Welch test on summary statistics treats GDAE's five runs and the authors' five runs as samples from the same evaluation population. Because of the differences in concern 2 (data subsample, features, splits, thresholds), the gap mixes the method effect with a systematic protocol effect that neither standard deviation captures. Small p-values therefore say nothing about which method is better.
- (ii) The pre-registration (plan_v5) lists both a one-sample test and a Welch test. The paper reports only Welch and states that Holm runs "over all comparisons of the plan", yet the 62-test family in `t3_stats.json` excludes the 32 one-sample tests. The one-sample tests are anti-conservative, so leaving them out is the right decision. It is still an undeclared deviation from the plan and must be stated.
- (iii) The family mixes the confirmatory hypotheses (P1, P2: comparisons with GDAE) with dozens of tests against weak baselines. This makes the Holm correction lenient for the comparisons that matter. Under the authors' own Holm adjustment, the UNSW PR-AUC advantage over GraphIDS (p = 0.062) and over the AE (p = 0.083) is not significant. Yet the Abstract and Conclusion state without qualification that HoCo-kNN "ranks attacks better than the published graph models".
- (iv) The standard deviations from GDAE are rounded to four decimals. It is unknown whether they use ddof = 0 or 1. Some are implausibly small (Deep SVDD CIC Macro-F1 ± 0.0001). n = 5 per side gives Welch degrees of freedom near 4, so the test depends strongly on these values.

*What would resolve this:*
- Make the GDAE comparisons (P1, P2) the confirmatory family and treat everything else as descriptive.
- Present the comparison with reported numbers as descriptive, with effect sizes and a clear caveat, rather than as hypothesis tests. Alternatively, support it with concern 2's re-runs on identical splits, where paired tests are valid.
- Qualify the GraphIDS and AE claims on UNSW-v2.
- State the deviation from the plan.

## Minor concerns

**5. [MINOR] Per-attack rates rest on very few flows.** On the 10 % CIC subsample, SQL Injection has about 4 test flows per seed, Brute Force-XSS about 9 and Brute Force-Web about 21 (these follow from the flag-rate granularities in `t3_per_attack.csv`). A statement such as "100.0 %" for these classes needs counts and binomial confidence intervals.
*Resolve:* add an n column and Wilson intervals to Table 5. Alternatively, merge the rare classes or evaluate the rare classes on the full CIC data.

**6. [MINOR] "Each component helps" is true only for mean PR-AUC.** On UNSW, adding context changes Macro-F1 by +0.0064, with Holm p = 0.64. At the attack level, log rescaling lowers SSH-Bruteforce from 61.5 % to 15.9 %, GoldenEye from 100 % to 77.8 % and Hulk from 100 % to 89.5 %. Context lowers Bot from 100 % to 67 % and UNSW Worms from 83.8 % to 58.8 %. The explanation that context dilution causes the Bot drop is speculation and is not tested.
*Resolve:* qualify the claim, and test the Bot explanation with the per-host attack share of bot hosts.

**7. [MINOR] The ablation is incomplete relative to the plan.** The k = 5, destination-only and context-only (`hc1_os`) variants are reported only for CIC. The context-only control in particular is essential on UNSW (see concern 1). The final configuration hc1_s at r = 200 k was never evaluated on CIC validation; only r = 50 k was. On CIC validation, hc1_sd at r = 200 k was better on both metrics (0.9785 / 0.9815 against 0.9752 / 0.9583).
*Resolve:* run the missing UNSW ablations and state how the choice between s and sd was made.

**8. [MINOR] There is no sensitivity analysis.** The paper reports nothing on c (log constant), R (reference size), k, or the FPR budget. Its Macro-F1 deficit on UNSW is attributed to the operating point, but this is not shown.
*Resolve:* add sensitivity curves for c, R and k on validation. Report Macro-F1 and recall at several FPR budgets (0.1 %, 0.3 %, 1 %), and also the best-threshold Macro-F1, to separate ranking from calibration. Report ROC-AUC, which is already computed in `t3_test_table.csv`.

**9. [MINOR] The runtime table is misleading.** "fit = 0.0 s" for HoCo-kNN excludes the context computation and the `np.unique` / reference subsample, which both run before `t0` in `nfv2_bench.run`. For raw kNN, the same work counts as fit time. Scoring takes about 420–570 s per seed, roughly 2 ms per flow on one core, and it requires the whole split to be available, so the method is transductive. This should be contrasted with GDAE's claimed latency.
*Resolve:* time the end-to-end pipeline and report per-flow latency.

**10. [MINOR] Duplicates and memorisation.** NetFlow-v2 contains many exact duplicate flows, and random splits place copies in both training and test. A 1-NN detector gives such benign test flows a score of exactly 0. With host context, a benign test flow from a frequent host has a context almost identical to that host's training context.
*Resolve:* report results on a test set de-duplicated against training, at least as a supplementary analysis.

**11. [MINOR] Reproducibility of the host-purity analysis.** The code that produces `t3_host_purity.json` is not among the supplied source files. The precise definitions of "seen src" (seen in benign training) and "attacker attack share" (pooled over flows or averaged over hosts) should be given.
*Resolve:* add the script and the definitions.

**12. [MINOR] Wording.**
- "turned the failed nearest-neighbour detector into the most accurate detector we evaluated" is contradicted by the UNSW Macro-F1 and accuracy results.
- "official open-access release" and the GDAE author list should be properly cited.
- The References section points to internal files (`literature/prior_art_v2/...`), which must be replaced by full citations.

## Verdict
The core idea is simple and worth publishing: a non-learned, one-hop host aggregation is a strong and cheap baseline for E-GraphSAGE-style detectors. The current evidence, however, does not support the headline claim that the method beats the graph models. The comparison mixes pipelines whose standard baselines disagree by up to 0.34 Macro-F1. The CIC result is almost entirely reproduced by host identity alone. The benign-only claim overlooks labelled design selection. A revision that adds host-disjoint or inductive evaluations, a host-novelty baseline, and at least one GNN re-run on identical splits would make this a solid contribution.
