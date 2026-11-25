# Prior art for H6 (minimax / bottleneck distance to the training mass core) — 2026-11-25
Search done by a sub-agent: OpenAlex (~48 queries), arXiv (~32), Semantic Scholar (6, all HTTP 429), Crossref (4); the full query list is in the session report summarised below. "Opened" = abstract at least; full text where marked.

## Verdict
No paper found that scores test points by minimax (bottleneck) path distance to the MST/single-linkage component holding ≥ 50 % of the training mass. The ingredients are known, so H6 is a recombination:
- **GLOSH** (Campello, Moulavi, Zimek, Sander, TKDD 2015, 10.1145/2733381): the exit level is normalised by the densest level of x's OWN cluster, so a dense anomaly cluster becomes its own cluster and scores low (checked in hdbscan `_hdbscan_tree.pyx`: λ(x)/λ_max(cluster)). H6 uses the unnormalised minimax height to ONE mass-defined component.
- **Chehreghani** (SDM 2016 10.1137/1.9781611974348.46; MLJ 2020 arXiv:1904.13223 §4.4, full text read): yes/no outlier flag found during minimax-kNN search ("min direct edge > max indirect edge"). No score, no core, no ADBench.
- **CBLOF** (He, Xu, Deng, PRL 2003, 10.1016/S0167-8655(03)00003-5): small clusters scored by Euclidean distance to the centroids of the "large" k-means clusters (α = 0.9). H6 uses minimax path distance through the MST, not distance to centroids.
- Masking motivation: D.MCA (Jiang, Cordeiro, Akoglu, ICDM 2022, 10.1109/ICDM54844.2022.00119); DROD (arXiv:2603.12847); SCiForest (10.1007/978-3-642-15883-4_18); LOCI (10.1109/ICDE.2003.1260802).
- MST-based detectors: RIFT (Szalai & Horváth 2026, arXiv:2610.12244, full text read; ADBench Table 7, ≤20k rows: IF 0.7561, RIFT 0.7526, KNN 0.7476, CBLOF 0.7461); LoMST (10.1109/TASE.2018.2848198, closed access); MS2OD (10.1088/2632-2153/ad2492); COF (10.1007/3-540-47887-6_53).
- Model selection: MetaOD (arXiv:2009.10606), ELECT (arXiv:2211.01834), UOMS (arXiv:2104.01422: internal strategies "none practically useful"), IREOS (10.1145/3394053), HPOD (arXiv:2208.11727).
- Contamination remedies: SRR (arXiv:2106.06115), AAR (arXiv:2511.21378), EPHAD (arXiv:2510.21296).
- The "ZEN/FOCUS" papers named in journal 19 could not be found by title. They remain UNVERIFIED until located.

## Baselines this implies
CBLOF (PyOD), COF (PyOD), GLOSH (`hdbscan` package; PyOD's `hdbscan` model is NOT GLOSH), plus kNN with k=1 and k=5. RIFT has no package; it is deferred and noted as a limitation if it is not re-implemented.

## One-sentence difference (claim table)
H6 scores x by the single-linkage (subdominant-ultrametric) height at which x joins the component holding the majority of the training mass. GLOSH normalises per own cluster, CBLOF uses distances to centroids, and Chehreghani gives only a binary flag.
