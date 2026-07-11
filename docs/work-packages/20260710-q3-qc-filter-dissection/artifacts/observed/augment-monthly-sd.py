#!/usr/bin/env python3
"""Q3 addendum: add per-calendar-month interannual SDs of monthly
precipitation totals to observed-stats.json.

Closes the record gap the operator identified (2026-07-10): the
pre-registration's Measurements section names monthly totals compared
to the observed reference, but the original acquisition computed only
annual statistics. This script recomputes from the SAME raw downloads
(SHA-256-verified against the pinned hashes — no re-acquisition, no
network) and augments the JSON in place with
`monthly_precip_total_sd_mm` (12 values, Jan..Dec) per source.

Daymet uses a 365-day no-leap calendar: yday 1..365 maps to fixed
month lengths (Feb always 28). GHCN months come from the date field;
the same completeness screen as the original acquisition applies.

Usage: augment-monthly-sd.py <raw-dir>
"""

import csv
import datetime
import gzip
import hashlib
import io
import json
import math
import os
import sys

STATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "observed-stats.json")

# Cumulative day-of-year bounds for Daymet's fixed 365-day calendar.
_NOLEAP = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_CUM = []
_total = 0
for _n in _NOLEAP:
    _total += _n
    _CUM.append(_total)


def month_of_yday(yday):
    for month, bound in enumerate(_CUM):
        if yday <= bound:
            return month
    raise ValueError(yday)


def sd(xs):
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def monthly_sds(monthly_by_year):
    """monthly_by_year: {year: [12 totals]} -> 12 interannual SDs."""
    return [
        round(sd([months[m] for months in monthly_by_year.values()]), 3)
        for m in range(12)
    ]


def daymet_monthly(path):
    years = {}
    daycount = {}
    with open(path, encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header_seen = False
        for row in reader:
            if not header_seen:
                if row and row[0] == "year":
                    header_seen = True
                continue
            y, yday = int(row[0]), int(row[1])
            years.setdefault(y, [0.0] * 12)[month_of_yday(yday)] += float(row[2])
            daycount[y] = daycount.get(y, 0) + 1
    # same completeness rule as the original acquisition (>= 360 days)
    return {y: m for y, m in years.items() if daycount[y] >= 360}


def ghcn_monthly(path):
    years = {}
    daycount = {}
    with gzip.open(path, "rt") as handle:
        for row in csv.reader(handle):
            if row[2] != "PRCP" or row[5].strip():
                continue
            y, month = int(row[1][:4]), int(row[1][4:6]) - 1
            years.setdefault(y, [0.0] * 12)[month] += int(row[3]) / 10.0
            daycount[y] = daycount.get(y, 0) + 1
    return {y: m for y, m in years.items() if daycount[y] >= 360}


def main(raw_dir):
    out = json.load(open(STATS))
    for name, entry in out["stations"].items():
        daymet_path = os.path.join(raw_dir, f"daymet-{name}.csv")
        digest = hashlib.sha256(open(daymet_path, "rb").read()).hexdigest()
        assert digest == entry["daymet"]["raw_sha256"], f"{name}: daymet raw hash mismatch"
        entry["daymet"]["monthly_precip_total_sd_mm"] = monthly_sds(daymet_monthly(daymet_path))
        if entry.get("ghcn"):
            ghcn_path = os.path.join(raw_dir, f"ghcn-{entry['ghcn']['station']}.csv.gz")
            digest = hashlib.sha256(open(ghcn_path, "rb").read()).hexdigest()
            assert digest == entry["ghcn"]["raw_sha256"], f"{name}: ghcn raw hash mismatch"
            entry["ghcn"]["monthly_precip_total_sd_mm"] = monthly_sds(ghcn_monthly(ghcn_path))
    out["monthly_sd_augmented"] = {
        "date": datetime.date.today().isoformat(),
        "note": "recomputed from the original raws (hash-verified); "
                "see augment-monthly-sd.py",
    }
    with open(STATS, "w") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("augmented", STATS)


if __name__ == "__main__":
    main(sys.argv[1])
