#!/usr/bin/env python3
"""G11 integrity audit: every decimal number in paper/*.md must trace to a value in a result file.

Collects all numeric leaves from results/**/*.json, results/**/*.csv, journal_selection/*.json, and tables/*.md.
A paper number with d decimals matches if some source value v satisfies round(v, d) == number, or
round(100*v, d) == number (percent form). Integers, years, section/table/figure/equation numbers and
numbers inside lines tagged `<!-- audit:skip -->` are ignored; numbers that only come from cited papers must be
written inside a line tagged `<!-- audit:cited -->` (checked manually against literature/reported_results.md).
Exit code 1 if any untraced number. Usage: python scripts/audit_numbers.py [paper/manuscript.md ...]
"""
import os, re, sys, json, glob, csv

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = re.compile(r"(?<![\w.])[-+−]?\d+\.\d+(?![\w.])")


def leaves(o):
    if isinstance(o, dict):
        for v in o.values(): yield from leaves(v)
    elif isinstance(o, list):
        for v in o: yield from leaves(v)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield float(o)


def sources():
    vals = set()
    for p in glob.glob(os.path.join(R, "results", "**", "*.json"), recursive=True) + glob.glob(os.path.join(R, "journal_selection", "*.json")):
        try:
            vals.update(leaves(json.load(open(p))))
        except Exception:
            pass
    for p in glob.glob(os.path.join(R, "results", "**", "*.csv"), recursive=True):
        for row in csv.reader(open(p)):
            for x in row:
                try: vals.add(float(x))
                except ValueError: pass
    for p in glob.glob(os.path.join(R, "tables", "*.md")):
        vals.update(float(x.replace("−", "-")) for x in NUM.findall(open(p).read()))
    return vals


def main():
    files = sys.argv[1:] or glob.glob(os.path.join(R, "paper", "*.md"))
    vals = sources(); index = {}
    for v in vals:
        for d in range(1, 5):
            index.setdefault(d, set()).update({abs(round(v, d)), abs(round(100 * v, d))})
    bad = []
    for f in files:
        for ln, line in enumerate(open(f), 1):
            if "audit:skip" in line or "audit:cited" in line:
                continue
            for s in NUM.findall(line):
                x = float(s.replace("−", "-")); d = len(s.split(".")[1])
                if round(abs(x), d) not in index.get(min(d, 4), set()):
                    bad.append(f"{os.path.relpath(f, R)}:{ln}: {s}")
    print(f"audit: {len(files)} file(s), {len(vals)} source values, {len(bad)} untraced numbers")
    for b in bad: print("  UNTRACED", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
