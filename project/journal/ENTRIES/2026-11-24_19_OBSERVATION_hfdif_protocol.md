# 19 OBSERVATION — HF-DIF's real protocol is transductive, contaminated (2026-11-24, session 3)
I fetched the HF-DIF full text and Tables 1–4 with headless Chromium (Springer blocks curl with a JS challenge; text in
literature/fulltext/hfdif_2026_page.txt, parsed numbers in literature/hfdif_tables.csv).
The paper describes two incompatible protocols: "50 % of the normal samples are used for training" (Sec. 6.1, metrics) and
"each model ... is trained with bootstrapping on the entire dataset, and anomaly scores are evaluated for all samples" (Sec. 6.1, splitting).
Test: ECOD and COPOD are deterministic, so their numbers fingerprint the protocol. Under our `transd` protocol (z-score whole set,
fit all, score all), ECOD seed 0 reproduces their Table 2 within 1.1 AUC-ROC points on 19/20 datasets (e.g. Cardiotocography 78.5 vs 78.4,
Wilt 39.4 vs 39.4, Landsat 36.8 vs 36.8). Backdoor is the outlier: ours 84.6 vs theirs 50.0 (COPOD 78.9 vs 51.0) — probably a failed
run on their side (50.0 = random). Their HF-DIF Backdoor number (93.9) therefore sits next to broken baselines.
Consequence: the setting to beat is the CONTAMINATED transductive one, where kNN is known to suffer (Bershtman & Cohen: kNN −11 points
under contamination). That points the method design at contamination/masking, not at the clean one-class setting.
