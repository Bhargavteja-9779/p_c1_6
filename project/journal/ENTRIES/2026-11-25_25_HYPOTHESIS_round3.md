# 25 HYPOTHESIS — round 3: a different signal (written before results)
Journal 24 showed that selecting/fusing existing detectors has ≤ 1.4 points of headroom on DEV. Two new signals:
- LWK (locally whitened kNN): anchors by k-means on the data; each anchor owns its K = 10 % n nearest points (masking-safe scale);
  local mean + Ledoit–Wolf covariance; a point's score = min Mahalanobis distance over its 3 nearest anchors. Prediction: gains on
  sets with correlated / mixed-scale features (where Euclidean kNN mis-measures distance), e.g. letter, annthyroid, pima, skin.
- AntiHub at scale (reverse-kNN count with k = 1–10 % n; few points name you as a neighbour → anomalous). Known (Radovanović et al. 2015)
  — enters as a component/baseline, not as the contribution.
Keep rule: DEV mean AUC-ROC > 83.5 (kNN 10 %) without AUC-PR loss > 1, or AUC-PR > 47.1 without AUC-ROC loss > 1.
