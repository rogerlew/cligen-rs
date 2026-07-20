#!/usr/bin/env python3
"""Frozen realized temporal metrics shared by all A10M5R4R2 arms."""

from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from typing import Any, Iterable

import numpy as np


def _mean(values: np.ndarray) -> float:
    return float(np.mean(values, dtype=np.float64))


def _std(values: np.ndarray) -> float:
    return float(np.std(values, ddof=1, dtype=np.float64)) if len(values) > 1 else 0.0


def _quantile(values: np.ndarray, probability: float) -> float:
    return float(np.quantile(values.astype(np.float64), probability))


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3 or _std(left) == 0.0 or _std(right) == 0.0:
        return 0.0
    return float(np.corrcoef(left.astype(np.float64), right.astype(np.float64))[0, 1])


def _skew(values: np.ndarray) -> float:
    standard = float(np.std(values, dtype=np.float64))
    if standard == 0.0:
        return 0.0
    centered = values.astype(np.float64) - _mean(values)
    return float(np.mean((centered / standard) ** 3))


def _spell_survival(wet: np.ndarray, dates: list[dt.date], target: bool, length: int) -> float:
    runs: list[int] = []
    current = 0
    previous: dt.date | None = None
    for value, date in zip(wet, dates):
        contiguous = previous is None or date == previous + dt.timedelta(days=1)
        if not contiguous or bool(value) != target:
            if current:
                runs.append(current)
            current = 0
        if bool(value) == target:
            current += 1
        previous = date
    if current:
        runs.append(current)
    return float(sum(run >= length for run in runs) / len(runs)) if runs else 0.0


def _annual_groups(dates: list[dt.date]) -> dict[int, np.ndarray]:
    groups: dict[int, list[int]] = defaultdict(list)
    for index, date in enumerate(dates):
        groups[date.year].append(index)
    return {year: np.asarray(indices, dtype=np.int64) for year, indices in sorted(groups.items())}


def realized_metrics(
    dates: Iterable[dt.date],
    precipitation_mm: np.ndarray,
    tmax_c: np.ndarray,
    tmin_c: np.ndarray,
    peak_rate_mm_per_hour: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute the prospectively registered common temporal metric vector."""
    date_list = list(dates)
    arrays = [np.asarray(value, dtype=np.float64) for value in (precipitation_mm, tmax_c, tmin_c)]
    if any(len(value) != len(date_list) for value in arrays):
        raise RuntimeError("daily metric array length mismatch")
    precipitation, tmax, tmin = arrays
    if not len(date_list) or not all(np.isfinite(value).all() for value in arrays):
        raise RuntimeError("daily metric input is empty or non-finite")
    if np.any(precipitation < 0.0) or np.any(tmax < tmin):
        raise RuntimeError("daily metric support failure")
    peak = None if peak_rate_mm_per_hour is None else np.asarray(peak_rate_mm_per_hour, dtype=np.float64)
    if peak is not None and (len(peak) != len(date_list) or not np.isfinite(peak).all() or np.any(peak < 0.0)):
        raise RuntimeError("peak-rate metric support failure")

    output: dict[str, float] = {}
    monthly: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, date in enumerate(date_list):
        monthly[(date.year, date.month)].append(index)
    for month in range(1, 13):
        groups = [np.asarray(indices, dtype=np.int64) for (year, value), indices in sorted(monthly.items()) if value == month]
        totals = np.asarray([np.sum(precipitation[group], dtype=np.float64) for group in groups])
        tx = np.asarray([np.mean(tmax[group], dtype=np.float64) for group in groups])
        tn = np.asarray([np.mean(tmin[group], dtype=np.float64) for group in groups])
        prefix = f"monthly.{month:02d}"
        mean = _mean(totals)
        standard = _std(totals)
        output[f"{prefix}.precipitation_mean"] = mean
        output[f"{prefix}.precipitation_standard_deviation"] = standard
        output[f"{prefix}.precipitation_coefficient_of_variation"] = standard / mean if mean > 0.0 else 0.0
        output[f"{prefix}.precipitation_skew"] = _skew(totals)
        output[f"{prefix}.precipitation_dry_frequency"] = float(np.mean(totals < 1.0))
        for label, probability in (("q10", 0.10), ("q50", 0.50), ("q90", 0.90), ("q95", 0.95)):
            output[f"{prefix}.precipitation_{label}"] = _quantile(totals, probability)
        output[f"{prefix}.tmax_mean"] = _mean(tx)
        output[f"{prefix}.tmax_standard_deviation"] = _std(tx)
        output[f"{prefix}.tmin_mean"] = _mean(tn)
        output[f"{prefix}.tmin_standard_deviation"] = _std(tn)
        output[f"{prefix}.tmax_tmin_correlation"] = _correlation(tx, tn)

    annual = _annual_groups(date_list)
    years = list(annual)
    ap = np.asarray([np.sum(precipitation[annual[year]], dtype=np.float64) for year in years])
    atx = np.asarray([np.mean(tmax[annual[year]], dtype=np.float64) for year in years])
    atn = np.asarray([np.mean(tmin[annual[year]], dtype=np.float64) for year in years])
    output.update({
        "annual.precipitation_mean": _mean(ap),
        "annual.precipitation_standard_deviation": _std(ap),
        "annual.precipitation_q95": _quantile(ap, 0.95),
        "annual.tmax_mean": _mean(atx),
        "annual.tmax_standard_deviation": _std(atx),
        "annual.tmin_mean": _mean(atn),
        "annual.tmin_standard_deviation": _std(atn),
        "annual.precipitation_lag1": _correlation(ap[:-1], ap[1:]),
        "annual.tmax_lag1": _correlation(atx[:-1], atx[1:]),
        "annual.tmin_lag1": _correlation(atn[:-1], atn[1:]),
        "annual.precipitation_tmax_correlation": _correlation(ap, atx),
        "annual.precipitation_tmin_correlation": _correlation(ap, atn),
        "annual.tmax_tmin_correlation": _correlation(atx, atn),
    })

    wet = precipitation >= 1.0
    ww = wd = dw = dd = 0
    for index in range(1, len(date_list)):
        if date_list[index] != date_list[index - 1] + dt.timedelta(days=1):
            continue
        previous, current = bool(wet[index - 1]), bool(wet[index])
        ww += previous and current
        wd += previous and not current
        dw += not previous and current
        dd += not previous and not current
    output["occurrence.p_wet_given_wet"] = ww / (ww + wd) if ww + wd else 0.0
    output["occurrence.p_wet_given_dry"] = dw / (dw + dd) if dw + dd else 0.0
    for target, label in ((True, "wet"), (False, "dry")):
        for length in (3, 7):
            output[f"occurrence.{label}_spell_survival_{length}"] = _spell_survival(wet, date_list, target, length)
    seasons = {"djf": {12, 1, 2}, "mam": {3, 4, 5}, "jja": {6, 7, 8}, "son": {9, 10, 11}}
    frequencies = [float(np.mean(wet[[date.month in months for date in date_list]])) for months in seasons.values()]
    output["occurrence.seasonal_wet_frequency_range"] = max(frequencies) - min(frequencies)

    if peak is not None:
        maxima = np.asarray([np.max(peak[annual[year]]) for year in years])
        output["intensity.annual_peak_rate_q95_mm_per_hour"] = _quantile(maxima, 0.95)
    if not all(math.isfinite(value) for value in output.values()):
        raise RuntimeError("non-finite realized metric")
    return output
