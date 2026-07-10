#!/usr/bin/env python3
"""Q3/Q4 analysis over the matrix sidecars: evaluates exactly the
pre-registered surfaces (pre-registration.md §Bounds).

Per-station group A scalar = mean over the 12 whole-run month cells'
|rel_err| (fixed here, applied identically to every config, so the
B1/Q4 ratios are estimator-invariant). Corpus statistic = median.

Usage: analyze-matrix.py <matrix-dir> <observed-stats.json> <out.json>
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


def report(matrix, station, config, years):
    path = os.path.join(matrix, f"{station}-{config}-{years}yr.cli.quality.json")
    return json.load(open(path))


def group_a_relerr(rep, parameter):
    cells = rep["par_convergence"][parameter]
    values = [cells[m]["rel_err"] for m in MONTHS if cells[m]["rel_err"] is not None]
    return sum(abs(v) for v in values) / len(values)


def annual_sd(rep):
    return rep["interannual"]["annual"]["precip_total_mm"]["sd"]


def annual_cv(rep):
    return rep["interannual"]["annual"]["precip_total_mm"]["cv"]


def decade0_sd(rep):
    return rep["interannual"]["by_decade"][0]["annual"]["precip_total_mm"]["sd"]


def main(matrix, observed_path, out_path):
    observed = json.load(open(observed_path))["stations"]
    runs = json.load(open(os.path.join(matrix, "runs.json")))
    wall = {}
    for run in runs:
        wall[(run["station"], run["config"], run["years"])] = run["wall_s"]

    out = {"per_station": {}, "bounds": {}}
    A_PARAMS = ["precip_wet_mean_mm", "precip_wet_sd_mm"]
    Q4_PARAMS = ["precip_wet_mean_mm", "precip_wet_sd_mm", "precip_wet_skew",
                 "wet_day_fraction"]

    for years in (30, 100):
        rows = {}
        for station in CORPUS:
            reps = {c: report(matrix, station, c, years)
                    for c in ("faithful", "qc-off", "fast-v0")}
            entry = {}
            for config, rep in reps.items():
                entry[config] = {
                    "a_qc_targets": statistics.mean(
                        group_a_relerr(rep, p) for p in A_PARAMS),
                    "a_q4_targets": statistics.mean(
                        group_a_relerr(rep, p) for p in Q4_PARAMS),
                    "annual_sd": annual_sd(rep),
                    "annual_cv": annual_cv(rep),
                    "decade0_sd": decade0_sd(rep),
                    "wall_s": wall[(station, config, years)],
                }
                process = rep["process"]
                if config == "qc-off":
                    cf = process["counterfactual"]
                    entry[config]["would_reject_rate"] = cf["would_reject"] / cf["batches"]
                if config == "faithful":
                    rejected = sum(
                        sum(p["rejected_attempts"][m] for m in MONTHS)
                        for p in process["retries"])
                    accepted = sum(
                        sum(p["accepted_batches"][m] for m in MONTHS)
                        for p in process["retries"])
                    entry[config]["rejected_attempts"] = rejected
                    entry[config]["accepted_batches"] = accepted
                    entry[config]["cap_give_ups"] = len(process["cap_give_ups"])
            entry["observed_cv_daymet"] = observed[station]["daymet"]["annual_precip_cv"]
            rows[station] = entry
        out["per_station"][years] = rows

        med = lambda xs: statistics.median(xs)
        f = {s: rows[s]["faithful"] for s in CORPUS}
        o = {s: rows[s]["qc-off"] for s in CORPUS}
        v = {s: rows[s]["fast-v0"] for s in CORPUS}
        b1_f = med([f[s]["a_qc_targets"] for s in CORPUS])
        b1_o = med([o[s]["a_qc_targets"] for s in CORPUS])
        b2_ratio = med([f[s]["annual_sd"] / o[s]["annual_sd"] for s in CORPUS])
        cv_worse = sum(
            1 for s in CORPUS
            if abs(f[s]["annual_cv"] - rows[s]["observed_cv_daymet"])
            > abs(o[s]["annual_cv"] - rows[s]["observed_cv_daymet"]))
        b3 = None
        if years == 100:
            early = [
                (f[s]["decade0_sd"] / o[s]["decade0_sd"])
                < (f[s]["annual_sd"] / o[s]["annual_sd"])
                for s in CORPUS
            ]
            b3 = {"stations_confirming": sum(early), "of": len(early)}
        out["bounds"][years] = {
            "B1": {
                "median_relerr_faithful": round(b1_f, 5),
                "median_relerr_off": round(b1_o, 5),
                "off_over_faithful": round(b1_o / b1_f, 4),
                "material_buy_threshold_1.2": b1_o / b1_f >= 1.2,
            },
            "B2": {
                "median_sd_ratio_faithful_over_off": round(b2_ratio, 4),
                "material_cost_sd": b2_ratio < 0.9,
                "faithful_cv_farther_from_observed_n": cv_worse,
                "of": len(CORPUS),
                "material_cost_cv_two_thirds": cv_worse >= (2 * len(CORPUS)) // 3 + 1,
            },
            "B3": b3,
            "B4": {
                "median_would_reject_rate_off": round(
                    med([o[s]["would_reject_rate"] for s in CORPUS]), 4),
                "total_cap_give_ups_faithful": sum(f[s]["cap_give_ups"] for s in CORPUS),
                "total_rejected_attempts_faithful": sum(
                    f[s]["rejected_attempts"] for s in CORPUS),
            },
            "B5": {
                "median_wall_faithful_s": round(med([f[s]["wall_s"] for s in CORPUS]), 3),
                "median_wall_off_s": round(med([o[s]["wall_s"] for s in CORPUS]), 3),
                "median_wall_fastv0_s": round(med([v[s]["wall_s"] for s in CORPUS]), 3),
            },
            "Q4_gate": {
                "a_median_relerr_v0": round(med([v[s]["a_q4_targets"] for s in CORPUS]), 5),
                "a_median_relerr_off": round(med([o[s]["a_q4_targets"] for s in CORPUS]), 5),
                "a_ratio_v0_over_off": round(
                    med([v[s]["a_q4_targets"] for s in CORPUS])
                    / med([o[s]["a_q4_targets"] for s in CORPUS]), 4),
                "a_pass_1.1": med([v[s]["a_q4_targets"] for s in CORPUS])
                <= 1.1 * med([o[s]["a_q4_targets"] for s in CORPUS]),
                "b_median_sd_ratio_v0_over_off": round(
                    med([v[s]["annual_sd"] / o[s]["annual_sd"] for s in CORPUS]), 4),
                "b_pass_0.9_1.15": 0.9
                <= med([v[s]["annual_sd"] / o[s]["annual_sd"] for s in CORPUS])
                <= 1.15,
                "c_wall_gain_off_over_v0": round(
                    med([o[s]["wall_s"] for s in CORPUS])
                    / med([v[s]["wall_s"] for s in CORPUS]), 3),
                "c_pass_1.5x": med([o[s]["wall_s"] for s in CORPUS])
                / med([v[s]["wall_s"] for s in CORPUS]) >= 1.5,
            },
        }
    with open(out_path, "w") as handle:
        json.dump(out, handle, indent=1)
    print(json.dumps(out["bounds"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
