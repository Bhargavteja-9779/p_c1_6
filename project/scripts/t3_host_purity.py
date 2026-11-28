"""Host-purity analysis across all 5 seeds (journal 32), saved to results/t3_host_purity.json."""
import json, os, collections
import numpy as np
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); out = {}
for ds in ["NF-UNSW-NB15-v2", "NF-CSE-CIC-IDS2018-v2"]:
    seen, share = [], []
    for s in [42, 123, 456, 789, 1234]:
        d = np.load(f"data/nfv2/{ds}_s{s}.npz"); tr = set(np.unique(d["str_"])); y = d["yte"]; src = d["ste"]
        seen.append(np.mean([x in tr for x in src[y == 1]]))
        c = collections.Counter(src); a = collections.Counter(src[y == 1]); share.append(np.mean([a[x] / c[x] for x in src[y == 1]]))
    out[f"{ds}_attack_from_seen_src"] = round(float(np.mean(seen)), 4); out[f"{ds}_attacker_attack_share"] = round(float(np.mean(share)), 4)
json.dump(out, open("results/t3_host_purity.json", "w"), indent=1); print(out)
