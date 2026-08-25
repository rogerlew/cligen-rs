#!/usr/bin/env python3
"""Fit, generate, and adjudicate the frozen A11 research candidate."""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import math
import struct
import tarfile
import time
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
DAYMET_ROOT = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort/raw/training/daymet-v1"
NORMAL_ROOT = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort/artifacts/normal-conditioning"
SITES = ROOT / "docs/work-packages/20260718-a10m5r4r2-realized-temporal-adjudication/artifacts/sites.json"
PRIOR_RESULT = ROOT / "docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/artifacts/execution/temporal-result.json"
FREEZE = PACKAGE / "design-freeze-v1.json"
NORMAL = NormalDist()
MONTHS = range(1, 13)
FIELDS = ("prcp", "tmax", "tmin")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    partial.replace(path)


def seed(point: str, member: int, domain: str) -> int:
    payload = f"a11-v1\0{point}\0{member}\0{domain}".encode()
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def rng(point: str, member: int, domain: str) -> np.random.Generator:
    return np.random.Generator(np.random.Philox(seed(point, member, domain)))


def iter_records() -> Any:
    for path in sorted(DAYMET_ROOT.glob("daymet-*.tar.gz")):
        with tarfile.open(path, "r:gz") as archive:
            for member in sorted(archive.getmembers(), key=lambda value: value.name.encode()):
                handle = archive.extractfile(member)
                if handle is None:
                    raise RuntimeError(f"unreadable member: {path.name}/{member.name}")
                yield path, json.load(handle)


def validate_record(record: dict[str, Any]) -> tuple[list[dt.date], np.ndarray, np.ndarray, np.ndarray]:
    dates = [dt.date.fromisoformat(value) for value in record["dates"]]
    observed = record["source_observed"]
    if (
        record.get("calendar_transform_id") != "daymet_official_365_v1"
        or len(dates) != 10958
        or len(observed) != 10958
        or sum(value is True for value in observed) != 10950
    ):
        raise RuntimeError(f"calendar contract failure: {record.get('point_id')}")
    keep = np.asarray([
        value is True and all(record["fields"][name][index] is not None for name in FIELDS)
        for index, value in enumerate(observed)
    ])
    if int(np.sum(keep)) != 10950:
        raise RuntimeError(f"core-field mask failure: {record.get('point_id')}")
    for index, date in enumerate(dates):
        if date.month == 2 and date.day == 29 and not keep[index]:
            raise RuntimeError("February 29 must be observed")
        if date.month == 12 and date.day == 31 and calendar.isleap(date.year) and keep[index]:
            raise RuntimeError("leap-year December 31 must be masked")
    arrays = [np.asarray([record["fields"][name][i] for i in np.flatnonzero(keep)], dtype=np.float64) for name in FIELDS]
    return [date for date, include in zip(dates, keep) if include], *arrays


def month_indices(dates: list[dt.date]) -> dict[tuple[int, int], np.ndarray]:
    groups: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, date in enumerate(dates):
        groups[(date.year, date.month)].append(index)
    return {key: np.asarray(value, dtype=np.int64) for key, value in groups.items()}


