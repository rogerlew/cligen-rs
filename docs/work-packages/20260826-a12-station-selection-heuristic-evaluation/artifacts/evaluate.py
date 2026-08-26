#!/usr/bin/env python3
"""Source-bound A12 station-selection heuristic evaluation."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
MANIFEST_PATH = PACKAGE / "evaluation-manifest-v1.json"
SCHEMA_PATH = PACKAGE / "evaluation-manifest-v1.schema.json"
SPEC_PATH = ROOT / "docs/specifications/SPEC-A12-STATION-SELECTION-EVALUATION.md"
A10_SPEC = ROOT / "docs/specifications/SPEC-A10-CORPUS.md"
A10_PRISM_SPEC = ROOT / "docs/specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md"
PACKAGE_PATH = PACKAGE.parent / "package.md"
PLAN_PATH = ROOT / "docs/exec-plans/20260826-a12-station-selection-heuristic-evaluation.md"
REVIEW_PATH = PACKAGE / "review.md"
TEST_RESULTS_PATH = PACKAGE / "test-results.md"
CLI_GUIDE = ROOT / "docs/cli-guide.md"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs/ROADMAP.md"
SPEC_REGISTRY = ROOT / "docs/specifications/README.md"
PACKAGE_CATALOG = ROOT / "docs/work-packages/README.md"
LOCALIZE_RS = ROOT / "crates/cligen/src/prism/localize.rs"
RUN_RS = ROOT / "crates/cligen/src/prism/run.rs"
STATION_MANIFESTS = ROOT / "crates/cligen/src/stations/manifests.json"
PRISM_DISTRIBUTION = ROOT / "crates/cligen/src/prism/distribution.json"
COHORT_ROOT = ROOT / "docs/work-packages/20260721-a10m5r15r1-prism-eligible-cohort"
COHORT = COHORT_ROOT / "artifacts/cohort-selection.json"
NORMALIZED = COHORT_ROOT / "artifacts/normalized-manifest-v1.json"
SHARDS = COHORT_ROOT / "artifacts/daymet-shard-manifest-v1.json"
DAYMET_ROOT = COHORT_ROOT / "raw/training/daymet-v1"
DAYS = np.array([31.0, 28.25, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0])
POLICIES = ("closest_v1", "cligen_prism_rank_sum_v1", "wepppy_elevation_prism_reference_v1")
METRICS = (
    "wet_day_precipitation_sd_relative_absolute_error",
    "wet_day_precipitation_skew_scaled_absolute_error",
    "wet_after_wet_probability_absolute_error",
    "wet_after_dry_probability_absolute_error",
    "tmax_sd_relative_absolute_error",
    "tmin_sd_relative_absolute_error",
)
REGIMES = (
    "arid_boundary", "cold", "hot_arid", "humid", "monsoonal_transition",
    "non_monsoonal_semi_arid",
)


class EvaluationError(RuntimeError):
    """A prospective A12 contract or identity failed closed."""


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


def git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if result.returncode != 0:
        raise EvaluationError(f"git command failed: {' '.join(arguments)}")
    return result.stdout


def validate_manifest(value: Any) -> dict[str, Any]:
    expected_fields = {"bootstrap", "corpus", "decision", "evaluation_id", "input_hashes", "metrics", "runtime", "schema_version"}
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise EvaluationError("evaluation manifest fields differ")
    if value["schema_version"] != 1 or value["evaluation_id"] != "a12-station-selection-heuristic-evaluation-v1":
        raise EvaluationError("evaluation identity differs")
    if tuple(value["metrics"]) != METRICS or tuple(value["decision"]["policies"]) != POLICIES:
        raise EvaluationError("metric or policy roster differs")
    if value["bootstrap"] != {
        "algorithm": "numpy_philox",
        "common_resamples": True,
        "domain": "a12_station_selection_site_median_v1",
        "quantile_method": "linear",
        "replicates": 10000,
        "seed_derivation": "numpy_seedsequence_u32le_sha256_domain_plus_integer_seed",
        "seed": 12012,
    }:
        raise EvaluationError("bootstrap contract differs")
    if value["decision"] != {
        "family_worsening_limit_fraction": 0.05,
        "heuristic_support_rule": "paired_composite_median_lt_0_and_bootstrap_upper_lt_0_and_site_win_fraction_gt_0.5_and_no_family_median_more_than_5pct_above_closest",
        "policies": list(POLICIES),
    }:
        raise EvaluationError("decision contract differs")
    if value["runtime"] != {"python": "3.12.13", "numpy": "2.3.5"}:
        raise EvaluationError("runtime contract differs")
    if value["corpus"] != {
        "calendar_axis_rows": 10958,
        "masked_dates": [f"{year}-12-31" for year in range(1980, 2010) if year % 4 == 0],
        "observed_rows": 10950,
        "period_end_inclusive": "2009-12-31",
        "period_start": "1980-01-01",
        "role": "fit_validation",
        "site_count": 240,
        "source_transform": "daymet_official_365_v1",
    }:
        raise EvaluationError("corpus contract differs")
    return value


def verify_inputs(manifest: dict[str, Any]) -> dict[str, str]:
    paths = {
        "a10_corpus_spec": A10_SPEC,
        "cohort_selection": COHORT,
        "daymet_shard_manifest": SHARDS,
        "normalized_manifest": NORMALIZED,
        "station_manifests": STATION_MANIFESTS,
    }
    actual = {name: digest(path) for name, path in paths.items()}
    if actual != manifest["input_hashes"]:
        raise EvaluationError("registered input identity differs")
    return actual


def verify_source(source_commit: str) -> dict[str, str]:
    if len(source_commit) != 40 or source_commit != git("rev-parse", "origin/main").decode().strip():
        raise EvaluationError("source commit is not exact origin/main")
    paths = [Path(__file__), MANIFEST_PATH, SCHEMA_PATH, PACKAGE / "test_evaluate.py", SPEC_PATH,
             A10_PRISM_SPEC, PACKAGE_PATH, PLAN_PATH, REVIEW_PATH, TEST_RESULTS_PATH, CLI_GUIDE,
             README, ROADMAP, SPEC_REGISTRY,
             PACKAGE_CATALOG, LOCALIZE_RS, RUN_RS, PRISM_DISTRIBUTION, STATION_MANIFESTS,
             ROOT / "Cargo.lock", ROOT / "rust-toolchain.toml"]
    result = {}
    for path in paths:
        current = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        committed = git("show", f"{source_commit}:{relative}")
        if current != committed:
            raise EvaluationError(f"working source differs from commit: {relative}")
        result[relative] = digest_bytes(current)
    return result


def command_output(*arguments: str) -> str:
    result = subprocess.run(arguments, cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise EvaluationError(f"command failed: {' '.join(arguments)}")
    return result.stdout.strip()


def build_release(source_commit: str) -> None:
    source_hashes = verify_source(source_commit)
    if git("rev-parse", "HEAD").decode().strip() != source_commit or git("status", "--porcelain"):
        raise EvaluationError("release build requires the exact clean published source commit")
    command = ["cargo", "build", "--release", "--locked", "--bin", "cligen"]
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise EvaluationError("release build failed")
    binary = ROOT / "target/release/cligen"
    receipt = {
        "schema_version": "a12-build-receipt-1",
        "source_commit": source_commit,
        "source_hashes": source_hashes,
        "cargo_lock_sha256": digest(ROOT / "Cargo.lock"),
        "rust_toolchain_sha256": digest(ROOT / "rust-toolchain.toml"),
        "rustc_verbose": command_output("rustc", "-vV"),
        "cargo_version": command_output("cargo", "--version"),
        "build_command": command,
        "features": "default",
        "binary_path": str(binary.relative_to(ROOT)),
        "cligen_binary_sha256": digest(binary),
    }
    atomic_json(PACKAGE / "build-receipt-v1.json", receipt)


def validate_build_receipt_fields(receipt: dict[str, Any], source_commit: str,
                                  source_hashes: dict[str, str], expected: dict[str, Any]) -> None:
    required = {"schema_version", "source_commit", "source_hashes", *expected}
    if set(receipt) != required or receipt.get("schema_version") != "a12-build-receipt-1":
        raise EvaluationError("build receipt fields differ")
    if receipt["source_commit"] != source_commit or receipt["source_hashes"] != source_hashes:
        raise EvaluationError("build receipt source identity differs")
    if any(receipt[key] != value for key, value in expected.items()):
        raise EvaluationError("build receipt does not bind the supplied binary and toolchain")


def verify_build_receipt(source_commit: str, source_hashes: dict[str, str], binary: Path,
                         receipt_path: Path) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text())
    expected = {
        "cargo_lock_sha256": digest(ROOT / "Cargo.lock"),
        "rust_toolchain_sha256": digest(ROOT / "rust-toolchain.toml"),
        "rustc_verbose": command_output("rustc", "-vV"),
        "cargo_version": command_output("cargo", "--version"),
        "build_command": ["cargo", "build", "--release", "--locked", "--bin", "cligen"],
        "features": "default",
        "binary_path": str(binary.relative_to(ROOT)),
        "cligen_binary_sha256": digest(binary),
    }
    validate_build_receipt_fields(receipt, source_commit, source_hashes, expected)
    return receipt


def cache_root() -> Path:
    if os.environ.get("CLIGEN_DATA_DIR"):
        return Path(os.environ["CLIGEN_DATA_DIR"]).resolve()
    if os.environ.get("XDG_CACHE_HOME"):
        return Path(os.environ["XDG_CACHE_HOME"]).resolve() / "cligen"
    return Path.home() / ".cache/cligen"


def verify_prism_cache(root: Path) -> dict[str, Any]:
    distribution = json.loads(PRISM_DISTRIBUTION.read_text())
    runtime = root / "prism" / distribution["bundle_id"] / distribution["version"]
    grid_path = runtime / "grid-manifest.json"
    if digest(grid_path) != distribution["grid_manifest_sha256"]:
        raise EvaluationError("PRISM grid manifest identity differs")
    grid = json.loads(grid_path.read_text())
    expected = {
        "grid-manifest.json": distribution["grid_manifest_sha256"],
        "source-manifest.json": distribution["source_manifest_sha256"],
        "BUILD-RECEIPT.json": distribution["build_receipt_sha256"],
        "ATTRIBUTION.md": distribution["attribution_sha256"],
        grid["normals"]["path"]: grid["normals"]["sha256"],
        grid["validity_mask"]["path"]: grid["validity_mask"]["sha256"],
    }
    actual = {}
    for name, expected_hash in expected.items():
        path = runtime / name
        actual_hash = digest(path)
        if actual_hash != expected_hash:
            raise EvaluationError(f"PRISM runtime file identity differs: {name}")
        actual[name] = {"bytes": path.stat().st_size, "sha256": actual_hash}
    return {
        "bundle_id": distribution["bundle_id"],
        "bundle_version": distribution["version"],
        "registered_runtime_archive_sha256": distribution["runtime_archive"]["sha256"],
        "_runtime_path": str(runtime),
        "files": actual,
        "file_set_sha256": canonical_digest(actual),
    }


def extract_registered_station_archive(archive_path: Path, data_root: Path) -> tuple[Path, dict[str, Any]]:
    manifests = json.loads(STATION_MANIFESTS.read_text())
    collection = next(row for row in manifests["collections"] if row["name"] == "us-2015")
    archive_path = archive_path.resolve()
    if archive_path.stat().st_size != collection["archive"]["bytes"] or digest(archive_path) != collection["archive"]["sha256"]:
        raise EvaluationError("station archive identity differs")
    destination = data_root / "stations/us-2015/2026.07"
    destination.mkdir(parents=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if member.name.startswith("/") or ".." in parts or not (member.isdir() or member.isfile()):
                raise EvaluationError("unsafe station archive member")
        archive.extractall(destination, filter="data")
    files = {}
    for path in sorted(item for item in destination.rglob("*") if item.is_file()):
        relative = path.relative_to(destination).as_posix()
        files[relative] = {"bytes": path.stat().st_size, "sha256": digest(path)}
    return destination, {
        "name": collection["name"],
        "version": collection["version"],
        "archive_bytes": collection["archive"]["bytes"],
        "archive_sha256": collection["archive"]["sha256"],
        "extracted_file_count": len(files),
        "extracted_tree_sha256": canonical_digest(files),
        "catalog_sha256": files[collection["catalog"]]["sha256"],
    }


def resolve_par(root: Path, name: str) -> Path:
    for relative in (name, f"all_years/{name}", f"additional/{name}", f"30-year/{name}", f"20-year/{name}", f"10-year/{name}"):
        path = root / relative
        if path.is_file():
            return path
    raise EvaluationError(f"catalog station does not resolve: {name}")


def station_rows(root: Path) -> list[dict[str, Any]]:
    catalog = root / "2015_stations.db"
    if not catalog.is_file():
        raise EvaluationError("us-2015 collection is not synced")
    connection = sqlite3.connect(f"file:{catalog}?mode=ro", uri=True)
    try:
        rows = connection.execute("select desc, par, latitude, longitude, years, elevation from stations").fetchall()
    finally:
        connection.close()
    if len(rows) != 2765:
        raise EvaluationError("us-2015 catalog row count differs")
    return [{"description": row[0], "id": row[1], "latitude": float(row[2]), "longitude": float(row[3]),
             "years": float(row[4]), "elevation": None if row[5] is None else float(row[5]),
             "path": resolve_par(root, row[1])} for row in rows]


def haversine_km(latitude: float, longitude: float, row: dict[str, Any]) -> float:
    p1, p2 = math.radians(latitude), math.radians(row["latitude"])
    dp = p2 - p1
    dl = math.radians(row["longitude"] - longitude)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 6371.0088 * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def monthly_row(lines: list[str], record: int) -> np.ndarray:
    line = lines[record - 1]
    return np.array(
        [float(line[8 + 6 * index:14 + 6 * index].replace(" ", "") or "0") for index in range(12)],
        dtype=np.float32,
    )


def parse_par(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise EvaluationError(f"non-ASCII par: {path}") from error
    if len(lines) < 83:
        raise EvaluationError(f"short par: {path}")
    return {
        "sha256": digest_bytes(raw), "mean": monthly_row(lines, 4), "sd": monthly_row(lines, 5),
        "skew": monthly_row(lines, 6), "pww": monthly_row(lines, 7), "pwd": monthly_row(lines, 8),
        "tmax": monthly_row(lines, 9), "tmin": monthly_row(lines, 10),
        "tmax_sd": monthly_row(lines, 11), "tmin_sd": monthly_row(lines, 12),
        "intensity": monthly_row(lines, 15),
    }


def station_ppt(par: dict[str, Any]) -> np.ndarray:
    mean = par["mean"].astype(np.float64)
    pww = par["pww"].astype(np.float64)
    pwd = par["pwd"].astype(np.float64)
    denominator = 1.0 - pww + pwd
    if np.any(denominator <= 0.0):
        raise EvaluationError("invalid occurrence denominator")
    return mean * DAYS * pwd / denominator


def f6_2_f32(value: float) -> float:
    rendered = f"{value:.2f}"
    if rendered == "-0.00":
        rendered = "0.00"
    if len(rendered) > 6:
        raise EvaluationError("localized value does not fit F6.2")
    return float(np.float32(float(rendered)))


def localized_parameters(par: dict[str, Any], normals: dict[str, Any]) -> dict[str, np.ndarray]:
    old_mean = par["mean"].astype(np.float64)
    old_pww = par["pww"].astype(np.float64)
    old_pwd = par["pwd"].astype(np.float64)
    targets = np.array(normals["monthly_ppt_in"], dtype=np.float64)
    target_tmax = np.array(normals["monthly_tmax_f"], dtype=np.float64)
    target_tmin = np.array(normals["monthly_tmin_f"], dtype=np.float64)
    intensity = par["intensity"].astype(np.float64)
    encoded_mean = np.zeros(12)
    encoded_pww = np.zeros(12)
    encoded_pwd = np.zeros(12)
    encoded_intensity = np.zeros(12)
    for month in range(12):
        denominator = 1.0 - old_pww[month] + old_pwd[month]
        q = old_pwd[month] / denominator
        current = DAYS[month] * q * old_mean[month]
        if not math.isfinite(current) or current <= 0.0 or not math.isfinite(q) or not 0.0 < q < 1.0:
            raise EvaluationError(f"month {month + 1} cannot be localized")
        delta = targets[month] / current
        old_count = DAYS[month] * q
        count = old_count
        if targets[month] >= 0.05 and current >= 0.05:
            count = min(max(old_count * (1.0 + delta) / 2.0, old_count / 2.0), old_count * 2.0)
            count = min(max(count, 0.1), DAYS[month] - 0.25)
        new_q = count / DAYS[month]
        persistence = old_pwd[month] / old_pww[month]
        new_pww = 1.0 / (1.0 - persistence + persistence / new_q)
        new_pwd = ((new_pww - 1.0) * new_q) / (new_q - 1.0)
        new_mean = targets[month] / (DAYS[month] * new_q)
        new_intensity = intensity[month] * (min(max(delta, 0.5), 2.0) if targets[month] >= 0.05 and current >= 0.05 else 1.0)
        if not all(math.isfinite(item) for item in (new_pww, new_pwd)) or not 0.0 < new_pww < 1.0 or not 0.0 < new_pwd < 1.0:
            raise EvaluationError(f"month {month + 1} produced invalid localized occurrence")
        encoded_mean[month] = f6_2_f32(new_mean)
        encoded_pww[month] = f6_2_f32(new_pww)
        encoded_pwd[month] = f6_2_f32(new_pwd)
        encoded_intensity[month] = f6_2_f32(new_intensity)
    encoded_tmax = np.array([f6_2_f32(value) for value in target_tmax])
    encoded_tmin = np.array([f6_2_f32(value) for value in target_tmin])
    for month in range(12):
        if ((targets[month] > 0.0 and encoded_mean[month] <= 0.0)
                or not 0.0 < encoded_pww[month] < 1.0
                or not 0.0 < encoded_pwd[month] < 1.0
                or encoded_tmax[month] < encoded_tmin[month]):
            raise EvaluationError(f"encoded constraints fail in month {month + 1}")
    return {"mean": encoded_mean, "pww": encoded_pww, "pwd": encoded_pwd,
            "tmax": encoded_tmax, "tmin": encoded_tmin, "intensity": encoded_intensity}


def localized_occurrence(par: dict[str, Any], target_ppt: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    normals = {"monthly_ppt_in": list(target_ppt), "monthly_tmax_f": [50.0] * 12,
               "monthly_tmin_f": [40.0] * 12}
    localized = localized_parameters(par, normals)
    return localized["pww"], localized["pwd"]


def ranks(values: Iterable[float], ids: list[str]) -> list[int]:
    values_list = list(values)
    order = sorted(range(len(values_list)), key=lambda index: (values_list[index], ids[index]))
    result = [0] * len(values_list)
    for rank, index in enumerate(order):
        result[index] = rank
    return result


def select_policies(rows: list[dict[str, Any]], target: dict[str, Any], normals: dict[str, Any], par_cache: dict[Path, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    nearest = sorted(rows, key=lambda row: (haversine_km(target["latitude"], target["longitude"], row), row["id"]))[:10]
    ids = [row["id"] for row in nearest]
    for row in nearest:
        row["distance_km"] = haversine_km(target["latitude"], target["longitude"], row)
        par_cache.setdefault(row["path"], parse_par(row["path"]))
    distance = ranks((row["distance_km"] for row in nearest), ids)
    latitude = ranks((abs(row["latitude"] - target["latitude"]) for row in nearest), ids)
    ppt_errors = [float(np.linalg.norm(station_ppt(par_cache[row["path"]]) - np.array(normals["monthly_ppt_in"]))) for row in nearest]
    ppt = ranks(ppt_errors, ids)
    tmax_errors = [float(np.linalg.norm(par_cache[row["path"]]["tmax"] - np.array(normals["monthly_tmax_f"]))) for row in nearest]
    tmin_errors = [float(np.linalg.norm(par_cache[row["path"]]["tmin"] - np.array(normals["monthly_tmin_f"]))) for row in nearest]
    tmax = ranks(tmax_errors, ids)
    tmin = ranks(tmin_errors, ids)
    elevation_errors = [math.inf if row["elevation"] is None else abs(row["elevation"] * 0.3048 - target["elevation_m"]) for row in nearest]
    elevation = ranks(elevation_errors, ids)
    current_scores = [distance[i] + latitude[i] + 3.0 * ppt[i] + 1.5 * tmax[i] + 1.5 * tmin[i] for i in range(10)]
    reference_scores = [distance[i] + latitude[i] + elevation[i] + 3.0 * ppt[i] for i in range(10)]
    def winner(scores: list[float]) -> dict[str, Any]:
        index = min(range(10), key=lambda i: (scores[i], nearest[i]["distance_km"], nearest[i]["id"]))
        return nearest[index]
    diagnostics = [
        {
            "station_id": row["id"], "source_par_sha256": par_cache[row["path"]]["sha256"],
            "distance_km": row["distance_km"], "latitude_error": abs(row["latitude"] - target["latitude"]),
            "ppt_error": ppt_errors[index], "tmax_error": tmax_errors[index], "tmin_error": tmin_errors[index],
            "distance_rank": distance[index], "latitude_rank": latitude[index], "ppt_rank": ppt[index],
            "tmax_rank": tmax[index], "tmin_rank": tmin[index], "current_score": current_scores[index],
            "elevation_rank": elevation[index], "reference_score": reference_scores[index],
        }
        for index, row in enumerate(nearest)
    ]
    return ({"closest_v1": nearest[0], "cligen_prism_rank_sum_v1": winner(current_scores),
             "wepppy_elevation_prism_reference_v1": winner(reference_scores)}, diagnostics)


def adjusted_skew(values: np.ndarray) -> float:
    n = len(values)
    sd = float(np.std(values, ddof=1))
    if n < 3 or sd <= 0.0:
        raise EvaluationError("skew descriptor is ineligible")
    return float(n / ((n - 1) * (n - 2)) * np.sum(((values - np.mean(values)) / sd) ** 3))


def wet_transition_counts(dates: list[dt.date], observed: np.ndarray, precipitation: np.ndarray,
                          indexes: Iterable[int]) -> tuple[int, int, int, int]:
    ww = wd = wet_prev = dry_prev = 0
    for index in indexes:
        if (index == 0 or not observed[index - 1]
                or dates[index] - dates[index - 1] != dt.timedelta(days=1)):
            continue
        previous_wet = precipitation[index - 1] > 0.0
        current_wet = precipitation[index] > 0.0
        if previous_wet:
            wet_prev += 1
            ww += int(current_wet)
        else:
            dry_prev += 1
            wd += int(current_wet)
    return ww, wd, wet_prev, dry_prev


def observed_descriptors(value: dict[str, Any]) -> dict[str, np.ndarray]:
    dates = [dt.date.fromisoformat(text) for text in value["dates"]]
    observed = np.array(value["source_observed"], dtype=bool)
    fields = {name: np.array(value["fields"][name], dtype=float) for name in ("prcp", "tmax", "tmin")}
    result = {name: np.zeros(12) for name in ("sd", "skew", "pww", "pwd", "tmax_sd", "tmin_sd")}
    for month in range(1, 13):
        indexes = [i for i, date in enumerate(dates) if date.month == month and observed[i]]
        positive = fields["prcp"][indexes]
        positive = positive[positive > 0.0]
        if len(positive) < 3:
            raise EvaluationError(f"{value['point_id']} month {month} has fewer than three wet days")
        result["sd"][month - 1] = float(np.std(positive / 25.4, ddof=1))
        result["skew"][month - 1] = adjusted_skew(positive)
        result["tmax_sd"][month - 1] = float(np.std(fields["tmax"][indexes], ddof=1) * 1.8)
        result["tmin_sd"][month - 1] = float(np.std(fields["tmin"][indexes], ddof=1) * 1.8)
        ww, wd, wet_prev, dry_prev = wet_transition_counts(
            dates, observed, fields["prcp"], indexes
        )
        if wet_prev == 0 or dry_prev == 0:
            raise EvaluationError(f"{value['point_id']} month {month} has incomplete transitions")
        result["pww"][month - 1] = ww / wet_prev
        result["pwd"][month - 1] = wd / dry_prev
    return result


def errors(par: dict[str, Any], observed: dict[str, np.ndarray], normals: dict[str, Any],
           localized_override: dict[str, Any] | None = None) -> dict[str, float]:
    localized = localized_parameters(par, normals) if localized_override is None else localized_override
    families = {
        METRICS[0]: np.abs(par["sd"].astype(np.float64) - observed["sd"]) / np.maximum(observed["sd"], 1e-6),
        METRICS[1]: np.abs(par["skew"].astype(np.float64) - observed["skew"]) / np.maximum(1.0, np.abs(observed["skew"])),
        METRICS[2]: np.abs(localized["pww"] - observed["pww"]),
        METRICS[3]: np.abs(localized["pwd"] - observed["pwd"]),
        METRICS[4]: np.abs(par["tmax_sd"].astype(np.float64) - observed["tmax_sd"]) / np.maximum(observed["tmax_sd"], 1e-6),
        METRICS[5]: np.abs(par["tmin_sd"].astype(np.float64) - observed["tmin_sd"]) / np.maximum(observed["tmin_sd"], 1e-6),
    }
    output = {name: float(np.median(values)) for name, values in families.items()}
    if not all(math.isfinite(value) for value in output.values()):
        raise EvaluationError("non-finite metric")
    output["composite"] = float(np.mean(list(output.values())))
    return output


def expected_axis(start: str, end: str) -> list[str]:
    current = dt.date.fromisoformat(start)
    stop = dt.date.fromisoformat(end)
    output = []
    while current <= stop:
        output.append(current.isoformat())
        current += dt.timedelta(days=1)
    return output


def load_fit_validation(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cohort = json.loads(COHORT.read_text())
    roster = {row["point_id"]: row for row in cohort["locations"] if row["role"] == "fit_validation"}
    if len(roster) != manifest["corpus"]["site_count"]:
        raise EvaluationError("fit-validation roster differs")
    regime_counts = {regime: sum(row["regime"] == regime for row in roster.values()) for regime in REGIMES}
    if regime_counts != {regime: 40 for regime in REGIMES}:
        raise EvaluationError("fit-validation regime balance differs")
    normalized = json.loads(NORMALIZED.read_text())
    objects: dict[str, dict[str, Any]] = {}
    shard_hashes = {}
    for shard in normalized["daymet_shards"]:
        path = ROOT / shard["path"]
        if digest(path) != shard["sha256"]:
            raise EvaluationError(f"Daymet shard hash differs: {path.name}")
        shard_hashes[path.name] = shard["sha256"]
        wanted = {f"{point_id}.json" for point_id in roster if point_id in shard["point_ids"]}
        if not wanted:
            continue
        with tarfile.open(path, "r:gz") as archive:
            for name in wanted:
                member = archive.extractfile(name)
                if member is None:
                    raise EvaluationError(f"missing Daymet object {name}")
                value = json.load(member)
                objects[value["point_id"]] = value
    if set(objects) != set(roster):
        raise EvaluationError("fit-validation objects are incomplete")
    masked_expected = set(manifest["corpus"]["masked_dates"])
    axis_expected = expected_axis(manifest["corpus"]["period_start"], manifest["corpus"]["period_end_inclusive"])
    object_hashes = {}
    for point_id, value in objects.items():
        if value["role"] != "fit_validation" or value["calendar_transform_id"] != manifest["corpus"]["source_transform"]:
            raise EvaluationError(f"role/calendar mismatch: {point_id}")
        if value["dates"] != axis_expected or len(value["source_observed"]) != 10958:
            raise EvaluationError(f"axis count mismatch: {point_id}")
        if set(value["fields"]) < {"prcp", "tmax", "tmin"}:
            raise EvaluationError(f"required field missing: {point_id}")
        if any(len(value["fields"][name]) != 10958 for name in ("prcp", "tmax", "tmin")):
            raise EvaluationError(f"field axis mismatch: {point_id}")
        masked = {date for date, flag in zip(value["dates"], value["source_observed"]) if not flag}
        if masked != masked_expected or sum(value["source_observed"]) != 10950:
            raise EvaluationError(f"observed mask mismatch: {point_id}")
        for index, flag in enumerate(value["source_observed"]):
            if flag and not all(math.isfinite(float(value["fields"][name][index])) for name in ("prcp", "tmax", "tmin")):
                raise EvaluationError(f"non-finite observed field: {point_id}")
        object_hashes[point_id] = canonical_digest(value)
    ordered = [objects[point_id] for point_id in sorted(objects)]
    preflight = {
        "schema_version": "a12-calendar-preflight-1",
        "source_transform": manifest["corpus"]["source_transform"],
        "role": "fit_validation",
        "period_start": axis_expected[0],
        "period_end_inclusive": axis_expected[-1],
        "calendar_axis_rows": len(axis_expected),
        "observed_rows_per_site": 10950,
        "masked_dates": sorted(masked_expected),
        "site_count": len(ordered),
        "regime_counts": regime_counts,
        "object_hashes": object_hashes,
        "shard_hashes": shard_hashes,
        "object_set_sha256": canonical_digest(object_hashes),
        "shard_set_sha256": canonical_digest(shard_hashes),
    }
    return ordered, preflight


def query_normals(binary: Path, data_root: Path, latitude: float, longitude: float) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["CLIGEN_DATA_DIR"] = str(data_root)
    result = subprocess.run([str(binary), "prism", "query", "--longitude", str(longitude), "--latitude", str(latitude), "--json"],
                            cwd=ROOT, check=False, capture_output=True, text=True, env=environment)
    if result.returncode != 0:
        raise EvaluationError(f"PRISM query failed: {result.stderr.strip()}")
    value = json.loads(result.stdout)
    expected_fields = {
        "schema_version", "bundle_id", "bundle_version", "grid_manifest_sha256",
        "source_manifest_sha256", "attribution", "requested_longitude", "requested_latitude",
        "row", "column", "cell_center_longitude", "cell_center_latitude", "monthly_ppt_mm",
        "monthly_tmax_c", "monthly_tmin_c", "monthly_ppt_in", "monthly_tmax_f", "monthly_tmin_f",
    }
    distribution = json.loads(PRISM_DISTRIBUTION.read_text())
    identity_ok = (
        value.get("schema_version") == 1
        and value.get("bundle_id") == distribution["bundle_id"]
        and value.get("bundle_version") == distribution["version"]
        and value.get("grid_manifest_sha256") == distribution["grid_manifest_sha256"]
        and value.get("source_manifest_sha256") == distribution["source_manifest_sha256"]
        and value.get("requested_latitude") == latitude
        and value.get("requested_longitude") == longitude
    )
    arrays = [value.get(name) for name in ("monthly_ppt_mm", "monthly_tmax_c", "monthly_tmin_c",
                                           "monthly_ppt_in", "monthly_tmax_f", "monthly_tmin_f")]
    if (set(value) != expected_fields or not identity_ok or
            any(not isinstance(array, list) or len(array) != 12 or
                not all(isinstance(item, (int, float)) and math.isfinite(item) for item in array)
                for array in arrays)):
        raise EvaluationError("PRISM query response contract differs")
    return value


def runtime_selection(binary: Path, data_root: Path, target: dict[str, Any]) -> dict[str, Any]:
    output = data_root / "runtime-selections" / target["point_id"]
    output.parent.mkdir(exist_ok=True)
    environment = os.environ.copy()
    environment["CLIGEN_DATA_DIR"] = str(data_root)
    result = subprocess.run(
        [str(binary), "prism", "run", "--longitude", str(target["longitude"]),
         "--latitude", str(target["latitude"]), "--years", "1", "--output-dir", str(output)],
        cwd=ROOT, check=False, capture_output=True, text=True, env=environment,
    )
    if result.returncode != 0:
        raise EvaluationError(f"runtime receipt probe failed: {result.stderr.strip()}")
    selection_path = output / "station-selection.json"
    artifact_path = output / "artifact-manifest.json"
    selection = json.loads(selection_path.read_text())
    artifact = json.loads(artifact_path.read_text())
    normals = json.loads((output / "prism-normals.json").read_text())
    binary_hash = digest(binary)
    if selection["schema_version"] != 2 or selection["cligen_binary_sha256"] != binary_hash:
        raise EvaluationError("station-selection receipt binary identity differs")
    if artifact["executable"]["sha256"] != binary_hash:
        raise EvaluationError("artifact manifest binary identity differs")
    source_hash = digest(output / "source-station.par")
    if selection["selected_source_par_sha256"] != source_hash:
        raise EvaluationError("station-selection source .par identity differs")
    normalized_selection = json.loads(json.dumps(selection))
    normalized_selection["selected_source_par_path"] = f"<station-cache>/{selection['selected_station_id']}"
    for candidate in normalized_selection["candidates"]:
        candidate["path"] = f"<station-cache>/{candidate['station_id']}"
    return {
        "point_id": target["point_id"],
        "normalized_station_selection_sha256": canonical_digest(normalized_selection),
        "cligen_binary_sha256": binary_hash,
        "selected_station_id": selection["selected_station_id"],
        "selected_source_par_sha256": source_hash,
        "selection_and_manifest_binary_sha256_equal": True,
        "_selection": selection,
        "_normals": normals,
        "_localized_par": parse_par(output / "localized.par"),
    }


def verify_selector_parity(selection: dict[str, Any], selected: dict[str, dict[str, Any]],
                           diagnostics: list[dict[str, Any]]) -> None:
    if selection["selected_station_id"] != selected["cligen_prism_rank_sum_v1"]["id"]:
        raise EvaluationError("Python/Rust current-selector winner differs")
    rust = {row["station_id"]: row for row in selection["candidates"]}
    if set(rust) != {row["station_id"] for row in diagnostics}:
        raise EvaluationError("Python/Rust current-selector pool differs")
    exact_fields = ("distance_rank", "latitude_rank", "ppt_rank", "tmax_rank", "tmin_rank")
    value_fields = ("distance_km", "latitude_error", "ppt_error", "tmax_error", "tmin_error")
    for row in diagnostics:
        actual = rust[row["station_id"]]
        if any(actual[name] != row[name] for name in exact_fields):
            raise EvaluationError("Python/Rust current-selector ranks differ")
        if any(not math.isclose(actual[name], row[name], rel_tol=1e-13, abs_tol=1e-13)
               for name in value_fields):
            raise EvaluationError("Python/Rust current-selector component differs")


def bootstrap_rng(contract: dict[str, Any]) -> np.random.Generator:
    domain_words = np.frombuffer(hashlib.sha256(contract["domain"].encode()).digest(), dtype="<u4")
    seed = np.random.SeedSequence([contract["seed"], *[int(word) for word in domain_words]])
    return np.random.Generator(np.random.Philox(seed))


def bootstrap_interval(deltas: np.ndarray, manifest: dict[str, Any]) -> list[float]:
    contract = manifest["bootstrap"]
    rng = bootstrap_rng(contract)
    indexes = rng.integers(0, len(deltas), size=(manifest["bootstrap"]["replicates"], len(deltas)))
    medians = np.median(deltas[indexes], axis=1)
    return [float(np.quantile(medians, 0.025, method=contract["quantile_method"])),
            float(np.quantile(medians, 0.975, method=contract["quantile_method"]))]


def summarize(site_rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_policy = {policy: [row["policies"][policy] for row in site_rows] for policy in POLICIES}
    summaries = {}
    supported = {}
    closest = by_policy["closest_v1"]
    closest_family = {metric: float(np.median([row["metrics"][metric] for row in closest])) for metric in METRICS}
    for policy in POLICIES:
        rows = by_policy[policy]
        summary = {"median_composite": float(np.median([row["metrics"]["composite"] for row in rows])),
                   "family_medians": {metric: float(np.median([row["metrics"][metric] for row in rows])) for metric in METRICS}}
        if policy != "closest_v1":
            deltas = np.array([row["metrics"]["composite"] - closest[index]["metrics"]["composite"] for index, row in enumerate(rows)])
            summary["paired_composite_median_delta"] = float(np.median(deltas))
            summary["paired_bootstrap_95_interval"] = bootstrap_interval(deltas, manifest)
            summary["strict_site_win_fraction"] = float(np.mean(deltas < 0.0))
            paired_family = {
                metric: float(np.median([row["metrics"][metric] - closest[index]["metrics"][metric]
                                         for index, row in enumerate(rows)]))
                for metric in METRICS
            }
            summary["paired_family_median_deltas"] = paired_family
            summary["family_worsening_fractions"] = {
                metric: None if closest_family[metric] == 0.0 else
                (summary["family_medians"][metric] - closest_family[metric]) / closest_family[metric]
                for metric in METRICS
            }
            family_ok = all(summary["family_medians"][metric] <=
                            closest_family[metric] * (1.0 + manifest["decision"]["family_worsening_limit_fraction"])
                            for metric in METRICS)
            supported[policy] = (summary["paired_composite_median_delta"] < 0.0 and summary["paired_bootstrap_95_interval"][1] < 0.0
                                 and summary["strict_site_win_fraction"] > 0.5
                                 and family_ok)
            summary["supported"] = supported[policy]
        summaries[policy] = summary
    current, reference = POLICIES[1], POLICIES[2]
    if supported[current] and (not supported[reference] or summaries[current]["median_composite"] <= summaries[reference]["median_composite"]):
        disposition = "CURRENT_HEURISTIC_APPROPRIATE"
    elif supported[reference]:
        disposition = "ELEVATION_REFERENCE_BETTER"
    else:
        disposition = "CLOSEST_PREFERRED"
    return summaries, {"schema_version": "a12-station-selection-decision-1", "evaluation_id": manifest["evaluation_id"],
                       "disposition": disposition, "current_heuristic_supported": supported[current],
                       "elevation_reference_supported": supported[reference], "confirmation_authorized": False,
                       "runtime_default_change_authorized": False, "terminal": "EXECUTED-COMPLETE"}


def execute(source_commit: str, binary: Path, build_receipt_path: Path, station_archive: Path) -> None:
    started = time.perf_counter()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if {"python": platform.python_version(), "numpy": np.__version__} != manifest["runtime"]:
        raise EvaluationError("scientific runtime identity differs")
    input_hashes = verify_inputs(manifest)
    source_hashes = verify_source(source_commit)
    binary = binary.resolve()
    if not binary.is_file():
        raise EvaluationError("cligen binary does not exist")
    binary_sha256 = digest(binary)
    verify_build_receipt(source_commit, source_hashes, binary, build_receipt_path)
    station_manifest = json.loads(STATION_MANIFESTS.read_text())
    next(row for row in station_manifest["collections"] if row["name"] == "us-2015")
    prism_cache_identity = verify_prism_cache(cache_root())
    prism_runtime_path = Path(prism_cache_identity.pop("_runtime_path"))
    with tempfile.TemporaryDirectory(prefix="cligen-a12-") as temporary:
        isolated_root = Path(temporary)
        collection_root, station_cache_identity = extract_registered_station_archive(station_archive, isolated_root)
        isolated_prism = (isolated_root / "prism" / prism_cache_identity["bundle_id"] /
                          prism_cache_identity["bundle_version"])
        isolated_prism.parent.mkdir(parents=True)
        shutil.copytree(prism_runtime_path, isolated_prism, copy_function=shutil.copy2)
        isolated_prism_identity = verify_prism_cache(isolated_root)
        isolated_prism_identity.pop("_runtime_path")
        if isolated_prism_identity != prism_cache_identity:
            raise EvaluationError("isolated PRISM copy identity differs")
        isolated_binary = isolated_root / "bin/cligen"
        isolated_binary.parent.mkdir()
        shutil.copy2(binary, isolated_binary)
        if digest(isolated_binary) != binary_sha256:
            raise EvaluationError("isolated cligen binary identity differs")
        rows = station_rows(collection_root)
        objects, preflight_identity = load_fit_validation(manifest)
        preflight_path = PACKAGE / "calendar-preflight-v1.json"
        atomic_json(preflight_path, preflight_identity)
        par_cache: dict[Path, dict[str, Any]] = {}
        site_rows = []
        grid_identities = set()
        runtime_probes = []
        for value in objects:
            target = {"point_id": value["point_id"], "latitude": value["latitude"], "longitude": value["longitude"], "elevation_m": value["elevation_m"]}
            probe = runtime_selection(isolated_binary, isolated_root, target)
            normals = probe.pop("_normals")
            current_localized = probe.pop("_localized_par")
            grid_identities.add((normals["bundle_id"], normals["bundle_version"], normals["grid_manifest_sha256"], normals["source_manifest_sha256"]))
            selected, candidate_diagnostics = select_policies(rows, target, normals, par_cache)
            verify_selector_parity(probe["_selection"], selected, candidate_diagnostics)
            selected["cligen_prism_rank_sum_v1"] = next(
                row for row in rows if row["id"] == probe["selected_station_id"]
            )
            selected["cligen_prism_rank_sum_v1"]["distance_km"] = haversine_km(
                target["latitude"], target["longitude"], selected["cligen_prism_rank_sum_v1"]
            )
            del probe["_selection"]
            runtime_probes.append(probe)
            observed = observed_descriptors(value)
            policy_rows = {}
            for policy, station in selected.items():
                par = par_cache[station["path"]]
                localized_override = current_localized if policy == "cligen_prism_rank_sum_v1" else None
                policy_rows[policy] = {"selected_station_id": station["id"], "selected_source_par_sha256": par["sha256"],
                                       "distance_km": station["distance_km"],
                                       "metrics": errors(par, observed, normals, localized_override)}
            site_rows.append({"point_id": value["point_id"], "regime": value["regime"],
                              "candidate_pool": candidate_diagnostics, "policies": policy_rows})
        if digest(isolated_binary) != binary_sha256 or verify_prism_cache(isolated_root)["file_set_sha256"] != prism_cache_identity["file_set_sha256"]:
            raise EvaluationError("isolated runtime identity changed during evaluation")
    if len(grid_identities) != 1 or len(site_rows) != 240:
        raise EvaluationError("PRISM identity or site count differs")
    summaries, decision = summarize(site_rows, manifest)
    evidence = {"schema_version": "a12-station-selection-evidence-1", "evaluation_id": manifest["evaluation_id"],
                "source_commit": source_commit, "cligen_binary_sha256": binary_sha256,
                "build_receipt_sha256": digest(build_receipt_path),
                "station_collection": station_cache_identity,
                "prism_identity": list(next(iter(grid_identities))), "prism_cache_identity": prism_cache_identity,
                "preflight_identity": {"sha256": digest(preflight_path), "object_set_sha256": preflight_identity["object_set_sha256"],
                                       "shard_set_sha256": preflight_identity["shard_set_sha256"]},
                "runtime_selection_receipts": runtime_probes,
                "site_count": len(site_rows), "policy_summaries": summaries, "site_results": site_rows,
                "confirmation_target_series_accessed": False}
    evidence["evidence_sha256"] = canonical_digest(evidence)
    evidence_path = PACKAGE / "station-selection-evidence-v1.json"
    decision_path = PACKAGE / "station-selection-decision-v1.json"
    atomic_json(evidence_path, evidence)
    atomic_json(decision_path, decision)
    receipt = {"schema_version": "a12-execution-receipt-1", "evaluation_id": manifest["evaluation_id"],
               "source_commit": source_commit, "cligen_binary_sha256": binary_sha256, "input_hashes": input_hashes,
               "build_receipt_sha256": digest(build_receipt_path),
               "station_archive_sha256": digest(station_archive),
               "prism_cache_file_set_sha256": prism_cache_identity["file_set_sha256"],
               "source_hashes": source_hashes,
               "outputs": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size}
                           for path in (preflight_path, evidence_path, decision_path)},
               "elapsed_seconds": time.perf_counter() - started, "confirmation_target_series_accessed": False}
    atomic_json(PACKAGE / "execution-receipt-v1.json", receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--cligen-binary", type=Path)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--station-archive", type=Path)
    arguments = parser.parse_args()
    manifest = validate_manifest(json.loads(MANIFEST_PATH.read_text()))
    if arguments.validate_manifest:
        verify_inputs(manifest)
        print(canonical_digest(manifest))
        return
    if arguments.build and arguments.source_commit:
        build_release(arguments.source_commit)
        return
    if (arguments.execute and arguments.source_commit and arguments.cligen_binary
            and arguments.build_receipt and arguments.station_archive):
        execute(arguments.source_commit, arguments.cligen_binary, arguments.build_receipt,
                arguments.station_archive)
        return
    parser.error("choose --validate-manifest, --build with source, or --execute with source, binary, build receipt, and station archive")


if __name__ == "__main__":
    main()
