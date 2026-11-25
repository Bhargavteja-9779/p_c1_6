"""Topic-2 methods (H5). All label-free. PyOD-style: fit(X), decision_function(X) -> higher = more anomalous."""
import numpy as np
from sklearn.neighbors import NearestNeighbors


def _subsample_knn_scores(R, Q, n_sub, psi, k, rng, exclude_self=False):
    """Mean over n_sub random subsamples (size psi) of R of the k-th NN distance from Q to the subsample."""
    out = np.zeros(len(Q)); n = len(R)
    for _ in range(n_sub):
        idx = rng.choice(n, min(psi, n), replace=False)
        kk = min(k + (1 if exclude_self else 0), len(idx))
        d, i = NearestNeighbors(n_neighbors=kk).fit(R[idx]).kneighbors(Q)
        if exclude_self:  # drop a neighbour that is the query itself (distance 0 and same index)
            d = np.where(d[:, :1] == 0, d[:, 1:kk] if kk > 1 else d, d[:, :kk - 1] if kk > 1 else d)
        out += d[:, -1]
    return out / n_sub


class KNNScreen:
    def __init__(self, seed=0, k=5, trust="iforest", drop=0.10, adaptive=False, n_sub=50, psi=256):
        self.seed, self.k, self.trust, self.drop, self.adaptive, self.n_sub, self.psi = seed, k, trust, drop, adaptive, n_sub, psi

    def fit(self, X):
        rng = np.random.default_rng(self.seed)
        if self.trust == "iforest":
            from sklearn.ensemble import IsolationForest
            t = -IsolationForest(max_samples=min(self.psi, len(X)), random_state=self.seed).fit(X).score_samples(X)
        elif self.trust == "subknn":
            t = _subsample_knn_scores(X, X, self.n_sub, self.psi, 1, rng, exclude_self=True)
        else:
            raise ValueError(self.trust)
        if self.adaptive:
            q1, q3 = np.percentile(t, [25, 75]); keep = t <= q3 + 1.5 * (q3 - q1)
        else:
            keep = t <= np.quantile(t, 1 - self.drop)
        if keep.sum() < self.k + 1:
            keep = np.ones(len(X), bool)
        self.R = X[keep]; self.kept_frac = float(keep.mean())
        self.nn = NearestNeighbors(n_neighbors=min(self.k, len(self.R))).fit(self.R)
        return self

    def decision_function(self, X):
        return self.nn.kneighbors(X)[0][:, -1]


class SubKNN:
    """B1 baseline: subsampled kNN ensemble without cleaning (Aggarwal & Sathe 2015 style)."""
    def __init__(self, seed=0, k=5, n_sub=50, psi=256):
        self.seed, self.k, self.n_sub, self.psi = seed, k, n_sub, psi

    def fit(self, X):
        self.X = X; return self

    def decision_function(self, X):
        return _subsample_knn_scores(self.X, X, self.n_sub, self.psi, self.k, np.random.default_rng(self.seed))


def make(method, seed, n_train):
    M = {"scr_a1": lambda: KNNScreen(seed, trust="iforest", drop=0.10), "scr_a2": lambda: KNNScreen(seed, trust="iforest", drop=0.20),
         "scr_a3": lambda: KNNScreen(seed, trust="subknn", drop=0.10), "scr_a4": lambda: KNNScreen(seed, trust="subknn", drop=0.20),
         "scr_a5": lambda: KNNScreen(seed, trust="subknn", adaptive=True), "subknn": lambda: SubKNN(seed)}
    if method not in M:
        raise ValueError(f"unknown method {method}")
    return M[method]()
