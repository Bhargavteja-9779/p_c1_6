"""Core library: data access, feature treatments, models, metrics.

All selection (hyper-parameters, thresholds) uses SOURCE validation data only.
The TARGET test pool is only read when eval_split == "test" (confirmation runs).
"""
import os, time, json, pickle, io
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, roc_auc_score, average_precision_score, balanced_accuracy_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data/proc")
DATASETS = ["UNSW", "BOT", "TON", "CIC"]
META = ["Label", "Attack", "FLOW_START_MILLISECONDS"]
N_THREADS = max(1, (os.cpu_count() or 2))

# feature groups used in diagnostics (names from the UQ NetFlow V3 feature dictionary)
GROUPS = {
    "ttl": ["MIN_TTL", "MAX_TTL", "DNS_TTL_ANSWER"],
    "tcpwin": ["TCP_WIN_MAX_IN", "TCP_WIN_MAX_OUT"],
    "port_proto": ["L4_DST_PORT", "L7_PROTO", "PROTOCOL"],
    "app_fields": ["DNS_QUERY_TYPE", "FTP_COMMAND_RET_CODE", "ICMP_TYPE", "ICMP_IPV4_TYPE"],
    "flags": ["TCP_FLAGS", "CLIENT_TCP_FLAGS", "SERVER_TCP_FLAGS"],
}

# exhaustive partition of the 47 model features for transplant tests (E7)
TRANSPLANT_GROUPS = {
    "ttl": ["MIN_TTL", "MAX_TTL", "DNS_TTL_ANSWER"],
    "tcpwin": ["TCP_WIN_MAX_IN", "TCP_WIN_MAX_OUT"],
    "port_proto": ["L4_DST_PORT", "L7_PROTO", "PROTOCOL"],
    "app_fields": ["DNS_QUERY_TYPE", "FTP_COMMAND_RET_CODE", "ICMP_TYPE", "ICMP_IPV4_TYPE"],
    "flags": ["TCP_FLAGS", "CLIENT_TCP_FLAGS", "SERVER_TCP_FLAGS"],
    "volume": ["IN_BYTES", "OUT_BYTES", "IN_PKTS", "OUT_PKTS"],
    "pktsize": ["LONGEST_FLOW_PKT", "SHORTEST_FLOW_PKT", "MIN_IP_PKT_LEN", "MAX_IP_PKT_LEN", "NUM_PKTS_UP_TO_128_BYTES",
                "NUM_PKTS_128_TO_256_BYTES", "NUM_PKTS_256_TO_512_BYTES", "NUM_PKTS_512_TO_1024_BYTES", "NUM_PKTS_1024_TO_1514_BYTES"],
    "timing": ["FLOW_DURATION_MILLISECONDS", "DURATION_IN", "DURATION_OUT", "SRC_TO_DST_IAT_MIN", "SRC_TO_DST_IAT_MAX",
               "SRC_TO_DST_IAT_AVG", "SRC_TO_DST_IAT_STDDEV", "DST_TO_SRC_IAT_MIN", "DST_TO_SRC_IAT_MAX", "DST_TO_SRC_IAT_AVG", "DST_TO_SRC_IAT_STDDEV"],
    "rate": ["SRC_TO_DST_SECOND_BYTES", "DST_TO_SRC_SECOND_BYTES", "SRC_TO_DST_AVG_THROUGHPUT", "DST_TO_SRC_AVG_THROUGHPUT"],
    "retrans": ["RETRANSMITTED_IN_BYTES", "RETRANSMITTED_IN_PKTS", "RETRANSMITTED_OUT_BYTES", "RETRANSMITTED_OUT_PKTS"],
}

_cache = {}


def load(ds, scheme, part):
    k = (ds, scheme, part)
    if k not in _cache:
        if part == "test":
            assert os.environ.get("NIDS_ALLOW_TEST") == "1", "TEST pool is locked (set only by confirmation runs)"
        df = pd.read_parquet(os.path.join(PROC, f"{ds}_{scheme}_{part}.parquet"))
        fc = feature_cols(df)  # D12: rate fields are NaN/inf for zero-duration flows (UNSW, BOT only) -> 0
        df[fc] = df[fc].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        _cache[k] = df
    return _cache[k]


