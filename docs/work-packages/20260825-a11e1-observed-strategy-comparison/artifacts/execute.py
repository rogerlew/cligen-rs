#!/usr/bin/env python3
"""Execute the source-bound A11E1 observed exploratory comparison."""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tarfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
LAB_PACKAGE = ROOT / "docs/work-packages/20260825-a11e-exploratory-strategy-lab/artifacts"
LAB_PATH = LAB_PACKAGE / "strategy_lab.py"
LAB_MANIFEST = LAB_PACKAGE / "strategy-manifest-v1.json"
FIT_PACKAGE = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort"
DAYMET_ROOT = FIT_PACKAGE / "raw/training/daymet-v1"
DAYMET_MANIFEST = FIT_PACKAGE / "artifacts/daymet-shard-manifest-v1.json"
NORMALIZED_MANIFEST = FIT_PACKAGE / "artifacts/normalized-manifest-v1.json"
COHORT_SELECTION = FIT_PACKAGE / "artifacts/cohort-selection.json"
DEVELOPMENT_MANIFEST = ROOT / "docs/work-packages/20260715-a9c-observed-development/artifacts/observed-source-manifest-v1.json"
MANIFEST_PATH = PACKAGE / "execution-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "execution-manifest-v1.schema.json"
FIT_YEARS = tuple(range(1980, 2010))
DEVELOPMENT_YEARS = tuple(range(2010, 2026))
MONTHS = tuple(range(1, 13))
EQUIVALENT_DAYS = 30.4375
FIT_MASKED = tuple(f"{year}-12-31" for year in range(1980, 2010) if calendar.isleap(year))
DEVELOPMENT_MASKED = tuple(f"{year}-12-31" for year in DEVELOPMENT_YEARS if calendar.isleap(year))
BASE_STRATEGIES = ("gaussian_latent_scalar_ar1_v1", "circular_fixed_block_bootstrap_v1")
INTEGRATED_STRATEGIES = (
    "gaussian_latent_ar1_physical_core_v1",
    "circular_fixed_block_physical_core_v1",
)
BASE_BY_INTEGRATED = dict(zip(INTEGRATED_STRATEGIES, BASE_STRATEGIES))


class ExecutionError(RuntimeError):
    """The prospective A11E1 execution contract was violated."""


def _load_lab() -> Any:
    specification = importlib.util.spec_from_file_location("a11e_strategy_lab", LAB_PATH)
    if specification is None or specification.loader is None:
        raise ExecutionError("cannot load published strategy implementation")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


lab = _load_lab()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    partial.replace(path)