def safe_corr(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def fit_surface() -> tuple[dict[str, Any], dict[str, Any]]:
    targets: dict[str, list[np.ndarray]] = defaultdict(list)
    textures: dict[str, dict[str, list[list[float]]]] = defaultdict(
        lambda: {name: [[] for _ in MONTHS] for name in ("temp_sd", "temp_phi", "amount_sigma", "amount_phi", "dtr_sigma", "dtr_phi", "pww", "pwd")}
    )
    points: dict[str, int] = defaultdict(int)
    calendar_count = 0
    shard_hashes = {path.name: digest(path) for path in sorted(DAYMET_ROOT.glob("daymet-*.tar.gz"))}
    for _, record in iter_records():
        dates, prcp, tmax, tmin = validate_record(record)
        calendar_count += 1
        if record["role"] != "candidate_fit":
            continue
        regime = record["regime"]
        points[regime] += 1
        groups = month_indices(dates)
        year_rows = []
        for year in range(1980, 2010):
            values = [[], [], [], []]
            for month in MONTHS:
                idx = groups[(year, month)]
                p = prcp[idx]
                mean_temp = (tmax[idx] + tmin[idx]) / 2.0
                dtr = tmax[idx] - tmin[idx]
                wet = p >= 1.0
                total = float(np.sum(p))
                values[0].append(math.log1p(total))
                values[1].append(float(np.mean(wet)))
                values[2].append(float(np.mean(mean_temp)))
                values[3].append(math.log(max(float(np.mean(dtr)), 1e-6)))
                residual = mean_temp - float(np.mean(mean_temp))
                log_dtr = np.log(np.maximum(dtr, 1e-6))
                wet_amounts = p[wet]
                log_amount = np.log(np.maximum(wet_amounts, 1e-6))
                slot = month - 1
                textures[regime]["temp_sd"][slot].append(float(np.std(residual, ddof=1)))
                textures[regime]["temp_phi"][slot].append(safe_corr(residual[:-1], residual[1:]))
                textures[regime]["dtr_sigma"][slot].append(float(np.std(log_dtr, ddof=1)))
                textures[regime]["dtr_phi"][slot].append(safe_corr(log_dtr[:-1], log_dtr[1:]))
                if len(log_amount) >= 2:
                    textures[regime]["amount_sigma"][slot].append(float(np.std(log_amount, ddof=1)))
                    textures[regime]["amount_phi"][slot].append(safe_corr(log_amount[:-1], log_amount[1:]))
                previous = wet[:-1]
                current = wet[1:]
                ww = int(np.sum(previous & current)); wd = int(np.sum(previous & ~current))
                dw = int(np.sum(~previous & current)); dd = int(np.sum(~previous & ~current))
                textures[regime]["pww"][slot].append(ww / (ww + wd) if ww + wd else 0.0)
                textures[regime]["pwd"][slot].append(dw / (dw + dd) if dw + dd else 0.0)
            year_rows.append(np.concatenate([np.asarray(value, dtype=np.float64) for value in values]))
        targets[regime].extend(year_rows)
    if calendar_count != 1440 or any(value != 200 for value in points.values()):
        raise RuntimeError(f"candidate-fit roster failure: calendars={calendar_count}, points={dict(points)}")

    surface: dict[str, Any] = {}
    for regime in sorted(targets):
        raw = np.vstack(targets[regime])
        if raw.shape != (6000, 48):
            raise RuntimeError(f"target shape failure: {regime}/{raw.shape}")
        latent = np.empty_like(raw)
        for column in range(raw.shape[1]):
            order = np.argsort(raw[:, column], kind="stable")
            ranks = np.empty(len(raw), dtype=np.float64)
            ranks[order] = np.arange(1, len(raw) + 1)
            latent[:, column] = [NORMAL.inv_cdf((rank - 0.5) / len(raw)) for rank in ranks]
        requested = np.corrcoef(latent, rowvar=False)
        requested = (requested + requested.T) / 2.0
        eigenvalues, eigenvectors = np.linalg.eigh(requested)
        clipped = np.maximum(eigenvalues, 1e-10)
        effective = (eigenvectors * clipped) @ eigenvectors.T
        diagonal = np.sqrt(np.diag(effective))
        effective = effective / np.outer(diagonal, diagonal)
        effective = (effective + effective.T) / 2.0
        row_texture = {}
        for name, months in textures[regime].items():
            defaults = {"temp_sd": 1.0, "amount_sigma": 0.8, "dtr_sigma": 0.25, "pww": 0.4, "pwd": 0.2}.get(name, 0.0)
            row_texture[name] = [float(np.median(values)) if values else defaults for values in months]
        for name in ("temp_phi", "amount_phi", "dtr_phi"):
            row_texture[name] = [float(np.clip(value, -0.8, 0.8)) for value in row_texture[name]]
        for name in ("pww", "pwd"):
            row_texture[name] = [float(np.clip(value, 1e-6, 1.0 - 1e-6)) for value in row_texture[name]]
        raw_p = np.expm1(raw[:, :12])
        raw_t = raw[:, 24:36]
        raw_dtr = np.exp(raw[:, 36:48])
        surface[regime] = {
            "copula_correlation": effective.tolist(),
            "eigenvalue_min_requested": float(np.min(eigenvalues)),
            "eigenvalue_min_effective": float(np.min(np.linalg.eigvalsh(effective))),
            "frobenius_adjustment": float(np.linalg.norm(effective - requested, ord="fro")),
            "marginals": [np.sort(raw[:, column]).tolist() for column in range(48)],
            "monthly_precip_mean": np.mean(raw_p, axis=0).tolist(),
            "monthly_tmean_mean": np.mean(raw_t, axis=0).tolist(),
            "monthly_dtr_mean": np.mean(raw_dtr, axis=0).tolist(),
            "requested_annual_precip_variance": float(np.var(np.sum(raw_p, axis=1), ddof=1)),
            "effective_annual_precip_variance": float(np.ones(12) @ np.cov(raw_p, rowvar=False, ddof=1) @ np.ones(12)),
            "requested_annual_tmean_variance": float(np.var(np.mean(raw_t, axis=1), ddof=1)),
            "texture": row_texture,
        }
    preflight = {
        "schema_version": "a11-calendar-preflight-1",
        "calendar_objects": calendar_count,
        "candidate_fit_objects": sum(points.values()),
        "fit_validation_objects": calendar_count - sum(points.values()),
        "axis_rows_per_object": 10958,
        "observed_rows_per_object": 10950,
        "masked_leap_december_31_per_object": 8,
        "february_29_observed": True,
        "window_start_inclusive": "1980-01-01",
        "window_end_inclusive": "2009-12-31",
        "mask_based_eligibility": True,
        "shard_count": len(shard_hashes),
        "shard_manifest_sha256": canonical_digest(shard_hashes),
        "valid": True,
    }
    return surface, preflight


def prism_normals(point_id: str) -> np.ndarray:
    index = json.loads((NORMAL_ROOT / "normal-conditioning-index.json").read_text())
    position = index["point_ids"].index(f"temporal/{point_id}")
    normalized = struct.unpack_from("<36f", (NORMAL_ROOT / "normal-conditioning.f32le").read_bytes(), position * 144)
    normalizer = struct.unpack("<72d", (NORMAL_ROOT / "normalizer.f64le").read_bytes())
    means = np.asarray(normalizer[:36]); scales = np.asarray(normalizer[36:])
    return means + scales * np.asarray(normalized)


def nearest_quantiles(marginals: list[list[float]], latent: np.ndarray) -> np.ndarray:
    output = np.empty_like(latent)
    for column, values in enumerate(marginals):
        probabilities = np.asarray([NORMAL.cdf(value) for value in latent[:, column]])
        output[:, column] = np.quantile(np.asarray(values), probabilities, method="linear")
    return output


def markov_bridge(days: int, count: int, start_wet: bool, pww: float, pwd: float, generator: np.random.Generator) -> np.ndarray:
    if count < 0 or count > days:
        raise RuntimeError("wet count outside month support")
    probabilities = np.zeros((days + 1, count + 1, 2), dtype=np.float64)
    probabilities[days, 0, :] = 1.0
    for position in range(days - 1, -1, -1):
        remaining = days - position
        for needed in range(min(count, remaining) + 1):
            for previous in (0, 1):
                wet_probability = pww if previous else pwd
                value = (1.0 - wet_probability) * probabilities[position + 1, needed, 0]
                if needed:
                    value += wet_probability * probabilities[position + 1, needed - 1, 1]
                probabilities[position, needed, previous] = value
    if probabilities[0, count, int(start_wet)] <= 0.0:
        raise RuntimeError("zero-probability Markov bridge")
    output = np.zeros(days, dtype=bool)
    needed = count; previous = int(start_wet)
    for position in range(days):
        wet_probability = pww if previous else pwd
        wet_weight = wet_probability * probabilities[position + 1, needed - 1, 1] if needed else 0.0
        dry_weight = (1.0 - wet_probability) * probabilities[position + 1, needed, 0]
        choose_wet = generator.random() < wet_weight / (wet_weight + dry_weight)
        output[position] = choose_wet
        needed -= int(choose_wet); previous = int(choose_wet)
    if int(np.sum(output)) != count:
        raise RuntimeError("Markov bridge count failure")
    return output


def ar1(days: int, phi: float, generator: np.random.Generator) -> np.ndarray:
    innovations = generator.standard_normal(days)
    output = np.empty(days, dtype=np.float64)
    output[0] = innovations[0]
    scale = math.sqrt(max(1.0 - phi * phi, 1e-12))
    for index in range(1, days):
        output[index] = phi * output[index - 1] + scale * innovations[index]
    return output


def dates_for_years(begin: int, years: int) -> list[dt.date]:
    start = dt.date(begin, 1, 1); end = dt.date(begin + years, 1, 1)
    return [start + dt.timedelta(days=index) for index in range((end - start).days)]


def generate_stream(site: dict[str, Any], member: int, fit: dict[str, Any]) -> tuple[list[dt.date], np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    point = site["point_id"]; regime = site["regime"]
    normals = prism_normals(point)
    prism_p = normals[:12]; prism_tx = normals[12:24]; prism_tn = normals[24:36]
    prism_t = (prism_tx + prism_tn) / 2.0; prism_dtr = prism_tx - prism_tn
    row = fit[regime]
    correlation = np.asarray(row["copula_correlation"])
    eigenvalues, eigenvectors = np.linalg.eigh(correlation)
    root = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0.0)))
    target_rng = rng(point, member, "target")
    latent = target_rng.standard_normal((100, 48)) @ root.T
    targets = nearest_quantiles(row["marginals"], latent)
    target_p = np.expm1(targets[:, :12]) * prism_p / np.asarray(row["monthly_precip_mean"])
    target_wet = targets[:, 12:24]
    target_t = targets[:, 24:36] + prism_t - np.asarray(row["monthly_tmean_mean"])
    target_dtr = np.exp(targets[:, 36:48]) * prism_dtr / np.asarray(row["monthly_dtr_mean"])
    texture = row["texture"]
    all_dates = dates_for_years(2001, 100)
    precipitation = np.zeros(len(all_dates)); tmax = np.zeros(len(all_dates)); tmin = np.zeros(len(all_dates))
    groups = month_indices(all_dates)
    previous_wet = False
    occurrence_rng = rng(point, member, "occurrence")
    amount_rng = rng(point, member, "amount")
    temperature_rng = rng(point, member, "temperature")
    dtr_rng = rng(point, member, "dtr")
    support_adjustments = 0
    for year_index, year in enumerate(range(2001, 2101)):
        for month in MONTHS:
            slot = month - 1; indices = groups[(year, month)]; days = len(indices)
            total = max(float(target_p[year_index, slot]), 0.0)
            if total < 1.0:
                total = 0.0; count = 0
            else:
                proposed = int(round(float(target_wet[year_index, slot]) * days))
                count = min(days, max(1, proposed), int(math.floor(total)))
                support_adjustments += int(count != proposed)
            wet = markov_bridge(days, count, previous_wet, texture["pww"][slot], texture["pwd"][slot], occurrence_rng)
            previous_wet = bool(wet[-1])
            amounts = np.zeros(days)
            if count:
                weights = np.exp(texture["amount_sigma"][slot] * ar1(count, texture["amount_phi"][slot], amount_rng))
                amounts[wet] = 1.0 + (total - count) * weights / float(np.sum(weights))
            precipitation[indices] = amounts
            residual = ar1(days, texture["temp_phi"][slot], temperature_rng)
            residual -= float(np.mean(residual))
            sd = float(np.std(residual, ddof=1))
            if sd == 0.0:
                raise RuntimeError("zero temperature residual scale")
            residual *= texture["temp_sd"][slot] / sd
            log_range = texture["dtr_sigma"][slot] * ar1(days, texture["dtr_phi"][slot], dtr_rng)
            ranges = np.exp(log_range)
            ranges *= float(target_dtr[year_index, slot]) / float(np.mean(ranges))
            means = float(target_t[year_index, slot]) + residual
            tmax[indices] = means + ranges / 2.0; tmin[indices] = means - ranges / 2.0
            if abs(float(np.sum(amounts)) - total) > 1e-8 or abs(float(np.mean(means)) - target_t[year_index, slot]) > 1e-10:
                raise RuntimeError("conditional monthly target identity failure")
    if not (np.isfinite(precipitation).all() and np.isfinite(tmax).all() and np.isfinite(tmin).all() and np.all(precipitation >= 0.0) and np.all(tmax >= tmin)):
        raise RuntimeError("generated support failure")
    payload = np.column_stack((precipitation, tmax, tmin)).astype("<f4").tobytes()
    return all_dates, precipitation, tmax, tmin, {
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "row_count": len(all_dates),
        "support_adjusted_wet_counts": support_adjustments,
        "support": True,
    }


