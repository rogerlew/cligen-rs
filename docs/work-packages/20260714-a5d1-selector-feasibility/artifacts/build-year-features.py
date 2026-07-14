#!/usr/bin/env python3
"""Build sufficient-statistic rows from frozen A5d1 physical libraries."""

from __future__ import annotations

import math
import sys
import time

import numpy as np

from a5d1_common import (
    A5B_BUNDLES,
    FEATURE_DIR,
    FEATURE_MANIFEST,
    LIBRARY_MANIFEST,
    MONTH_NAMES,
    ROOT,
    daymet_annual_series,
    freeze_identity,
    load_json,
    parse_cli,
    relative,
    sample_covariance,
    sample_mean,
    sample_variance,
    sha256,
    station_records,
    write_json,
)


def empty_month() -> dict[str, float | int]:
    return {
        "days": 0,
        "wet_days": 0,
        "wet_sum": 0.0,
        "wet_sq_sum": 0.0,
        "tmax_sum": 0.0,
        "tmax_sq_sum": 0.0,
        "tmin_sum": 0.0,
        "tmin_sq_sum": 0.0,
        "dry_predecessors": 0,
        "wet_after_dry": 0,
        "wet_predecessors": 0,
        "wet_after_wet": 0,
        "bin_0_1": 0,
        "bin_1_5": 0,
        "bin_5_20": 0,
        "bin_20_inf": 0,
        "p_tmax_sum": 0.0,
        "p_tmin_sum": 0.0,
        "tmax_tmin_sum": 0.0,
        "duration_sum": 0.0,
        "duration_sq_sum": 0.0,
        "time_to_peak_sum": 0.0,
        "time_to_peak_sq_sum": 0.0,
        "peak_ratio_sum": 0.0,
        "peak_ratio_sq_sum": 0.0,
        "temperature_ordering_violations": 0,
    }


def build_block(year: int, rows: list[dict]) -> dict:
    months = [empty_month() for _ in range(12)]
    previous_wet: bool | None = None
    annual_p = 0.0
    annual_x = 0.0
    annual_n = 0.0
    for row in rows:
        p, duration, time_to_peak, peak_ratio, tmax, tmin = row["values"][:6]
        wet = p > 0.0
        month_index = row["month"] - 1
        month = months[month_index]
        month["days"] += 1
        month["tmax_sum"] += tmax
        month["tmax_sq_sum"] += tmax * tmax
        month["tmin_sum"] += tmin
        month["tmin_sq_sum"] += tmin * tmin
        month["p_tmax_sum"] += p * tmax
        month["p_tmin_sum"] += p * tmin
        month["tmax_tmin_sum"] += tmax * tmin
        month["temperature_ordering_violations"] += int(tmax < tmin)
        if wet:
            month["wet_days"] += 1
            month["wet_sum"] += p
            month["wet_sq_sum"] += p * p
            month["duration_sum"] += duration
            month["duration_sq_sum"] += duration * duration
            month["time_to_peak_sum"] += time_to_peak
            month["time_to_peak_sq_sum"] += time_to_peak * time_to_peak
            month["peak_ratio_sum"] += peak_ratio
            month["peak_ratio_sq_sum"] += peak_ratio * peak_ratio
            if p < 1.0:
                month["bin_0_1"] += 1
            elif p < 5.0:
                month["bin_1_5"] += 1
            elif p < 20.0:
                month["bin_5_20"] += 1
            else:
                month["bin_20_inf"] += 1
        # Attribute within-block transitions to the destination month. An
        # unordered marginal weight vector has no predecessor coupling, so
        # realized Jan 1 cross-block pairs are owned by finite-path replay.
        if previous_wet is not None:
            if previous_wet:
                month["wet_predecessors"] += 1
                month["wet_after_wet"] += int(wet)
            else:
                month["dry_predecessors"] += 1
                month["wet_after_dry"] += int(wet)
        previous_wet = wet
        annual_p += p
        annual_x += tmax
        annual_n += tmin
    days = len(rows)
    tmax_mean = annual_x / days
    tmin_mean = annual_n / days
    first_wet = rows[0]["values"][0] > 0.0
    last_wet = rows[-1]["values"][0] > 0.0
    leading_spell = 0
    for row in rows:
        if (row["values"][0] > 0.0) != first_wet:
            break
        leading_spell += 1
    trailing_spell = 0
    for row in reversed(rows):
        if (row["values"][0] > 0.0) != last_wet:
            break
        trailing_spell += 1
    return {
        "source_year": year,
        "calendar_days": days,
        "calendar_class": "leap" if days == 366 else "common",
        "first_day_wet": first_wet,
        "last_day_wet": last_wet,
        "leading_same_state_spell_days": leading_spell,
        "trailing_same_state_spell_days": trailing_spell,
        "annual": {
            "precip_total_mm": annual_p,
            "tmax_mean_c": tmax_mean,
            "tmin_mean_c": tmin_mean,
            "precip_total_mm.raw_second_moment": annual_p * annual_p,
            "tmax_mean_c.raw_second_moment": tmax_mean * tmax_mean,
            "tmin_mean_c.raw_second_moment": tmin_mean * tmin_mean,
            "precip_total_mm_x_tmax_mean_c.raw_cross_moment": annual_p * tmax_mean,
            "precip_total_mm_x_tmin_mean_c.raw_cross_moment": annual_p * tmin_mean,
            "tmax_mean_c_x_tmin_mean_c.raw_cross_moment": tmax_mean * tmin_mean,
        },
        "monthly": {name: months[index] for index, name in enumerate(MONTH_NAMES)},
    }


