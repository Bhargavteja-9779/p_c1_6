"""Verified submission->acceptance times for Frontiers journals.

Frontiers does not deposit Received/Accepted in Crossref `assertion`, so we list recent
DOIs from Crossref and read the dates printed on each article page
("Received</p><p>19 October 2025", "Accepted</p><p>...").

Usage: python scripts/frontiers_times.py ISSN [ISSN ...] [--n 60] [--force]
Writes journal_selection/times_<ISSN>.json (same format as journal_times.py). Idempotent.
"""
import json, sys, os, re, time, random, statistics, urllib.request, urllib.parse
from datetime import datetime

OUT = os.path.join(os.path.dirname(__file__), "..", "journal_selection")
FROM, UNTIL = "2024-11-01", "2026-11-24"
UA = {"User-Agent": "Mozilla/5.0 (research-script)"}


def fetch(url, js=True):
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
    for k in ("Received", "Accepted", "Published"):
        m = re.search(k + r"</p><p>(\d{1,2} [A-Z][a-z]+ \d{4})", html)
        if m:
            out[k.lower()] = datetime.strptime(m.group(1), "%d %B %Y").date()
    return out


def run(issn, n):
    dois, cursor, title = [], "*", None
    for _ in range(5):
        q = urllib.parse.urlencode({"filter": f"from-pub-date:{FROM},until-pub-date:{UNTIL},type:journal-article",
                                    "rows": 200, "cursor": cursor, "select": "DOI,container-title"})
        d = fetch(f"https://api.crossref.org/journals/{issn}/works?{q}")["message"]
        for it in d["items"]:
            title = title or (it.get("container-title") or [None])[0]
            dois.append(it["DOI"])
        cursor = d.get("next-cursor")
        if not d["items"] or not cursor:
            break
    random.Random(0).shuffle(dois)   # fixed-seed random sample, not cherry-picked
    rows, tried = [], 0
    for doi in dois:
        if len(rows) >= n or tried >= 3 * n:
            break
        tried += 1
        html = fetch(f"https://www.frontiersin.org/articles/{doi}/full", js=False)
        dd = dates(html or "")
        if "received" in dd and "accepted" in dd:
            rows.append({"doi": doi, "received": dd["received"].isoformat(), "accepted": dd["accepted"].isoformat(),
                         "days": (dd["accepted"] - dd["received"]).days})
        time.sleep(1.0)
    days = sorted(x["days"] for x in rows if x["days"] >= 0)
    summ = {"issn": issn, "journal": title, "window": [FROM, UNTIL], "n_dois_listed": len(dois),
            "sample": f"fixed-seed random sample, pages tried={tried}", "n_with_dates": len(days),
            "source": "frontiersin.org article pages (Received/Accepted lines)"}
    if days:
        qq = statistics.quantiles(days, n=4) if len(days) > 3 else [days[0]] * 3
        summ.update(median=statistics.median(days), q1=qq[0], q3=qq[2], min=days[0], max=days[-1],
                    frac_le_72=round(sum(d <= 72 for d in days) / len(days), 3))
    json.dump({"summary": summ, "articles": rows}, open(os.path.join(OUT, f"times_{issn}.json"), "w"), indent=1)
    return summ


if __name__ == "__main__":
    a = sys.argv[1:]; force = "--force" in a
    n = int(a[a.index("--n") + 1]) if "--n" in a else 60
    issns = [x for x in a if re.fullmatch(r"\d{4}-\d{3}[\dX]", x)]
    for issn in issns:
        p = os.path.join(OUT, f"times_{issn}.json")
        if os.path.exists(p) and not force:
            print(json.dumps(json.load(open(p))["summary"])); continue
        print(json.dumps(run(issn, n)), flush=True)
