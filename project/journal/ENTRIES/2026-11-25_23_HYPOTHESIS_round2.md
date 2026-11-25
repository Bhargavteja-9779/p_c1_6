# 23 HYPOTHESIS — round 2 "improvise more" (user, 2026-11-25); written before any DEV result of these variants
Four bolder mechanisms, each aimed at a different failure seen so far (journal 21–22):
- MRK: masking-safe kNN (k = 10 % n) averaged over random representations (z, rank/copula, random tanh MLP d=40, half-feature
  subspaces). Expect gains on sets where irrelevant/badly scaled features hurt kNN (DIF/HF-DIF's source of diversity, CPU only).
- FUSE: rank fusion of kNN-scale and isolation forest. Expect AUC-PR of iForest with AUC-ROC of kNN-scale.
- NCB: noise-contrastive boosting/MLP (real vs Gaussian-perturbed copies, cross-fitted); CPU analogue of DNE (which wins Wilt/Vowels).
  Expect large gains on "manifold" sets, losses on high-anomaly-rate sets.
- PLST: pseudo-label self-training from the FUSE consensus (top 5 % vs bottom 50 %, cross-fitted gradient boosting, 2 rounds).
  Risk: confirmation bias; expect gains only where the consensus top is already precise.
Decision rule (fixed now): a variant is kept for the next round only if its DEV mean AUC-ROC beats kNN k=10 % n (83.5) or its AUC-PR
beats iForest (47.1) without losing > 1 AUC-ROC point. All variants enter variants_tried / Holm family.
