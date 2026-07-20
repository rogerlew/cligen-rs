#!/usr/bin/env python3
"""Run frozen comparators and score A10M5R12 continuous latent streams."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from temporal_metrics import realized_metrics

PACKAGE_ID = "20260719-a10m5r12r1-admission-materialization-remedy"
RUN_ID = "a10m5r12r1-admission-materialization-remedy-r0"
HEX64 = re.compile(r"[0-9a-f]{64}")
GIT_COMMIT = re.compile(r"[0-9a-f]{40}")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def authenticated(value: dict[str, Any]) -> bool:
    recorded = value.get("record_sha256")
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    return (
        isinstance(recorded, str)
        and HEX64.fullmatch(recorded) is not None
        and recorded == hashlib.sha256(canonical(semantic)).hexdigest()
    )


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
        except ValueError as error:
            if fields[0].lstrip("+-").isdigit():
                raise RuntimeError(f"malformed comparator daily row: {line}") from error
            continue
        prcp, duration, _, peak_ratio, tx, tn = values[:6]
        dates.append(date)
        precipitation.append(prcp)
        tmax.append(tx)
        tmin.append(tn)
        peak.append(peak_ratio * prcp / duration if duration > 0.0 else 0.0)
    expected = [
        dt.date(2001, 1, 1) + dt.timedelta(days=index)
        for index in range((dt.date(2101, 1, 1) - dt.date(2001, 1, 1)).days)
    ]
    arrays = tuple(
        np.asarray(values, dtype=np.float64)
        for values in (precipitation, tmax, tmin, peak)
    )
    if (
        dates != expected
        or any(len(values) != len(expected) for values in arrays)
        or not all(np.isfinite(values).all() for values in arrays)
        or np.any(arrays[0] < 0.0)
        or np.any(arrays[1] < arrays[2])
    ):
        raise RuntimeError(f"comparator daily axis/support failure: {path}")
    return dates, *arrays


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
        leap = any(date.month == 2 and date.day == 29 for date in block["dates"])
        target_year = 2000 + 16 * position + (0 if leap else 1)
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
            spec.write_text(runspec(localize / parameter_name, cli, years, burn, f"a10m5r12 {arm} {member}"), encoding="utf-8")
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


def expected_metric_keys(contract: dict[str, Any]) -> set[str]:
    metrics = contract["metrics"]
    monthly = {
        f"monthly.{month:02d}.precipitation_{name}"
        for month in range(1, 13)
        for name in metrics["monthly_precipitation"]
    }
    monthly.update(
        f"monthly.{month:02d}.{name}"
        for month in range(1, 13)
        for name in metrics["monthly_temperature"]
    )
    return (
        monthly
        | {f"annual.{name}" for name in metrics["annual"]}
        | {f"occurrence.{name}" for name in metrics["occurrence"]}
    )


def metrics_close(left: dict[str, float], right: dict[str, float]) -> bool:
    return left.keys() == right.keys() and all(
        math.isclose(
            float(left[name]), float(right[name]), rel_tol=1e-12, abs_tol=1e-12
        )
        for name in left
    )


def annual_family_keys() -> dict[str, tuple[str, ...]]:
    return {
        "annual_location": (
            "annual.precipitation_mean",
            "annual.precipitation_q95",
            "annual.tmax_mean",
            "annual.tmin_mean",
        ),
        "annual_dispersion": (
            "annual.precipitation_standard_deviation",
            "annual.tmax_standard_deviation",
            "annual.tmin_standard_deviation",
        ),
        "annual_lag": (
            "annual.precipitation_lag1",
            "annual.tmax_lag1",
            "annual.tmin_lag1",
        ),
        "annual_cross_field_dependence": (
            "annual.precipitation_tmax_correlation",
            "annual.precipitation_tmin_correlation",
            "annual.tmax_tmin_correlation",
        ),
    }


def family_composite(
    streams: list[dict[str, float]],
    observed: dict[str, float],
    keys: tuple[str, ...],
) -> float:
    generated = mean_metrics(streams)
    if not set(keys) <= generated.keys() or not set(keys) <= observed.keys():
        raise RuntimeError("annual diagnostic family registry incomplete")
    return float(np.mean([scale(key, generated[key], observed[key]) for key in keys]))


def validated_time_scales(
    role: dict[str, Any],
    training: dict[str, Any],
    portfolio_contract: dict[str, Any],
) -> dict[str, dict[str, list[float]]]:
    definition = portfolio_contract["architectures"][role["architecture"]]
    shape = portfolio_contract["capacity_shapes"][role["capacity"]]
    expected = {
        "medium_time_scale_days": (
            int(shape["continuous_medium_state_dim"]),
            tuple(float(value) for value in definition["medium_time_scale_days"]),
        )
    }
    if definition["slow_state"]:
        expected["slow_time_scale_days"] = (
            int(shape["continuous_slow_state_dim"]),
            tuple(float(value) for value in definition["slow_time_scale_days"]),
        )
    output = {}
    for row in training["seeds"]:
        values = row.get("time_scales_days", {})
        if set(values) != set(expected):
            raise RuntimeError("learned time-scale registry drift")
        for name, (count, bounds) in expected.items():
            field = values[name]
            if not (
                len(field) == count
                and all(math.isfinite(float(value)) for value in field)
                and all(bounds[0] <= float(value) <= bounds[1] for value in field)
            ):
                raise RuntimeError("learned time-scale support drift")
        output[str(row["seed"])] = values
    if set(output) != {str(value) for value in role["seeds"]}:
        raise RuntimeError("learned time-scale seed roster drift")
    return output


def neural_streams(
    root: Path,
    contract: dict[str, Any],
    sites: list[dict[str, Any]],
    expected_calendar: dict[str, Any],
    temporal_contract_sha256: str,
    portfolio_contract_sha256: str,
) -> dict[str, dict[str, list[dict[str, float]]]]:
    output: dict[str, dict[str, list[tuple[int, int, dict[str, float]]]]] = defaultdict(lambda: defaultdict(list))
    site_regimes = {site["point_id"]: site["regime"] for site in sites}
    generation = contract["generation"]
    members = {int(value) for value in generation["member_ids"]}
    begin = int(generation["begin_year"])
    expected_rows = (dt.date(begin + int(generation["horizon_years"]), 1, 1) - dt.date(begin, 1, 1)).days
    expected_dates = [
        dt.date(begin, 1, 1) + dt.timedelta(days=index)
        for index in range(expected_rows)
    ]
    site_indices = {site["point_id"]: index for index, site in enumerate(sites)}
    source_commits: set[str] = set()
    metric_keys = expected_metric_keys(contract)
    for role in contract["roles"]:
        role_id = role["role_id"]
        role_root = root / "results" / role_id
        admission = read(root / "admissions" / f"{role_id}.json")
        evidence = read(role_root / "evidence.json")
        summary = read(role_root / "candidate-summary.json")
        training = read(role_root / "training.json")
        control = read(role_root / "control-identity.json")
        calendar = read(role_root / "calendar-preflight.json")
        document = read(role_root / "streams.json")
        seeds = tuple(int(value) for value in role["seeds"])
        source_commit = admission.get("source_commit")
        if not (
            authenticated(admission)
            and admission.get("record_type") == "a10m5r12-submission-admission"
            and admission.get("decision") == "PASS"
            and admission.get("valid") is True
            and admission.get("package_id") == PACKAGE_ID
            and admission.get("run_id") == RUN_ID
            and admission.get("role") == role_id
            and isinstance(source_commit, str)
            and GIT_COMMIT.fullmatch(source_commit) is not None
            and isinstance(admission.get("gates"), dict)
            and bool(admission["gates"])
            and all(value is True for value in admission["gates"].values())
        ):
            raise RuntimeError(f"candidate admission identity failed: {role_id}")
        source_commits.add(source_commit)
        required_gates = {
            "all_seed_results_published",
            "calendar_preflight",
            "calendar_surface_complete",
            "candidate_parameter_ceiling",
            "controls_reconstructed_exactly",
            "fit_validation_gradient_free",
            "job_local_cleanup",
            "physical_support",
            "protected_roles_sealed",
            "submission_admission_authenticated",
            "temporal_stream_archive_published",
            "temporal_stream_matrix_complete",
            "temporal_stream_support",
        }
        gates = evidence.get("gates", {})
        if not (
            evidence.get("valid") is True
            and evidence.get("verdict") == "PASS"
            and evidence.get("role") == role_id
            and evidence.get("run_id") == RUN_ID
            and evidence.get("protected_roles_opened") == []
            and required_gates <= set(gates)
            and bool(gates)
            and all(value is True for value in gates.values())
        ):
            raise RuntimeError(f"candidate terminal evidence failed: {role_id}")
        expected_identity = {
            "architecture": role["architecture"],
            "capacity": role["capacity"],
            "configuration_id": role["configuration_id"],
            "role_id": role_id,
        }
        if any(summary.get(name) != value for name, value in expected_identity.items()):
            raise RuntimeError(f"candidate summary identity failed: {role_id}")
        if (
            tuple(int(value) for value in summary.get("seeds", [])) != seeds
            or summary.get("protected_roles_opened") != []
            or summary.get("contract_sha256") != portfolio_contract_sha256
            or training.get("architecture") != role["architecture"]
            or training.get("capacity") != role["capacity"]
            or tuple(int(row.get("seed", -1)) for row in training.get("seeds", [])) != seeds
            or control.get("exact") is not True
            or calendar != expected_calendar
        ):
            raise RuntimeError(f"candidate supporting evidence failed: {role_id}")
        training_by_seed = {
            int(row["seed"]): row for row in training.get("seeds", [])
        }
        for seed in seeds:
            seed_record = read(role_root / "seeds" / f"{seed}.json")
            checkpoint = role_root / "seed-work" / str(seed) / "checkpoint.pt"
            training_record = training_by_seed.get(seed, {})
            if (
                seed_record.get("seed") != seed
                or any(seed_record.get(name) != value for name, value in expected_identity.items())
                or seed_record.get("contract_sha256") != portfolio_contract_sha256
                or seed_record.get("protected_roles_opened") != []
                or seed_record.get("candidate", {}).get("support") is not True
                or seed_record.get("fit_validation_gradient") is not False
                or checkpoint.stat().st_size != training_record.get("checkpoint_bytes")
                or digest(checkpoint) != training_record.get("checkpoint_sha256")
                or seed_record.get("training", {}).get("checkpoint_bytes")
                != training_record.get("checkpoint_bytes")
                or seed_record.get("training", {}).get("checkpoint_sha256")
                != training_record.get("checkpoint_sha256")
            ):
                raise RuntimeError(f"candidate seed identity failed: {role_id}/{seed}")
        if not (
            document.get("architecture") == role["architecture"]
            and document.get("capacity") == role["capacity"]
            and document.get("configuration_id") == role["configuration_id"]
            and document.get("role_id") == role_id
            and document.get("protected_roles_opened") == []
            and document.get("temporal_contract_sha256") == temporal_contract_sha256
            and document.get("stream_count") == int(generation["expected_streams_per_configuration"])
            and isinstance(document.get("streams"), list)
        ):
            raise RuntimeError("configuration stream identity mismatch")
        archive_path = role_root / "streams.npz"
        archive_identity = document.get("stream_archive", {})
        if not (
            archive_identity.get("bytes") == archive_path.stat().st_size
            and archive_identity.get("sha256") == digest(archive_path)
        ):
            raise RuntimeError(f"candidate stream archive identity failed: {role_id}")
        with np.load(archive_path, allow_pickle=False) as archive:
            if set(archive.files) != {"member_id", "site_index", "training_seed", "weather"}:
                raise RuntimeError("candidate stream archive registry drift")
            archived_members = archive["member_id"]
            archived_sites = archive["site_index"]
            archived_seeds = archive["training_seed"]
            archived_weather = archive["weather"]
        if (
            archived_members.shape != (int(generation["expected_streams_per_configuration"]),)
            or archived_sites.shape != archived_members.shape
            or archived_seeds.shape != archived_members.shape
            or archived_weather.shape != (len(archived_members), expected_rows, 3)
            or archived_weather.dtype != np.dtype("<f4")
            or not np.isfinite(archived_weather).all()
        ):
            raise RuntimeError(f"candidate stream archive shape failed: {role_id}")
        realized: set[tuple[int, str, int]] = set()
        for row_index, stream in enumerate(document["streams"]):
            identity = (
                int(stream.get("training_seed", -1)),
                stream.get("point_id"),
                int(stream.get("member_id", -1)),
            )
            metrics = stream.get("metrics")
            keys = set(metrics) if isinstance(metrics, dict) else set()
            if not (
                identity[0] in seeds
                and identity[1] in site_regimes
                and identity[2] in members
                and identity not in realized
                and stream.get("regime") == site_regimes[identity[1]]
                and stream.get("support") is True
                and stream.get("row_count") == expected_rows
                and isinstance(stream.get("stream_sha256"), str)
                and HEX64.fullmatch(stream["stream_sha256"]) is not None
                and keys
                and all(math.isfinite(float(value)) for value in metrics.values())
            ):
                raise RuntimeError(f"candidate stream evidence failed: {role_id}")
            values = archived_weather[row_index]
            recomputed = realized_metrics(
                expected_dates, values[:, 0], values[:, 1], values[:, 2]
            )
            if not (
                int(archived_members[row_index]) == identity[2]
                and int(archived_sites[row_index]) == site_indices[identity[1]]
                and int(archived_seeds[row_index]) == identity[0]
                and hashlib.sha256(values.astype("<f4", copy=False).tobytes()).hexdigest()
                == stream["stream_sha256"]
                and metrics_close(recomputed, metrics)
            ):
                raise RuntimeError(f"candidate stream replay failed: {role_id}/{row_index}")
            if keys != metric_keys:
                raise RuntimeError("candidate temporal metric registry drift")
            realized.add(identity)
            output[role["configuration_id"]][stream["point_id"]].append(
                (stream["training_seed"], stream["member_id"], stream["metrics"])
            )
        expected = {
            (seed, point_id, member)
            for seed in seeds
            for point_id in site_regimes
            for member in members
        }
        if realized != expected:
            raise RuntimeError(f"candidate stream matrix mismatch: {role_id}")
    if len(source_commits) != 1:
        raise RuntimeError("candidate source commit mismatch")
    ordered: dict[str, dict[str, list[dict[str, float]]]] = defaultdict(dict)
    for configuration, sites in output.items():
        for point, rows in sites.items():
            rows.sort(key=lambda value: (value[0], value[1]))
            ordered[configuration][point] = [value[2] for value in rows]
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
    parser.add_argument("--portfolio-contract", type=Path, required=True)
    parser.add_argument("--calendar-control-expectation", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True)
    options = parser.parse_args()
    contract = read(options.contract)
    portfolio_contract = read(options.portfolio_contract)
    sites = read(options.sites)["sites"]
    neural = neural_streams(
        options.neural_root,
        contract,
        sites,
        read(options.calendar_control_expectation),
        digest(options.contract),
        digest(options.portfolio_contract),
    )
    configurations = [row["configuration_id"] for row in contract["roles"]]
    time_scales = {}
    for role in contract["roles"]:
        training = read(
            options.neural_root / "results" / role["role_id"] / "training.json"
        )
        time_scales[role["configuration_id"]] = validated_time_scales(
            role, training, portfolio_contract
        )
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
        candidate_errors = {
            configuration: composite(neural[configuration][point], observations[point])
            for configuration in configurations
        }
        candidate_family_errors = {
            configuration: {
                family: family_composite(
                    neural[configuration][point], observations[point], keys
                )
                for family, keys in annual_family_keys().items()
            }
            for configuration in configurations
        }
        point_rows[point] = {
            "candidate_errors": candidate_errors,
            "candidate_family_errors": candidate_family_errors,
            "candidate_ratios": {
                configuration: value / reference
                for configuration, value in candidate_errors.items()
            },
            "comparator_errors": errors,
            "reference_error": reference,
            "regime": site["regime"],
        }
    rng = np.random.default_rng(410542)
    bootstrap_contract = contract["scoring"]["bootstrap"]
    replicates = int(bootstrap_contract["replicates"])
    if int(bootstrap_contract["seed"]) != 410542:
        raise RuntimeError("bootstrap seed drift")
    medians = {configuration: [] for configuration in configurations}
    paired_means = {configuration: [] for configuration in configurations}
    for _ in range(replicates):
        ratios = {configuration: [] for configuration in configurations}
        paired_errors = {configuration: [] for configuration in configurations}
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
            for configuration in configurations:
                error = composite(
                    [neural[configuration][point][int(index)] for index in candidate_indices],
                    observed,
                )
                paired_errors[configuration].append(error)
                ratios[configuration].append(error / reference)
        for configuration in configurations:
            medians[configuration].append(float(np.median(ratios[configuration])))
            paired_means[configuration].append(float(np.mean(paired_errors[configuration])))
    decisions = {}
    gate = contract["scoring"]["candidate_noninferiority"]
    for configuration in configurations:
        upper = float(np.quantile(medians[configuration], 0.90))
        maximum = max(
            row["candidate_ratios"][configuration] for row in point_rows.values()
        )
        decisions[configuration] = {
            "bootstrap_median_regime_ratio_upper_90_percent": upper,
            "maximum_regime_ratio": maximum,
            "temporally_eligible": (
                upper <= float(gate["median_regime_ratio_upper_90_percent"])
                and maximum <= float(gate["maximum_regime_ratio"])
            ),
        }
    eligible = [
        configuration for configuration in configurations
        if decisions[configuration]["temporally_eligible"]
    ]
    diagnostic_rng = np.random.default_rng(410543)
    family_samples = {
        family: {configuration: [] for configuration in configurations}
        for family in annual_family_keys()
    }
    for _ in range(replicates):
        diagnostic_indices = {
            site["point_id"]: diagnostic_rng.integers(0, 24, 24)
            for site in sites
        }
        for family, keys in annual_family_keys().items():
            for configuration in configurations:
                errors = []
                for site in sites:
                    point = site["point_id"]
                    errors.append(
                        family_composite(
                            [
                                neural[configuration][point][int(index)]
                                for index in diagnostic_indices[point]
                            ],
                            observations[point],
                            keys,
                        )
                    )
                family_samples[family][configuration].append(float(np.mean(errors)))
    annual_diagnostics = {}
    for family, values in family_samples.items():
        summaries = {
            configuration: {
                "median_error": float(np.median(samples)),
                "upper_90_percent_error": float(np.quantile(samples, 0.90)),
            }
            for configuration, samples in values.items()
        }
        left, right = configurations
        left_values = np.asarray(values[left])
        right_values = np.asarray(values[right])
        annual_diagnostics[family] = {
            "configurations": summaries,
            "probability_medium_lower_error": float(np.mean(left_values < right_values)),
            "selection_gating": False,
        }
    contrasts = {}
    for left_index, left in enumerate(configurations):
        for right in configurations[left_index + 1:]:
            left_values = np.asarray(paired_means[left])
            right_values = np.asarray(paired_means[right])
            contrasts[f"{left}__vs__{right}"] = {
                "probability_left_lower_error": float(np.mean(left_values < right_values)),
                "median_relative_error_reduction_left_vs_right": float(
                    np.median((right_values - left_values) / right_values)
                ),
                "selection_gating": False,
            }
    result = {
        "bootstrap": {"replicates": replicates, "seed": 410542},
        "candidate_decisions": decisions,
        "annual_actual_series_member_bootstrap": {
            "diagnostics": annual_diagnostics,
            "observation_basis": "fixed actual 1980-2009 series; annual lag order preserved",
            "replicates": replicates,
            "seed": 410543,
            "selection_gating": False,
        },
        "eligible_configurations": eligible,
        "non_gating_pairwise_contrasts": contrasts,
        "point_results": point_rows,
        "learned_time_scales_days": time_scales,
        "prism_provenance": provenance,
        "protected_roles_opened": [],
        "schema_version": 1,
        "terminal": (
            "A10M5R12-TEMPORAL-READY"
            if eligible
            else "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
        ),
    }
    atomic_json(options.output, result)
    print(result["terminal"])


if __name__ == "__main__":
    main()
