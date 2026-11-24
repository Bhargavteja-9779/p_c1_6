#!/usr/bin/env python3
"""Layer-A job runner: persistent queue, lock, heartbeat, compute-budget ledger, retries, timeouts.

  python run_all.py --mode quick            # < 10 min smoke run (results/quick, state/queue_quick.json)
  python run_all.py --mode full --resume    # run/resume the latest experiments/plan_v*.yaml
Safe to run twice (file lock); never re-runs 'done' jobs; never overwrites results.
"""
import os, sys, json, time, glob, fcntl, argparse, subprocess, threading, itertools, re
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
ST = os.path.join(ROOT, "state")
MAX_ATTEMPTS = 3          # 1 try + 2 retries
JOB_TIMEOUT_S = 3 * 3600


def jload(p, default):
    try:
        return json.load(open(p))
    except Exception:
        return default


def jsave(p, obj):
    json.dump(obj, open(p + ".tmp", "w"), indent=1); os.replace(p + ".tmp", p)


def latest_plan():
    ps = sorted(glob.glob(os.path.join(ROOT, "experiments", "plan_v*.yaml")), key=lambda p: int(re.findall(r"v(\d+)", p)[-1]))
    return ps[-1]


def expand(plan, quick=False):
    """Expand plan YAML into concrete job specs."""
    jobs = []
    g = plan.get("globals", {})
    for blk in plan["blocks"]:
        keys = [k for k, v in blk.items() if isinstance(v, list) and k not in ("after",)]
        for combo in itertools.product(*[blk[k] for k in keys]):
            spec = {k: v for k, v in blk.items() if k not in keys}
            spec.update(dict(zip(keys, combo)))
            for k, v in g.items():
                spec.setdefault(k, v)
            fmt = {k: (str(v).replace("+", "-") if v is not None else "na") for k, v in spec.items()}
            spec["job_id"] = blk["id"].format(**fmt)
            if "cfg_from" in spec:
                spec["cfg_from"] = spec["cfg_from"].format(**fmt)
            spec.pop("id", None)
            if quick:
                spec.update({"n_per_source": 5000, "n_val_per_source": 5000, "n_configs": 2, "results_dir": "results/quick"})
                if "cfg" in spec and isinstance(spec["cfg"], dict) and "epochs" in spec["cfg"]:
                    spec["cfg"]["epochs"] = 1
            if quick and (spec.get("target") != "UNSW" or spec.get("seed", 0) != 0 or spec.get("tau", 0.4) != 0.4
                          or str(spec.get("n_per_source")) in ("10000", "30000") and spec.get("exp") == "E3"):
                continue
            jobs.append(spec)
    return jobs


class Budget:
    def __init__(self, cycle):
        self.p = os.path.join(ST, "budget.json"); self.cycle = str(cycle)
        b = jload(self.p, {}); b.setdefault("cycles", {}); b.setdefault("global_s", 0.0)
        b.setdefault("ceil_cycle_h", 15); b.setdefault("ceil_global_h", 120); b.setdefault("unit", "CPU wall-clock seconds while jobs run (4 cores)")
        b["cycles"].setdefault(self.cycle, 0.0); self.b = b; jsave(self.p, b)
        self.active = False; self.last = time.time(); self.lock = threading.Lock()

    def tick(self):
        with self.lock:
            now = time.time()
            if self.active:
                d = now - self.last
                self.b["cycles"][self.cycle] += d; self.b["global_s"] += d
            self.last = now; jsave(self.p, self.b)

    def exhausted(self):
        return (self.b["cycles"][self.cycle] >= self.b["ceil_cycle_h"] * 3600 or self.b["global_s"] >= self.b["ceil_global_h"] * 3600)


