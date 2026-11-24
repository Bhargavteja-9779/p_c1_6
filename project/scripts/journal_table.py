"""Build journal_selection/journal_comparison.md from times_*.json + manually verified IF table."""
import json, glob, os
IF = {  # JIF as shown on the official Springer journal page (fetched 2026-11-24 via headless browser); None = no JIF shown
 "2213-1248": ("6.4 (2025)", ""), "1319-1578": ("6.4 (2025)", ""),
 "2196-1115": ("10.8 (2025)", "57"), "2198-6053": ("4.5 (2025)", "20"), "1758-2946": ("7.9 (2025)", "10"),
 "2523-3246": ("4.1 (2025)", "15"), "2192-113X": ("5.5 (2025)", "40"), "1479-5876": ("9.7 (2025)", "11"),
 "1572-8145": ("7.7 (2025)", "8"), "2520-8942": ("none shown (not JCR-listed on page)", "13"),
 "1875-6883": ("none shown on fetched page", "11"),
}
rows = []
for p in sorted(glob.glob("journal_selection/times_*.json")):
    s = json.load(open(p))["summary"]
    if not s.get("n_with_dates"): continue
    rows.append(s)
rows.sort(key=lambda s: s["median"])
L = ["# Journal comparison (verified Received→Accepted from Crossref publisher-deposited article history)",
     "", f"Window: articles published {rows[0]['window'][0]} … {rows[0]['window'][1]}; up to 600 articles per journal; raw DOIs+dates in times_<ISSN>.json.",
     "JIF column = value displayed on official Springer journal page (fetched 2026-11-24); '-' = not fetched.", "",
     "| Journal | ISSN | n articles | median days | IQR | min–max | share ≤72 d | JIF (source: publisher page) |", "|---|---|---|---|---|---|---|---|"]
for s in rows:
    L.append(f"| {s['journal']} | {s['issn']} | {s['n_with_dates']} | {s['median']} | {s['q1']}–{s['q3']} | {s['min']}–{s['max']} | {s['frac_le_72']} | {IF.get(s['issn'],('-',))[0]} |")
open("journal_selection/journal_comparison.md","w").write("\n".join(L)+"\n")
print("\n".join(L))
