# Prior art — full-text / deposit check (session 2, 2026-11-24)

Checked by a sub-agent; files downloaded to an ephemeral scratch dir (not in git). Numbers marked "computed" are means the agent computed from deposited run CSVs, NOT quoted from a paper.

## P01 Gazi, Prappo & Hossain 2026 — CLOSEST
- Opened: Zenodo code records 24172401 / 24195343 and GitHub nahidgaziang/Code-for-Cross-Network-NetFlow-Intrusion-Detection (results_archive/ run CSVs, docs/PROTOCOL.md, EXPERIMENTS.md, ANALYSIS_PLAN.md). **Paper PDF not found** (README: "venue and DOI to be added").
- NF-v2 (41 feats) and NF-v3 (49 feats), all 4 testbeds; leave-one-testbed-out; 100k flows/source (80/20); target eval 100k; unlabeled target buffer 1,500 (S1); 500-flow 95%-benign window (S2). Source-only tuning via leave-one-source-out, 12 configs/method. 10 seeds. Wilcoxon over 40 target×seed pairs, Holm, bootstrap CIs; claims must hold in both releases; hypotheses dated internally (not externally registered).
- 18 methods: ERM, ERM-CB, XGB, RF, IRM, V-REx, GroupDRO, CORAL, DANN, IW-DANN, DANN-R, AdaBN, TENT, DomNorm, BRN, BRN-XGB, IF-win, KNN-win.
- Thresholds: 0.5; EM prior on buffer; window median+3·1.4826·MAD; window p99; source-val 1%-FPR (E2, E7).
- **E7 (group ablation, overlaps our angle a):** untuned XGB (100 trees, depth 6), drop one group at a time: TTL, TCP window, timing, "artifacts" (TTL+TCPwin+ports, DNS_QUERY_ID, ICMP types, FTP code). Metrics: target AUROC, target-benign FPR at source 1%-FPR threshold. Labelled "association only". NF-v3 computed means (AUROC/FPR): all 0.586/0.242; −TTL 0.556/0.221; −TCPwin 0.606/0.332; −timing 0.634/0.296; −artifacts 0.565/0.431. NF-v3 BoT target: −TTL AUROC 0.684→0.413.
- **E6:** benign-only source-vs-target divergence (PSI, Wasserstein, |z|) averaged over ALL features, 12 directions; pre-declared gate ρ ≥ 0.5 vs transfer loss; recomputed Spearman ρ −0.29…0.44 → gate fails. No per-group shift.
- **E4 (identifier removal, overlaps angle b):** NF-v3 AUROC XGB 0.510 [E1 0.597], RF 0.560 [0.627], ERM-CB 0.428 [0.536], BRN 0.388 [0.582] → removal hurts.
- **BRN** = per-source z-score on own benign (log then z), target z-scored on target window. NF-v3 benchmark mean AUROC: ERM-CB 0.536, XGB 0.597, RF 0.627, CORAL 0.484, DANN 0.466, DomNorm 0.496, BRN 0.582, BRN-XGB 0.627, KNN-win 0.842.

## P02 Rayamajhi 2026 "Is It Transfer?" (10.20944/preprints202610.1041.v1)
- Full text NOT obtained (preprints.org 403). Abstract only: pairwise (12 directed), 10 seeds, 540 Wilcoxon comparisons; source helps 8 %, hurts 38 %; domain AUC ≥ 0.996; 23–40 of 45 features must be removed for AUC < 0.9; TTL removal does not change conclusion; per-domain scaling corrupts separability measurements. Rest UNVERIFIED.

## P04 Valencia Vélez 2026 (Zenodo 23291192)
- Opened code/results zip (README, configs, result txt files); manuscript not deposited. NF-v2/v3 ToN, BoT, CIC (no UNSW). Pairwise, XGB/RF, 5 seeds. Removal conditions G-NP (no dst port), G-NI (no ports/TTL/TCPwin/DNS), G-NIS0 (+no L7/ICMP): transfer worse than baseline in 18/24 (p=0.023), 18/24, 19/24 (p=0.0066) cases (rq3_figures.txt). DNS_TTL_ANSWER anomaly (320 BoT-v3 rows > int32 max).

## Layeghy & Portmann 2023 — via arXiv 2205.04112v1 (OA copy; published version may differ)
- NF-v2, 4 datasets, 1M stratified samples, single-source→target, default hyper-params, no seeds/stats. Supervised mean F1 decay 56.28 % (Table 5), unsupervised 28.33 %. SHAP: UNSW→BoT ET ≈ MAX_TTL rule (Fig. 6); F1 94.83 % UNSW→BoT vs 4.90 % BoT→UNSW (Table 4).

## Sarhan, Layeghy & Portmann 2022 — via arXiv 2104.07183v2
- Within-dataset only; SHAP ranks TCP window and TTL highly. No cross-dataset.

## Verdict (updates prior_art.md "Blunt verdict")
- Angle (a) is PARTLY DONE (Gazi E7 group ablations + E6 all-feature benign divergence that fails to predict loss). Remaining delta: per-GROUP benign shift measurement linked quantitatively to per-group ablation effect, with tuned models, finer groups (DNS/FTP/flags/ports separately), and benign-vs-attack-shift decomposition.
- Angle (b) is PARTLY DONE: removal tested and found harmful (Gazi E4/E7, Valencia, Rayamajhi); per-domain benign z-normalisation (BRN) benchmarked. Remaining delta: source-only quantile normalisation (PEN), data-driven ESF selection, external pre-registration. Narrow.
- Prediction from prior work: ESF/removal null or negative.
