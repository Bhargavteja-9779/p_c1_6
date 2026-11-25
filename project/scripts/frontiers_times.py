"""Submission->acceptance times for Frontiers journals.

Frontiers does NOT deposit Received/Accepted in Crossref `assertion` (checked 2026-11-24),
so DOIs are listed via Crossref and the dates are read from the official article page
(div.Summary__dates: Received / Revised / Accepted / Published).

Usage: python scripts/frontiers_times.py ISSN [ISSN ...] [--n 80] [--force]
Writes journal_selection/times_<ISSN>.json (same format as journal_times.py). Idempotent.
"""
import json, os, random, re, statistics, sys, time, urllib.parse, urllib.request
from datetime import datetime

OUT = os.path.join(os.path.dirname(__file__), "..", "journal_selection")
FROM, UNTIL = "2024-11-01", "2026-11-24"
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


def dois(issn, pages=5):
    out, cursor, title = [], "*", None
    for _ in range(pages):
        q = urllib.parse.urlencode({"filter": f"from-pub-date:{FROM},until-pub-date:{UNTIL},type:journal-article",
                                    "rows": 200, "cursor": cursor, "select": "DOI,container-title"})
        d = fetch(f"https://api.crossref.org/journals/{issn}/works?{q}", js=True)["message"]
        for it in d["items"]:
            title = title or (it.get("container-title") or [None])[0]
            out.append(it["DOI"])
        cursor = d.get("next-cursor")
        if not d["items"] or not cursor:
            break
    return title, out


DATE = re.compile(r'<p class="h5">(Received|Accepted)</p><p>([^<]+)</p>')


def dates(doi):
    html = fetch(f"https://doi.org/{doi}")
    if not html:
        return None
    d = {k: v.strip() for k, v in DATE.findall(html)}
    try:
        r = datetime.strptime(d["Received"], "%d %B %Y")
        a = datetime.strptime(d["Accepted"], "%d %B %Y")
    except Exception:
        return None
    return {"doi": doi, "received": r.date().isoformat(), "accepted": a.date().isoformat(), "days": (a - r).days}


def run(issn, n):
    title, all_dois = dois(issn)
    random.Random(0).shuffle(all_dois)  # fixed-seed random sample, chosen before seeing any dates
    rows = []
    for doi in all_dois[:n]:
        x = dates(doi)
        if x:
            rows.append(x)
        time.sleep(0.5)
    days = sorted(x["days"] for x in rows if x["days"] >= 0)
    s = {"issn": issn, "journal": title, "window": [FROM, UNTIL], "n_population": len(all_dois),
         "n_sampled": min(n, len(all_dois)), "n_with_dates": len(days), "source": "frontiersin.org article pages"}
    if days:
        q = statistics.quantiles(days, n=4) if len(days) > 3 else [days[0]] * 3
        s.update(median=statistics.median(days), q1=q[0], q3=q[2], min=days[0], max=days[-1],
                 frac_le_72=round(sum(d <= 72 for d in days) / len(days), 3))
    json.dump({"summary": s, "articles": rows}, open(os.path.join(OUT, f"times_{issn}.json"), "w"), indent=1)
    return s


if __name__ == "__main__":
    a = sys.argv[1:]
    n = int(a[a.index("--n") + 1]) if "--n" in a else 80
    force = "--force" in a
    issns = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--n")]
    for issn in issns:
        p = os.path.join(OUT, f"times_{issn}.json")
        if os.path.exists(p) and not force:
            print(json.dumps(json.load(open(p))["summary"])); continue
        print(json.dumps(run(issn, n)), flush=True)
