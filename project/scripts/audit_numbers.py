#!/usr/bin/env python3
"""G11 integrity audit: every decimal number in paper/*.md must match (after rounding to the number of decimals shown)
some numeric value found in results/**/*.json|csv, tables/*, journal_selection/*.json, literature/* (for cited numbers).
Integers < 1000, years, and numbers inside lines marked '<!-- noaudit -->' are skipped. Exit code 1 on any mismatch."""
import os, re, json, glob, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = re.compile(r"(?<![\w.])[-−]?\d+\.\d+(?![\w.])")


def harvest():
    vals = set()
    files = (glob.glob(os.path.join(R, "results", "**", "*.json"), recursive=True) + glob.glob(os.path.join(R, "results", "*.csv"))
             + glob.glob(os.path.join(R, "tables", "*")) + glob.glob(os.path.join(R, "journal_selection", "*"))
             + glob.glob(os.path.join(R, "literature", "*")) + glob.glob(os.path.join(R, "data", "proc", "*.json")))
    for f in files:
        try:
            txt = open(f, errors="ignore").read()
        except Exception:
            continue
        for m in re.findall(r"[-]?\d+\.?\d*(?:e[-+]?\d+)?", txt):
            try:
                vals.add(float(m))
            except ValueError:
                pass
    return vals


def main():
    vals = harvest(); bad = []; n = 0
    pct = {v * 100 for v in vals}
    for f in glob.glob(os.path.join(R, "paper", "*.md")):
        for i, line in enumerate(open(f), 1):
            if "noaudit" in line:
                continue
            for s in NUM.findall(line):
                x = float(s.replace("−", "-")); d = len(s.split(".")[1]); n += 1
                ok = any(round(v, d) == round(x, d) or round(v, d) == round(-x, d) for v in vals) or \
                     any(round(v, d) == round(x, d) for v in pct)
                if not ok:
                    bad.append(f"{os.path.relpath(f, R)}:{i}: {s}")
    print(f"audited {n} numbers; {len(bad)} unmatched")
    for b in bad[:200]:
        print("  UNMATCHED", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
