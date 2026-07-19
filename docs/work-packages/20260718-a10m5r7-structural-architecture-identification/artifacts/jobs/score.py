#!/usr/bin/env python3
"""Run the conditional unchanged temporal score for A10M5R7."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from temporal_metrics import realized_metrics

EXPECTED_COMPARATOR_TREE = "c4d7bf9c2b8441b89ceda42ec1ef5e7976ee533f998eff473bece2f967154607"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def tree_identity(root: Path) -> tuple[int, int, str]:
    value = hashlib.sha256()
    files = 0
    byte_count = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        relative = str(path.relative_to(root))
        value.update(relative.encode())
        value.update(b"\0")
        value.update(str(len(payload)).encode())
        value.update(b"\0")
        value.update(hashlib.sha256(payload).hexdigest().encode())
        value.update(b"\n")
        files += 1
        byte_count += len(payload)
    return files, byte_count, value.hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    partial.replace(path)


def parse_cli(path: Path) -> tuple[list[dt.date], np.ndarray, np.ndarray, np.ndarray]:
    dates: list[dt.date] = []
    precipitation: list[float] = []
    tmax: list[float] = []
    tmin: list[float] = []
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
        dates.append(date)
        precipitation.append(values[0])
        tmax.append(values[4])
        tmin.append(values[5])
    if not dates:
        raise RuntimeError(f"no daily rows parsed from {path}")
    return dates, *(np.asarray(values, dtype=np.float64) for values in (precipitation, tmax, tmin))


def observation(shard_root: Path, site: dict[str, Any]) -> tuple[dict[str, float], list[dict[str, Any]]]:
    path = shard_root / site["daymet_shard"]
    if digest(path) != site["daymet_shard_sha256"]:
        raise RuntimeError("observation shard identity mismatch")
    with tarfile.open(path, "r:gz") as archive:
        handle = archive.extractfile(f"{site['point_id']}.json")
        if handle is None:
            raise RuntimeError("observation point absent")
        document = json.load(handle)
    keep = [
        bool(observed)
        and all(document["fields"][name][index] is not None for name in ("prcp", "tmax", "tmin"))
        for index, observed in enumerate(document["source_observed"])
    ]
    dates = [dt.date.fromisoformat(value) for value, include in zip(document["dates"], keep) if include]
    arrays = [
        np.asarray(
            [value for value, include in zip(document["fields"][name], keep) if include],
            dtype=np.float64,
        )
        for name in ("prcp", "tmax", "tmin")
    ]
    if len(dates) != 10950:
        raise RuntimeError("observation row contract mismatch")
    blocks = []
    for year in sorted({date.year for date in dates}):
        indices = [index for index, date in enumerate(dates) if date.year == year]
        blocks.append(
            {
                "dates": [dates[index] for index in indices],
                "precipitation": arrays[0][indices],
                "tmax": arrays[1][indices],
                "tmin": arrays[2][indices],
            }
        )
    return realized_metrics(dates, *arrays), blocks


def resampled_observation(blocks: list[dict[str, Any]], indices: np.ndarray) -> dict[str, float]:
    dates: list[dt.date] = []
    precipitation: list[np.ndarray] = []
    tmax: list[np.ndarray] = []
    tmin: list[np.ndarray] = []
    for position, index in enumerate(indices):
        block = blocks[int(index)]
        leap = any(date.month == 2 and date.day == 29 for date in block["dates"])
        target_year = 2000 + 16 * position + (0 if leap else 1)
        dates.extend(date.replace(year=target_year) for date in block["dates"])
        precipitation.append(block["precipitation"])
        tmax.append(block["tmax"])
        tmin.append(block["tmin"])
    return realized_metrics(
        dates,
        np.concatenate(precipitation),
        np.concatenate(tmax),
        np.concatenate(tmin),
    )


def mean_metrics(streams: list[dict[str, float]]) -> dict[str, float]:
    keys = set(streams[0])
    if any(set(stream) != keys for stream in streams):
        raise RuntimeError("metric key mismatch")
    return {
        key: float(np.mean([stream[key] for stream in streams]))
        for key in sorted(keys)
    }


def scale(key: str, generated: float, observed: float) -> float:
    if key.startswith("intensity."):
        raise KeyError(key)
    if "precipitation_" in key and any(
        name in key for name in ("mean", "standard_deviation", "q10", "q50", "q90", "q95")
    ):
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
    common = sorted(
        set(generated) & set(observed)
        - {key for key in generated if key.startswith("intensity.")}
    )
    errors = [scale(key, generated[key], observed[key]) for key in common]
    if not errors or not all(math.isfinite(value) for value in errors):
        raise RuntimeError("empty or non-finite composite")
    return float(np.mean(errors))


def comparator_streams(scratch: Path, site: dict[str, Any], burns: list[int]) -> dict[str, list[dict[str, float]]]:
    arms: dict[str, list[dict[str, float]]] = defaultdict(list)
    for arm in ("faithful", "stochastic_prism_localized_par_v1"):
        for member, _ in enumerate(burns):
            cli = scratch / "runs" / site["point_id"] / arm / f"member-{member}" / "climate.cli"
            arms[arm].append(realized_metrics(*parse_cli(cli)))
    return dict(arms)


def candidate_streams(document: dict[str, Any]) -> dict[str, list[dict[str, float]]]:
    rows: dict[str, list[tuple[int, int, dict[str, float]]]] = defaultdict(list)
    for stream in document["streams"]:
        rows[stream["point_id"]].append(
            (stream["training_seed"], stream["member_id"], stream["metrics"])
        )
    output = {}
    for point, point_rows in rows.items():
        point_rows.sort(key=lambda value: (value[0], value[1]))
        if len(point_rows) != 24:
            raise RuntimeError("candidate stream count mismatch")
        output[point] = [value[2] for value in point_rows]
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--observation-shards", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    candidate_document = read(options.candidate)
    contract = read(options.contract)
    if not candidate_document["temporal_candidate_available"]:
        result = {
            "candidate_identity": candidate_document["candidate_identity"],
            "protected_roles_opened": [],
            "reached": False,
            "schema_version": 1,
            "terminal": "A10M5R7-TEMPORAL-NOT-REACHED",
        }
        atomic_json(options.output, result)
        print(result["terminal"])
        return
    if tree_identity(options.scratch) != (354, 280551300, EXPECTED_COMPARATOR_TREE):
        raise RuntimeError("retained comparator tree identity mismatch")

    sites = read(options.sites)["sites"]
    candidate = candidate_streams(candidate_document)
    observations = {}
    blocks = {}
    comparators = {}
    point_rows = {}
    burns = [0, 100003, 200009, 300007, 400009, 500009, 600011, 700001]
    for site in sites:
        point = site["point_id"]
        observations[point], blocks[point] = observation(options.observation_shards, site)
        comparators[point] = comparator_streams(options.scratch, site, burns)
        comparator_errors = {
            arm: composite(streams, observations[point])
            for arm, streams in comparators[point].items()
        }
        reference = min(comparator_errors.values())
        error = composite(candidate[point], observations[point])
        point_rows[point] = {
            "candidate_error": error,
            "candidate_ratio": error / reference,
            "comparator_errors": comparator_errors,
            "reference_error": reference,
            "regime": site["regime"],
        }

    rng = np.random.default_rng(contract["full_temporal"]["bootstrap_seed"])
    medians = []
    for _ in range(contract["full_temporal"]["bootstrap_replicates"]):
        ratios = []
        for site in sites:
            point = site["point_id"]
            observed = resampled_observation(
                blocks[point], rng.integers(0, len(blocks[point]), len(blocks[point]))
            )
            comparator_indices = rng.integers(0, 8, 8)
            reference = min(
                composite(
                    [comparators[point][arm][int(index)] for index in comparator_indices],
                    observed,
                )
                for arm in ("faithful", "stochastic_prism_localized_par_v1")
            )
            candidate_indices = rng.integers(0, 24, 24)
            error = composite(
                [candidate[point][int(index)] for index in candidate_indices], observed
            )
            ratios.append(error / reference)
        medians.append(float(np.median(ratios)))
    upper = float(np.quantile(medians, 0.90))
    maximum = max(row["candidate_ratio"] for row in point_rows.values())
    eligible = bool(
        upper
        <= contract["full_temporal"]["median_regime_ratio_upper_90_percent_limit"]
        and maximum <= contract["full_temporal"]["maximum_regime_ratio_limit"]
    )
    result = {
        "bootstrap": {
            "replicates": contract["full_temporal"]["bootstrap_replicates"],
            "seed": contract["full_temporal"]["bootstrap_seed"],
        },
        "candidate_identity": candidate_document["candidate_identity"],
        "decision": {
            "bootstrap_median_regime_ratio_upper_90_percent": upper,
            "maximum_regime_ratio": maximum,
            "temporally_eligible": eligible,
        },
        "point_results": point_rows,
        "protected_roles_opened": [],
        "reached": True,
        "schema_version": 1,
        "terminal": (
            "A10M5R7-TEMPORAL-CANDIDATE-READY"
            if eligible
            else "HOLD-A10M5R7-GENERATED-FEEDBACK-TEMPORAL"
        ),
    }
    atomic_json(options.output, result)
    print(result["terminal"])


if __name__ == "__main__":
    main()
