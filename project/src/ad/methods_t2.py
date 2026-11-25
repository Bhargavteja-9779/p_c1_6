"""Topic 2 candidate methods (developed on DEV sets only, D35).

Core idea under test (H4, journal 20): in the contaminated transductive setting, anomalies sit inside the reference set
that distance/isolation detectors score against. Clustered anomalies then vouch for each other (masking): their k nearest
neighbours are other anomalies, and isolation trees spend splits on them. We rebuild the reference set from the points the
detector itself trusts most, re-score EVERY point against that trimmed reference, and repeat.

All methods expose fit(X) / decision_function(X) (higher = more anomalous), PyOD-style, CPU only.
"""
import numpy as np
from scipy.stats import rankdata
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import IsolationForest


def _rank01(s):
    return (rankdata(s) - 1) / max(1, len(s) - 1)


def knn_to_ref(X, ref_idx, k, self_in_ref=None):
    """Mean distance of every row of X to its k nearest rows of X[ref_idx]; a point never counts as its own neighbour."""
    R = X[ref_idx]
    kk = min(k + 1, len(R))
    nn = NearestNeighbors(n_neighbors=kk, n_jobs=1).fit(R)
    d, i = nn.kneighbors(X)
    is_self = ref_idx[i] == np.arange(len(X))[:, None]
    d = np.where(is_self, np.inf, d)
    d = np.sort(d, axis=1)[:, : kk - 1] if kk > 1 else d
    d = d[:, :k]
    d = np.where(np.isfinite(d), d, np.nan)
    return np.nanmean(d, axis=1)


class TrimKNN:
    """Iteratively trimmed-reference kNN (variant family; hyper-parameters chosen on DEV only)."""

    def __init__(self, k=10, trim=0.1, iters=2, use_if=False, n_trees=200, seed=0, feat_w=False, if_weight=0.5):
        self.k, self.trim, self.iters, self.use_if, self.n_trees, self.seed = k, trim, iters, use_if, n_trees, seed
        self.feat_w, self.if_weight = feat_w, if_weight

    def _score(self, X, ref):
        s = _rank01(knn_to_ref(X, ref, self.k))
        if self.use_if:
            f = IsolationForest(n_estimators=self.n_trees, max_samples=min(256, len(ref)), random_state=self.seed, n_jobs=1)
            f.fit(X[ref])
            s = (1 - self.if_weight) * s + self.if_weight * _rank01(-f.score_samples(X))
        return s

    def fit(self, X):
        self.X_ = X = np.asarray(X, float)
        n = len(X); ref = np.arange(n)
        s = self._score(X, ref)
        self.trace_ = [s]
        for _ in range(self.iters):
            keep = s <= np.quantile(s, 1 - self.trim)
            ref = np.flatnonzero(keep)
            if self.feat_w:
                Xw = self._weight(X, s, keep)
                s = self._score_w(Xw, ref)
            else:
                s = self._score(X, ref)
            self.trace_.append(s)
        self.s_ = s
        return self

    def _weight(self, X, s, keep):
        # pseudo-label contrast: features where suspected anomalies differ from the trusted reference get more weight
        a, r = X[~keep], X[keep]
        sd = r.std(0) + 1e-9
        w = np.abs(a.mean(0) - r.mean(0)) / sd + 0.5 * np.abs(np.log((a.std(0) + 1e-9) / sd))
        w = w / (w.mean() + 1e-12)
        return X * np.sqrt(w)

    def _score_w(self, Xw, ref):
        return self._score(Xw, ref)

    def decision_function(self, X):
        assert X is self.X_ or np.array_equal(X, self.X_), "transductive method: score the fitted set"
        return self.s_


class TrimIF:
    """Isolation forest re-grown on the trimmed reference set (subsamples drawn only from trusted points), every point re-scored."""

    def __init__(self, trim=0.1, iters=2, n_trees=200, seed=0):
        self.trim, self.iters, self.n_trees, self.seed = trim, iters, n_trees, seed

    def _if(self, X, ref, r):
        f = IsolationForest(n_estimators=self.n_trees, max_samples=min(256, len(ref)), random_state=self.seed + r, n_jobs=1)
        return -f.fit(X[ref]).score_samples(X)

    def fit(self, X):
        self.X_ = X = np.asarray(X, float)
        ref = np.arange(len(X)); s = self._if(X, ref, 0)
        for r in range(self.iters):
            ref = np.flatnonzero(s <= np.quantile(s, 1 - self.trim)); s = self._if(X, ref, r + 1)
        self.s_ = s
        return self

    def decision_function(self, X):
        return self.s_


