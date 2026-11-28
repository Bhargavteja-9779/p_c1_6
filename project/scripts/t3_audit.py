"""G11 integrity audit (topic 3): every 0.xxx / 0.xxxx number and every percentage in paper/manuscript.md must match a value
derivable from results_t3 (5-seed means/stds of our runs, per-attack rates), results/t3_stats.json, or literature/gdae_table5.csv
(rounded to the precision written). Exit code 1 and a list on any unmatched number. Whitelist: numbers that are protocol constants."""
import glob, json, os, re, sys
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
vals = set()
def add(x):
    for p in (2, 3, 4): vals.add(round(float(x), p))
T = pd.read_csv("results/t3_test_table.csv", header=[0, 1], index_col=[0, 1])
for v in T.values.ravel():
    if np.isfinite(v): add(v); add(v * 100)
for v in pd.read_csv("literature/gdae_table5.csv").select_dtypes("number").values.ravel(): add(v); add(v * 100)
for v in pd.read_csv("results/t3_per_attack.csv", index_col=[0, 1]).values.ravel():
    if np.isfinite(v): add(v * 100)
for ds in json.load(open("results/t3_stats.json")).values():
    for c in ds.values():
        for k, v in c.items():
            if isinstance(v, (int, float)): add(v); add(abs(v))
for v in json.load(open("results/t3_host_purity.json")).values() if os.path.exists("results/t3_host_purity.json") else []: add(v); add(v * 100)
WHITE = {0.003, 0.3, 99.7, 0.05, 0.01, 0.001, 0.8, 0.1, 0.9, 1.0, 10.0, 3.98, 11.95, 0.5}
txt = open("paper/manuscript.md").read()
bad = []
for m in re.finditer(r"(?<![\w.])(\d+\.\d{1,4})(?![\d])", txt):
    s = m.group(1); x = float(s); p = len(s.split(".")[1]); after = txt[m.end():m.end() + 3]; before = txt[max(0, m.start() - 6):m.start()]
    if after.startswith("e-") or after.startswith("/") or re.match(r"\.\d", after) or before.endswith(("doi:", "ython ", "PyOD ")):
        continue  # p-values in e-notation (generated from t3_stats.json), DOIs, software versions
    if x in WHITE or round(x, p) in vals: continue
    if any(abs(x - v) <= 0.5 * 10 ** -p + 1e-12 for v in vals): continue
    bad.append((s, txt[max(0, m.start() - 60):m.end() + 20].replace("\n", " ")))
print(f"checked numbers; unmatched: {len(bad)}")
for b in bad: print("  UNMATCHED", b[0], "|", b[1])
sys.exit(1 if bad else 0)
