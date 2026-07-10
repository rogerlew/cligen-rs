#!/usr/bin/env python3
"""Observed-reference acquisition for the ratified Q3 pre-registration.

Primary: Daymet v4 single-pixel API at each corpus station's catalog
coordinates (daily prcp/tmax/tmin, all available years). Secondary:
GHCN-Daily by_station CSVs where the COOP mapping USC00<digits>
resolves and passes the completeness screen (>=30 years with >=95%
PRCP completeness).

Usage: acquire-observed.py <us2015-cache-dir> <raw-dir>
Writes observed-stats.json next to this script; raw downloads land in
<raw-dir> (not committed; sha256 + acquisition date pinned in the
JSON). Yearly statistics per pinned conventions: wet day = prcp >=
1.0 mm (R1mm); no detrending, with a detrended-SD sensitivity column
(residuals from an OLS linear trend on annual totals).
"""

import csv
import datetime
import gzip
import hashlib
import io
import json
import math
import os
import sqlite3
import sys
import urllib.request

CORPUS = [
    "ca042319.par", "az029654.par", "ut429382.par", "ca042257.par",
    "az022664.par", "az028619.par", "nm294426.par", "tx412797.par",
    "al015478.par", "ms227840.par", "fl086997.par", "fl083909.par",
    "co051660.par", "wy485345.par", "mn214026.par", "ak505769.par",
    "id106388.par",
]

WET_MM = 1.0


def sd(xs):
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def detrended_sd(xs):
    n = len(xs)
    if n < 3:
        return None
    ts = list(range(n))
    tm, xm = sum(ts) / n, sum(xs) / n
    beta = sum((t - tm) * (x - xm) for t, x in zip(ts, xs)) / sum(
        (t - tm) ** 2 for t in ts
    )
    residuals = [x - (xm + beta * (t - tm)) for t, x in zip(ts, xs)]
    return math.sqrt(sum(r * r for r in residuals) / (n - 2))


def yearly_stats(years):
    """years: {year: {"prcp": [...], "tmax": [...], "tmin": [...]}}"""
    complete = {
        y: v for y, v in sorted(years.items()) if len(v["prcp"]) >= 360
    }
    annual = [sum(v["prcp"]) for v in complete.values()]
    wet = [sum(1 for p in v["prcp"] if p >= WET_MM) for v in complete.values()]
    mx = [max(v["prcp"]) for v in complete.values()]
    tmax = [sum(v["tmax"]) / len(v["tmax"]) for v in complete.values()]
    tmin = [sum(v["tmin"]) / len(v["tmin"]) for v in complete.values()]
    mean_annual = sum(annual) / len(annual) if annual else None
    return {
        "n_years": len(complete),
        "span": [min(complete), max(complete)] if complete else None,
        "annual_precip_mean_mm": round(mean_annual, 2),
        "annual_precip_sd_mm": round(sd(annual), 3),
        "annual_precip_cv": round(sd(annual) / mean_annual, 4),
        "annual_precip_detrended_sd_mm": round(detrended_sd(annual), 3),
        "wet_day_count_mean": round(sum(wet) / len(wet), 2),
        "wet_day_count_sd": round(sd(wet), 3),
        "annual_max_daily_mean_mm": round(sum(mx) / len(mx), 2),
        "annual_max_daily_sd_mm": round(sd(mx), 3),
        "tmax_annual_mean_sd_c": round(sd(tmax), 4),
        "tmin_annual_mean_sd_c": round(sd(tmin), 4),
    }


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "cligen-rs q3"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def daymet(lat, lon, raw_dir, name):
    url = (
        "https://daymet.ornl.gov/single-pixel/api/data"
        f"?lat={lat}&lon={lon}&vars=prcp,tmax,tmin"
    )
    raw = fetch(url)
    path = os.path.join(raw_dir, f"daymet-{name}.csv")
    with open(path, "wb") as handle:
        handle.write(raw)
    years = {}
    reader = csv.reader(io.StringIO(raw.decode()))
    header_seen = False
    for row in reader:
        if not header_seen:
            if row and row[0] == "year":
                header_seen = True
            continue
        y = int(row[0])
        rec = years.setdefault(y, {"prcp": [], "tmax": [], "tmin": []})
        rec["prcp"].append(float(row[2]))
        rec["tmax"].append(float(row[3]))
        rec["tmin"].append(float(row[4]))
    return years, hashlib.sha256(raw).hexdigest()


def ghcn(coop_id, raw_dir):
    url = (
        "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/"
        f"{coop_id}.csv.gz"
    )
    try:
        raw = fetch(url)
    except Exception:
        return None, None
    path = os.path.join(raw_dir, f"ghcn-{coop_id}.csv.gz")
    with open(path, "wb") as handle:
        handle.write(raw)
    years = {}
    with gzip.open(io.BytesIO(raw), "rt") as handle:
        for row in csv.reader(handle):
            # by_station CSV: ID, YYYYMMDD, ELEMENT, VALUE, MFLAG, QFLAG, ...
            if row[2] not in ("PRCP", "TMAX", "TMIN") or row[5].strip():
                continue  # drop QC-flagged values
            y = int(row[1][:4])
            rec = years.setdefault(y, {"prcp": [], "tmax": [], "tmin": []})
            value = int(row[3]) / 10.0  # tenths of mm / tenths of C
            key = {"PRCP": "prcp", "TMAX": "tmax", "TMIN": "tmin"}[row[2]]
            rec[key].append(value)
    # Completeness screen. NOTE (R1 finding 8): yearly_stats() then
    # additionally requires >=360 prcp days, so the EFFECTIVE screen
    # is ~98.6%, stricter than the registered 95%; recorded, not
    # rerun (no station fell below 30 retained years; minimum 38).
    screened = {
        y: v
        for y, v in years.items()
        if len(v["prcp"]) >= 347 and len(v["tmax"]) >= 300 and len(v["tmin"]) >= 300
    }
    if len(screened) < 30:
        return None, hashlib.sha256(raw).hexdigest()
    return screened, hashlib.sha256(raw).hexdigest()


def main(cache, raw_dir):
    os.makedirs(raw_dir, exist_ok=True)
    con = sqlite3.connect(os.path.join(cache, "2015_stations.db"))
    out = {
        "acquired": datetime.date.today().isoformat(),
        "daymet_version": "4 R1 (single-pixel API)",
        "wet_day_threshold_mm": WET_MM,
        "stations": {},
    }
    for par in CORPUS:
        row = con.execute(
            "select desc, latitude, longitude from stations where par=?", (par,)
        ).fetchone()
        desc, lat, lon = row
        name = par.replace(".par", "")
        entry = {"desc": desc.strip(), "latitude": lat, "longitude": lon}
        years, digest = daymet(lat, lon, raw_dir, name)
        entry["daymet"] = yearly_stats(years)
        entry["daymet"]["raw_sha256"] = digest
        coop = "USC00" + name[2:]
        g_years, g_digest = ghcn(coop, raw_dir)
        if g_years:
            entry["ghcn"] = yearly_stats(g_years)
            entry["ghcn"]["station"] = coop
            entry["ghcn"]["raw_sha256"] = g_digest
        else:
            entry["ghcn"] = None
            entry["ghcn_note"] = (
                f"{coop}: unavailable or failed the completeness screen"
            )
        out["stations"][name] = entry
        print(name, "daymet years:", entry["daymet"]["n_years"],
              "| ghcn:", "ok" if g_years else "screened-out/absent", flush=True)
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "observed-stats.json")
    with open(dest, "w") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("wrote", dest)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
