"""Execute one job spec (JSON) and atomically write results/<job_id>.json (+ append raw_results.csv).

kind = "tune": evaluate N_CONFIGS configs of a base method (seed 0), select by pooled-SOURCE-val macro-F1.
kind = "run" : train with the selected config and evaluate.
Idempotent: if the result file exists, exit immediately.
"""
import os, sys, json, time, argparse, hashlib
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nids
from nids import load, feature_cols, subsample, make_model, metrics, best_threshold

ROOT = nids.ROOT


def _ckpt_path(job_id, cfg_i=0):
    d = os.path.join(ROOT, "checkpoints"); os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{job_id}_{cfg_i}.pt")


def assemble(spec, seed):
    """Return dict with train / thr(val) / eval sets as numpy, plus domain ids and per-env refs."""
    proto, target = spec["protocol"], spec["target"]
    n_src = spec.get("n_per_source", 100_000)
    ev = spec.get("eval_split", "val")
    if proto == "lodo":
        sources = [d for d in spec.get("sources", nids.DATASETS) if d != target]
        tr = [subsample(load(s, "random", "train"), n_src, seed).assign(_env=s) for s in sources]
        va = [subsample(load(s, "random", "val"), spec.get("n_val_per_source", 60_000), 0).assign(_env=s) for s in sources]
        te = load(target, "random", ev).assign(_env=target)
    elif proto in ("id_random", "id_chrono"):
        sch = proto.split("_")[1]
        tr = [subsample(load(target, sch, "train"), n_src, seed).assign(_env=target)]
        v = load(target, sch, "val")
        if ev == "val":   # exploration: first half (random) of val for threshold, second half for evaluation
            idx = np.random.default_rng(0).permutation(len(v)); h = len(v) // 2
            va = [v.iloc[idx[:h]].assign(_env=target)]; te = v.iloc[idx[h:]].assign(_env=target)
        else:
            va = [v.assign(_env=target)]; te = load(target, sch, "test").assign(_env=target)
    else:
        raise ValueError(proto)
    tr = pd.concat(tr, ignore_index=True); va = pd.concat(va, ignore_index=True)
    return tr, va, te


def treat(spec, cfg, tr, va, te, cols):
    """Apply feature treatments named in the method prefix (esf / pen / drop_<group>)."""
    parts = spec["method"].split("+")[:-1]
    info = {}
    use = list(cols)
    for p in parts:
        if p.startswith("drop_"):
            g = p[5:]; use = [c for c in use if c not in nids.GROUPS[g]]
    if "esf" in parts:
        ben = {e: d[d.Label == 0] for e, d in tr.groupby("_env")}
        sc = nids.env_discriminability(ben, use)
        tau = cfg.get("tau", spec.get("tau", 0.8))
        dropped = [c for c in use if sc[c] > tau]
        use = [c for c in use if sc[c] <= tau]
        info["esf_scores"] = sc; info["esf_dropped"] = dropped; info["tau"] = tau
    Xtr, Xva, Xte = (d[use].to_numpy(np.float32) for d in (tr, va, te))
    if "pen" in parts:
        refs = {e: tr.loc[tr._env == e, use].to_numpy(np.float32) for e in tr._env.unique()}
        Xtr = np.vstack([nids.pen_transform(tr.loc[tr._env == e, use].to_numpy(np.float32), refs[e]) for e in tr._env.unique()])
        # keep row order consistent with labels
        order = np.concatenate([np.flatnonzero(tr._env.to_numpy() == e) for e in tr._env.unique()])
        ytr_order = order
        Xva = np.empty((len(va), len(use)), np.float32)
        for e in va._env.unique():
            m = va._env.to_numpy() == e; Xva[m] = nids.pen_transform(va.loc[m, use].to_numpy(np.float32), refs[e])
        Xte = nids.pen_transform(te[use].to_numpy(np.float32), te[use].to_numpy(np.float32))  # target: its own unlabeled flows
        info["pen_order"] = True
        return Xtr, Xva, Xte, use, info, ytr_order
    return Xtr, Xva, Xte, use, info, None