class ProjPursuitIF:
    """Random (linear or random-tanh) projections; keep the most outlier-revealing ones (|skew| + excess kurtosis, computed on the
    data itself, no labels); isolation forest on the kept projections. Optional trimming rounds (TrimIF logic) and kNN fusion."""

    def __init__(self, n_proj=256, keep=0.25, kind="lin", trim=0.0, iters=0, n_trees=200, knn=0, seed=0, crit="kurt"):
        self.n_proj, self.keep, self.kind, self.trim, self.iters = n_proj, keep, kind, trim, iters
        self.n_trees, self.knn, self.seed, self.crit = n_trees, knn, seed, crit

    def _proj(self, X, rng):
        d = X.shape[1]
        if self.kind == "lin":
            W = rng.standard_normal((d, self.n_proj)) / np.sqrt(d); return X @ W
        if self.kind == "mlp":  # one random tanh hidden layer then a random linear read-out (DIF-style random representation)
            h = 128; W1 = rng.standard_normal((d, h)) / np.sqrt(d); W2 = rng.standard_normal((h, self.n_proj)) / np.sqrt(h)
            return np.tanh(X @ W1) @ W2
        raise ValueError(self.kind)

    def _select(self, Z, ref):
        R = Z[ref]; mu = R.mean(0); sd = R.std(0) + 1e-12; U = (R - mu) / sd
        sk = np.abs((U ** 3).mean(0)); ku = (U ** 4).mean(0) - 3
        c = {"kurt": ku, "skew": sk, "both": sk + np.maximum(ku, 0) / 2}[self.crit]
        m = max(1, int(round(self.keep * Z.shape[1])))
        idx = np.argsort(-c)[:m]
        return (Z[:, idx] - mu[idx]) / sd[idx]

    def _score(self, X, ref, r):
        rng = np.random.default_rng(self.seed * 1000 + r)
        Z = self._proj(X, rng) if self.keep < 1 or self.kind != "none" else X
        Zs = self._select(Z, ref)
        f = IsolationForest(n_estimators=self.n_trees, max_samples=min(256, len(ref)), random_state=self.seed + r, n_jobs=1)
        s = _rank01(-f.fit(Zs[ref]).score_samples(Zs))
        if self.knn:
            s = 0.5 * s + 0.5 * _rank01(knn_to_ref(X, ref, self.knn))
        return s

    def fit(self, X):
        self.X_ = X = np.asarray(X, float)
        ref = np.arange(len(X)); s = self._score(X, ref, 0)
        for r in range(self.iters):
            ref = np.flatnonzero(s <= np.quantile(s, 1 - self.trim)); s = self._score(X, ref, r + 1)
        self.s_ = s
        return self

    def decision_function(self, X):
        return self.s_


class RankEns:
    """Rank-average of iForest, kNN(k) and ECOD (all transductive)."""
    def __init__(self, k=10, seed=0, parts="ike"):
        self.k, self.seed, self.parts = k, seed, parts
    def fit(self, X):
        from pyod.models.ecod import ECOD
        X = np.asarray(X, float); S = []
        if "i" in self.parts: S.append(_rank01(-IsolationForest(n_estimators=200, random_state=self.seed, n_jobs=1).fit(X).score_samples(X)))
        if "k" in self.parts: S.append(_rank01(knn_to_ref(X, np.arange(len(X)), self.k)))
        if "e" in self.parts: S.append(_rank01(ECOD().fit(X).decision_scores_))
        self.s_ = np.mean(S, 0); return self
    def decision_function(self, X):
        return self.s_


class _Plain:
    def __init__(self, f): self.f = f
    def fit(self, X): self.s_ = self.f(np.asarray(X, float)); return self
    def decision_function(self, X): return self.s_


def knn_profile(X, ref_idx, ks):
    """Distances of every row to its k-th nearest reference row (self excluded) for each k in ks (sorted); returns (n, len(ks))."""
    R = X[ref_idx]; K = min(max(ks) + 1, len(R))
    nn = NearestNeighbors(n_neighbors=K, n_jobs=1).fit(R)
    out = np.empty((len(X), len(ks)))
    for b in range(0, len(X), 4096):  # chunk to bound memory (K can be large)
        d, i = nn.kneighbors(X[b:b + 4096])
        self_ = ref_idx[i] == np.arange(b, b + len(d))[:, None]
        d = np.where(self_, np.inf, d); d.sort(axis=1)
        cm = np.cumsum(np.where(np.isfinite(d), d, 0), axis=1)
        for j, k in enumerate(ks):
            kk = min(k, K - 1); out[b:b + len(d), j] = cm[:, kk - 1] / kk  # mean distance to the kk nearest
    return out


