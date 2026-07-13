#!/usr/bin/env python3
"""Build deterministic A5a-v1 observed targets from the archived sources."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from corpus_common import (
    archive_records,
    expected_dates,
    logical_records_bytes,
    next_date,
    sha256,
    write_canonical_json,
)

MONTHS = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)
R1MM = 1.0
METRICS_HELPER: Path | None = None


def row_sum(values):
    """Accumulate left-to-right with one f64 addition per input value."""
    total = 0.0
    for value in values:
        total += value
    return total


def mean(values):
    return None if not values else row_sum(values) / len(values)


def sample_sd(values):
    if len(values) < 2:
        return None
    center = mean(values)
    squares = ((value - center) * (value - center) for value in values)
    return math.sqrt(row_sum(squares) / (len(values) - 1))


def covariance(xs, ys):
    if len(xs) < 2:
        return None
    mx, my = mean(xs), mean(ys)
    products = ((x - mx) * (y - my) for x, y in zip(xs, ys))
    return row_sum(products) / (len(xs) - 1)


def pearson(xs, ys):
    if len(xs) < 2:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sxx = syy = 0.0
    for x, y in zip(xs, ys):
        dx, dy = x - mx, y - my
        sxy += dx * dy
        sxx += dx * dx
        syy += dy * dy
    if sxx == 0.0 or syy == 0.0:
        return None
    value = sxy / math.sqrt(sxx * syy)
    return max(-1.0, min(1.0, value))


def ranks(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        rank = (start + end) / 2.0 + 1.0
        for index in order[start : end + 1]:
            result[index] = rank
        start = end + 1
    return result


def corr_cell(xs, ys):
    return {
        "n": len(xs),
        "pearson": pearson(xs, ys),
        "spearman": pearson(ranks(xs), ranks(ys)) if len(xs) >= 2 else None,
    }


def detrend(series):
    years = sorted(series)
    if len(years) < 2:
        return dict(series)
    xs = [float(year) for year in years]
    ys = [series[year] for year in years]
    mx, my = mean(xs), mean(ys)
    denom = row_sum((x - mx) * (x - mx) for x in xs)
    numerator = row_sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = 0.0 if denom == 0.0 else numerator / denom
    return {year: value - (my + slope * (year - mx)) for year, value in zip(years, ys)}


def dispersion(series, cv=True):
    years = sorted(series)
    values = [series[year] for year in years]
    center, spread = mean(values), sample_sd(values)
    return {
        "cv": (
            None
            if not cv or center in (None, 0.0) or spread is None
            else spread / center
        ),
        "detrended_sd": sample_sd(list(detrend(series).values())),
        "mean": center,
        "n_years": len(values),
        "sd": spread,
    }


def quantile(values, probability):
    if not values or not 0.0 < probability <= 1.0:
        return None
    ordered = sorted(values)
    rank = math.ceil(probability * len(ordered))
    return ordered[max(rank - 1, 0)]


def distribution(values):
    return {
        "max": max(values) if values else None,
        "mean": mean(values),
        "n": len(values),
        "p50": quantile(values, 0.50),
        "p90": quantile(values, 0.90),
        "p95": quantile(values, 0.95),
        "p99": quantile(values, 0.99),
        "sd": sample_sd(values),
    }


def low_frequency(series):
    years = sorted(series)
    values = [series[year] for year in years]
    n = len(values)
    if n < 4 or years != list(range(years[0], years[-1] + 1)):
        return None
    if METRICS_HELPER is None:
        raise RuntimeError("metrics helper was not configured")
    completed = subprocess.run(
        [str(METRICS_HELPER)],
        input=json.dumps(values, allow_nan=False, separators=(",", ":")),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    result = json.loads(completed.stdout)
    if result is not None and (
        not isinstance(result, (int, float))
        or not math.isfinite(result)
        or not 0.0 <= result <= 1.0
    ):
        raise ValueError(f"invalid metrics-helper result: {result!r}")
    return result


def complete_values(records, dates, variable):
    if all(variable in records.get(date, {}) for date in dates):
        return [records[date][variable] for date in dates]
    return None


def aggregate_series(records, calendar, start, end):
    annual = {
        name: {}
        for name in (
            "precip_total_mm",
            "r1mm_wet_day_count",
            "max_daily_precip_mm",
            "tmax_mean_c",
            "tmin_mean_c",
        )
    }
    monthly = {
        month: {
            name: {}
            for name in (
                "precip_total_mm",
                "r1mm_wet_day_count",
                "r1mm_wet_day_mean_amount_mm",
                "tmax_mean_c",
                "tmin_mean_c",
            )
        }
        for month in MONTHS
    }
    aligned_month = {month: {} for month in MONTHS}
    for year in range(start, end + 1):
        year_dates = expected_dates(calendar, year, year)
        precip = complete_values(records, year_dates, "prcp")
        tmax = complete_values(records, year_dates, "tmax")
        tmin = complete_values(records, year_dates, "tmin")
        if precip is not None:
            annual["precip_total_mm"][year] = row_sum(precip)
            annual["r1mm_wet_day_count"][year] = float(
                sum(value >= R1MM for value in precip)
            )
            annual["max_daily_precip_mm"][year] = max(precip)
        if tmax is not None:
            annual["tmax_mean_c"][year] = mean(tmax)
        if tmin is not None:
            annual["tmin_mean_c"][year] = mean(tmin)
        for month_index, month in enumerate(MONTHS, 1):
            dates = [date for date in year_dates if date[1] == month_index]
            p = complete_values(records, dates, "prcp")
            tx = complete_values(records, dates, "tmax")
            tn = complete_values(records, dates, "tmin")
            if p is not None:
                wet = [value for value in p if value >= R1MM]
                monthly[month]["precip_total_mm"][year] = row_sum(p)
                monthly[month]["r1mm_wet_day_count"][year] = float(len(wet))
                if wet:
                    monthly[month]["r1mm_wet_day_mean_amount_mm"][year] = mean(wet)
            if tx is not None:
                monthly[month]["tmax_mean_c"][year] = mean(tx)
            if tn is not None:
                monthly[month]["tmin_mean_c"][year] = mean(tn)
            if p is not None and tx is not None and tn is not None:
                aligned_month[month][year] = (row_sum(p), mean(tx), mean(tn))
    return annual, monthly, aligned_month


def paired_values(left, right):
    years = sorted(set(left).intersection(right))
    return [left[year] for year in years], [right[year] for year in years]


def month_matrix(monthly, variable, use_detrended):
    series = []
    for month in MONTHS:
        values = monthly[month][variable]
        series.append(detrend(values) if use_detrended else values)
    covariance_rows = []
    correlation_rows = []
    count_rows = []
    for left in series:
        covariance_row = []
        correlation_row = []
        count_row = []
        for right in series:
            xs, ys = paired_values(left, right)
            covariance_row.append(covariance(xs, ys))
            correlation_row.append(pearson(xs, ys))
            count_row.append(len(xs))
        covariance_rows.append(covariance_row)
        correlation_rows.append(correlation_row)
        count_rows.append(count_row)
    return {
        "covariance": covariance_rows,
        "n_pairs": count_rows,
        "pearson_correlation": correlation_rows,
    }


def cross_variable_by_month(aligned_month, use_detrended):
    result = {}
    for month in MONTHS:
        years = sorted(aligned_month[month])
        columns = [
            {year: aligned_month[month][year][index] for year in years}
            for index in range(3)
        ]
        if use_detrended:
            columns = [detrend(column) for column in columns]
        values = [[column[year] for year in years] for column in columns]
        result[month] = {
            "precip_tmax": corr_cell(values[0], values[1]),
            "precip_tmin": corr_cell(values[0], values[2]),
            "tmax_tmin": corr_cell(values[1], values[2]),
        }
    return result


def series_dependence(series):
    years = sorted(series)
    consecutive = [(year, year + 1) for year in years if year + 1 in series]
    return {
        "lag_one": corr_cell(
            [series[left] for left, _ in consecutive],
            [series[right] for _, right in consecutive],
        ),
        "n_years": len(years),
        "period_ge_4y_power_fraction": low_frequency(series),
    }


def dependence_variant(annual, monthly, aligned_month, use_detrended):
    annual_dependence = {}
    for variable in ("precip_total_mm", "tmax_mean_c", "tmin_mean_c"):
        values = annual[variable]
        if use_detrended:
            values = detrend(values)
        annual_dependence[variable] = series_dependence(values)
    return {
        "annual": annual_dependence,
        "cross_variable_by_month": cross_variable_by_month(
            aligned_month, use_detrended
        ),
        "precip_cross_month": month_matrix(monthly, "precip_total_mm", use_detrended),
        "tmax_cross_month": month_matrix(monthly, "tmax_mean_c", use_detrended),
        "tmin_cross_month": month_matrix(monthly, "tmin_mean_c", use_detrended),
    }


def dependence(annual, monthly, aligned_month):
    return {
        "detrended": dependence_variant(annual, monthly, aligned_month, True),
        "raw": dependence_variant(annual, monthly, aligned_month, False),
    }


def precipitation_structure(records, calendar, start, end):
    dates = [
        date
        for date in sorted(records)
        if start <= date[0] <= end and "prcp" in records[date]
    ]
    expected = expected_dates(calendar, start, end)
    observed = set(dates)
    missing_days = 0
    missing_gap_runs = 0
    prior_missing = False
    for date in expected:
        missing = date not in observed
        missing_days += int(missing)
        if missing and not prior_missing:
            missing_gap_runs += 1
        prior_missing = missing
    wet_amounts = [
        records[date]["prcp"] for date in dates if records[date]["prcp"] >= R1MM
    ]
    wet_spells = {month: [] for month in MONTHS}
    dry_spells = {month: [] for month in MONTHS}
    run, start_month, prior_state, prior_date = 0, None, None, None
    adjacent_x, adjacent_y = [], []
    prior_wet_amount = None

    def finish_spell():
        if run:
            target = wet_spells if prior_state else dry_spells
            target[MONTHS[start_month - 1]].append(float(run))

    for date in dates:
        adjacent = prior_date is not None and next_date(calendar, prior_date) == date
        wet = records[date]["prcp"] >= R1MM
        if not adjacent or wet != prior_state:
            finish_spell()
            run = 1
            start_month = date[1]
        else:
            run += 1
        amount = records[date]["prcp"] if wet else None
        if adjacent and wet and prior_state and prior_wet_amount is not None:
            adjacent_x.append(prior_wet_amount)
            adjacent_y.append(amount)
        prior_wet_amount, prior_state, prior_date = amount, wet, date
    finish_spell()

    maxima_by_window = {window: {} for window in (1, 3, 5)}
    for window in maxima_by_window:
        for end_index in range(window - 1, len(dates)):
            window_dates = dates[end_index + 1 - window : end_index + 1]
            if any(
                next_date(calendar, left) != right
                for left, right in zip(window_dates, window_dates[1:])
            ):
                continue
            total = row_sum(records[date]["prcp"] for date in window_dates)
            end_year = window_dates[-1][0]
            prior_maximum = maxima_by_window[window].get(end_year)
            if prior_maximum is None or total > prior_maximum:
                maxima_by_window[window][end_year] = total

    complete_years = []
    for year in range(start, end + 1):
        if (
            complete_values(records, expected_dates(calendar, year, year), "prcp")
            is not None
        ):
            complete_years.append(year)
    maxima = []
    for year in complete_years:
        row = {"year": year}
        for window in (1, 3, 5):
            row[f"max_{window}_day_mm"] = maxima_by_window[window].get(year)
        maxima.append(row)

    def spell_summary(spells):
        whole = [value for month in MONTHS for value in spells[month]]
        return {
            "by_start_month": {month: distribution(spells[month]) for month in MONTHS},
            "whole_run": distribution(whole),
        }

    return {
        "adjacent_wet_day_amount": corr_cell(adjacent_x, adjacent_y),
        "annual_max_1_day_mm": distribution(
            [row["max_1_day_mm"] for row in maxima if row["max_1_day_mm"] is not None]
        ),
        "annual_max_3_day_mm": distribution(
            [row["max_3_day_mm"] for row in maxima if row["max_3_day_mm"] is not None]
        ),
        "annual_max_5_day_mm": distribution(
            [row["max_5_day_mm"] for row in maxima if row["max_5_day_mm"] is not None]
        ),
        "annual_rolling_maxima": maxima,
        "coverage": {
            "expected_days": len(expected),
            "missing_days": missing_days,
            "missing_gap_runs": missing_gap_runs,
            "observed_precip_days": len(dates),
        },
        "dry_spells_days": spell_summary(dry_spells),
        "threshold_mm": R1MM,
        "wet_day_amount_mm": distribution(wet_amounts),
        "wet_spells_days": spell_summary(wet_spells),
    }


def fraction_cell(rows):
    if not rows:
        return {
            "fraction": None,
            "freezing_air_day_count": 0,
            "n_days": 0,
            "precipitation_on_freezing_air_days_mm": None,
            "total_precipitation_mm": None,
        }
    denominator = row_sum(value[0] for value in rows)
    freezing = [value for value in rows if value[1] <= 0.0]
    numerator = row_sum(value[0] for value in freezing)
    return {
        "fraction": (
            None if denominator == 0.0 else max(0.0, min(1.0, numerator / denominator))
        ),
        "freezing_air_day_count": len(freezing),
        "n_days": len(rows),
        "precipitation_on_freezing_air_days_mm": numerator,
        "total_precipitation_mm": denominator,
    }


def count_dispersion(values):
    center = mean(values)
    spread = sample_sd(values)
    return {
        "cv": None if center in (None, 0.0) or spread is None else spread / center,
        "mean": center,
        "n_years": len(values),
        "sd": spread,
    }


def winter_proxy(records, calendar, start, end):
    rows = []
    for date in sorted(records):
        if not start <= date[0] <= end:
            continue
        values = records[date]
        if all(name in values for name in ("prcp", "tmax", "tmin")):
            rows.append((date, values["prcp"], (values["tmax"] + values["tmin"]) / 2.0))
    months = {
        month: fraction_cell([(p, t) for date, p, t in rows if date[1] == index])
        for index, month in enumerate(MONTHS, 1)
    }
    winter = [(p, t) for date, p, t in rows if date[1] in (12, 1, 2) and p >= R1MM]
    transitions = [
        right[0]
        for left, right in zip(rows, rows[1:])
        if next_date(calendar, left[0]) == right[0]
        and (left[2] <= 0.0) != (right[2] <= 0.0)
    ]
    by_year = []
    for year in range(start, end + 1):
        selected = [row for row in rows if row[0][0] == year]
        expected = expected_dates(calendar, year, year)
        by_year.append(
            {
                "complete_year": len(selected) == len(expected)
                and [row[0] for row in selected] == expected,
                "freeze_thaw_air_temperature_proxy_cycles": sum(
                    date[0] == year for date in transitions
                ),
                "n_days": len(selected),
                "precipitation_on_freezing_air_days": fraction_cell(
                    [(p, t) for _, p, t in selected]
                ),
                "year": year,
            }
        )
    complete_cycles = [
        float(row["freeze_thaw_air_temperature_proxy_cycles"])
        for row in by_year
        if row["complete_year"]
    ]
    return {
        "by_month": months,
        "djf_r1mm_precip_mean_air_temperature": corr_cell(
            [p for p, _ in winter], [t for _, t in winter]
        ),
        "freeze_thaw_air_temperature_proxy_cycles": count_dispersion(complete_cycles),
        "per_year": by_year,
        "precipitation_on_freezing_air_days": fraction_cell(
            [(p, t) for _, p, t in rows]
        ),
    }


def period_targets(records, calendar, bounds):
    start, end = bounds
    annual, monthly, aligned = aggregate_series(records, calendar, start, end)
    return {
        "annual": {
            name: dispersion(values, cv=name not in ("tmax_mean_c", "tmin_mean_c"))
            for name, values in annual.items()
        },
        "dependence": dependence(annual, monthly, aligned),
        "monthly": {
            month: {
                name: dispersion(
                    values,
                    cv=name
                    in (
                        "precip_total_mm",
                        "r1mm_wet_day_count",
                        "r1mm_wet_day_mean_amount_mm",
                    ),
                )
                for name, values in monthly[month].items()
            }
            for month in MONTHS
        },
        "period": {"end_year": end, "start_year": start},
        "precipitation_structure": precipitation_structure(
            records, calendar, start, end
        ),
        "storm_descriptors": {
            "availability": "unavailable",
            "reason": "daily Daymet/GHCN sources do not contain duration, time-to-peak fraction, or peak-intensity ratio",
        },
        "winter_air_temperature_proxies": winter_proxy(records, calendar, start, end),
    }


def main():
    global METRICS_HELPER
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--metrics-helper", type=Path, required=True)
    args = parser.parse_args()
    script = Path(__file__).resolve()
    repo = script.parents[5]
    config_path = args.config or script.with_name("corpus-config-v1.json")
    source_path = args.source_manifest or script.with_name("source-manifest-v1.json")
    output = args.output or script.with_name("observed-target-corpus-v1.json")
    METRICS_HELPER = args.metrics_helper.resolve(strict=True)
    if not METRICS_HELPER.is_file():
        raise FileNotFoundError(METRICS_HELPER)
    config = json.loads(config_path.read_text())
    source_manifest = json.loads(source_path.read_text())
    if config.get("config_version") != 1:
        raise ValueError("unsupported corpus config version")
    if source_manifest.get("source_manifest_schema_version") != 1:
        raise ValueError("unsupported source-manifest schema version")
    if source_manifest.get("config_sha256") != sha256(config_path.read_bytes()):
        raise ValueError("source manifest does not bind the corpus config")
    if source_manifest.get("fixed_periods") != config.get("periods"):
        raise ValueError("source manifest fixed periods differ from config")
    if source_manifest.get("station_collection") != config.get("station_collection"):
        raise ValueError("source manifest station collection differs from config")
    source_by_station = {row["station_id"]: row for row in source_manifest["stations"]}
    if len(source_by_station) != len(source_manifest["stations"]):
        raise ValueError("duplicate station identifier in source manifest")
    if set(source_by_station) != {
        station["station_id"] for station in config["stations"]
    }:
        raise ValueError("source manifest station identifiers differ from config")
    stations = []
    for station in config["stations"]:
        source_meta = source_by_station[station["station_id"]]["sources"]
        targets = {}
        for kind in ("daymet", "ghcn"):
            metadata = source_meta[kind]
            if metadata.get("availability") == "unavailable":
                targets[kind] = metadata
                continue
            archive = repo / metadata["archive_path"]
            if sha256(archive.read_bytes()) != metadata["archive_sha256"]:
                raise ValueError(f"archive hash mismatch: {archive}")
            records, checked = archive_records(archive, kind, station)
            if checked["source_sha256"] != metadata["source_sha256"]:
                raise ValueError(f"source hash mismatch: {archive}")
            if checked["calendar"] != metadata["calendar"]:
                raise ValueError(f"source calendar mismatch: {archive}")
            logical = logical_records_bytes(
                records,
                config["periods"]["full"][0],
                config["periods"]["full"][1],
            )
            if sha256(logical) != metadata["fixed_window_logical_records_sha256"]:
                raise ValueError(f"fixed-window logical hash mismatch: {archive}")
            targets[kind] = {
                "availability": "available",
                "periods": {
                    name: period_targets(records, str(metadata["calendar"]), bounds)
                    for name, bounds in config["periods"].items()
                },
                "source_identity": {
                    key: metadata[key]
                    for key in (
                        "archive_sha256",
                        "calendar",
                        "fixed_window_logical_records_sha256",
                        "source_id",
                        "source_sha256",
                    )
                },
            }
        stations.append(
            {
                "catalog_elevation_ft": station["catalog_elevation_ft"],
                "latitude": station["latitude"],
                "longitude": station["longitude"],
                "name": station["name"],
                "regime": station["regime"],
                "sources": targets,
                "station_id": station["station_id"],
                "station_parameter": {
                    "collection": "us-2015",
                    "collection_version": "2026.07",
                    "legacy_par_sha256": station["par_sha256"],
                    "model": "fixed_monthly_5_32_3",
                },
            }
        )
    corpus = {
        "conventions": {
            "air_freezing_threshold_c": 0.0,
            "detrending": "OLS linear residual by integer year",
            "low_frequency": "centered DFT positive-frequency power fraction with period >= 4 years; contiguous annual series required",
            "precipitation_wet_day_threshold_mm": R1MM,
            "quantile": "empirical inverse-CDF nearest rank: sorted[ceil(p*n)-1]",
            "rolling_maxima": "consecutive source-calendar windows attributed to end year; distributions retain complete precipitation years",
        },
        "corpus_id": "cligen-a5a-observed-v1",
        "fixed_periods": config["periods"],
        "metrics_version": 3,
        "observed_target_corpus_schema_version": 1,
        "source_manifest_sha256": sha256(source_path.read_bytes()),
        "station_collection": config["station_collection"],
        "stations": stations,
    }
    write_canonical_json(output, corpus)
    print(output)


if __name__ == "__main__":
    main()
