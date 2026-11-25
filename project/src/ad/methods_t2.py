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


class MinimaxCore:
    """H6 candidate (journal 24): minimax (bottleneck) path distance from a test point to the training 'core'.
    Core = Kruskal components of the training MST at the first level where the largest component holds >= frac*n
    points; with min_comp>0, every component of size >= min_comp*n at that level also joins the core.
    m_j = minimax path distance from training point j to the core (0 inside); score(x) = min_j max(d(x,j), m_j)."""
    def __init__(self, seed=0, frac=0.5, min_comp=0.0, chunk=512):
        self.frac, self.min_comp, self.chunk = frac, min_comp, chunk

    def fit(self, X):
        from scipy.sparse.csgraph import minimum_spanning_tree
        from sklearn.metrics import pairwise_distances
        n = len(X); self.X = X
        D = pairwise_distances(X); D[D == 0] = 1e-12; np.fill_diagonal(D, 0)
        T = minimum_spanning_tree(D).tocoo(); del D
        order = np.argsort(T.data); a, b, w = T.row[order], T.col[order], T.data[order]
        parent = np.arange(n); size = np.ones(n, int)
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        for u, v in zip(a, b):
            ru, rv = find(u), find(v)
            if ru != rv:
                if size[ru] < size[rv]: ru, rv = rv, ru
                parent[rv] = ru; size[ru] += size[rv]
                if size[ru] >= self.frac * n: break
        roots = np.array([find(i) for i in range(n)])
        csize = np.bincount(roots, minlength=n)
        big = roots == np.argmax(csize)
        if self.min_comp > 0:
            big |= csize[roots] >= self.min_comp * n
        # propagate minimax distance outward from the core along the MST (a tree: unique path)
        adj = [[] for _ in range(n)]
        for u, v, ww in zip(T.row, T.col, T.data):
            adj[u].append((v, ww)); adj[v].append((u, ww))
        m = np.full(n, np.inf); m[big] = 0.0
        stack = list(np.flatnonzero(big))
        while stack:
            u = stack.pop()
            for v, ww in adj[u]:
                c = max(m[u], ww)
                if c < m[v]:
                    m[v] = c; stack.append(v)
        self.m = m; self.core_frac_ = float(big.mean())
        return self

    def decision_function(self, Q):
        from sklearn.metrics import pairwise_distances
        out = np.empty(len(Q))
        for i in range(0, len(Q), self.chunk):
            d = pairwise_distances(Q[i:i + self.chunk], self.X)
            out[i:i + self.chunk] = np.maximum(d, self.m[None, :]).min(1)
        return out


class GLOSH:
    """Baseline: GLOSH (Campello et al. 2015) via the hdbscan package; test points via approximate_predict_scores."""
    def __init__(self, seed=0, mcs=5, ms=5):
        self.mcs, self.ms = mcs, ms

    def fit(self, X):
        import hdbscan
        self.h = hdbscan.HDBSCAN(min_cluster_size=self.mcs, min_samples=self.ms, prediction_data=True).fit(X); return self

    def decision_function(self, X):
        import hdbscan
        return np.asarray(hdbscan.prediction.approximate_predict_scores(self.h, X), float)


class LocoKNN:
    """H7 (journal 28): leave-own-cluster-out kNN. Training graph = MUTUAL kNN (k_m); components of size <= cap*n are
    'small groups'. A test point's score is its k-th NN distance to the training set after removing every small group that
    contains one of its k nearest training neighbours. Large components (normal modes) are never removed. Per query, no
    iteration, no contamination ratio."""
    def __init__(self, seed=0, k=5, k_m=5, cap=0.05, chunk=512):
        self.k, self.k_m, self.cap, self.chunk = k, k_m, cap, chunk

    def fit(self, X):
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import connected_components
        n = len(X); self.X = X; km = min(self.k_m, n - 1)
        _, nb = NearestNeighbors(n_neighbors=km + 1).fit(X).kneighbors(X)
        nb = nb[:, 1:]
        A = csr_matrix((np.ones(n * km), (np.repeat(np.arange(n), km), nb.ravel())), shape=(n, n))
        M = A.multiply(A.T)                                   # mutual edges only
        _, lab = connected_components(M, directed=False)
        size = np.bincount(lab)
        self.lab = lab; self.small = size[lab] <= max(1, self.cap * n)
        self.small_frac_ = float(self.small.mean())
        return self

    def decision_function(self, Q):
        from sklearn.metrics import pairwise_distances
        n = len(self.X); k = min(self.k, n); out = np.empty(len(Q))
        for i in range(0, len(Q), self.chunk):
            d = pairwise_distances(Q[i:i + self.chunk], self.X)
            nn = np.argpartition(d, k - 1, axis=1)[:, :k]
            for r in range(len(d)):
                g = self.lab[nn[r][self.small[nn[r]]]]
                if len(g):
                    ex = np.isin(self.lab, g)
                    if ex.sum() <= n - k:
                        d[r, ex] = np.inf
            out[i:i + self.chunk] = np.partition(d, k - 1, axis=1)[:, k - 1]
        return out