class SubKNN:
    """Subsampled kNN ensemble (Zimek et al. 2013 style): B random reference subsamples of size m, mean-distance kNN, averaged."""
    def __init__(self, m=256, k=5, B=20, seed=0):
        self.m, self.k, self.B, self.seed = m, k, B, seed
    def fit(self, X):
        X = np.asarray(X, float); rng = np.random.default_rng(self.seed); n = len(X); S = np.zeros(n)
        for b in range(self.B):
            ref = rng.choice(n, min(self.m, n), replace=False)
            S += knn_to_ref(X, ref, min(self.k, len(ref) - 1))
        self.s_ = S / self.B; return self
    def decision_function(self, X): return self.s_


class ScaleKNN:
    """kNN whose neighbourhood size is a fraction of n (frac) or a multi-scale rank aggregate over a geometric k grid."""
    def __init__(self, frac=0.01, mode="frac", kmax_frac=0.05, agg="mean", cap=20000, seed=0):
        self.frac, self.mode, self.kmax_frac, self.agg, self.cap, self.seed = frac, mode, kmax_frac, agg, cap, seed
    def fit(self, X):
        X = np.asarray(X, float); n = len(X); rng = np.random.default_rng(self.seed)
        ref = np.sort(rng.choice(n, self.cap, replace=False)) if n > self.cap else np.arange(n)  # bounded reference for huge n
        m = len(ref)
        if self.mode == "frac":
            k = max(1, int(round(self.frac * m))); self.s_ = knn_profile(X, ref, [k])[:, 0]
        else:
            kmax = max(2, int(round(self.kmax_frac * m))); ks = sorted(set(int(2 ** e) for e in np.arange(0, np.log2(kmax) + 1)))
            P = knn_profile(X, ref, ks)
            Rk = np.column_stack([_rank01(P[:, j]) for j in range(P.shape[1])])
            self.s_ = Rk.mean(1) if self.agg == "mean" else Rk.max(1)
        return self
    def decision_function(self, X): return self.s_


def make(method, seed, n_train):
    p = method.split("_")
    name, kw = p[0], {}
    for t in p[1:]:
        key, val = t[0], t[1:]
        if key == "k": kw["k"] = int(val)
        elif key == "t": kw["trim"] = float(val)
        elif key == "i": kw["iters"] = int(val)
        elif key == "f": kw["use_if"] = val == "1"
        elif key == "w": kw["feat_w"] = val == "1"
        elif key == "a": kw["if_weight"] = float(val)
        elif key == "P": kw["n_proj"] = int(val)
        elif key == "K": kw["keep"] = float(val)
        elif key == "R": kw["kind"] = val
        elif key == "N": kw["knn"] = int(val)
        elif key == "C": kw["crit"] = val
        elif key == "E": kw["parts"] = val
        elif key == "F": kw["frac"] = float(val)
        elif key == "M": kw["mode"] = val
        elif key == "X": kw["kmax_frac"] = float(val)
        elif key == "G": kw["agg"] = val
        elif key == "m": kw["m"] = int(val)
        elif key == "B": kw["B"] = int(val)
    if name == "trim":
        return TrimKNN(seed=seed, **kw)
    if name == "trimif":
        return TrimIF(seed=seed, **{k: v for k, v in kw.items() if k in ("trim", "iters")})
    if name == "ppif":
        return ProjPursuitIF(seed=seed, **{k: v for k, v in kw.items() if k in ("n_proj", "keep", "kind", "trim", "iters", "knn", "crit")})
    if name == "ens":
        return RankEns(seed=seed, **{k: v for k, v in kw.items() if k in ("k", "parts")})
    if name == "knnk":   # plain transductive kNN (mean distance, self excluded) with chosen k
        return _Plain(lambda X: knn_to_ref(X, np.arange(len(X)), kw.get("k", 10)))
    if name == "lofk":
        from sklearn.neighbors import LocalOutlierFactor
        return _Plain(lambda X: -LocalOutlierFactor(n_neighbors=kw.get("k", 20)).fit(X).negative_outlier_factor_)
    if name == "scknn":
        return ScaleKNN(seed=seed, **{k: v for k, v in kw.items() if k in ("frac", "mode", "kmax_frac", "agg")})
    if name == "subknn":
        return SubKNN(seed=seed, **{k: v for k, v in kw.items() if k in ("m", "k", "B")})
    raise ValueError(f"unknown method {method}")


