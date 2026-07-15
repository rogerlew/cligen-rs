"""Candidate-blind A9c same-observed-law null calibration."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from research.a9c.data import ARTIFACTS, LARGE, REPO, canonical_bytes, sha256_path
from research.a9c.models import FIT_DIRECTORY, load_daymet, load_uscrn


REGISTRY = REPO / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/objective-registry-v1.json"
THRESHOLDS = ARTIFACTS / "null-thresholds-v1.json"
REPLICATES = ARTIFACTS / "large/null-calibration/null-replicates-v1.json.gz"
FAMILIES = ("occurrence_spell", "wet_amount", "aggregate", "extreme", "storm_descriptor", "compound_context", "winter_proxy")


def lag1(values: list[float]) -> float:
    if len(values) < 3 or np.std(values[:-1]) == 0.0 or np.std(values[1:]) == 0.0:
        return 0.0
    return float(np.corrcoef(values[:-1], values[1:])[0, 1])


def daymet_year_features(payload: dict[str, Any]) -> dict[int, dict[str, list[float]]]:
    by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in payload["records"]:
        by_year[int(row["date"][:4])].append(row)
    result = {}
    for year, rows in sorted(by_year.items()):
        precip = np.asarray([float(row["prcp_mm"]) for row in rows])
        wet0 = precip > 0.0
        wet1 = precip >= 1.0
        positive = precip[wet0]
        tmean = np.asarray([(float(row["tmax_c"]) + float(row["tmin_c"])) / 2.0 for row in rows])
        monthly = defaultdict(float)
        for row in rows:
            monthly[int(row["date"][5:7])] += float(row["prcp_mm"])
        month_values = [monthly[index] for index in range(1, 13)]
        rolling = {window: max(float(np.convolve(precip, np.ones(window), mode="valid").max()), 0.0) for window in (1, 3, 5)}
        wet_temp = float(tmean[wet0].mean()) if wet0.any() else float(tmean.mean())
        dry_temp = float(tmean[~wet0].mean()) if (~wet0).any() else float(tmean.mean())
        cold = tmean < 0.0
        transitions = float(np.count_nonzero((tmean[:-1] < 0.0) != (tmean[1:] < 0.0)))
        result[year] = {
            "aggregate": [float(sum(month_values)), float(np.std(month_values) / max(np.mean(month_values), 1.0e-6)), float(sum(value == 0.0 for value in month_values) / 12.0), lag1(month_values)],
            "compound_context": [wet_temp - dry_temp, float(np.mean((precip > 0.0) & (tmean < 0.0))), 0.0, 0.0, 0.0],
            "extreme": [rolling[1], rolling[3], rolling[5]],
            "occurrence_spell": [float(wet0.mean()), float(wet1.mean()), float(np.mean(wet1[:-1] == wet1[1:])), float(np.mean(wet1[:-2] == wet1[2:]))],
            "wet_amount": [float(positive.mean()) if len(positive) else 0.0, float(positive.std() / max(positive.mean(), 1.0e-6)) if len(positive) else 0.0, float(np.quantile(positive, 0.95)) if len(positive) else 0.0, lag1(positive.tolist())],
            "winter_proxy": [float(np.mean(wet0[cold])) if cold.any() else 0.0, transitions, float(np.corrcoef(precip, tmean)[0, 1]) if np.std(precip) > 0.0 else 0.0],
        }
    return result


def uscrn_year_features(payload: dict[str, Any]) -> dict[int, dict[str, list[float]]]:
    events: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in payload["events"]:
        events[int(event["start_lst"][:4])].append(event)
    result = {}
    for year, rows in sorted(events.items()):
        duration = np.asarray([float(row["duration_min"]) for row in rows])
        ttp = np.asarray([float(row["time_to_peak_fraction"]) for row in rows])
        peak = np.asarray([float(row["peak_ratio"]) for row in rows])
        depth = np.asarray([float(row["depth_mm"]) for row in rows])
        correlation = float(np.corrcoef(np.log1p(depth), np.log(duration))[0, 1]) if len(rows) >= 3 and np.std(depth) > 0.0 and np.std(duration) > 0.0 else 0.0

        def present(name: str) -> list[float]:
            return [float(row[name]) for row in rows if row.get(name) is not None]

        humidity = present("relative_humidity_pct")
        solar = present("solar_radiation_w_m2")
        wind = present("wind_speed_1_5m_m_s")
        result[year] = {
            "compound_context": [0.0, 0.0, float(np.mean(humidity)) if humidity else 0.0, float(np.mean(solar)) if solar else 0.0, float(np.mean(wind)) if wind else 0.0],
            "storm_descriptor": [float(np.median(duration)), float(np.median(ttp)), float(np.median(peak)), correlation],
        }
    return result


def observed_blocks() -> dict[str, dict[str, list[list[float]]]]:
    blocks: dict[str, dict[str, list[list[float]]]] = {family: defaultdict(list) for family in FAMILIES}
    for payload in load_daymet("development").values():
        for features in daymet_year_features(payload).values():
            for family, vector in features.items():
                blocks[family][payload["stratum"]].append(vector)
    for payload in load_uscrn("development").values():
        for features in uscrn_year_features(payload).values():
            for family, vector in features.items():
                blocks[family][payload["stratum"]].append(vector)
    return blocks


def seed(family: str, horizon: int, replicate: int) -> int:
    material = f"a9c-null-v1\0{family}\0{horizon}\0{replicate}".encode()
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


def calibrate() -> None:
    if FIT_DIRECTORY.exists() and any(FIT_DIRECTORY.glob("*.json")):
        raise ValueError("candidate fits exist before candidate-blind calibration")
    if THRESHOLDS.exists() or REPLICATES.exists():
        raise FileExistsError("null evidence exists")
    registry = json.loads(REGISTRY.read_text())
    blocks = observed_blocks()
    replicates = []
    threshold_rows = []
    for family in FAMILIES:
        objectives = [row for row in registry["objectives"] if row["family"] == family]
        floor = max(float(row.get("absolute_floor", 0.0)) for row in objectives)
        for horizon in (30, 100):
            values = []
            identities = []
            for replicate in range(500):
                generator = np.random.Generator(np.random.Philox(seed(family, horizon, replicate)))
                maxima = []
                for stratum, raw in sorted(blocks[family].items()):
                    array = np.asarray(raw, dtype=float)
                    scale = np.maximum(np.std(array, axis=0, ddof=1), floor if floor > 0.0 else 1.0e-6)
                    first = array[generator.integers(0, len(array), size=horizon)].mean(axis=0)
                    second = array[generator.integers(0, len(array), size=horizon)].mean(axis=0)
                    maxima.append(float(np.max(np.abs(first - second) / scale)))
                statistic = max(maxima)
                values.append(statistic)
                identity = hashlib.sha256(f"{family}:{horizon}:{replicate}:{statistic:.17g}".encode()).hexdigest()
                identities.append(identity)
                replicates.append({"family": family, "horizon_years": horizon, "identity_sha256": identity, "replicate": replicate, "max_statistic": statistic})
            threshold = float(np.quantile(np.asarray(values), 0.95, method="higher"))
            threshold_rows.append(
                {
                    "absolute_floor_max": floor,
                    "family": family,
                    "horizon_years": horizon,
                    "max_statistic_95": threshold,
                    "replicate_count": 500,
                    "replicate_identity_sha256": hashlib.sha256(canonical_bytes(identities)).hexdigest(),
                }
            )
    REPLICATES.parent.mkdir(parents=True, exist_ok=True)
    logical = canonical_bytes({"replicates": replicates, "schema_version": 1})
    with REPLICATES.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
            stream.write(logical)
    output = {
        "candidate_access_prohibited": True,
        "candidate_fit_count_at_calibration": 0,
        "familywise_alpha": 0.05,
        "method": "paired_same_observed_law_stratified_year_or_event_block_max_statistic",
        "objective_registry_sha256": sha256_path(REGISTRY),
        "replicate_object": {
            "bytes": REPLICATES.stat().st_size,
            "logical_sha256": hashlib.sha256(logical).hexdigest(),
            "object_sha256": sha256_path(REPLICATES),
            "path": str(REPLICATES.relative_to(REPO)),
        },
        "schema_version": 1,
        "thresholds": threshold_rows,
    }
    THRESHOLDS.write_bytes(canonical_bytes(output))
    print(f"calibrated {len(threshold_rows)} family/horizon gates from {len(replicates)} identities")


def verify() -> None:
    thresholds = json.loads(THRESHOLDS.read_text())
    with gzip.open(REPLICATES, "rb") as stream:
        logical = stream.read()
    if hashlib.sha256(logical).hexdigest() != thresholds["replicate_object"]["logical_sha256"]:
        raise ValueError("null logical hash")
    if sha256_path(REPLICATES) != thresholds["replicate_object"]["object_sha256"]:
        raise ValueError("null object hash")
    payload = json.loads(logical)
    if len(payload["replicates"]) != 7000:
        raise ValueError("null replicate count")
    if len(thresholds["thresholds"]) != 14 or any(row["replicate_count"] != 500 for row in thresholds["thresholds"]):
        raise ValueError("null threshold matrix")
    print("PASS: 7 families x 2 horizons x 500 candidate-blind replicates")


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["calibrate"]:
        calibrate()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("usage: python -m research.a9c.nulls calibrate|verify")
