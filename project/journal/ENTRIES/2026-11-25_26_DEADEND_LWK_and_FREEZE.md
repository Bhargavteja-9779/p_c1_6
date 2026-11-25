# 26 DEAD END (LWK, AntiHub) and FREEZE decision
DEV (27 sets): LWK 63.9 → with shrinkage toward isotropic λ=0.5: 77.7, λ=0.8: 79.6 — monotone toward plain Euclidean kNN (83.5),
so local whitening only hurts on average (one exception: letter 91.7 vs 78.3). AntiHub at k = 1/5/10 % n: 60.7 / 71.0 / 75.4.
Diagnosis: whitening amplifies low-variance and discrete feature directions (cardio, Pima), which dominate the Mahalanobis distance.
After 3 rounds (~25 variants, variants_tried.csv) the only robust DEV gain is the neighbourhood SCALE (journal 21–22).
TURN: freeze kNN at k = 10 % n as the candidate (plan_v4, D36) and run it ONCE on EVAL; decide the paper's direction from that.