class INNE:
    """Baseline: iNNE (Bandaragoda et al. 2018, 10.1111/coin.12156). t subsamples of size psi; each sampled point c has
    radius tau(c) = distance to its nearest neighbour in the subsample; x covered by balls -> take the smallest-radius ball c,
    isolation score 1 - tau(nn_in_sample(c)) / tau(c); not covered -> 1. Final score = mean over subsamples."""
    def __init__(self, seed=0, psi=16, t=100):
        self.psi, self.t, self.seed = psi, t, seed

    def fit(self, X):
        rng = np.random.default_rng(self.seed); self.models = []
        for _ in range(self.t):
            S = X[rng.choice(len(X), min(self.psi, len(X)), replace=False)]
            d, i = NearestNeighbors(n_neighbors=2).fit(S).kneighbors(S)
            tau = d[:, 1]; ratio = 1 - tau[i[:, 1]] / np.where(tau > 0, tau, 1e-12)
            self.models.append((S, tau, ratio))
        return self

    def decision_function(self, Q):
        from sklearn.metrics import pairwise_distances
        out = np.zeros(len(Q))
        for S, tau, ratio in self.models:
            d = pairwise_distances(Q, S); cov = d <= tau[None, :]
            r = np.where(cov, tau[None, :], np.inf); c = r.argmin(1)
            out += np.where(cov.any(1), ratio[c], 1.0)
        return out / self.t


def _KNNk(k):
    from pyod.models.knn import KNN
    return KNN(n_neighbors=k, method="largest")


def make(method, seed, n_train):
    M = {"scr_a1": lambda: KNNScreen(seed, trust="iforest", drop=0.10), "scr_a2": lambda: KNNScreen(seed, trust="iforest", drop=0.20),
         "scr_a3": lambda: KNNScreen(seed, trust="subknn", drop=0.10), "scr_a4": lambda: KNNScreen(seed, trust="subknn", drop=0.20),
         "scr_a5": lambda: KNNScreen(seed, trust="subknn", adaptive=True), "subknn": lambda: SubKNN(seed),
         "mmc_a": lambda: MinimaxCore(seed, frac=0.5), "mmc_b": lambda: MinimaxCore(seed, frac=0.5, min_comp=0.05),
         "mmc_c": lambda: MinimaxCore(seed, frac=0.3), "glosh": lambda: GLOSH(seed),
         "loco_a": lambda: LocoKNN(seed, k_m=5, cap=0.05), "loco_b": lambda: LocoKNN(seed, k_m=10, cap=0.05),
         "loco_c": lambda: LocoKNN(seed, k_m=5, cap=0.10), "inne": lambda: INNE(seed, psi=16),
         "subknn16": lambda: SubKNN(seed, k=1, psi=16), "knn50": lambda: _KNNk(min(50, max(1, n_train - 1)))}
    if method == "knn1":
        from pyod.models.knn import KNN
        return KNN(n_neighbors=1)
    if method == "cblof":
        from pyod.models.cblof import CBLOF
        return CBLOF(random_state=seed)
    if method == "cof":
        from pyod.models.cof import COF
        return COF(n_neighbors=min(20, max(2, n_train - 1)), method="fast")
    if method not in M:
        raise ValueError(f"unknown method {method}")
    return M[method]()
