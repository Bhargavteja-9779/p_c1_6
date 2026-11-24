"""Torch MLP baselines: plain MLP, DANN (gradient reversal over network ids incl. unlabeled target),
CORAL (hidden-feature covariance alignment between pooled source and unlabeled target).
Per-epoch atomic checkpoints (model+optimizer+RNG) so a killed job resumes."""
import os, numpy as np, torch, torch.nn as nn

torch.set_num_threads(max(1, os.cpu_count() or 1))


class _GRL(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, lam):
        ctx.lam = lam; return x.view_as(x)

    @staticmethod
    def backward(ctx, g):
        return -ctx.lam * g, None


def _coral(a, b):
    d = a.shape[1]
    ca = torch.cov(a.T); cb = torch.cov(b.T)
    return ((ca - cb) ** 2).sum() / (4 * d * d)


class TorchMLP:
    def __init__(self, kind="mlp", seed=0, hidden=256, depth=2, dropout=0.1, lr=1e-3, epochs=10, lam=0.1, batch=1024, **_):
        self.kind, self.seed, self.h, self.depth, self.do = kind, seed, hidden, depth, dropout
        self.lr, self.epochs, self.lam, self.batch = lr, epochs, lam, batch

    def _prep(self, X):
        X = np.sign(X) * np.log1p(np.abs(X))
        return ((X - self.mu) / self.sd).astype(np.float32)

    def fit(self, X, y, domains=None, X_target=None, ckpt=None):
        torch.manual_seed(self.seed); rng = np.random.default_rng(self.seed)
        Xl = np.sign(X) * np.log1p(np.abs(X)); self.mu = Xl.mean(0); self.sd = Xl.std(0) + 1e-6
        Xs = torch.tensor(self._prep(X)); ys = torch.tensor(y, dtype=torch.float32)
        d_in = Xs.shape[1]; layers = []; w = d_in
        for _ in range(self.depth):
            layers += [nn.Linear(w, self.h), nn.ReLU(), nn.Dropout(self.do)]; w = self.h
        self.feat = nn.Sequential(*layers); self.head = nn.Linear(w, 1)
        params = list(self.feat.parameters()) + list(self.head.parameters())
        use_t = self.kind in ("dann", "coral") and X_target is not None
        if use_t:
            Xt = torch.tensor(self._prep(X_target))
            dom = np.asarray(domains); uniq = sorted(set(dom.tolist())); self.dmap = {u: i for i, u in enumerate(uniq)}
            ds = torch.tensor([self.dmap[v] for v in dom]); n_dom = len(uniq) + 1
            if self.kind == "dann":
                self.dhead = nn.Sequential(nn.Linear(w, 64), nn.ReLU(), nn.Linear(64, n_dom)); params += list(self.dhead.parameters())
        opt = torch.optim.Adam(params, lr=self.lr); start = 0
        if ckpt and os.path.exists(ckpt):
            st = torch.load(ckpt, weights_only=False)
            self.feat.load_state_dict(st["feat"]); self.head.load_state_dict(st["head"]); opt.load_state_dict(st["opt"])
            if self.kind == "dann" and use_t: self.dhead.load_state_dict(st["dhead"])
            torch.set_rng_state(st["torch_rng"]); rng.bit_generator.state = st["np_rng"]; start = st["epoch"] + 1
        bce = nn.BCEWithLogitsLoss(); ce = nn.CrossEntropyLoss(); n = len(Xs)
        for ep in range(start, self.epochs):
            self.feat.train(); perm = rng.permutation(n)
            for i in range(0, n, self.batch):
                b = perm[i:i + self.batch]
                hs = self.feat(Xs[b]); loss = bce(self.head(hs).squeeze(1), ys[b])
                if use_t:
                    tb = rng.integers(0, len(Xt), size=len(b)); ht = self.feat(Xt[tb])
                    if self.kind == "coral":
                        loss = loss + self.lam * _coral(hs, ht)
                    else:
                        p = min(1.0, (ep * n + i) / (self.epochs * n)); lam = self.lam * (2 / (1 + np.exp(-10 * p)) - 1)
                        z = torch.cat([hs, ht]); dl = torch.cat([ds[b], torch.full((len(b),), n_dom - 1)])
                        loss = loss + ce(self.dhead(_GRL.apply(z, lam)), dl)
                opt.zero_grad(); loss.backward(); opt.step()
            if ckpt:
                st = {"feat": self.feat.state_dict(), "head": self.head.state_dict(), "opt": opt.state_dict(), "epoch": ep,
                      "torch_rng": torch.get_rng_state(), "np_rng": rng.bit_generator.state}
                if self.kind == "dann" and use_t: st["dhead"] = self.dhead.state_dict()
                torch.save(st, ckpt + ".tmp"); os.replace(ckpt + ".tmp", ckpt)
        return self

    def predict_proba(self, X):
        self.feat.eval()
        with torch.no_grad():
            out = []
            Xp = torch.tensor(self._prep(X))
            for i in range(0, len(Xp), 65536):
                out.append(torch.sigmoid(self.head(self.feat(Xp[i:i + 65536]))).squeeze(1).numpy())
        p = np.concatenate(out); return np.c_[1 - p, p]
