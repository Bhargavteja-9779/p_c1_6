"""Frontiers does not deposit article history in Crossref; parse Received/Accepted from official article pages.
Usage: python scripts/frontiers_times.py ISSN [...]  -> journal_selection/times_<ISSN>.json (same format as journal_times.py)"""
import json, sys, os, re, time, random, statistics, urllib.request, urllib.parse
from datetime import datetime
OUT = os.path.join(os.path.dirname(__file__), "..", "journal_selection")
N = 60
def get(url, js=True):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read(); return json.loads(b) if js else b.decode("utf8", "ignore")
def run(issn):
    q = urllib.parse.urlencode({"filter": "from-pub-date:2025-06-01,until-pub-date:2026-11-24,type:journal-article", "sample": 100, "select": "DOI,container-title"})
    items = get(f"https://api.crossref.org/journals/{issn}/works?{q}")["message"]["items"]
    title = (items[0].get("container-title") or [None])[0] if items else None
    rows = []
    for it in items[:N]:
        try:
            h = get("https://doi.org/" + it["DOI"], js=False)
            d = dict(re.findall(r'<p class="h5">(Received|Accepted)</p><p>([^<]+)</p>', h))
            r, a = (datetime.strptime(d[k].strip(), "%d %B %Y") for k in ("Received", "Accepted"))
            rows.append({"doi": it["DOI"], "received": r.date().isoformat(), "accepted": a.date().isoformat(), "days": (a - r).days})
        except Exception:
            pass
        time.sleep(0.5)
    days = sorted(x["days"] for x in rows)
    s = {"issn": issn, "journal": title, "window": ["2025-06-01", "2026-11-24"], "n_with_dates": len(days), "source": "frontiersin.org article pages (random Crossref sample)"}
    if len(days) > 3:
        qq = statistics.quantiles(days, n=4)
        s.update(median=statistics.median(days), q1=qq[0], q3=qq[2], min=days[0], max=days[-1], frac_le_72=round(sum(x <= 72 for x in days) / len(days), 3))
    json.dump({"summary": s, "articles": rows}, open(os.path.join(OUT, f"times_{issn}.json"), "w"), indent=1)
    return s
if __name__ == "__main__":
    for i in sys.argv[1:]:
        if os.path.exists(os.path.join(OUT, f"times_{i}.json")):
            print(json.dumps(json.load(open(os.path.join(OUT, f"times_{i}.json")))["summary"])); continue
        try: print(json.dumps(run(i)), flush=True)
        except Exception as e: print(json.dumps({"issn": i, "error": str(e)}), flush=True)