def feature_cols(df):
    return [c for c in df.columns if c not in META]


def subsample(df, n, seed):
    if len(df) <= n:
        return df
    return df.sample(n=n, random_state=seed)


# ---------------------------------------------------------------- feature treatments
def env_discriminability(benign_by_env, cols, max_n=20000, seed=0):
    """Gini |2*AUC-1| of each single feature for separating benign traffic of every pair of environments;
    returns mean over pairs. High = feature identifies the network ("environment signature")."""
    rng = np.random.default_rng(seed)
    envs = list(benign_by_env)
    out = {}
    for c in cols:
        g = []
        for i in range(len(envs)):
            for j in range(i + 1, len(envs)):
                a = benign_by_env[envs[i]][c].to_numpy(); b = benign_by_env[envs[j]][c].to_numpy()
                if len(a) > max_n: a = rng.choice(a, max_n, replace=False)
                if len(b) > max_n: b = rng.choice(b, max_n, replace=False)
                if len(a) < 20 or len(b) < 20:
                    continue
                y = np.r_[np.zeros(len(a)), np.ones(len(b))]
                x = np.r_[a, b]
                if np.all(x == x[0]):
                    g.append(0.0); continue
                g.append(abs(2 * roc_auc_score(y, x) - 1))
        out[c] = float(np.mean(g)) if g else 0.0
    return out


def pen_transform(X, ref):
    """Per-environment empirical-CDF transform: each column of X mapped to its mid-rank quantile within ref
    (unlabeled flows of the SAME environment)."""
    Z = np.empty(X.shape, dtype=np.float32)
    for j in range(X.shape[1]):
        r = np.sort(ref[:, j])
        lo = np.searchsorted(r, X[:, j], side="left"); hi = np.searchsorted(r, X[:, j], side="right")
        Z[:, j] = (lo + hi) / (2.0 * len(r))
    return Z


# ---------------------------------------------------------------- models
def make_model(method, cfg, seed):
    base = method.split("+")[-1]
    if base == "lr":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler, FunctionTransformer
        return make_pipeline(FunctionTransformer(_slog), StandardScaler(),
                             LogisticRegression(C=cfg.get("C", 1.0), max_iter=300, random_state=seed))
    if base == "rf":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=cfg.get("n_estimators", 200), max_depth=cfg.get("max_depth"),
                                      min_samples_leaf=cfg.get("min_samples_leaf", 1), max_features=cfg.get("max_features", "sqrt"),
                                      n_jobs=N_THREADS, random_state=seed)
    if base == "lgbm":
        import lightgbm as lgb
        return lgb.LGBMClassifier(n_estimators=cfg.get("n_estimators", 300), learning_rate=cfg.get("learning_rate", 0.05),
                                  num_leaves=cfg.get("num_leaves", 63), min_child_samples=cfg.get("min_child_samples", 20),
                                  subsample=cfg.get("subsample", 0.8), subsample_freq=1, colsample_bytree=cfg.get("colsample_bytree", 0.8),
                                  reg_lambda=cfg.get("reg_lambda", 0.0), n_jobs=N_THREADS, random_state=seed, verbose=-1)
    if base == "xgb":
        import xgboost as xgb
        return xgb.XGBClassifier(n_estimators=cfg.get("n_estimators", 300), learning_rate=cfg.get("learning_rate", 0.1),
                                 max_depth=cfg.get("max_depth", 6), subsample=cfg.get("subsample", 0.8),
                                 colsample_bytree=cfg.get("colsample_bytree", 0.8), reg_lambda=cfg.get("reg_lambda", 1.0),
                                 tree_method="hist", n_jobs=N_THREADS, random_state=seed, verbosity=0)
    if base in ("mlp", "dann", "coral"):
        from mlp import TorchMLP
        return TorchMLP(kind=base, seed=seed, **cfg)
    raise ValueError(method)


