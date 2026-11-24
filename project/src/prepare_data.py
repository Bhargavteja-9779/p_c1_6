"""Prepare chronological train/val/test pools for the four NetFlow-V3 datasets.

Idempotent: skips datasets whose pools already exist (unless --force).
Outputs data/proc/<DS>_{train,val,test}.parquet and data/proc/prep_report.json
"""
import os, sys, json, argparse
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, PROC = os.path.join(ROOT, "data/raw"), os.path.join(ROOT, "data/proc")
DATASETS = {"UNSW": "NF-UNSW-NB15-v3", "BOT": "NF-BoT-IoT-v3", "TON": "NF-ToN-IoT-v3", "CIC": "NF-CICIDS2018-v3"}
EXPECTED_ROWS = {"UNSW": 2365424, "BOT": 16933808, "TON": 27520260, "CIC": 20115529}  # mirror README; re-checked here
DROP = ["IPV4_SRC_ADDR", "IPV4_DST_ADDR", "L4_SRC_PORT", "DNS_QUERY_ID", "FLOW_END_MILLISECONDS"]
POOL = {"train": 300_000, "val": 60_000, "test": 100_000}
FRAC = (0.6, 0.2, 0.2)
DATA_SEED = 0


def prep(key, force=False):
    outs = {(sch, p): os.path.join(PROC, f"{key}_{sch}_{p}.parquet") for sch in ("chrono", "random") for p in POOL}
    if all(os.path.exists(o) for o in outs.values()) and not force:
        return json.load(open(os.path.join(PROC, f"{key}_report.json")))
    pf = pq.ParquetFile(os.path.join(RAW, DATASETS[key] + ".parquet"))
    n = pf.metadata.num_rows
    t = pf.read(columns=["FLOW_START_MILLISECONDS"]).column(0).to_numpy()
    order = np.argsort(t, kind="stable")          # chronological rank
    rank = np.empty(n, dtype=np.int64); rank[order] = np.arange(n)
    c1, c2 = int(n * FRAC[0]), int(n * (FRAC[0] + FRAC[1]))
    part_c = np.where(rank < c1, 0, np.where(rank < c2, 1, 2))
    rng = np.random.default_rng(DATA_SEED)
    u = rng.random(n)                     # random scheme: i.i.d. assignment over the whole time span
    part_r = np.where(u < FRAC[0], 0, np.where(u < FRAC[0] + FRAC[1], 1, 2))
    keep_c = np.zeros(n, dtype=np.int8) - 1; keep_r = keep_c.copy()
    for keep, part in ((keep_c, part_c), (keep_r, part_r)):
        for pi, p in enumerate(POOL):
            idx = np.flatnonzero(part == pi)
            sel = rng.choice(idx, size=min(POOL[p], idx.size), replace=False)
            keep[sel] = pi
    cols = [c for c in pf.schema_arrow.names if c not in DROP]
    frames, off = [], 0
    for rg in range(pf.num_row_groups):
        tb = pf.read_row_group(rg, columns=cols).to_pandas()
        kc, kr = keep_c[off:off + len(tb)], keep_r[off:off + len(tb)]; off += len(tb)
        m = (kc >= 0) | (kr >= 0)
        if m.any():
            sub = tb[m].copy(); sub["_pc"] = kc[m]; sub["_pr"] = kr[m]; frames.append(sub)
    df = pd.concat(frames, ignore_index=True)
    assert off == n
    for c in df.columns:
        if c not in ("Attack", "_pc", "_pr", "Label", "FLOW_START_MILLISECONDS"):
            df[c] = df[c].astype("float32")
    rep = {"dataset": key, "file": DATASETS[key], "rows_total": n, "rows_expected": EXPECTED_ROWS[key],
           "rows_match": n == EXPECTED_ROWS[key], "attack_rate_total": None,
           "time_cut_ms": [int(t[order[c1]]), int(t[order[c2]])], "partitions": {}}
    lab = pf.read(columns=["Label"]).column(0).to_numpy()
    rep["attack_rate_total"] = float(lab.mean())
    for sch, col, part in (("chrono", "_pc", part_c), ("random", "_pr", part_r)):
      for pi, p in enumerate(POOL):
        d = df[df[col] == pi].drop(columns=["_pc", "_pr"]).sort_values("FLOW_START_MILLISECONDS").reset_index(drop=True)
        o = outs[(sch, p)]; d.to_parquet(o + ".tmp", index=False); os.replace(o + ".tmp", o)
        rep["partitions"][f"{sch}_{p}"] = {"n": len(d), "attack_rate": float(d.Label.mean()),
                                "attack_classes": d.Attack.value_counts().to_dict(),
                                "n_in_partition_total": int((part == pi).sum()),
                                "attack_rate_partition_total": float(lab[part == pi].mean())}
    json.dump(rep, open(os.path.join(PROC, f"{key}_report.json"), "w"), indent=1)
    return rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--force", action="store_true")
    ap.add_argument("datasets", nargs="*", default=list(DATASETS))
    a = ap.parse_args(); os.makedirs(PROC, exist_ok=True)
    allrep = {}
    for k in a.datasets:
        r = prep(k, a.force); allrep[k] = r
        print(k, r["rows_total"], r["rows_match"], {p: (v["n"], round(v["attack_rate"], 4)) for p, v in r["partitions"].items()}, flush=True)
    json.dump(allrep, open(os.path.join(PROC, "prep_report.json"), "w"), indent=1)