def heartbeat_loop(budget, stop):
    while not stop.is_set():
        open(os.path.join(ST, "heartbeat"), "w").write(time.strftime("%Y-%m-%dT%H:%M:%S") + f" pid={os.getpid()}\n")
        budget.tick(); stop.wait(30)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", default="full", choices=["quick", "full"])
    ap.add_argument("--resume", action="store_true"); ap.add_argument("--plan", default=None)
    ap.add_argument("--only", default=None, help="regex on job_id to restrict this invocation")
    a = ap.parse_args(); quick = a.mode == "quick"
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    lockf = open(os.path.join(ST, f"run_all_{a.mode}.lock"), "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another run_all is active; exiting"); return
    agent = jload(os.path.join(ST, "agent_state.json"), {"cycle": 1})
    plan_p = a.plan or latest_plan(); plan = yaml.safe_load(open(plan_p))
    qpath = os.path.join(ST, "queue_quick.json" if quick else "queue.json")
    q = jload(qpath, {"jobs": {}})
    for spec in expand(plan, quick):
        j = q["jobs"].get(spec["job_id"])
        if j is None:
            q["jobs"][spec["job_id"]] = {"spec": spec, "status": "pending", "attempts": 0, "plan": os.path.basename(plan_p)}
    for j in q["jobs"].values():                       # resume: anything left 'running' by a crash goes back to pending
        if j["status"] == "running":
            j["status"] = "pending"
    jsave(qpath, q)
    budget = Budget(agent.get("cycle", 1) if not quick else "quick")
    stop = threading.Event(); threading.Thread(target=heartbeat_loop, args=(budget, stop), daemon=True).start()
    log = open(os.path.join(ROOT, "logs", f"run_all_{a.mode}.log"), "a")
    try:
        while True:
            q = jload(qpath, q)
            pend = [j for j in q["jobs"].values() if j["status"] == "pending" and (not a.only or re.search(a.only, j["spec"]["job_id"]))]
            def ready(j):
                dep = j["spec"].get("cfg_from")
                return not dep or q["jobs"].get(dep, {}).get("status") == "done"
            rdy = [j for j in pend if ready(j)]
            blocked = [j for j in pend if not ready(j)]
            for j in blocked:   # dependency permanently failed -> mark
                dep = j["spec"].get("cfg_from")
                if q["jobs"].get(dep, {}).get("status") in ("failed", "skipped_budget"):
                    j["status"] = "failed"; j["error"] = f"dependency {dep} failed"
            if not rdy:
                jsave(qpath, q); break
            if not quick and budget.exhausted():
                for j in pend: j["status"] = "skipped_budget"
                jsave(qpath, q); log.write("budget exhausted\n"); break
            j = sorted(rdy, key=lambda j: (j["spec"].get("priority", 5), j["spec"]["job_id"]))[0]
            j["status"] = "running"; j["attempts"] += 1; j["started"] = time.strftime("%Y-%m-%dT%H:%M:%S"); jsave(qpath, q)
            log.write(f"{j['started']} START {j['spec']['job_id']} attempt {j['attempts']}\n"); log.flush()
            budget.active = True; budget.last = time.time()
            try:
                r = subprocess.run([sys.executable, os.path.join(ROOT, "src", "run_job.py"), "--job", json.dumps(j["spec"])],
                                   cwd=ROOT, capture_output=True, text=True, timeout=JOB_TIMEOUT_S)
                ok = r.returncode == 0; err = r.stderr[-2000:]
                log.write(r.stdout[-3000:])
            except subprocess.TimeoutExpired:
                ok, err = False, "timeout"
            budget.tick(); budget.active = False
            q = jload(qpath, q); jj = q["jobs"][j["spec"]["job_id"]]
            if ok:
                jj["status"] = "done"; jj["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                jj["error"] = err; jj["status"] = "failed" if jj["attempts"] >= MAX_ATTEMPTS else "pending"
                log.write(f"FAIL {jj['spec']['job_id']}: {err}\n")
            jsave(qpath, q); log.flush()
    finally:
        stop.set(); budget.tick()
    st = {}
    for j in q["jobs"].values(): st[j["status"]] = st.get(j["status"], 0) + 1
    print("queue status:", st); log.write(f"END {st}\n")
    if not quick and not any(j["status"] in ("pending", "running") for j in q["jobs"].values()):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "final_report.py")], cwd=ROOT)


if __name__ == "__main__":
    main()