def _slog(X):
    return np.sign(X) * np.log1p(np.abs(X))


SEARCH = {  # identical budget (N_CONFIGS draws) for every method
    "lr": {"C": [0.001, 0.003, 0.01, 0.03, 0.1, 1.0, 10.0, 100.0]},
    "rf": {"n_estimators": [100, 200, 300], "max_depth": [None, 12, 20, 30], "min_samples_leaf": [1, 2, 5, 10], "max_features": ["sqrt", 0.3, 0.5]},
    "lgbm": {"n_estimators": [200, 400, 800], "learning_rate": [0.02, 0.05, 0.1], "num_leaves": [15, 31, 63, 127],
             "min_child_samples": [10, 20, 50, 100], "colsample_bytree": [0.5, 0.8, 1.0], "reg_lambda": [0.0, 1.0, 10.0]},
    "xgb": {"n_estimators": [200, 400, 800], "learning_rate": [0.03, 0.1, 0.3], "max_depth": [4, 6, 8, 10],
            "subsample": [0.7, 0.9, 1.0], "colsample_bytree": [0.5, 0.8, 1.0], "reg_lambda": [0.1, 1.0, 10.0]},
    "mlp": {"hidden": [128, 256, 512], "depth": [2, 3], "dropout": [0.0, 0.1, 0.3], "lr": [3e-4, 1e-3, 3e-3], "epochs": [8, 15]},
    "dann": {"hidden": [128, 256, 512], "depth": [2, 3], "dropout": [0.0, 0.1, 0.3], "lr": [3e-4, 1e-3, 3e-3], "epochs": [8, 15], "lam": [0.1, 0.3, 1.0]},
    "coral": {"hidden": [128, 256, 512], "depth": [2, 3], "dropout": [0.0, 0.1, 0.3], "lr": [3e-4, 1e-3, 3e-3], "epochs": [8, 15], "lam": [0.1, 1.0, 10.0]},
}
N_CONFIGS = 8


def sample_configs(base, seed=12345):
    rng = np.random.default_rng(seed)
    sp = SEARCH[base]; out = []
    if base == "lr":
        return [{"C": c} for c in sp["C"]]
    seen = set()
    while len(out) < N_CONFIGS:
        c = {k: v[rng.integers(len(v))] for k, v in sp.items()}
        c = {k: (v.item() if hasattr(v, "item") else v) for k, v in c.items()}
        key = json.dumps(c, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key); out.append(c)
    return out


# ---------------------------------------------------------------- metrics
def best_threshold(y, p):
    qs = np.unique(np.quantile(p, np.linspace(0.001, 0.999, 400)))
    cand = np.unique(np.r_[qs, 0.5])
    best, bt = -1, 0.5
    for t in cand:
        f = f1_score(y, p >= t, average="macro", zero_division=0)
        if f > best:
            best, bt = f, t
    return float(bt), float(best)


def metrics(y, p, thr):
    yhat = (p >= thr).astype(int)
    out = {"macro_f1": f1_score(y, yhat, average="macro", zero_division=0),
           "f1_attack": f1_score(y, yhat, zero_division=0),
           "bal_acc": balanced_accuracy_score(y, yhat) if len(np.unique(y)) > 1 else float("nan"),
           "tpr": float(yhat[y == 1].mean()) if (y == 1).any() else float("nan"),
           "fpr": float(yhat[y == 0].mean()) if (y == 0).any() else float("nan"),
           "auroc": roc_auc_score(y, p) if len(np.unique(y)) > 1 else float("nan"),
           "prauc": average_precision_score(y, p) if len(np.unique(y)) > 1 else float("nan"),
           "n_eval": int(len(y)), "attack_rate_eval": float(y.mean()), "threshold": float(thr)}
    return {k: float(v) if isinstance(v, (np.floating, float)) else v for k, v in out.items()}


def model_size_bytes(m):
    try:
        b = io.BytesIO(); pickle.dump(m, b); return b.tell()
    except Exception:
        return -1
