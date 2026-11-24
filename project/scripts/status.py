#!/usr/bin/env python3
"""Print project state: agent phase, queue counts, budget, heartbeat age, data presence."""
import json, os, time, collections, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def j(p, d=None):
    try: return json.load(open(os.path.join(R, p)))
    except Exception: return d
print("agent_state:", j("state/agent_state.json"))
for qn in ("state/queue.json", "state/queue_quick.json"):
    q = j(qn, {"jobs": {}})["jobs"]; print(qn, dict(collections.Counter(x["status"] for x in q.values())))
b = j("state/budget.json", {}); print("budget (h):", {k: round(v/3600, 2) for k, v in b.get("cycles", {}).items()}, "global", round(b.get("global_s", 0)/3600, 2))
hb = os.path.join(R, "state/heartbeat")
print("heartbeat age (s):", round(time.time()-os.path.getmtime(hb)) if os.path.exists(hb) else "none")
print("raw data present:", sorted(os.path.basename(p) for p in glob.glob(os.path.join(R, "data/raw/*.parquet"))))
print("proc pools:", len(glob.glob(os.path.join(R, "data/proc/*.parquet"))), "/ 24")
