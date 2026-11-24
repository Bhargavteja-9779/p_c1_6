"""Compute verified submission->acceptance times from Crossref 'assertion' metadata
(Received / Accepted dates deposited by the publisher, e.g. Springer Nature).

Usage: python scripts/journal_times.py ISSN [ISSN ...]
Writes journal_selection/times_<ISSN>.json (raw DOIs + dates) and prints a summary.
Idempotent: skips ISSNs whose output already exists unless --force.
"""
import json, sys, os, time, statistics, urllib.request, urllib.parse
from datetime import datetime

OUT = os.path.join(os.path.dirname(__file__), "..", "journal_selection")
FROM, UNTIL = "2024-11-01", "2026-11-24"


def get(url):
    for k in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa
            time.sleep(2 * (k + 1))
    raise RuntimeError(url)


def parse(v):
    for f in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(v.strip(), f)
        except Exception:
            pass
    return None


def run(issn, n_pages=3):
    rows, cursor, title = [], "*", None
    for _ in range(n_pages):
        q = urllib.parse.urlencode({
            "filter": f"from-pub-date:{FROM},until-pub-date:{UNTIL},type:journal-article",
            "rows": 200, "cursor": cursor, "select": "DOI,assertion,container-title,title"})
        d = get(f"https://api.crossref.org/journals/{issn}/works?{q}")["message"]
        for it in d["items"]:
            title = title or (it.get("container-title") or [None])[0]
            a = {x.get("name"): x.get("value") for x in it.get("assertion", []) if x.get("value")}
            r, ac = parse(a.get("received", "")), parse(a.get("accepted", ""))
            if r and ac:
                rows.append({"doi": it["DOI"], "received": r.date().isoformat(),
                             "accepted": ac.date().isoformat(), "days": (ac - r).days})
        cursor = d.get("next-cursor")
        if not d["items"] or not cursor:
            break
    days = sorted(x["days"] for x in rows if x["days"] >= 0)
    summ = {"issn": issn, "journal": title, "window": [FROM, UNTIL], "n_with_dates": len(days)}
    if days:
        q = statistics.quantiles(days, n=4) if len(days) > 3 else [days[0]] * 3
        summ.update(median=statistics.median(days), q1=q[0], q3=q[2], min=days[0], max=days[-1],
                    frac_le_72=round(sum(d <= 72 for d in days) / len(days), 3))
    json.dump({"summary": summ, "articles": rows}, open(os.path.join(OUT, f"times_{issn}.json"), "w"), indent=1)
    return summ


if __name__ == "__main__":
    force = "--force" in sys.argv
    for issn in [a for a in sys.argv[1:] if not a.startswith("--")]:
        p = os.path.join(OUT, f"times_{issn}.json")
        if os.path.exists(p) and not force:
            print(json.dumps(json.load(open(p))["summary"])); continue
        try:
            print(json.dumps(run(issn)))
        except Exception as e:
            print(json.dumps({"issn": issn, "error": str(e)}))
