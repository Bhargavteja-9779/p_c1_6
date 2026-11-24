#!/usr/bin/env python3
"""G11 integrity audit: every decimal number in paper/*.md must match a number in a result file
(results/**/*.json|csv|md, tables/*.md, journal_selection/*.json, literature/*.md for cited prior numbers),
after rounding to the number of decimals shown (also tries x100 for percentages).
Integers, years, DOIs, and lines containing '<!-- noaudit -->' are skipped. Exit 1 if any number is unmatched."""
import os, re, sys, glob, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = re.compile(r"(?<![\w./-])[-−]?\d+\.\d+")

def source_numbers():
    vals = set()
    pats = ["results/**/*.json", "results/**/*.csv", "results/**/*.md", "tables/*.md", "journal_selection/*.json",
            "journal_selection/*.md", "literature/*.md", "literature/*.csv"]
    for p in pats:
        for f in glob.glob(os.path.join(R, p), recursive=True):
            if "/quick" in f: continue
            for m in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", open(f, errors="ignore").read()):
                try: vals.add(float(m))
                except ValueError: pass
    return vals

def matches(tok, vals):
    x = float(tok.replace("−", "-")); d = len(tok.split(".")[1])
    for v in vals:
        for s in (v, v * 100, abs(v), abs(v) * 100):
            if round(s, d) == x or abs(round(s, d) - x) < 10 ** -d / 2 + 1e-12: return True
    return False

def main():
    files = glob.glob(os.path.join(R, "paper", "*.md"))
    if not files: print("no paper/*.md yet"); return 0
    vals = sorted(source_numbers()); bad = []
    for f in files:
        for i, line in enumerate(open(f), 1):
            if "noaudit" in line or "doi" in line.lower(): continue
            for tok in NUM.findall(line):
                if not matches(tok, vals): bad.append(f"{os.path.relpath(f, R)}:{i}: {tok}")
    print("\n".join(bad) or "AUDIT PASS"); print(f"{len(bad)} unmatched numbers")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
