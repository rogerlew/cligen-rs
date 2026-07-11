#!/usr/bin/env python3
"""Q3 addendum analysis: monthly interannual dispersion vs observed.

Joins each config's group-B `monthly_precip_total_sd_mm` (from the
matrix sidecars) against the observed per-month interannual SDs
(Daymet primary, GHCN where screened-in). Reports, per horizon:

- station-month counts of which config's monthly SD is closer to
  observed (faithful vs off; off vs fast-v0), full and with a
  noise-floor sensitivity (observed mean monthly total >= 5 mm,
  approximated by observed SD >= 2 mm when means are unavailable);
- the per-month corpus-median SD_faithful/SD_off ratio (the seasonal
  clipping profile) and median SD_config/SD_observed;
- GHCN-secondary direction counts for the 8 screened stations.

Usage: analyze-monthly-sd.py <matrix-dir> <observed-stats.json> <out.json>
"""

import json
import os
import statistics
import sys

CORPUS = [
    "ca042319", "az029654", "ut429382", "ca042257",
    "az022664", "az028619", "nm294426", "tx412797",
    "al015478", "ms227840", "fl086997", "fl083909",
    "co051660", "wy485345", "mn214026", "ak505769",
    "id106388",
]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]


def generated_monthly_sd(matrix, station, config, years):
    path = os.path.join(matrix, f"{station}-{config}-{years}yr.cli.quality.json")
    cells = json.load(open(path))["interannual"]["monthly_precip_total_sd_mm"]
    return [cells[m]["sd"] for m in MONTHS]


def closer_counts(a, b, observed, floor=None):
    """Count station-months where |a-obs| < |b-obs| (and the reverse)."""
    a_closer = b_closer = n = 0
    for x, y, o in zip(a, b, observed):
        if x is None or y is None or o is None:
            continue
        if floor is not None and o < floor:
            continue
        n += 1
        if abs(x - o) < abs(y - o):
            a_closer += 1
        elif abs(y - o) < abs(x - o):
            b_closer += 1
    return a_closer, b_closer, n


def main(matrix, observed_path, out_path):
    observed = json.load(open(observed_path))["stations"]
    out = {}
    for years in (30, 100):
        flat = {"faithful": [], "qc-off": [], "fast-v0": [], "obs": [], "obs_ghcn": []}
        per_month = {m: {"f": [], "o": [], "obs": []} for m in range(12)}
        for station in CORPUS:
            obs_sd = observed[station]["daymet"]["monthly_precip_total_sd_mm"]
            ghcn = observed[station].get("ghcn")
            ghcn_sd = ghcn["monthly_precip_total_sd_mm"] if ghcn else [None] * 12
            series = {
                config: generated_monthly_sd(matrix, station, config, years)
                for config in ("faithful", "qc-off", "fast-v0")
            }
            for m in range(12):
                for config in series:
                    flat[config].append(series[config][m])
                flat["obs"].append(obs_sd[m])
                flat["obs_ghcn"].append(ghcn_sd[m])
                if series["faithful"][m] is not None and series["qc-off"][m] is not None:
                    per_month[m]["f"].append(series["faithful"][m])
                    per_month[m]["o"].append(series["qc-off"][m])
                    per_month[m]["obs"].append(obs_sd[m])

        f_closer, o_closer, n = closer_counts(flat["faithful"], flat["qc-off"], flat["obs"])
        f_closer5, o_closer5, n5 = closer_counts(
            flat["faithful"], flat["qc-off"], flat["obs"], floor=2.0)
        v_closer, o2_closer, n2 = closer_counts(flat["fast-v0"], flat["qc-off"], flat["obs"])
        gf, go, gn = closer_counts(flat["faithful"], flat["qc-off"], flat["obs_ghcn"])

        seasonal = {}
        for m in range(12):
            ratios = [f / o for f, o in zip(per_month[m]["f"], per_month[m]["o"]) if o]
            vs_obs_f = [f / ob for f, ob in zip(per_month[m]["f"], per_month[m]["obs"]) if ob]
            vs_obs_o = [o / ob for o, ob in zip(per_month[m]["o"], per_month[m]["obs"]) if ob]
            seasonal[MONTHS[m]] = {
                "median_sd_ratio_faithful_over_off": round(statistics.median(ratios), 4),
                "median_faithful_over_observed": round(statistics.median(vs_obs_f), 4),
                "median_off_over_observed": round(statistics.median(vs_obs_o), 4),
            }
        out[str(years)] = {
            "station_months": {
                "off_closer_to_observed": o_closer,
                "faithful_closer_to_observed": f_closer,
                "of": n,
                "noise_floor_2mm": {
                    "off_closer": o_closer5, "faithful_closer": f_closer5, "of": n5},
                "ghcn_secondary": {
                    "off_closer": go, "faithful_closer": gf, "of": gn},
                "v0_vs_off": {
                    "v0_closer": v_closer, "off_closer": o2_closer, "of": n2},
            },
            "seasonal": seasonal,
        }
    with open(out_path, "w") as handle:
        json.dump(out, handle, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
