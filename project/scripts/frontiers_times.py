#!/usr/bin/env python3
"""Frontiers does not deposit Received/Accepted in Crossref; scrape them from the article pages.
Usage: python scripts/frontiers_times.py ISSN [ISSN ...]   (sample up to N=80 recent articles per journal)
Writes journal_selection/times_<ISSN>.json (same format as journal_times.py). Idempotent (skips existing unless --force).
"""
import json, sys, os, re, time, random, statistics, urllib.request, urllib.parse
from datetime import datetime
OUT = os.path.join(os.path.dirname(__file__), "..", "journal_selection")
FROM, UNTIL, N = "2024-11-01", "2026-11-24", 80
UA = {"User-Agent": "Mozilla/5.0 (research-script)"}

def fetch(url, js=False):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                b = r.read()
                return json.loads(b) if js else b.decode("utf-8", "replace")
        except Exception:
            time.sleep(2 * (k + 1))
    return None

def dates(html):
    out = {}
    for lab in ("Received", "Accepted"):
        m = re.search(r'<p class="h5">%s</p><p>([^<]+)</p>' % lab, html)
        if m:
            out[lab.lower()] = datetime.strptime(m.group(1).strip(), "%d %B %Y")
    return out

def run(issn):
    dois, cursor, title = [], "*", None
    for _ in range(10):
        q = urllib.parse.urlencode({"filter": f"from-pub-date:{FROM},until-pub-date:{UNTIL},type:journal-article",
                                    "rows": 500, "cursor": cursor, "select": "DOI,container-title"})
        d = fetch(f"https://api.crossref.org/journals/{issn}/works?{q}", js=True)["message"]
        for it in d["items"]:
            title = title or (it.get("container-title") or [None])[0]
            dois.append(it["DOI"])
        cursor = d.get("next-cursor")
        if not d["items"] or not cursor:
            break
    random.Random(0).shuffle(dois)
    rows = []
    for doi in dois[: N + 20]:
        if len(rows) >= N:
            break
        h = fetch(f"https://doi.org/{doi}")
        dd = dates(h or "")
        if "received" in dd and "accepted" in dd:
            rows.append({"doi": doi, "received": dd["received"].date().isoformat(),
                         "accepted": dd["accepted"].date().isoformat(), "days": (dd["accepted"] - dd["received"]).days})
        time.sleep(0.5)
    days = sorted(x["days"] for x in rows if x["days"] >= 0)
    s = {"issn": issn, "journal": title, "window": [FROM, UNTIL], "n_dois_in_window": len(dois),
         "n_with_dates": len(days), "method": "random sample (seed 0) of Crossref DOIs; dates scraped from article pages"}
    if days:
        q = statistics.quantiles(days, n=4)
        s.update(median=statistics.median(days), q1=q[0], q3=q[2], min=days[0], max=days[-1],
                 frac_le_72=round(sum(x <= 72 for x in days) / len(days), 3))
    json.dump({"summary": s, "articles": rows}, open(os.path.join(OUT, f"times_{issn}.json"), "w"), indent=1)
    return s

if __name__ == "__main__":
    force = "--force" in sys.argv
    for issn in [a for a in sys.argv[1:] if not a.startswith("--")]:
        if os.path.exists(os.path.join(OUT, f"times_{issn}.json")) and not force:
            print(issn, "exists, skip"); continue
        print(json.dumps(run(issn)), flush=True)