# ---------------------------------------------------------------- round 2 (journal 23): bolder ideas, DEV only
def _knn_scale(X, frac=0.1, cap=20000, seed=0):
    n = len(X); rng = np.random.default_rng(seed)
    ref = np.sort(rng.choice(n, cap, replace=False)) if n > cap else np.arange(n)
    k = max(1, int(round(frac * len(ref))))
    return knn_profile(X, ref, [k])[:, 0]


def _views(X, n_views, seed, kinds="zrms"):
    """Random representations: z (as is), r (rank/copula), m (random tanh MLP, d=40), s (random half feature subspace)."""
    rng = np.random.default_rng(seed); n, d = X.shape; V = []
    for v in range(n_views):
        kd = kinds[v % len(kinds)]
        if kd == "z": V.append(X)
        elif kd == "r": V.append(np.column_stack([_rank01(X[:, j]) for j in range(d)]) * np.sqrt(12))
        elif kd == "m":
            W1 = rng.standard_normal((d, 128)) / np.sqrt(d); W2 = rng.standard_normal((128, 40)) / np.sqrt(128)
            Z = np.tanh(X @ W1) @ W2; V.append((Z - Z.mean(0)) / (Z.std(0) + 1e-9))
        elif kd == "s":
            idx = rng.choice(d, max(1, d // 2), replace=False); V.append(X[:, idx])
    return V


class MRK:
    def __init__(self, frac=0.1, n_views=8, kinds="zrms", seed=0):
        self.frac, self.n_views, self.kinds, self.seed = frac, n_views, kinds, seed
    def fit(self, X):
        X = np.asarray(X, float)
        self.s_ = np.mean([_rank01(_knn_scale(V, self.frac, seed=self.seed + i)) for i, V in enumerate(_views(X, self.n_views, self.seed, self.kinds))], 0)
        return self
    def decision_function(self, X): return self.s_


class Fuse:
    """Rank fusion of masking-safe kNN and isolation forest."""
    def __init__(self, frac=0.1, w=0.5, seed=0):
        self.frac, self.w, self.seed = frac, w, seed
    def fit(self, X):
        X = np.asarray(X, float)
        a = _rank01(_knn_scale(X, self.frac, seed=self.seed))
        b = _rank01(-IsolationForest(n_estimators=200, random_state=self.seed, n_jobs=1).fit(X).score_samples(X))
        self.s_ = (1 - self.w) * a + self.w * b; return self
    def decision_function(self, X): return self.s_


class NCB:
    """Noise-contrastive scoring: a classifier learns real vs. Gaussian-perturbed copies (several noise scales); the cross-fitted
    probability that a REAL point is 'perturbed' is its anomaly score (off-manifold points look like noise)."""
    def __init__(self, clf="hgb", sigmas=(0.1, 0.3, 1.0), folds=3, cap=20000, seed=0):
        self.clf, self.sigmas, self.folds, self.cap, self.seed = clf, sigmas, folds, cap, seed
    def _model(self):
        if self.clf == "hgb":
            from sklearn.ensemble import HistGradientBoostingClassifier
            return HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, random_state=self.seed)
        from sklearn.neural_network import MLPClassifier
        return MLPClassifier(hidden_layer_sizes=(128, 128), max_iter=60, early_stopping=False, random_state=self.seed)
    def fit(self, X):
        X = np.asarray(X, float); n = len(X); rng = np.random.default_rng(self.seed)
        fold = rng.integers(0, self.folds, n); s = np.zeros(n)
        for f in range(self.folds):
            tr = np.flatnonzero(fold != f)
            if len(tr) > self.cap: tr = rng.choice(tr, self.cap, replace=False)
            Xr = X[tr]; Xn = np.vstack([Xr + sg * rng.standard_normal(Xr.shape) for sg in self.sigmas])
            m = self._model().fit(np.vstack([Xr, Xn]), np.r_[np.zeros(len(Xr)), np.ones(len(Xn))])
            te = np.flatnonzero(fold == f); s[te] = m.predict_proba(X[te])[:, 1]
        self.s_ = s; return self
    def decision_function(self, X): return self.s_


class PLST:
    """Pseudo-label self-training: consensus score -> top q as pseudo-anomalies, bottom half as pseudo-normals ->
    cross-fitted gradient boosting -> blend with the consensus; repeated `rounds` times."""
    def __init__(self, q=0.05, rounds=2, blend=0.5, frac=0.1, seed=0):
        self.q, self.rounds, self.blend, self.frac, self.seed = q, rounds, blend, frac, seed
    def fit(self, X):
        from sklearn.ensemble import HistGradientBoostingClassifier
        X = np.asarray(X, float); n = len(X); rng = np.random.default_rng(self.seed)
        s = 0.5 * _rank01(_knn_scale(X, self.frac, seed=self.seed)) + \
            0.5 * _rank01(-IsolationForest(n_estimators=200, random_state=self.seed, n_jobs=1).fit(X).score_samples(X))
        for r in range(self.rounds):
            hi = s >= np.quantile(s, 1 - self.q); lo = s <= np.quantile(s, 0.5)
            fold = rng.integers(0, 3, n); p = np.zeros(n)
            for f in range(3):
                tr = np.flatnonzero((fold != f) & (hi | lo))
                m = HistGradientBoostingClassifier(max_iter=100, random_state=self.seed + r, class_weight="balanced").fit(X[tr], hi[tr].astype(int))
                te = np.flatnonzero(fold == f); p[te] = m.predict_proba(X[te])[:, 1]
            s = (1 - self.blend) * s + self.blend * _rank01(p)
        self.s_ = s; return self
    def decision_function(self, X): return self.s_


class SelK:
    """Label-free choice of the kNN scale per dataset from the distance profile over a geometric k grid (k <= kmax_frac * n).
    rule 'stab': smallest k whose ranking agrees with the next scale (Spearman >= tau) -> end of the masking regime.
    rule 'cent': the scale whose ranking has the highest mean Spearman correlation with all other scales."""
    def __init__(self, rule="stab", tau=0.95, kmax_frac=0.2, cap=20000, seed=0):
        self.rule, self.tau, self.kmax_frac, self.cap, self.seed = rule, tau, kmax_frac, cap, seed
    def fit(self, X):
        X = np.asarray(X, float); n = len(X); rng = np.random.default_rng(self.seed)
        ref = np.sort(rng.choice(n, self.cap, replace=False)) if n > self.cap else np.arange(n)
        kmax = max(2, int(self.kmax_frac * len(ref))); ks = sorted(set(int(2 ** e) for e in np.arange(0, np.log2(kmax) + 1)))
        P = knn_profile(X, ref, ks); Rk = np.column_stack([_rank01(P[:, j]) for j in range(len(ks))])
        C = np.corrcoef(Rk.T)
        if self.rule == "stab":
            j = next((j for j in range(len(ks) - 1) if C[j, j + 1] >= self.tau), len(ks) - 1)
        else:
            j = int(np.argmax(C.mean(1)))
        self.k_ = ks[j]; self.s_ = Rk[:, j]; return self
    def decision_function(self, X): return self.s_


_make1 = make


def make(method, seed, n_train):
    p = method.split("_"); name = p[0]; kw = {}
    for t in p[1:]:
        key, val = t[0], t[1:]
        kw[key] = val
    if name == "mrk":
        return MRK(frac=float(kw.get("F", 0.1)), n_views=int(kw.get("V", 8)), kinds=kw.get("R", "zrms"), seed=seed)
    if name == "selk":
        return SelK(rule=kw.get("U", "stab"), tau=float(kw.get("T", 0.95)), kmax_frac=float(kw.get("X", 0.2)), seed=seed)
    if name == "fuse":
        return Fuse(frac=float(kw.get("F", 0.1)), w=float(kw.get("w", 0.5)), seed=seed)
    if name == "ncb":
        sg = tuple(float(x) for x in kw.get("S", "0.1-0.3-1.0").split("-"))
        return NCB(clf=kw.get("C", "hgb"), sigmas=sg, seed=seed)
    if name == "plst":
        return PLST(q=float(kw.get("q", 0.05)), rounds=int(kw.get("r", 2)), blend=float(kw.get("b", 0.5)), seed=seed)
    return _make1(method, seed, n_train)
