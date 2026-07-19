#!/usr/bin/env python3
"""Run frozen observation/comparator arms and score collected neural streams."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from temporal_metrics import realized_metrics


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    partial.replace(path)


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def parse_cli(path: Path) -> tuple[list[dt.date], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dates: list[dt.date] = []
    precipitation: list[float] = []
    tmax: list[float] = []
    tmin: list[float] = []
    peak: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            day, month, year = (int(fields[index]) for index in range(3))
            values = [float(value) for value in fields[3:]]
            date = dt.date(year, month, day)
        except ValueError:
            continue
        prcp, duration, _, peak_ratio, tx, tn = values[:6]
        dates.append(date)
        precipitation.append(prcp)
        tmax.append(tx)
        tmin.append(tn)
        peak.append(peak_ratio * prcp / duration if duration > 0.0 else 0.0)
    if not dates:
        raise RuntimeError(f"no daily rows parsed from {path}")
    return dates, *(np.asarray(values, dtype=np.float64) for values in (precipitation, tmax, tmin, peak))


def observation(shard_root: Path, site: dict[str, Any]) -> tuple[dict[str, float], list[dict[str, Any]]]:
    path = shard_root / site["daymet_shard"]
    if digest(path) != site["daymet_shard_sha256"]:
        raise RuntimeError(f"observation shard identity mismatch: {path.name}")
    with tarfile.open(path, "r:gz") as archive:
        handle = archive.extractfile(f"{site['point_id']}.json")
        if handle is None:
            raise RuntimeError(f"point absent from {path.name}")
        document = json.load(handle)
    keep = [
        bool(observed)
        and all(document["fields"][name][index] is not None for name in ("prcp", "tmax", "tmin"))
        for index, observed in enumerate(document["source_observed"])
    ]
    dates = [dt.date.fromisoformat(value) for value, include in zip(document["dates"], keep) if include]
    arrays = [
        np.asarray([value for value, include in zip(document["fields"][name], keep) if include], dtype=np.float64)
        for name in ("prcp", "tmax", "tmin")
    ]
    if len(dates) != 10950:
        raise RuntimeError("observation row contract mismatch")
    blocks = []
    for year in sorted({date.year for date in dates}):
        indices = [index for index, date in enumerate(dates) if date.year == year]
        blocks.append({
            "dates": [dates[index] for index in indices],
            "precipitation": arrays[0][indices],
            "tmax": arrays[1][indices],
            "tmin": arrays[2][indices],
        })
    return realized_metrics(dates, *arrays), blocks


def resampled_observation(blocks: list[dict[str, Any]], indices: np.ndarray) -> dict[str, float]:
    dates: list[dt.date] = []
    precipitation: list[np.ndarray] = []
    tmax: list[np.ndarray] = []
    tmin: list[np.ndarray] = []
    for position, index in enumerate(indices):
        block = blocks[int(index)]
        source_year = block["dates"][0].year
        target_year = source_year + 400 * (position + 1)
        dates.extend(date.replace(year=target_year) for date in block["dates"])
        precipitation.append(block["precipitation"])
        tmax.append(block["tmax"])
        tmin.append(block["tmin"])
    return realized_metrics(dates, np.concatenate(precipitation), np.concatenate(tmax), np.concatenate(tmin))


def runspec(par: Path, output: Path, years: int, burn: int, echo: str) -> str:
    return (
        "cligen_runspec: 1\n"
        f"station:\n  par: {par}\n"
        "mode: continuous\n"
        f"simulation:\n  begin_year: 2001\n  years: {years}\n  interpolation: none\n"
        f"rng:\n  burn: {burn}\n"
        "generation_profile: faithful_5_32_3\nqc_filter: faithful\n"
        f"output:\n  cli: {output}\n  quality: false\n  overwrite: false\n  command_echo: {echo}\n"
    )


def comparator_streams(
    binary: Path,
    data_root: Path,
    scratch: Path,
    site: dict[str, Any],
    years: int,
    burns: list[int],
) -> tuple[dict[str, list[dict[str, float]]], dict[str, Any]]:
    localize = scratch / "localization" / site["point_id"]
    localize.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(__import__("os").environ)
    environment["CLIGEN_DATA_DIR"] = str(data_root)
    run([
        str(binary), "prism", "run", "--longitude", str(site["longitude"]),
        "--latitude", str(site["latitude"]), "--years", str(years),
        "--output-dir", str(localize),
    ], env=environment)
    arms: dict[str, list[dict[str, float]]] = defaultdict(list)
    for arm, parameter_name in (("faithful", "source-station.par"), ("stochastic_prism_localized_par_v1", "localized.par")):
        for member, burn in enumerate(burns):
            root = scratch / "runs" / site["point_id"] / arm / f"member-{member}"
            root.mkdir(parents=True, exist_ok=False)
            cli = root / "climate.cli"
            spec = root / "inp.yaml"
            spec.write_text(runspec(localize / parameter_name, cli, years, burn, f"a10m5r4r2r1 {arm} {member}"), encoding="utf-8")
            run([str(binary), "run", str(spec)], env=environment)
            values = parse_cli(cli)
            arms[arm].append(realized_metrics(*values))
    provenance = {
        "artifact_manifest_sha256": digest(localize / "artifact-manifest.json"),
        "localization_sha256": digest(localize / "localization.json"),
        "normals_sha256": digest(localize / "prism-normals.json"),
        "source_station_sha256": digest(localize / "source-station.par"),
        "localized_station_sha256": digest(localize / "localized.par"),
        "station_selection_sha256": digest(localize / "station-selection.json"),
    }
    return dict(arms), provenance


def mean_metrics(streams: list[dict[str, float]]) -> dict[str, float]:
    keys = set(streams[0])
    if any(set(stream) != keys for stream in streams):
        raise RuntimeError("metric key mismatch")
    return {key: float(np.mean([stream[key] for stream in streams])) for key in sorted(keys)}


def scale(key: str, generated: float, observed: float) -> float:
    if key.startswith("intensity."):
        raise KeyError(key)
    if "precipitation_" in key and any(name in key for name in ("mean", "standard_deviation", "q10", "q50", "q90", "q95")):
        return abs(math.log(generated + 0.1) - math.log(observed + 0.1)) / 0.25
    if "coefficient_of_variation" in key:
        return abs(generated - observed) / 0.25
    if "skew" in key:
        return abs(generated - observed) / 0.5
    if key.startswith("occurrence.") or "dry_frequency" in key:
        return abs(generated - observed) / 0.05
    if "correlation" in key or "lag1" in key:
        return abs(generated - observed) / 0.1
    if "tmax_mean" in key or "tmin_mean" in key:
        return abs(generated - observed)
    if "tmax_standard_deviation" in key or "tmin_standard_deviation" in key:
        return abs(generated - observed) / 0.5
    raise RuntimeError(f"unregistered component scale: {key}")


def composite(streams: list[dict[str, float]], observed: dict[str, float]) -> float:
    generated = mean_metrics(streams)
    common = sorted(set(generated) & set(observed) - {key for key in generated if key.startswith("intensity.")})
    errors = [scale(key, generated[key], observed[key]) for key in common]
    if not errors or not all(math.isfinite(value) for value in errors):
        raise RuntimeError("empty or non-finite composite")
    return float(np.mean(errors))


def neural_streams(root: Path, models: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, float]]]]:
    output: dict[str, dict[str, list[tuple[int, int, dict[str, float]]]]] = defaultdict(lambda: defaultdict(list))
    for model in models:
        document = read(root / "results" / model["row_id"] / "streams.json")
        if document.get("valid") is False or not document.get("streams"):
            raise RuntimeError(f"invalid neural stream role: {model['row_id']}")
        for stream in document["streams"]:
            output[model["capacity_id"]][stream["point_id"]].append((model["training_seed"], stream["member_id"], stream["metrics"]))
    ordered: dict[str, dict[str, list[dict[str, float]]]] = defaultdict(dict)
    for capacity, sites in output.items():
        for point, rows in sites.items():
            rows.sort(key=lambda value: (value[0], value[1]))
            ordered[capacity][point] = [value[2] for value in rows]
            if len(rows) != 24:
                raise RuntimeError("candidate stream count mismatch")
    return dict(ordered)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--observation-shards", type=Path, required=True)
    parser.add_argument("--neural-root", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True)
    options = parser.parse_args()
    contract = read(options.contract)
    sites = read(options.sites)["sites"]
    neural = neural_streams(options.neural_root, contract["models"])
    observations: dict[str, dict[str, float]] = {}
    blocks: dict[str, list[dict[str, Any]]] = {}
    comparators: dict[str, dict[str, list[dict[str, float]]]] = {}
    provenance = {}
    for site in sites:
        point = site["point_id"]
        observations[point], blocks[point] = observation(options.observation_shards, site)
        comparators[point], provenance[point] = comparator_streams(
            options.binary, options.data_root, options.scratch, site,
            contract["generation"]["horizon_years"], contract["generation"]["stochastic_burn_counts"],
        )
    point_rows = {}
    for site in sites:
        point = site["point_id"]
        errors = {
            arm: composite(streams, observations[point])
            for arm, streams in comparators[point].items()
        }
        reference = min(errors.values())
        capacities = {capacity: composite(neural[capacity][point], observations[point]) for capacity in ("P1", "P2")}
        point_rows[point] = {
            "capacity_errors": capacities,
            "capacity_ratios": {capacity: value / reference for capacity, value in capacities.items()},
            "comparator_errors": errors,
            "reference_error": reference,
            "regime": site["regime"],
        }
    rng = np.random.default_rng(410542)
    medians = {"P1": [], "P2": []}
    reductions = []
    for _ in range(1000):
        ratios = {"P1": [], "P2": []}
        paired_errors = {"P1": [], "P2": []}
        for site in sites:
            point = site["point_id"]
            observed = resampled_observation(blocks[point], rng.integers(0, len(blocks[point]), len(blocks[point])))
            comparator_indices = rng.integers(0, 8, 8)
            comparator_errors = [
                composite([comparators[point][arm][int(index)] for index in comparator_indices], observed)
                for arm in ("faithful", "stochastic_prism_localized_par_v1")
            ]
            reference = min(comparator_errors)
            candidate_indices = rng.integers(0, 24, 24)
            for capacity in ("P1", "P2"):
                error = composite([neural[capacity][point][int(index)] for index in candidate_indices], observed)
                paired_errors[capacity].append(error)
                ratios[capacity].append(error / reference)
        for capacity in ("P1", "P2"):
            medians[capacity].append(float(np.median(ratios[capacity])))
        p1, p2 = float(np.mean(paired_errors["P1"])), float(np.mean(paired_errors["P2"]))
        reductions.append((p1 - p2) / p1)
    decisions = {}
    for capacity in ("P1", "P2"):
        upper = float(np.quantile(medians[capacity], 0.90))
        maximum = max(row["capacity_ratios"][capacity] for row in point_rows.values())
        decisions[capacity] = {
            "bootstrap_median_regime_ratio_upper_90_percent": upper,
            "maximum_regime_ratio": maximum,
            "temporally_eligible": upper <= 1.25 and maximum <= 1.5,
        }
    preference_probability = float(np.mean(np.asarray(reductions) >= 0.10))
    eligible = [capacity for capacity in ("P1", "P2") if decisions[capacity]["temporally_eligible"]]
    result = {
        "a10m5r5_authorized": bool(eligible),
        "bootstrap": {"replicates": 1000, "seed": 410542},
        "capacity_decisions": decisions,
        "eligible_capacities": eligible,
        "p2_temporal_preference": {
            "bootstrap_probability_reduction_at_least_10_percent": preference_probability,
            "preferred": preference_probability >= 0.90,
        },
        "point_results": point_rows,
        "prism_provenance": provenance,
        "protected_roles_opened": [],
        "schema_version": 1,
        "terminal": "A10M5R4R2R1-TEMPORAL-READY" if eligible else "HOLD-A10-NO-TEMPORALLY-ELIGIBLE-CAPACITY",
    }
    atomic_json(options.output, result)
    print(result["terminal"])


if __name__ == "__main__":
    main()
