"""G11 integrity audit: every decimal number in paper/*.md must match a value in result files.

A number like 0.4567 / 45.67 / 45.7 matches if some value v in results/**/*.json|csv or tables/*.csv
satisfies round(v, d) == number or round(100*v, d) == number (d = decimals shown).
Integers (years, counts, seeds) and numbers inside lines marked `<!-- audit:skip -->` are ignored.
Exit code 1 on any mismatch; writes results/audit_report.md.
Usage: python scripts/audit_numbers.py [paper_dir]
"""
import glob, json, os, re, sys
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NUM = re.compile(r"(?<![\w.])-?\d+\.\d+(?![\w.])")


def values():
    vals = set()
    def walk(x):
        if isinstance(x, dict): [walk(v) for v in x.values()]
        elif isinstance(x, list): [walk(v) for v in x]
        elif isinstance(x, (int, float)) and not isinstance(x, bool): vals.add(float(x))
    for p in glob.glob(os.path.join(ROOT, "results", "**", "*.json"), recursive=True):
        try: walk(json.load(open(p)))
        except Exception: pass
    for p in glob.glob(os.path.join(ROOT, "results", "**", "*.csv"), recursive=True) + glob.glob(os.path.join(ROOT, "tables", "*.csv")):
        try:
            d = pd.read_csv(p).select_dtypes("number")
            vals.update(float(v) for v in d.values.ravel() if pd.notna(v))
        except Exception: pass
    return vals


def main():
    pdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "paper")
    files = glob.glob(os.path.join(pdir, "**", "*.md"), recursive=True)
    vals = values()
    rounded = {}
    bad, n = [], 0
    for f in files:
        for i, line in enumerate(open(f), 1):
            if "audit:skip" in line: continue
            for s in NUM.findall(line):
                n += 1; d = len(s.split(".")[1]); x = float(s)
                key = d
                if key not in rounded:
                    rounded[key] = {round(v, d) for v in vals} | {round(100 * v, d) for v in vals}
                if round(x, d) not in rounded[key] and round(-x, d) not in rounded[key]:
                    bad.append(f"{os.path.relpath(f, ROOT)}:{i}: {s}")
    rep = [f"# Number audit — {n} decimal numbers checked in {len(files)} files, {len(bad)} unmatched", ""] + [f"- {b}" for b in bad]
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    open(os.path.join(ROOT, "results", "audit_report.md"), "w").write("\n".join(rep) + "\n")
    print(rep[0])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
