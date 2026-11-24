"""plan_v2 / E7: interventional attribution of cross-network (LODO) loss to feature groups.

A model is trained exactly as in E1 (pooled sources, tuned config, threshold on pooled SOURCE val). It is then
evaluated on the TARGET val pool and on intervened copies of it. For a feature group g and a class c (benign/attack):

  SRC  : for every target flow of class c, the columns of g are replaced by the g-columns of a random SOURCE flow of
         class c (one donor row per flow, so the joint distribution *within* g is kept).
  CTRL : identical, but the donor is a random TARGET flow of class c (within-target shuffle). This breaks the same
         cross-group dependence as SRC without changing g's distribution -> the control for the intervention itself.

  effect(g, c) = metric(SRC) - metric(CTRL)     (> 0 for macro-F1: shift in g/c causes that much of the loss)

Group "all" (every feature) with c=benign is the full benign swap: it estimates how much of the LODO loss is due to
benign-side shift as a whole; c=attack likewise for attack-side shift. Donors come from the pooled source VAL pools
(the same rows used for the threshold) and target VAL; the target TEST pool is never read (diagnostic, D9).
Class labels of the target val pool are used only to define the intervention (diagnostic analysis, not a method).
Each intervention is repeated with R independent donor draws and averaged.
"""
import time
import numpy as np
import nids

CLASSES = {"benign": 0, "attack": 1}


def groups_for(cols):
    g = {k: [c for c in v if c in cols] for k, v in nids.GROUPS.items()}
    used = {c for v in g.values() for c in v}
    g["rest"] = [c for c in cols if c not in used]       # volume / timing / rate / size features
    # finer split of "rest" (added before any full E7 run; decision D17) -- reported descriptively, not in H2b
    rest = g["rest"]
    g["rest_volume"] = [c for c in rest if c in ("IN_BYTES", "IN_PKTS", "OUT_BYTES", "OUT_PKTS") or c.startswith("RETRANSMITTED_")]
    g["rest_timing"] = [c for c in rest if "DURATION" in c or "_IAT_" in c]
    g["rest_rates"] = [c for c in rest if c.endswith("_SECOND_BYTES") or c.endswith("_AVG_THROUGHPUT")]
    g["rest_pktsize"] = [c for c in rest if c.endswith("FLOW_PKT") or "IP_PKT_LEN" in c or c.startswith("NUM_PKTS_")]
    g["all"] = list(cols)
    return {k: v for k, v in g.items() if v}


def intervene(Xte, yte, Xdon, ydon, idx, cls, rng):
    """Return a copy of Xte where rows of class cls get columns idx from random donor rows of class cls."""
    X = Xte.copy()
    rows = np.flatnonzero(yte == cls); pool = np.flatnonzero(ydon == cls)
    if len(rows) == 0 or len(pool) == 0:
        return None
    d = pool[rng.integers(len(pool), size=len(rows))]
    X[np.ix_(rows, idx)] = Xdon[np.ix_(d, idx)]
    return X


def run(m, thr, Xva, yva, Xte, yte, cols, reps=3, seed=0):
    G = groups_for(cols); ci = {c: i for i, c in enumerate(cols)}
    def ev(X):
        p = m.predict_proba(X)[:, 1]; r = nids.metrics(yte, p, thr)
        return {k: r[k] for k in ("macro_f1", "auroc", "tpr", "fpr", "f1_attack")}
    out = {"groups": G, "base": ev(Xte), "effects": {}}
    t0 = time.time()
    for g, gc in G.items():
        idx = np.array([ci[c] for c in gc])
        for cname, cls in CLASSES.items():
            acc = {"src": [], "ctrl": []}
            for r in range(reps):
                rng = np.random.default_rng(1000 * seed + r)
                Xs = intervene(Xte, yte, Xva, yva, idx, cls, rng)
                Xc = intervene(Xte, yte, Xte, yte, idx, cls, rng)
                if Xs is None or Xc is None:
                    break
                acc["src"].append(ev(Xs)); acc["ctrl"].append(ev(Xc))
            if not acc["src"]:
                out["effects"][f"{g}|{cname}"] = None; continue
            mean = lambda L: {k: float(np.mean([d[k] for d in L])) for k in L[0]}
            s, c = mean(acc["src"]), mean(acc["ctrl"])
            out["effects"][f"{g}|{cname}"] = {"src": s, "ctrl": c, "effect": {k: s[k] - c[k] for k in s},
                                              "effect_sd_reps": {k: float(np.std([a[k] - b[k] for a, b in zip(acc["src"], acc["ctrl"])]))
                                                                 for k in s}}
    out["transplant_s"] = time.time() - t0
    return out