def fit_eval(spec, cfg, seed, ckpt=None):
    tr, va, te = assemble(spec, seed)
    cols = feature_cols(load(spec["target"], "random", "train") if spec["protocol"] == "lodo" else tr.drop(columns="_env"))
    cols = [c for c in cols if c != "_env"]
    Xtr, Xva, Xte, use, info, order = treat(spec, cfg, tr, va, te, cols)
    ytr = tr.Label.to_numpy() if order is None else tr.Label.to_numpy()[order]
    dom = tr._env.to_numpy() if order is None else tr._env.to_numpy()[order]
    yva, yte = va.Label.to_numpy(), te.Label.to_numpy()
    base = spec["method"].split("+")[-1]
    m = make_model(spec["method"], cfg, seed)
    t0 = time.time()
    if base in ("mlp", "dann", "coral"):
        m.fit(Xtr, ytr, domains=dom, X_target=Xte if base != "mlp" else None, ckpt=ckpt)
    else:
        m.fit(Xtr, ytr)
    fit_s = time.time() - t0
    pva = m.predict_proba(Xva)[:, 1]
    thr, f_va = best_threshold(yva, pva)
    t1 = time.time(); pte = m.predict_proba(Xte)[:, 1]; pred_s = time.time() - t1
    res = metrics(yte, pte, thr)
    res.update({"src_val_macro_f1": f_va, "fit_s": fit_s, "pred_ms_per_1k": 1e6 * pred_s / max(1, len(Xte)),
                "n_features": len(use), "n_train": int(len(Xtr)), "model_bytes": nids.model_size_bytes(m) if base not in ("mlp", "dann", "coral") else -1})
    # per-attack-family recall on eval set (diagnostics)
    fam = te.Attack.to_numpy(); yhat = pte >= thr
    res["recall_by_family"] = {a: float(yhat[fam == a].mean()) for a in np.unique(fam) if a != "Benign"}
    # in-distribution check of the same model on source val (threshold-tuned) -> how much is lost
    res["src_val_auroc"] = float(nids.roc_auc_score(yva, pva)) if len(np.unique(yva)) > 1 else float("nan")
    if "esf_dropped" in info:
        res["esf_dropped"] = info["esf_dropped"]; res["esf_scores"] = info["esf_scores"]; res["tau"] = info["tau"]
    if spec.get("save_scores"):
        d = os.path.join(ROOT, "results", "scores"); os.makedirs(d, exist_ok=True)
        np.savez_compressed(os.path.join(d, spec["job_id"] + ".npz"), p=pte.astype(np.float32), y=yte.astype(np.int8))
    return res


def main(spec):
    out_dir = os.path.join(ROOT, spec.get("results_dir", "results"))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, spec["job_id"] + ".json")
    if os.path.exists(out):
        print("exists", out); return
    if spec.get("eval_split") == "test":
        os.environ["NIDS_ALLOW_TEST"] = "1"
    base = spec["method"].split("+")[-1]
    t0 = time.time()
    if spec["kind"] == "tune":
        trials = []
        cfgs = nids.sample_configs(base)[: spec.get("n_configs", nids.N_CONFIGS)]
        for i, c in enumerate(cfgs):
            r = fit_eval(spec, c, 0, ckpt=_ckpt_path(spec["job_id"], i) if base in ("mlp", "dann", "coral") else None)
            trials.append({"cfg": c, "src_val_macro_f1": r["src_val_macro_f1"], "fit_s": r["fit_s"]})
            print(f"  cfg{i} srcval={r['src_val_macro_f1']:.4f} fit={r['fit_s']:.1f}s", flush=True)
        best = max(trials, key=lambda t: t["src_val_macro_f1"])
        res = {"best_cfg": best["cfg"], "trials": trials}   # NOTE: target metrics deliberately NOT stored for tuning
    else:
        cfg = dict(spec.get("cfg") or {})
        if spec.get("cfg_from"):
            p = os.path.join(ROOT, spec.get("results_dir", "results"), spec["cfg_from"] + ".json")
            cfg = {**json.load(open(p))["best_cfg"], **cfg}
        res = fit_eval(spec, cfg, spec["seed"], ckpt=_ckpt_path(spec["job_id"]) if base in ("mlp", "dann", "coral") else None)
        res["cfg"] = cfg
    res.update({"spec": spec, "wall_s": time.time() - t0, "finished": time.strftime("%Y-%m-%dT%H:%M:%S")})
    json.dump(res, open(out + ".tmp", "w"), indent=1, default=str); os.replace(out + ".tmp", out)
    if spec["kind"] == "run":
        row = {k: spec.get(k) for k in ("job_id", "exp", "protocol", "target", "method", "seed", "eval_split")}
        row.update({k: res[k] for k in ("macro_f1", "f1_attack", "auroc", "prauc", "tpr", "fpr", "bal_acc", "threshold",
                                          "src_val_macro_f1", "n_eval", "attack_rate_eval", "fit_s", "pred_ms_per_1k", "n_features", "n_train")})
        csv = os.path.join(out_dir, "raw_results.csv")
        pd.DataFrame([row]).to_csv(csv, mode="a", header=not os.path.exists(csv), index=False)
    for f in os.listdir(os.path.join(ROOT, "checkpoints")) if os.path.isdir(os.path.join(ROOT, "checkpoints")) else []:
        if f.startswith(spec["job_id"] + "_"):
            os.remove(os.path.join(ROOT, "checkpoints", f))
    print("done", spec["job_id"], {k: res.get(k) for k in ("macro_f1", "auroc", "best_cfg")}, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--job", required=True)
    main(json.loads(ap.parse_args().job))