def mean(values: np.ndarray) -> float: return float(np.mean(values, dtype=np.float64))
def std(values: np.ndarray) -> float: return float(np.std(values, ddof=1, dtype=np.float64)) if len(values) > 1 else 0.0
def corr(left: np.ndarray, right: np.ndarray) -> float: return safe_corr(left.astype(np.float64), right.astype(np.float64))
def skew(values: np.ndarray) -> float:
    scale = float(np.std(values)); return 0.0 if scale == 0.0 else float(np.mean(((values - mean(values)) / scale) ** 3))


def spell(wet: np.ndarray, dates: list[dt.date], target: bool, length: int) -> float:
    runs = []; current = 0; previous = None
    for value, date in zip(wet, dates):
        if previous is None or date != previous + dt.timedelta(days=1) or bool(value) != target:
            if current: runs.append(current)
            current = 0
        if bool(value) == target: current += 1
        previous = date
    if current: runs.append(current)
    return float(sum(value >= length for value in runs) / len(runs)) if runs else 0.0


def metrics(dates: list[dt.date], p: np.ndarray, tx: np.ndarray, tn: np.ndarray) -> dict[str, float]:
    output: dict[str, float] = {}; monthly = month_indices(dates)
    for month in MONTHS:
        groups = [indices for (year, value), indices in sorted(monthly.items()) if value == month]
        totals = np.asarray([np.sum(p[index]) for index in groups]); txx = np.asarray([np.mean(tx[index]) for index in groups]); tnn = np.asarray([np.mean(tn[index]) for index in groups])
        prefix = f"monthly.{month:02d}"; pm = mean(totals); ps = std(totals)
        output.update({f"{prefix}.precipitation_mean": pm, f"{prefix}.precipitation_standard_deviation": ps, f"{prefix}.precipitation_coefficient_of_variation": ps / pm if pm > 0 else 0.0, f"{prefix}.precipitation_skew": skew(totals), f"{prefix}.precipitation_dry_frequency": float(np.mean(totals < 1.0)), f"{prefix}.tmax_mean": mean(txx), f"{prefix}.tmax_standard_deviation": std(txx), f"{prefix}.tmin_mean": mean(tnn), f"{prefix}.tmin_standard_deviation": std(tnn), f"{prefix}.tmax_tmin_correlation": corr(txx, tnn)})
        for label, probability in (("q10", .1), ("q50", .5), ("q90", .9), ("q95", .95)):
            output[f"{prefix}.precipitation_{label}"] = float(np.quantile(totals, probability))
    annual = {year: np.asarray([i for i, date in enumerate(dates) if date.year == year]) for year in sorted({date.year for date in dates})}
    ap = np.asarray([np.sum(p[index]) for index in annual.values()]); atx = np.asarray([np.mean(tx[index]) for index in annual.values()]); atn = np.asarray([np.mean(tn[index]) for index in annual.values()])
    output.update({"annual.precipitation_mean": mean(ap), "annual.precipitation_standard_deviation": std(ap), "annual.precipitation_q95": float(np.quantile(ap, .95)), "annual.tmax_mean": mean(atx), "annual.tmax_standard_deviation": std(atx), "annual.tmin_mean": mean(atn), "annual.tmin_standard_deviation": std(atn), "annual.precipitation_lag1": corr(ap[:-1], ap[1:]), "annual.tmax_lag1": corr(atx[:-1], atx[1:]), "annual.tmin_lag1": corr(atn[:-1], atn[1:]), "annual.precipitation_tmax_correlation": corr(ap, atx), "annual.precipitation_tmin_correlation": corr(ap, atn), "annual.tmax_tmin_correlation": corr(atx, atn)})
    wet = p >= 1.0; ww = wd = dw = dd = 0
    for index in range(1, len(dates)):
        if dates[index] != dates[index - 1] + dt.timedelta(days=1): continue
        previous = bool(wet[index - 1]); current = bool(wet[index]); ww += previous and current; wd += previous and not current; dw += not previous and current; dd += not previous and not current
    output["occurrence.p_wet_given_wet"] = ww / (ww + wd) if ww + wd else 0.0; output["occurrence.p_wet_given_dry"] = dw / (dw + dd) if dw + dd else 0.0
    for target, label in ((True, "wet"), (False, "dry")):
        for length in (3, 7): output[f"occurrence.{label}_spell_survival_{length}"] = spell(wet, dates, target, length)
    seasons = ({12, 1, 2}, {3, 4, 5}, {6, 7, 8}, {9, 10, 11}); frequencies = [float(np.mean(wet[[date.month in months for date in dates]])) for months in seasons]
    output["occurrence.seasonal_wet_frequency_range"] = max(frequencies) - min(frequencies)
    if not all(math.isfinite(value) for value in output.values()): raise RuntimeError("non-finite metric")
    return output


