# SURPRISE — 2026-11-24 (session 2) — the closest prior work already contains both of my remaining angles
I downloaded and read the code deposit of Gazi, Prappo & Hossain (Zenodo 10.5281/zenodo.24172401, v1.0.0, README + docs/EXPERIMENTS.md + crossnet/preprocess.py + experiments/feature_groups.py). The paper text is still not public. The code shows:
- Leave-one-testbed-out on all four NF-v2 and NF-v3 testbeds, 18 methods, equal source-only tuning budget (12 configs), 10 seeds.
- `brn_transform` ("benign-referenced normalisation"): each source testbed z-scored with its own benign flows, the target with a short mostly-benign target window. This is essentially my PEN remedy (per-network benign-relative normalisation). They also have a `DomNorm` control that differs only in the reference population.
- E7 feature-group ablation: XGBoost retrained without TTL / TCP window / timing / all artefacts incl. ports, reporting target AUROC and target-benign FPR at a source-calibrated 1% FPR threshold. This is my angle (a) in its associative form.
- E2 failure decomposition: target benign vs seen-family attacks vs novel-family attacks, i.e. "is the failure network-driven or caused by novel attacks?".
- E6 pairwise transfer with a divergence audit (PSI, Wasserstein, standardised difference of benign traffic) correlated with transfer loss.
- E4 identifier-free features; E5 within- vs cross-network temporal training; window size/contamination/poisoning studies.
So H1's remedy (PEN) and the attribution angle (a) are both covered, and the "pre-registered remedy test" angle (b) is covered by their S2 setting with hypothesis tests. What I planned as cycle 1 is now largely an independent replication.