def detrend(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    x = np.arange(len(array), dtype=np.float64)
    design = np.column_stack((np.ones(len(array)), x))
    fitted = design @ np.linalg.lstsq(design, array, rcond=None)[0]
    return [float(value) for value in array - fitted]


def build_target(station_id: str, bundle: dict) -> dict:
    params = bundle["base_station"]["parameters"]
    precipitation = params["precipitation"]
    temperature = params["temperature"]
    monthly = {}
    for index, name in enumerate(MONTH_NAMES):
        p_wd = precipitation["probability_wet_given_dry"][index]
        p_ww = precipitation["probability_wet_given_wet"][index]
        wet_fraction = p_wd / (1.0 - p_ww + p_wd)
        wet_mean = precipitation["mean_daily"][index] * 25.4
        wet_sd = precipitation["standard_deviation_daily"][index] * 25.4
        tmax_mean = (temperature["maximum_mean"][index] - 32.0) * 5.0 / 9.0
        tmin_mean = (temperature["minimum_mean"][index] - 32.0) * 5.0 / 9.0
        tmax_sd = temperature["maximum_standard_deviation"][index] * 5.0 / 9.0
        tmin_sd = temperature["minimum_standard_deviation"][index] * 5.0 / 9.0
        monthly[name] = {
            "wet_fraction": wet_fraction,
            "wet_mean_mm": wet_mean,
            "wet_raw_second_mm2": wet_mean * wet_mean + wet_sd * wet_sd,
            "wet_given_dry": p_wd,
            "wet_given_wet": p_ww,
            "tmax_mean_c": tmax_mean,
            "tmax_raw_second_c2": tmax_mean * tmax_mean + tmax_sd * tmax_sd,
            "tmin_mean_c": tmin_mean,
            "tmin_raw_second_c2": tmin_mean * tmin_mean + tmin_sd * tmin_sd,
        }
    series = daymet_annual_series(station_id)
    residuals = {name: detrend(values) for name, values in series.items()}
    means = {name: sample_mean(values) for name, values in series.items()}
    centered = {
        "precip_total_mm.variance": sample_variance(residuals["precip_total_mm"]),
        "tmax_mean_c.variance": sample_variance(residuals["tmax_mean_c"]),
        "tmin_mean_c.variance": sample_variance(residuals["tmin_mean_c"]),
        "precip_total_mm_x_tmax_mean_c.covariance": sample_covariance(
            residuals["precip_total_mm"], residuals["tmax_mean_c"]
        ),
        "precip_total_mm_x_tmin_mean_c.covariance": sample_covariance(
            residuals["precip_total_mm"], residuals["tmin_mean_c"]
        ),
        "tmax_mean_c_x_tmin_mean_c.covariance": sample_covariance(
            residuals["tmax_mean_c"], residuals["tmin_mean_c"]
        ),
    }
    return {
        "monthly_station_surface": monthly,
        "annual_daymet_means": means,
        "annual_daymet_centered_targets": centered,
        "annual_daymet_fit_series": series,
    }


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: build-year-features.py")
    started = time.monotonic()
    freeze_sha256 = freeze_identity()
    library_manifest = load_json(LIBRARY_MANIFEST)
    if not isinstance(library_manifest, dict):
        raise ValueError("invalid library manifest")
    if library_manifest["freeze_sha256"] != freeze_sha256:
        raise ValueError("library manifest freeze mismatch")
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for station in station_records():
        station_id = station["station_id"]
        cli = ROOT / next(
            row["cli"]["path"]
            for row in library_manifest["records"]
            if row["station_id"] == station_id
        )
        rows = parse_cli(cli)
        grouped: dict[int, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row["year"], []).append(row)
        blocks = [build_block(year, grouped[year]) for year in sorted(grouped)]
        bundle_path = A5B_BUNDLES / f"{station_id}.a5b.station.json"
        bundle = load_json(bundle_path)
        if not isinstance(bundle, dict):
            raise ValueError(f"invalid station bundle: {station_id}")
        fourier = next(
            item for item in bundle["extensions"] if item["candidate_id"] == "fourier_eof"
        )
        value = {
            "year_feature_schema_version": 1,
            "development_only": True,
            "freeze_sha256": freeze_sha256,
            "station_id": station_id,
            "source_cli_sha256": sha256(cli),
            "source_bundle_sha256": sha256(bundle_path),
            "fourier_eof_identity": {
                "fit_identity_sha256": fourier["fit_identity_sha256"],
                "payload_sha256": fourier["diagnostics"]["payload_sha256"],
                "retained_rank": fourier["diagnostics"]["retained_rank"],
                "role": "hash-locked exposed development descriptor; no daily mutation",
            },
            "targets": build_target(station_id, bundle),
            "blocks": blocks,
        }
        output = FEATURE_DIR / f"{station_id}-year-features-v1.json"
        write_json(output, value)
        outputs.append(
            {
                "station_id": station_id,
                "path": relative(output),
                "bytes": output.stat().st_size,
                "sha256": sha256(output),
                "blocks": len(blocks),
                "common_blocks": sum(row["calendar_class"] == "common" for row in blocks),
                "leap_blocks": sum(row["calendar_class"] == "leap" for row in blocks),
            }
        )
    manifest = {
        "year_feature_manifest_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "source_library_manifest_sha256": sha256(LIBRARY_MANIFEST),
        "station_count": len(outputs),
        "records": outputs,
        "wall_seconds": round(time.monotonic() - started, 6),
    }
    write_json(FEATURE_MANIFEST, manifest)
    print(f"A5d1 year features: PASS ({len(outputs)} stations)")


if __name__ == "__main__":
    main()