def observed(site: dict[str, Any]) -> dict[str, float]:
    path = DAYMET_ROOT / site["daymet_shard"]
    with tarfile.open(path, "r:gz") as archive:
        handle = archive.extractfile(f"{site['point_id']}.json")
        if handle is None: raise RuntimeError("site missing from observation shard")
        record = json.load(handle)
    dates, p, tx, tn = validate_record(record)
    if record["role"] != "fit_validation": raise RuntimeError("development observation role failure")
    return metrics(dates, p, tx, tn)


def mean_metrics(streams: list[dict[str, float]]) -> dict[str, float]:
    return {key: float(np.mean([stream[key] for stream in streams])) for key in sorted(streams[0])}


def scaled_error(key: str, generated: float, actual: float) -> float:
    if "precipitation_" in key and any(name in key for name in ("mean", "standard_deviation", "q10", "q50", "q90", "q95")): return abs(math.log(generated + .1) - math.log(actual + .1)) / .25
    if "coefficient_of_variation" in key: return abs(generated - actual) / .25
    if "skew" in key: return abs(generated - actual) / .5
    if key.startswith("occurrence.") or "dry_frequency" in key: return abs(generated - actual) / .05
    if "correlation" in key or "lag1" in key: return abs(generated - actual) / .1
    if "tmax_mean" in key or "tmin_mean" in key: return abs(generated - actual)
    if "tmax_standard_deviation" in key or "tmin_standard_deviation" in key: return abs(generated - actual) / .5
    raise RuntimeError(f"unregistered metric: {key}")


