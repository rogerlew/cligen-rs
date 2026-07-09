#!/usr/bin/env python3
"""Mechanical extraction over reference/cligen532/cligen.f.

Produces the unit inventory (boundaries, includes, callees), the
double-precision site list, and reference counts used by the dead-code
adjudication. Fortran-77 fixed-form aware: comment lines (c/C/*/! in
column 1) are excluded from code scans but retained for commented-call
detection.
"""

import re
import sys
from collections import defaultdict

SRC = "reference/cligen532/cligen.f"

unit_re = re.compile(
    r"^\s{6,}(?:(?:real|integer|double\s+precision|logical|character(?:\*\d+)?)\s+)?"
    r"(subroutine|function|block\s*data|program)\s*(\w*)",
    re.IGNORECASE,
)
include_re = re.compile(r"include\s+'([^']+)'", re.IGNORECASE)
call_re = re.compile(r"\bcall\s+(\w+)", re.IGNORECASE)
dp_re = re.compile(r"double\s+precision|real\s*\*\s*8|\bdble\s*\(|\b\d+\.?\d*[dD][+-]?\d+", re.IGNORECASE)
end_re = re.compile(r"^\s{6,}end\s*$", re.IGNORECASE)


def is_comment(line: str) -> bool:
    return bool(line) and line[0] in "cC*!"


def main() -> None:
    lines = open(SRC, encoding="latin-1").read().splitlines()

    # Pass 1: unit boundaries. The main program is everything before the
    # first declared unit that follows executable code; cligen.f's main is
    # implicit, so seed with it and correct by first declaration.
    units = []  # (name, kind, start_line)
    for i, line in enumerate(lines, 1):
        if is_comment(line):
            continue
        m = unit_re.match(line)
        if m:
            kind = m.group(1).lower().replace(" ", "")
            name = (m.group(2) or kind).lower()
            units.append((name, kind, i))
    # Determine spans: unit i runs to the 'end' before unit i+1.
    spans = []
    for idx, (name, kind, start) in enumerate(units):
        stop = units[idx + 1][2] - 1 if idx + 1 < len(units) else len(lines)
        spans.append((name, kind, start, stop))
    # Main program: from first executable line to first unit start - 1.
    main_start = 1
    main_stop = units[0][2] - 1 if units else len(lines)
    spans.insert(0, ("(preamble: header comments, no code)", "comments", main_start, main_stop))

    known_fns = {
        "randn", "dstn1", "dstg", "jdt", "timepk", "fouri2", "ryf2",
        "nrmd", "spmpar", "ipmpar", "erf", "erfc1", "exparg", "gam1",
        "gamma", "gratio", "rexp", "rlog", "cumchi", "cumgam",
    }

    inv = []
    dp_sites = []
    refcount = defaultdict(list)  # callee -> [(caller, line)]
    commented_calls = defaultdict(list)

    for name, kind, start, stop in spans:
        includes = set()
        callees = set()
        for i in range(start, stop + 1):
            line = lines[i - 1]
            if is_comment(line):
                m = call_re.search(line)
                if m:
                    commented_calls[m.group(1).lower()].append((name, i))
                continue
            m = include_re.search(line)
            if m:
                includes.add(m.group(1))
            for m in call_re.finditer(line):
                callee = m.group(1).lower()
                callees.add(callee)
                refcount[callee].append((name, i))
            # function references: known function name followed by '('
            low = line.lower()
            for fn in known_fns:
                for fm in re.finditer(r"\b" + fn + r"\s*\(", low):
                    # skip the unit's own declaration line
                    if unit_re.match(line):
                        continue
                    callees.add(fn)
                    refcount[fn].append((name, i))
            if dp_re.search(line):
                dp_sites.append((name, i, line.strip()[:90]))
        inv.append((name, kind, start, stop, sorted(includes), sorted(callees)))

    out = open("docs/work-packages/20260709-decomposition-ratification/artifacts/unit-extraction.md", "w")
    out.write("# Unit Extraction (mechanical)\n\nEvidence mode: Ran (this script; see extract.py)\n\n")
    out.write("| Unit | Kind | Lines | Includes | Callees |\n|---|---|---|---|---|\n")
    for name, kind, start, stop, incs, calls in inv:
        out.write(f"| `{name}` | {kind} | {start}-{stop} | {', '.join(incs) or '—'} | {', '.join(sorted(set(calls))) or '—'} |\n")

    out.write("\n## Reference counts (live code only)\n\n| Callee | Callers (line) |\n|---|---|\n")
    for callee in sorted(refcount):
        refs = refcount[callee]
        cs = ", ".join(f"{c}:{ln}" for c, ln in refs[:12])
        more = f" (+{len(refs)-12} more)" if len(refs) > 12 else ""
        out.write(f"| `{callee}` | {cs}{more} |\n")

    out.write("\n## Commented-out call sites\n\n| Callee | Sites |\n|---|---|\n")
    for callee in sorted(commented_calls):
        sites = commented_calls[callee]
        cs = ", ".join(f"{c}:{ln}" for c, ln in sites[:10])
        out.write(f"| `{callee}` | {cs} |\n")
    out.close()

    out = open("docs/work-packages/20260709-decomposition-ratification/artifacts/precision-sites.md", "w")
    out.write("# Double-Precision Sites (mechanical)\n\nEvidence mode: Ran.\n")
    out.write("Pattern: `double precision` | `real*8` | `dble(` | `D`-exponent literal.\n\n")
    out.write("| Unit | Line | Source (truncated) |\n|---|---|---|\n")
    for name, i, txt in dp_sites:
        out.write(f"| `{name}` | {i} | `{txt}` |\n")
    # Live include-file precision declarations (state, not cligen.f lines)
    out.write("\n## Include-file precision declarations (live includes)\n\n")
    out.write("| File | Line | Source |\n|---|---|---|\n")
    import glob
    for inc in sorted(glob.glob("reference/cligen532/*.inc")):
        if inc.endswith("crandom.inc") or inc.endswith("ctap2.inc"):
            continue  # not part of the live build surface
        for i, line in enumerate(open(inc, encoding="latin-1"), 1):
            if is_comment(line):
                continue
            if dp_re.search(line):
                out.write(f"| `{inc.split('/')[-1]}` | {i} | `{line.strip()[:90]}` |\n")
    out.close()

    print(f"units: {len(spans)} (incl. preamble row); dp sites in cligen.f: {len(dp_sites)}")


if __name__ == "__main__":
    main()
