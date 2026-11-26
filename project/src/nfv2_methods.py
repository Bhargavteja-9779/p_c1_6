"""Topic 3 candidate methods (designed in --eval val mode only, D40). Inputs are min-max scaled to [0,1] on benign train (nfv2_prep).
Method names: ck<k>_<flags>, flags = combination of
  L  : log-rescale every column x -> log1p(c x)/log1p(c), c = 1e4 (undoes min-max squashing of heavy-tailed counts)
  C  : categorical columns (protocol, L7 protocol, dst port, TCP flags, ICMP/DNS/FTP codes) re-encoded as one-hot of their
       benign-train top-32 values (+ 'other'), weight w per column (exact match matters, magnitude does not)
  P  : drop L4_SRC_PORT (ephemeral, random per flow)
"""
import numpy as np
FEATS = []
CAT = ["PROTOCOL", "L7_PROTO", "L4_DST_PORT", "TCP_FLAGS", "CLIENT_TCP_FLAGS", "SERVER_TCP_FLAGS", "ICMP_TYPE", "ICMP_IPV4_TYPE",
       "DNS_QUERY_TYPE", "FTP_COMMAND_RET_CODE"]


class Rep:
    def __init__(self, flags, Xtr, w=1.0, c=1e4):
        self.flags, self.w, self.c = flags, w, c
        self.keep = [i for i, f in enumerate(FEATS) if not ("P" in flags and f == "L4_SRC_PORT")]
        self.cat = [i for i in self.keep if FEATS[i] in CAT] if "C" in flags else []
        self.num = [i for i in self.keep if i not in self.cat]
        self.vocab = {i: np.unique(Xtr[:, i], return_counts=True) for i in self.cat}
        self.vocab = {i: v[np.argsort(-n)][:32] for i, (v, n) in self.vocab.items()}

    def __call__(self, X):
        N = X[:, self.num]
        if "L" in self.flags: N = np.log1p(self.c * N) / np.log1p(self.c)
        parts = [N]
        for i in self.cat:
            v = self.vocab[i]; oh = (X[:, i][:, None] == v[None, :]).astype(np.float64)
            oh = np.hstack([oh, (oh.sum(1) == 0)[:, None]]) * (self.w / np.sqrt(2))  # mismatch distance = w
            parts.append(oh)
        return np.hstack(parts)


def make(method, Xtr, seed, ref):
    import nfv2_bench
    head, flags = (method.split("_") + [""])[:2]
    if head.startswith("ck"):
        k = int(head[2:] or 1); w = 1.0
        rep = Rep(flags, Xtr, w=w); R = nfv2_bench.ref_subsample(rep(Xtr), ref, seed)
        return lambda Q: nfv2_bench.knn_scores(R, rep(Q), k)
    raise ValueError(method)


def group_mean(Z, g):
    """Mean of rows of Z within each group id g (closed-form one-hop mean aggregation)."""
    n_g = g.max() + 1; cnt = np.bincount(g, minlength=n_g).astype(np.float64)
    S = np.zeros((n_g, Z.shape[1]))
    np.add.at(S, g, Z)
    return S[g] / cnt[g][:, None]


def context(X, sip, dip, c=1e4, parts="sd"):
    """H8 representation: log-rescaled flow features + mean of log-rescaled features over flows with the same source IP (s) and
    the same destination IP (d), computed within the given partition."""
    L = np.log1p(c * X) / np.log1p(c); out = [] if "o" in parts else [L]  # 'o' = context only (ablation)
    if "s" in parts: out.append(group_mean(L, sip))
    if "d" in parts: out.append(group_mean(L, dip))
    return np.hstack(out)