def composite(streams: list[dict[str, float]], actual: dict[str, float]) -> float:
    generated = mean_metrics(streams); values = [scaled_error(key, generated[key], actual[key]) for key in generated]
    return float(np.mean(values))


def execute(output: Path) -> None:
    started = time.monotonic(); freeze = json.loads(FREEZE.read_text()); sites = json.loads(SITES.read_text())["sites"]
    fit, calendar_preflight = fit_surface()
    forcing_receipts = []
    for site in sites:
        row = fit[site["regime"]]; normals = prism_normals(site["point_id"])
        forcing_receipts.append({"point_id": site["point_id"], "regime": site["regime"], "prism_normals_sha256": hashlib.sha256(normals.astype("<f8").tobytes()).hexdigest(), "variation_scope": "region_pooled_candidate_fit_only", "requested_eigenvalue_min": row["eigenvalue_min_requested"], "effective_eigenvalue_min": row["eigenvalue_min_effective"], "frobenius_adjustment": row["frobenius_adjustment"], "requested_annual_precip_variance": row["requested_annual_precip_variance"], "effective_annual_precip_variance": row["effective_annual_precip_variance"]})
    stream_rows = []; candidate_by_site: dict[str, list[dict[str, float]]] = defaultdict(list); candidate_30_by_site: dict[str, list[dict[str, float]]] = defaultdict(list)
    for site in sites:
        for member in freeze["generation"]["member_ids"]:
            dates, p, tx, tn, identity = generate_stream(site, member, fit[site["regime"]] if False else fit)
            split = next(index for index, date in enumerate(dates) if date.year == 2031)
            metric100 = metrics(dates, p, tx, tn); metric30 = metrics(dates[:split], p[:split], tx[:split], tn[:split])
            candidate_by_site[site["point_id"]].append(metric100); candidate_30_by_site[site["point_id"]].append(metric30)
            stream_rows.append({"point_id": site["point_id"], "regime": site["regime"], "member_id": member, "horizon_years": 100, "prefix_30_metrics": metric30, "metrics": metric100, **identity})
    prior = json.loads(PRIOR_RESULT.read_text()); point_results = {}; ratios = []
    for site in sites:
        point = site["point_id"]; actual = observed(site); error = composite(candidate_by_site[point], actual)
        reference = float(prior["point_results"][point]["reference_error"]); ratio = error / reference; ratios.append(ratio)
        point_results[point] = {"regime": site["regime"], "candidate_error": error, "reference_error": reference, "ratio": ratio, "candidate_30_error": composite(candidate_30_by_site[point], actual)}
    climate_pass = float(np.median(ratios)) <= 1.25 and max(ratios) <= 1.5
    comparator_state = {"faithful": "inherited_compact_score_only", "faithful_qc_off": "mandatory_stream_metrics_absent", "stochastic_prism_localized_par_v1": "inherited_compact_score_only", "a11": "complete"}
    wepp = {"complete": False, "reason": "exact native executable and scenario materialization absent from checkout/cache", "protocol_id": freeze["wepp"]["protocol_id"]}
    integrated = climate_pass and all(value == "complete" for value in comparator_state.values()) and wepp["complete"]
    evidence = {"schema_version": "a11-evidence-1", "science_contract_id": freeze["science_contract_id"], "attempt_id": "a11-attempt-0002", "candidate_id": freeze["architecture"]["candidate_id"], "calendar_preflight": calendar_preflight, "forcing_receipts": forcing_receipts, "streams": stream_rows, "development": {"climate": {"complete": True, "candidate_pass": climate_pass, "median_site_ratio": float(np.median(ratios)), "maximum_site_ratio": max(ratios), "point_results": point_results, "bootstrap_complete": False, "bootstrap_reason": "prior compact comparator evidence does not retain matched stream metrics"}, "comparators": comparator_state, "wepp": wepp, "integrated_pass": integrated, "science_status": "FAIL", "terminal": "FAIL-A11-INTEGRATED-DEVELOPMENT-INCOMPLETE" if not integrated else "PASS-A11-INTEGRATED-DEVELOPMENT"}, "confirmation": {"state": "SEALED", "target_series_accessed": False, "consume_receipt": None}, "resource_use": {"cpu_seconds": time.monotonic() - started, "gpu_count": 0, "output_bytes": 0}}
    output.parent.mkdir(parents=True, exist_ok=True); atomic_json(output, evidence)
    evidence["resource_use"]["output_bytes"] = output.stat().st_size; atomic_json(output, evidence)
    atomic_json(output.with_name("fit-summary-v1.json"), {"schema_version": "a11-fit-summary-1", "fit_sha256": canonical_digest(fit), "regions": {key: {name: value for name, value in row.items() if name not in ("marginals", "copula_correlation")} for key, row in fit.items()}, "candidate_fit_only": True})
    print(evidence["development"]["terminal"])


def preflight(output: Path) -> None:
    freeze = json.loads(FREEZE.read_text())
    if digest(SITES) != freeze["roster"]["site_manifest_sha256"]: raise RuntimeError("site manifest hash drift")
    fit, calendar_preflight = fit_surface()
    receipt = {"schema_version": "a11-preflight-1", "design_freeze_sha256": digest(FREEZE), "calendar": calendar_preflight, "fit_sha256": canonical_digest(fit), "normal_conditioning": {"archive_sha256": digest(NORMAL_ROOT / "normal-conditioning.f32le"), "index_sha256": digest(NORMAL_ROOT / "normal-conditioning-index.json"), "normalizer_sha256": digest(NORMAL_ROOT / "normalizer.f64le")}, "confirmation_sealed": True, "candidate_output_produced": False, "valid": True}
    output.parent.mkdir(parents=True, exist_ok=True); atomic_json(output, receipt); print("A11-PREFLIGHT-PASS")


def main() -> None:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "execute"):
        command = sub.add_parser(name); command.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.command == "preflight": preflight(options.output)
    else: execute(options.output)


if __name__ == "__main__":
    main()
