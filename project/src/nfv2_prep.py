"""Topic 3: NF-v2 one-class splits following GDAE §3.2.2 (D39). Writes data/nfv2/<name>_s<seed>.npz with
Xtr (benign train), Xva/yva/ava (val features, label, attack name), Xte/yte/ate, feature names. Usage: python src/nfv2_prep.py NAME SEED"""
import glob, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROP = ["IPV4_SRC_ADDR", "IPV4_DST_ADDR"]


def load(name):
    pq = os.path.join(ROOT, "data", "nfv2", f"{name}.parquet")
    if not os.path.exists(pq):
        f = glob.glob(os.path.join(ROOT, "data", "nfv2", name, "**", f"{name}.csv"), recursive=True)[0]
        if "CIC" in name:  # 10 % stratified sample by attack type, data seed 0 (GDAE §3.2.1); chunked (18.9 M rows do not fit in RAM)
            parts = [c.groupby("Attack", group_keys=False).sample(frac=0.10, random_state=0)
                     for c in pd.read_csv(f, chunksize=1_000_000, low_memory=False)]
            df = pd.concat(parts, ignore_index=True)
        else:
            df = pd.read_csv(f, low_memory=False)
        df.to_parquet(pq)
    return pd.read_parquet(pq)


def make(name, seed):
    out = os.path.join(ROOT, "data", "nfv2", f"{name}_s{seed}.npz")
    if os.path.exists(out): return out
    df = load(name); y = df["Label"].astype(int).values; att = np.asarray(df["Attack"].astype(str).values, dtype=str)
    X = df.drop(columns=DROP + ["Label", "Attack"]).apply(pd.to_numeric, errors="coerce").astype(np.float64)
    feats = list(X.columns); X = np.nan_to_num(X.values, nan=0.0, posinf=0.0, neginf=0.0)
    rng = np.random.default_rng(seed); part = np.empty(len(y), int)
    for a in np.unique(att):  # stratified 8:1:1 by attack type
        i = np.flatnonzero(att == a); rng.shuffle(i); n = len(i); a1, a2 = int(round(0.8 * n)), int(round(0.9 * n))
        part[i[:a1]] = 0; part[i[a1:a2]] = 1; part[i[a2:]] = 2
    tr = (part == 0) & (y == 0)
    lo, hi = X[tr].min(0), X[tr].max(0); rg = np.where(hi > lo, hi - lo, 1.0)
    Z = np.clip((X - lo) / rg, 0, 1).astype(np.float32)
    np.savez_compressed(out, Xtr=Z[tr], Xva=Z[part == 1], yva=y[part == 1], ava=att[part == 1], Xte=Z[part == 2], yte=y[part == 2],
                        ate=att[part == 2], feats=np.array(feats))
    return out


if __name__ == "__main__":
    print(make(sys.argv[1], int(sys.argv[2])))