def validate_manifest(value: Any) -> dict[str, Any]:
    expected = {
        "adapter_id", "bootstrap", "confirmation_target_access", "cross_validation_folds",
        "development", "evaluator_id", "execution_id", "field_order", "fit",
        "integrated_strategies", "metric_set_id", "month_equivalent_days", "rng", "schema_version",
        "strategy_source", "uncertainty_id", "wet_threshold_mm",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ExecutionError("execution manifest fields differ")
    constants = {
        "adapter_id": "a11e_two_part_physical_core_36_v1",
        "bootstrap": {"replicates": 1000, "seed": 410542},
        "confirmation_target_access": False,
        "cross_validation_folds": 5,
        "evaluator_id": "a11e_mask_normalized_observed_diagnostics_v1",
        "execution_id": "a11e1-observed-development-v1",
        "field_order": ["equivalent_precipitation_months_01_12", "mean_temperature_months_01_12", "diurnal_range_months_01_12"],
        "metric_set_id": "a11e_mask_normalized_observed_metrics_v1",
        "month_equivalent_days": EQUIVALENT_DAYS,
        "rng": {"algorithm": "numpy_philox", "hurdle_domain": "month_hurdle",
                "hurdle_key_template": "a11e1-integrated-v1\\0{point_id}\\0{integrated_strategy_id}\\0{member_id}\\0month_hurdle",
                "seed_hash": "blake2b_64_little_endian"},
        "schema_version": 1,
        "uncertainty_id": "a11e_paired_development_site_bootstrap_v1",
        "wet_threshold_mm": 1.0,
    }
    if any(value.get(name) != expected_value for name, expected_value in constants.items()):
        raise ExecutionError("execution identity differs")
    expected_fit = {
        "calendar_profile": "daymet_official_365_v1",
        "daymet_manifest": "../../20260721-a10m5r15r1-prism-eligible-cohort/artifacts/daymet-shard-manifest-v1.json",
        "daymet_manifest_sha256": "552a88870014e5f50f1ad0acf17aa72495509b5ddc3f30461b7a744b0de6e7d9",
        "period_end_inclusive": "2009-12-31", "period_start": "1980-01-01", "role": "candidate_fit",
    }
    expected_development = {
        "calendar_profile": "daymet_official_365_v1", "horizon_years": 16, "member_ids": [0],
        "object_count": 20, "period_end_inclusive": "2025-12-31", "period_start": "2010-01-01",
        "role": "development",
        "source_manifest": "../../20260715-a9c-observed-development/artifacts/observed-source-manifest-v1.json",
        "source_manifest_sha256": "8c8e4c2dbcb70f40c0f4d0a6cfd3dd12f0fc1cbb6f0b47bc36653bc2c44fa46b",
    }
    expected_integrated = [
        {"annual_strategy_id": BASE_STRATEGIES[0], "strategy_id": INTEGRATED_STRATEGIES[0]},
        {"annual_strategy_id": BASE_STRATEGIES[1], "block_length_years": 5, "strategy_id": INTEGRATED_STRATEGIES[1]},
    ]
    source = value.get("strategy_source")
    if value.get("fit") != expected_fit or value.get("development") != expected_development or value.get("integrated_strategies") != expected_integrated:
        raise ExecutionError("fit, development, or integrated strategy identity differs")
    if not isinstance(source, dict) or set(source) != {"commit", "implementation_sha256", "manifest_sha256"}:
        raise ExecutionError("strategy source fields differ")
    return value


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        raise ExecutionError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def git_blob(commit: str, path: Path) -> bytes:
    return git("show", f"{commit}:{path.relative_to(ROOT).as_posix()}")


def verify_source(source_commit: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip():
        raise ExecutionError("execution source is not the exact published origin/main commit")
    required = [Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_execute.py"]
    hashes = {}
    for path in required:
        working = path.read_bytes()
        if working != git_blob(source_commit, path):
            raise ExecutionError(f"working source differs from execution commit: {path.name}")
        hashes[path.name] = digest_bytes(working)
    source = manifest["strategy_source"]
    if digest(LAB_PATH) != source["implementation_sha256"] or digest(LAB_MANIFEST) != source["manifest_sha256"]:
        raise ExecutionError("published strategy working bytes drifted")
    if digest_bytes(git_blob(source["commit"], LAB_PATH)) != source["implementation_sha256"] or digest_bytes(git_blob(source["commit"], LAB_MANIFEST)) != source["manifest_sha256"]:
        raise ExecutionError("published strategy commit binding failed")
    return {"execution_source_commit": source_commit, "published_ref": "origin/main", "source_hashes": hashes}


def verify_inputs(manifest: dict[str, Any]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    expected = {
        "daymet_manifest": (DAYMET_MANIFEST, manifest["fit"]["daymet_manifest_sha256"]),
        "normalized_manifest": (NORMALIZED_MANIFEST, "32edc2bf5dd14f5e7c7c47b5354f8d95dd4f601ea14f92fae734694177724f40"),
        "cohort_selection": (COHORT_SELECTION, "af20d8b44cbbffced284b7f9a1105335567ae9cf924e897d54fa9bd8d4f39c5b"),
        "development_manifest": (DEVELOPMENT_MANIFEST, manifest["development"]["source_manifest_sha256"]),
    }
    hashes = {}
    for name, (path, frozen) in expected.items():
        actual = digest(path)
        if actual != frozen:
            raise ExecutionError(f"input hash mismatch: {name}")
        hashes[name] = actual
    shard_manifest = json.loads(DAYMET_MANIFEST.read_text())
    normalized = json.loads(NORMALIZED_MANIFEST.read_text())
    if shard_manifest.get("shards") != normalized.get("daymet_shards") or len(shard_manifest.get("shards", [])) != 60:
        raise ExecutionError("Daymet manifest identity differs")
    for shard in shard_manifest["shards"]:
        path = ROOT / shard["path"]
        if digest(path) != shard["sha256"] or path.stat().st_size != shard["bytes"]:
            raise ExecutionError(f"Daymet shard mismatch: {path.name}")
    development_manifest = json.loads(DEVELOPMENT_MANIFEST.read_text())
    development_rows = [row for row in development_manifest.get("daymet_normalized_objects", []) if row.get("role") == "development"]
    if len(development_rows) != 20 or development_manifest.get("confirmation_series_accessed") is not False:
        raise ExecutionError("development manifest identity differs")
    for row in development_rows:
        path = ROOT / row["path"]
        if digest(path) != row["object_sha256"] or path.stat().st_size != row["bytes"]:
            raise ExecutionError(f"development object mismatch: {row['station_id']}")
    hashes["candidate_shard_set"] = canonical_digest({row["path"]: row["sha256"] for row in shard_manifest["shards"]})
    hashes["development_object_set"] = canonical_digest({row["path"]: row["object_sha256"] for row in development_rows})
    return hashes, development_rows


def safe_corr(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def pooled_lag(sequences: list[np.ndarray]) -> float:
    """Pool only like-field year-t/year-t+1 pairs, never site boundaries."""
    left = np.concatenate([sequence[:-1].ravel() for sequence in sequences])
    right = np.concatenate([sequence[1:].ravel() for sequence in sequences])
    return safe_corr(left, right)


def eligible_wet_counts(counts: Iterable[int], days: int) -> list[int]:
    """Condition the empirical count support on the generated month length."""
    eligible = [int(value) for value in counts if 0 <= int(value) <= days]
    if not eligible:
        raise ExecutionError("wet-count law has no support for generated month length")
    return eligible


def aggregate_months(point: str, regime: str, role: str, records: list[tuple[dt.date, float, float, float]], years: tuple[int, ...]) -> dict[str, Any]:
    grouped: dict[tuple[int, int], list[tuple[float, float, float]]] = defaultdict(list)
    for date, precipitation, maximum, minimum in records:
        if not all(math.isfinite(value) for value in (precipitation, maximum, minimum)) or precipitation < 0.0 or maximum < minimum:
            raise ExecutionError(f"required field failure: {point}/{date}")
        grouped[(date.year, date.month)].append((precipitation, maximum, minimum))
    if set(grouped) != {(year, month) for year in years for month in MONTHS}:
        raise ExecutionError(f"month/year eligibility failure: {point}")
    shape = (len(years), 12)
    precipitation = np.empty(shape); wet_count = np.empty(shape, dtype=np.int64)
    wet_fraction = np.empty(shape); tmean = np.empty(shape); dtr = np.empty(shape)
    texture = {name: np.empty(shape) for name in ("temp_sd", "temp_phi", "amount_phi", "range_phi", "pww", "pwd")}
    observed_days = np.empty(shape, dtype=np.int64)
    for year_index, year in enumerate(years):
        for month in MONTHS:
            slot = month - 1
            values = np.asarray(grouped[(year, month)], dtype=np.float64)
            p, tx, tn = values[:, 0], values[:, 1], values[:, 2]
            temp, daily_range = (tx + tn) / 2.0, tx - tn
            if np.any(daily_range <= 0.0):
                raise ExecutionError(f"nonpositive daily range: {point}/{year}/{month}")
            wet = p >= 1.0
            observed_days[year_index, slot] = len(values)
            precipitation[year_index, slot] = float(np.mean(p) * EQUIVALENT_DAYS)
            wet_count[year_index, slot] = int(np.sum(wet))
            wet_fraction[year_index, slot] = float(np.mean(wet))
            tmean[year_index, slot] = float(np.mean(temp))
            dtr[year_index, slot] = float(np.mean(daily_range))
            texture["temp_sd"][year_index, slot] = float(np.std(temp, ddof=1))
            texture["temp_phi"][year_index, slot] = safe_corr(temp[:-1], temp[1:])
            texture["range_phi"][year_index, slot] = safe_corr(np.log(daily_range[:-1]), np.log(daily_range[1:]))
            wet_amounts = p[wet]
            texture["amount_phi"][year_index, slot] = safe_corr(np.log(wet_amounts[:-1]), np.log(wet_amounts[1:])) if len(wet_amounts) >= 3 else 0.0
            previous, current = wet[:-1], wet[1:]
            ww, wd = int(np.sum(previous & current)), int(np.sum(previous & ~current))
            dw, dd = int(np.sum(~previous & current)), int(np.sum(~previous & ~current))
            texture["pww"][year_index, slot] = ww / (ww + wd) if ww + wd else 0.5
            texture["pwd"][year_index, slot] = dw / (dw + dd) if dw + dd else 0.5
    return {"point_id": point, "regime": regime, "role": role, "precipitation": precipitation,
            "wet_count": wet_count, "wet_fraction": wet_fraction, "tmean": tmean, "dtr": dtr,
            "texture": texture, "observed_days": observed_days}


def summarize_fit_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    point = record.get("point_id")
    dates = [dt.date.fromisoformat(value) for value in record.get("dates", [])]
    observed, fields = record.get("source_observed"), record.get("fields")
    if (record.get("schema_version") != 1 or record.get("source_id") != "daymet_v4r1_single_pixel"
            or record.get("calendar_transform_id") != "daymet_official_365_v1"
            or record.get("units", {}).get("prcp") != "mm/day" or record.get("units", {}).get("tmax") != "degC"
            or record.get("units", {}).get("tmin") != "degC" or record.get("role") not in {"candidate_fit", "fit_validation"}
            or len(dates) != 10958 or len(observed or []) != 10958 or not isinstance(fields, dict)
            or any(len(fields.get(name, [])) != 10958 for name in ("prcp", "tmax", "tmin"))
            or dates[0] != dt.date(1980, 1, 1) or dates[-1] != dt.date(2009, 12, 31)
            or any(dates[index] + dt.timedelta(days=1) != dates[index + 1] for index in range(len(dates) - 1))):
        raise ExecutionError(f"fit object identity failure: {point}")
    keep = [value is True and all(fields[name][index] is not None for name in ("prcp", "tmax", "tmin")) for index, value in enumerate(observed)]
    masked = tuple(date.isoformat() for date, include in zip(dates, keep) if not include)
    if sum(keep) != 10950 or masked != FIT_MASKED:
        raise ExecutionError(f"fit mask failure: {point}")
    rows = [(date, float(fields["prcp"][index]), float(fields["tmax"][index]), float(fields["tmin"][index])) for index, date in enumerate(dates) if keep[index]]
    return aggregate_months(point, record["regime"], record["role"], rows, FIT_YEARS), {
        "point_id": point, "role": record["role"], "axis_rows": len(dates), "observed_rows": sum(keep),
        "masked_dates": list(masked), "first_date": dates[0].isoformat(), "last_date": dates[-1].isoformat(),
    }


def load_fit_corpus() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selection = json.loads(COHORT_SELECTION.read_text())
    expected = {row["point_id"]: (row["regime"], row["role"], row["tile_id"]) for row in selection["locations"]}
    summaries, receipts, seen = [], [], set()
    for path in sorted(DAYMET_ROOT.glob("daymet-*.tar.gz")):
        with tarfile.open(path, "r:gz") as archive:
            for member in sorted(archive.getmembers(), key=lambda value: value.name.encode()):
                handle = archive.extractfile(member)
                if handle is None:
                    raise ExecutionError(f"unreadable member: {path.name}/{member.name}")
                raw = json.load(handle)
                point = raw.get("point_id")
                if point in seen or point not in expected or (raw.get("regime"), raw.get("role"), raw.get("tile_id")) != expected[point]:
                    raise ExecutionError(f"cohort identity failure: {point}")
                summary, receipt = summarize_fit_record(raw)
                summaries.append(summary); receipts.append(receipt); seen.add(point)
    roles = Counter(value["role"] for value in summaries)
    regimes = Counter(f"{value['regime']}/{value['role']}" for value in summaries)
    if seen != set(expected) or roles != {"candidate_fit": 1200, "fit_validation": 240} or regimes != Counter(selection["counts"]):
        raise ExecutionError("fit cohort roster/count failure")
    return summaries, {"calendar_objects": len(summaries), "axis_rows_per_object": 10958,
        "observed_rows_per_object": 10950, "masked_dates": list(FIT_MASKED), "role_counts": dict(roles),
        "object_receipts_sha256": canonical_digest(receipts)}


def load_development(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summaries, receipts = [], []
    for identity in sorted(rows, key=lambda row: row["station_id"]):
        with gzip.open(ROOT / identity["path"], "rt") as stream:
            raw = json.load(stream)
        if (raw.get("schema_version") != 1 or raw.get("calendar") != "daymet_official_365_v1"
                or raw.get("role") != "development" or raw.get("station_id") != identity["station_id"]
                or raw.get("stratum") != identity["stratum"] or len(raw.get("records", [])) != 5840):
            raise ExecutionError(f"development identity failure: {identity['station_id']}")
        values = [(dt.date.fromisoformat(row["date"]), float(row["prcp_mm"]), float(row["tmax_c"]), float(row["tmin_c"])) for row in raw["records"]]
        dates = [row[0] for row in values]
        complete = [dt.date(2010, 1, 1) + dt.timedelta(days=index) for index in range(5844)]
        masked = tuple(date.isoformat() for date in complete if date not in set(dates))
        if dates != sorted(dates) or dates[0] != dt.date(2010, 1, 1) or dates[-1] != dt.date(2025, 12, 31) or masked != DEVELOPMENT_MASKED:
            raise ExecutionError(f"development calendar failure: {identity['station_id']}")
        summaries.append(aggregate_months(raw["station_id"], raw["stratum"], "development", values, DEVELOPMENT_YEARS))
        receipts.append({"station_id": raw["station_id"], "axis_rows": 5844, "observed_rows": 5840, "masked_dates": list(masked)})
    return summaries, {"calendar_objects": 20, "axis_rows_per_object": 5844, "observed_rows_per_object": 5840,
        "masked_dates": list(DEVELOPMENT_MASKED), "role_counts": {"development": 20},
        "object_receipts_sha256": canonical_digest(receipts)}


def adapter_parameters(candidate: Iterable[dict[str, Any]]) -> dict[str, dict[str, np.ndarray]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in candidate:
        grouped[summary["regime"]].append(summary)
    output = {}
    for regime, records in grouped.items():
        floors, dry_probability, counts = [], [], []
        for slot, month in enumerate(MONTHS):
            all_counts = [int(value) for record in records for value in record["wet_count"][:, slot]]
            positive = [value for value in all_counts if value > 0]
            if not positive:
                raise ExecutionError(f"region/month lacks positive wet support: {regime}/{month}")
            minimum_days = calendar.monthrange(2001, month)[1]
            floors.append(min(positive) * EQUIVALENT_DAYS / minimum_days)
            dry_probability.append(all_counts.count(0) / len(all_counts))
            counts.append(all_counts)
        output[regime] = {"floors": np.asarray(floors), "dry_probability": np.asarray(dry_probability), "wet_counts": counts}
    return output


def state_matrix(summary: dict[str, Any], adapters: dict[str, dict[str, np.ndarray]]) -> np.ndarray:
    floor = adapters[summary["regime"]]["floors"]
    positive = summary["wet_count"] > 0
    residual = np.where(positive, np.maximum(summary["precipitation"] - floor, 0.01), 0.01)
    if np.any(summary["dtr"] <= 0.0):
        raise ExecutionError(f"nonpositive monthly range: {summary['point_id']}")
    return np.concatenate((np.log(residual), summary["tmean"], np.log(summary["dtr"])), axis=1)


def strategy_fit(base_id: str, summaries: list[dict[str, Any]], adapters: dict[str, dict[str, np.ndarray]], regime: str) -> dict[str, Any]:
    sites, years, rows = [], [], []
    for summary in sorted(summaries, key=lambda value: value["point_id"]):
        matrix = state_matrix(summary, adapters)
        for index, year in enumerate(FIT_YEARS):
            sites.append(summary["point_id"]); years.append(year); rows.append(matrix[index])
    values = np.asarray(rows)
    return lab.fit_gaussian_ar1(sites, years, values, regime) if base_id == BASE_STRATEGIES[0] else lab.fit_block_bootstrap(sites, years, values, 5, regime)


def fit_regions(candidate: list[dict[str, Any]], adapters: dict[str, dict[str, np.ndarray]]) -> tuple[dict[str, Any], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in candidate:
        grouped[summary["regime"]].append(summary)
    models, receipt = {}, {"schema_version": "a11e1-fit-summary-1", "candidate_fit_only": True, "regions": {}}
    weights = np.asarray([calendar.monthrange(2001, month)[1] for month in MONTHS], dtype=np.float64); weights /= np.sum(weights)
    for regime in sorted(grouped):
        records = grouped[regime]; matrices = [state_matrix(row, adapters) for row in records]
        variances = np.median(np.asarray([np.var(matrix, axis=0, ddof=1) for matrix in matrices]), axis=0)
        location = np.median(np.asarray([np.mean(matrix, axis=0) for matrix in matrices]), axis=0)
        annual_variance = float(np.median([np.var(matrix[:, 12:24] @ weights, ddof=1) for matrix in matrices]))
        if np.any(~np.isfinite(variances)) or np.any(variances <= 0.0) or annual_variance <= 0.0:
            raise ExecutionError(f"invalid fit variance: {regime}")
        texture = {}
        for name in ("temp_sd", "temp_phi", "amount_phi", "range_phi", "pww", "pwd"):
            values = np.asarray([row["texture"][name] for row in records])
            texture[name] = np.median(values, axis=(0, 1))
        texture["temp_sd"] = np.maximum(texture["temp_sd"], 0.01)
        for name in ("temp_phi", "amount_phi", "range_phi"):
            texture[name] = np.clip(texture[name], -0.8, 0.8)
        for name in ("pww", "pwd"):
            texture[name] = np.clip(texture[name], 1e-6, 1.0 - 1e-6)
        adapters[regime].update({"variances": variances, "location": location, "annual_weights": np.concatenate((np.zeros(12), weights, np.zeros(12))), "annual_variance": annual_variance, "texture": texture})
        region_receipt = {"candidate_sites": len(records), "candidate_site_years": len(records) * 30,
            "support_floor_equivalent_mm": adapters[regime]["floors"].tolist(), "dry_month_probability": adapters[regime]["dry_probability"].tolist(),
            "forcing_location": "median candidate-fit site mean; development targets excluded", "strategies": {}}
        for base_id, integrated_id in zip(BASE_STRATEGIES, INTEGRATED_STRATEGIES):
            model = strategy_fit(base_id, records, adapters, regime); models[f"{regime}/{integrated_id}"] = model
            region_receipt["strategies"][integrated_id] = {"annual_strategy_id": base_id, "model_sha256": canonical_digest(model), "scalar_persistence": model.get("scalar_persistence")}
        receipt["regions"][regime] = region_receipt
    receipt["fit_sha256"] = canonical_digest(receipt["regions"])
    return models, receipt


def cross_validate(candidate: list[dict[str, Any]], adapters: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate: grouped[row["regime"]].append(row)
    output = {"schema_version": "a11e1-cross-validation-1", "scope": "annual-strategy-only conditional on full-candidate adapter", "folds": 5, "regions": {}}
    for regime in sorted(grouped):
        records = sorted(grouped[regime], key=lambda row: row["point_id"]); results = []
        for fold in range(5):
            training = [row for index, row in enumerate(records) if index % 5 != fold]
            held = [row for index, row in enumerate(records) if index % 5 == fold]
            held_values = np.vstack([state_matrix(row, adapters) for row in held])
            held_sites = [row["point_id"] for row in held for _ in FIT_YEARS]
            observed = lab.within_site_standardize(held_sites, list(FIT_YEARS) * len(held), held_values)["anomalies"]
            observed_covariance = np.cov(observed, rowvar=False, ddof=1)
            observed_sequences = [observed[index * 30:(index + 1) * 30] for index in range(len(held))]
            for base_id, integrated_id in zip(BASE_STRATEGIES, INTEGRATED_STRATEGIES):
                model = strategy_fit(base_id, training, adapters, regime); generated = []
                for member in range(len(held)):
                    rng = lab.domain_rng(f"a11e1-cv-{regime}-{fold}", base_id, member, "annual_target")
                    generated.append(lab.generate_gaussian_ar1(model, 30, rng) if base_id == BASE_STRATEGIES[0] else lab.generate_block_bootstrap(model, 30, rng))
                generated_values = np.vstack(generated)
                results.append({"fold": fold, "strategy_id": integrated_id, "training_sites": len(training), "held_sites": len(held),
                    "covariance_frobenius_per_field": float(np.linalg.norm(np.cov(generated_values, rowvar=False, ddof=1) - observed_covariance, ord="fro") / 36.0),
                    "persistence_absolute_error": abs(pooled_lag(generated) - pooled_lag(observed_sequences))})
        output["regions"][regime] = results
    output["summary"] = {strategy: {"median_covariance_frobenius_per_field": float(np.median([row["covariance_frobenius_per_field"] for rows in output["regions"].values() for row in rows if row["strategy_id"] == strategy])),
        "median_persistence_absolute_error": float(np.median([row["persistence_absolute_error"] for rows in output["regions"].values() for row in rows if row["strategy_id"] == strategy]))} for strategy in INTEGRATED_STRATEGIES}
    return output


def hurdle_rng(point: str, strategy: str, member: int) -> np.random.Generator:
    payload = f"a11e1-integrated-v1\0{point}\0{strategy}\0{member}\0month_hurdle".encode()
    seed = int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")
    return np.random.Generator(np.random.Philox(seed))


def evaluate_site(observed: dict[str, Any], integrated_id: str, model: dict[str, Any], adapter: dict[str, Any], site_ordinal: int) -> dict[str, Any]:
    base_id = BASE_BY_INTEGRATED[integrated_id]; point = observed["point_id"]
    target_rng = lab.domain_rng(f"a11e1-development-{point}", base_id, 0, "annual_target")
    states, target_receipt = lab.generate_strategy_targets(model, 16, target_rng, adapter["location"], adapter["variances"], adapter["annual_weights"], adapter["annual_variance"])
    positive_equivalent = adapter["floors"] + np.exp(states[:, :12])
    temperature, daily_range = states[:, 12:24], np.exp(states[:, 24:36])
    generated_equivalent = np.empty((16, 12)); wet_fraction = np.empty((16, 12)); failures = 0; previous_wet = False
    hurdle = hurdle_rng(point, integrated_id, 0); texture = adapter["texture"]
    for year_index, year in enumerate(DEVELOPMENT_YEARS):
        for month in MONTHS:
            slot = month - 1; days = calendar.monthrange(year, month)[1]
            dry = float(hurdle.random()) < float(adapter["dry_probability"][slot])
            equivalent_total = 0.0 if dry else float(positive_equivalent[year_index, slot])
            total = equivalent_total * days / EQUIVALENT_DAYS
            streams = lab.domain_rngs(f"a11e1-core-{point}", base_id, site_ordinal * 192 + year_index * 12 + slot)
            required = {name: streams[name] for name in ("wet_count", "occurrence", "amount", "temperature", "range")}
            counts = eligible_wet_counts(adapter["wet_counts"][slot], days)
            generated, receipt = lab.generate_core_month(base_id, total, days, counts, 1.0, previous_wet,
                float(texture["pww"][slot]), float(texture["pwd"][slot]), float(temperature[year_index, slot]), float(texture["temp_sd"][slot]),
                float(daily_range[year_index, slot]), float(texture["amount_phi"][slot]), float(texture["temp_phi"][slot]), float(texture["range_phi"][slot]), required)
            previous_wet = bool(generated["wet"][-1]); generated_equivalent[year_index, slot] = receipt["precipitation_total_mm"] * EQUIVALENT_DAYS / days
            wet_fraction[year_index, slot] = receipt["wet_count"] / days
            failures += int(abs(receipt["precipitation_total_mm"] - total) > 1e-8)
            failures += int(abs(float(np.mean(generated["temperature_mean"])) - temperature[year_index, slot]) > 1e-10)
            failures += int(abs(receipt["range_mean"] - daily_range[year_index, slot]) > 1e-10)
            failures += int(np.any(generated["temperature_max"] < generated["temperature_min"]))
            failures += int((total == 0.0) != (receipt["wet_count"] == 0))
    observed_p, observed_t, observed_r = observed["precipitation"], observed["tmean"], observed["dtr"]
    weights = adapter["annual_weights"][12:24]
    gp, op = np.sum(generated_equivalent, axis=1), np.sum(observed_p, axis=1)
    gt, ot = temperature @ weights, observed_t @ weights
    metrics = {
        "monthly_equivalent_precipitation_mean_relative_absolute_error": float(np.mean(np.abs(np.mean(generated_equivalent, axis=0) - np.mean(observed_p, axis=0)) / np.maximum(np.mean(observed_p, axis=0), 0.01))),
        "monthly_temperature_mean_absolute_error_c": float(np.mean(np.abs(np.mean(temperature, axis=0) - np.mean(observed_t, axis=0)))),
        "monthly_range_mean_relative_absolute_error": float(np.mean(np.abs(np.mean(daily_range, axis=0) - np.mean(observed_r, axis=0)) / np.maximum(np.mean(observed_r, axis=0), 0.01))),
        "monthly_wet_fraction_mean_absolute_error": float(np.mean(np.abs(np.mean(wet_fraction, axis=0) - np.mean(observed["wet_fraction"], axis=0)))),
        "annual_precipitation_variance_absolute_log_ratio": abs(math.log(max(float(np.var(gp, ddof=1)), 1e-12) / max(float(np.var(op, ddof=1)), 1e-12))),
        "annual_temperature_variance_absolute_log_ratio": abs(math.log(max(float(np.var(gt, ddof=1)), 1e-12) / max(float(np.var(ot, ddof=1)), 1e-12))),
        "annual_precipitation_lag1_absolute_error": abs(safe_corr(gp[:-1], gp[1:]) - safe_corr(op[:-1], op[1:])),
        "daily_invariant_failures": failures,
    }
    metrics["descriptive_composite_score"] = (metrics["monthly_equivalent_precipitation_mean_relative_absolute_error"] + metrics["monthly_temperature_mean_absolute_error_c"] / 5.0 + metrics["monthly_range_mean_relative_absolute_error"] + metrics["monthly_wet_fraction_mean_absolute_error"] * 3.0 + metrics["annual_precipitation_variance_absolute_log_ratio"] + metrics["annual_temperature_variance_absolute_log_ratio"] + metrics["annual_precipitation_lag1_absolute_error"])
    return {"point_id": point, "regime": observed["regime"], "strategy_id": integrated_id, "annual_strategy_id": base_id,
        "member_id": 0, "years": 16, "metrics": metrics, "target_receipt": target_receipt,
        "stream_summary_sha256": canonical_digest({"precipitation": generated_equivalent.tolist(), "temperature": temperature.tolist(), "range": daily_range.tolist(), "wet_fraction": wet_fraction.tolist()})}


def paired_bootstrap(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    by_strategy = {strategy: {row["point_id"]: row["metrics"]["descriptive_composite_score"] for row in rows if row["strategy_id"] == strategy} for strategy in INTEGRATED_STRATEGIES}
    points = sorted(set(by_strategy[INTEGRATED_STRATEGIES[0]]) & set(by_strategy[INTEGRATED_STRATEGIES[1]]))
    if len(points) != 20: raise ExecutionError("paired bootstrap requires 20 common development sites")
    differences = np.asarray([by_strategy[INTEGRATED_STRATEGIES[0]][point] - by_strategy[INTEGRATED_STRATEGIES[1]][point] for point in points])
    generator = np.random.Generator(np.random.Philox(manifest["bootstrap"]["seed"])); samples = []
    for _ in range(manifest["bootstrap"]["replicates"]): samples.append(float(np.mean(differences[generator.integers(0, len(points), len(points))])))
    return {"rng": "numpy_philox/a11e1_site_bootstrap_domain_v1", "contrast": f"{INTEGRATED_STRATEGIES[0]} minus {INTEGRATED_STRATEGIES[1]}; lower score is better",
        "site_differences": dict(zip(points, differences.tolist())), "mean_difference": float(np.mean(differences)),
        "bootstrap_quantiles_05_50_95": np.quantile(samples, [0.05, 0.5, 0.95]).tolist(), "replicates": len(samples), "seed": manifest["bootstrap"]["seed"],
        "interpretation": "descriptive site resampling of one stochastic member; no Monte Carlo interval, confirmation, or promotion threshold"}


def execute(source_commit: str) -> None:
    started = time.monotonic(); manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    source_receipt = verify_source(source_commit, manifest); input_receipt, development_rows = verify_inputs(manifest)
    fit_summaries, fit_preflight = load_fit_corpus(); development, development_preflight = load_development(development_rows)
    preflight = {"schema_version": "a11e1-calendar-preflight-1", "valid": True, "source_transform": "daymet_official_365_v1",
        "normalized_statistic": "mask-normalized 30.4375-day equivalent precipitation; temperature/range observed-day means; wet fraction",
        "required_mask": "source-observed row with finite prcp/tmax/tmin", "fit": fit_preflight, "development": development_preflight,
        "leap_fixture": {"february_29": "observed", "leap_december_31": "masked at input; no fabricated raw value"},
        "confirmation_target_series_accessed": False}
    atomic_json(PACKAGE / "calendar-preflight-v1.json", preflight)
    candidate = [row for row in fit_summaries if row["role"] == "candidate_fit"]
    adapters = adapter_parameters(candidate); models, fit_receipt = fit_regions(candidate, adapters)
    atomic_json(PACKAGE / "fit-summary-v1.json", fit_receipt)
    cross_validation = cross_validate(candidate, adapters); atomic_json(PACKAGE / "cross-validation-v1.json", cross_validation)
    rows = []
    for site_ordinal, observed in enumerate(development):
        for strategy in INTEGRATED_STRATEGIES:
            rows.append(evaluate_site(observed, strategy, models[f"{observed['regime']}/{strategy}"], adapters[observed["regime"]], site_ordinal))
    if len(rows) != 40 or any(row["metrics"]["daily_invariant_failures"] for row in rows):
        raise ExecutionError("development streams are incomplete or violate invariants")
    bootstrap = paired_bootstrap(rows, manifest)
    evidence = {"schema_version": "a11e1-development-evidence-1", "execution_id": manifest["execution_id"], "source_commit": source_commit,
        "strategy_source_commit": manifest["strategy_source"]["commit"], "evaluator_id": manifest["evaluator_id"], "metric_set_id": manifest["metric_set_id"],
        "stream_count": len(rows), "rows": rows, "paired_bootstrap": bootstrap, "limitations": ["single generated member per site", "candidate-region pooled forcing levels rather than site normals", "development horizon is 16 years", "composite score is descriptive and uncalibrated"],
        "confirmation_target_series_accessed": False}
    evidence["evidence_sha256"] = canonical_digest(evidence); atomic_json(PACKAGE / "development-evidence-v1.json", evidence)
    strategy_summaries = {}
    for strategy in INTEGRATED_STRATEGIES:
        selected = [row for row in rows if row["strategy_id"] == strategy]
        strategy_summaries[strategy] = {"disposition": "RETAINED_FOR_EXPLORATION", "site_count": len(selected),
            "median_descriptive_composite_score": float(np.median([row["metrics"]["descriptive_composite_score"] for row in selected])),
            "maximum_daily_invariant_failures": max(row["metrics"]["daily_invariant_failures"] for row in selected),
            "scope": "observed development only; no confirmation or promotion authority"}
    decision = {"schema_version": "a11e1-development-decision-1", "execution_id": manifest["execution_id"], "science_status": "EXPLORATORY_EVALUATED",
        "terminal": "EXECUTED-COMPLETE", "strategies": strategy_summaries, "paired_bootstrap": bootstrap,
        "next_action": "interpret diagnostics and register only a falsifiable bounded successor", "confirmation_authorized": False, "production_authorized": False}
    atomic_json(PACKAGE / "development-decision-v1.json", decision)
    outputs = [PACKAGE / name for name in ("calendar-preflight-v1.json", "fit-summary-v1.json", "cross-validation-v1.json", "development-evidence-v1.json", "development-decision-v1.json")]
    receipt = {"schema_version": "a11e1-execution-receipt-1", "execution_id": manifest["execution_id"], **source_receipt,
        "input_hashes": input_receipt, "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in outputs},
        "elapsed_seconds": time.monotonic() - started, "fit_calendar_objects": len(fit_summaries), "candidate_fit_objects": len(candidate),
        "development_objects": len(development), "development_streams": len(rows), "confirmation_target_series_accessed": False}
    atomic_json(PACKAGE / "execution-receipt-v1.json", receipt)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--source-commit"); parser.add_argument("--validate-manifest", action="store_true"); parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args(); manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if arguments.validate_manifest: print(canonical_digest(manifest)); return
    if not arguments.execute or not arguments.source_commit: parser.error("--execute requires --source-commit")
    execute(arguments.source_commit)


if __name__ == "__main__":
    main()
