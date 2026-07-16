"""Execute the research-only A9c3 grouped observed-development campaign.

The module deliberately reuses the hash-frozen A9c normalized observations
and candidate implementation without modifying either historical package.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import resource
import shutil
import subprocess
import tarfile
import tempfile
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable

import numpy as np
from scipy.signal.windows import dpss
from scipy.stats import genpareto, rankdata, spearmanr
from sklearn.covariance import LedoitWolf

from research.a9_harness.moments import monthly_moments
from research.a9_harness.objectives import (
    SelectionSummary,
    pareto_frontier,
    select_candidate,
)
from research.a9c.models import (
    LATENT,
    RENEWAL,
    fit_latent,
    fit_renewal,
    gregorian_dates,
    hmm_fit,
    load_daymet,
    load_uscrn,
    simulate,
    transformed_event_laws,
)
from research.a9c.nulls import daymet_year_features, observed_blocks


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/work-packages/20260715-a9c3-two-site-grouped-observed-comparison"
ARTIFACTS = PACKAGE / "artifacts"
DESIGN = ARTIFACTS / "design-freeze-v1.json"
PREDECESSOR = ARTIFACTS / "predecessor-manifest-v1.json"
CALIBRATION = ARTIFACTS / "grouped-calibration-v1.json"
FIT_EXECUTION = ARTIFACTS / "fit-execution-v1.json"
STRUCTURAL = ARTIFACTS / "structural-audit-v1.json"
FIT_CORRECTION = ARTIFACTS / "pre-score-fit-closeout-correction.md"
BASELINE = ARTIFACTS / "faithful-baseline-v1.json"
EVALUATION = ARTIFACTS / "evaluation-v1.json"
FREEZE = ARTIFACTS / "candidate-freeze-v1.json"
A9C = ROOT / "docs/work-packages/20260715-a9c-observed-development/artifacts"
CONFIG_SOURCE = A9C / "campaign-freeze-v1.json"
NULL_SOURCE = A9C / "null-thresholds-v1.json"
OBJECTIVES = (
    ROOT
    / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/objective-registry-v1.json"
)
FIT_DETAILS = ARTIFACTS / "fits/detail"
FIT_RECORDS = ARTIFACTS / "fits"
SOURCE_COMMIT = "a0e24f0866f4536c168bfd809cb957d91e6d8bf3"
GROUP_SITES = ("az_yuma_27_ene", "ca_stovepipe_wells_1_sw")
FAMILIES = (
    "occurrence_spell",
    "wet_amount",
    "aggregate",
    "extreme",
    "storm_descriptor",
    "compound_context",
    "winter_proxy",
)
SEASONS = {
    12: "DJF",
    1: "DJF",
    2: "DJF",
    3: "MAM",
    4: "MAM",
    5: "MAM",
    6: "JJA",
    7: "JJA",
    8: "JJA",
    9: "SON",
    10: "SON",
    11: "SON",
}


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_once(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def maximum_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if __import__("sys").platform == "darwin" else value * 1024


def resource_snapshot(stage: str, started: float) -> dict[str, Any]:
    limits = load(DESIGN)["resource_limits"]
    snapshot = {
        "maximum_rss_bytes": maximum_rss_bytes(),
        "retained_bytes": directory_size(PACKAGE),
        "stage": stage,
        "wall_seconds": time.monotonic() - started,
        "worker_count": 1,
    }
    failures = []
    if snapshot["maximum_rss_bytes"] > int(limits["memory_gib"]) * 1024**3:
        failures.append("memory_gib")
    if snapshot["retained_bytes"] > int(limits["retained_gib"]) * 1024**3:
        failures.append("retained_gib")
    if snapshot["wall_seconds"] > int(limits["stage_wall_hours"]) * 3600:
        failures.append("stage_wall_hours")
    if snapshot["worker_count"] > int(limits["workers"]):
        failures.append("workers")
    snapshot["failed_limits"] = failures
    snapshot["status"] = "fail" if failures else "pass"
    if failures:
        raise RuntimeError(f"HOLD-A9C3-RESOURCE-BOUND: {','.join(failures)}")
    return snapshot


def expected_panels() -> tuple[dict[str, str], dict[str, str]]:
    grouped = load(DESIGN)["grouped_storm_amendment"]
    daily = {
        site: stratum
        for stratum, sites in grouped["generated_contributors"].items()
        for site in sites
    }
    storm = {
        site: stratum
        for stratum, sites in grouped["observed_contributors"].items()
        for site in sites
    }
    return daily, storm


def verify_panels(
    daily: dict[str, dict[str, Any]], storms: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    expected_daily, expected_storm = expected_panels()
    actual_daily = {site: payload["stratum"] for site, payload in daily.items()}
    actual_storm = {site: payload["stratum"] for site, payload in storms.items()}
    if actual_daily != expected_daily or actual_storm != expected_storm:
        raise ValueError("HOLD-A9C3-DATA-ROLE: exact panel mismatch")
    source = load(A9C / "observed-source-manifest-v1.json")
    rows = [
        row
        for row in source["daymet_normalized_objects"]
        + source["uscrn_normalized_objects"]
        if row["role"] == "development"
    ]
    expected_paths = {
        str(
            (A9C / f"large/observed/daymet/development/{site}.json.gz").relative_to(
                ROOT
            )
        )
        for site in expected_daily
    } | {
        str(
            (A9C / f"large/observed/uscrn/development/{site}.json.gz").relative_to(ROOT)
        )
        for site in expected_storm
    }
    indexed = {row["path"]: row for row in rows}
    if set(indexed) != expected_paths:
        raise ValueError("HOLD-A9C3-DATA-ROLE: source-manifest panel mismatch")
    for relative, row in indexed.items():
        path = ROOT / relative
        if sha256_path(path) != row["object_sha256"]:
            raise ValueError(f"HOLD-A9C3-DATA-ROLE: object hash {relative}")
    return {
        "daymet_development_count": len(expected_daily),
        "development_object_count": len(indexed),
        "source_manifest_sha256": sha256_path(A9C / "observed-source-manifest-v1.json"),
        "uscrn_development_count": len(expected_storm),
    }


def finite(values: Iterable[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def logit(value: float) -> float:
    clipped = min(1.0 - 1.0e-6, max(1.0e-6, float(value)))
    return math.log(clipped / (1.0 - clipped))


def event_vectors(events: list[dict[str, Any]]) -> dict[str, list[float]]:
    if len(events) < 3:
        raise ValueError("group event estimator requires at least three events")

    def event_time(row: dict[str, Any]) -> datetime:
        raw = row["start_lst"] if "start_lst" in row else row["date"]
        return datetime.fromisoformat(raw)

    ordered = sorted(
        events,
        key=lambda row: (
            row.get("_sequence", event_time(row).timestamp()),
            event_time(row),
        ),
    )
    duration = np.log(
        np.asarray([max(float(row["duration_min"]), 1.0e-6) for row in ordered])
    )
    ttp = np.asarray([logit(float(row["time_to_peak_fraction"])) for row in ordered])
    peak = np.log(np.asarray([max(float(row["peak_ratio"]), 1.0) for row in ordered]))
    depth = np.log1p(
        np.asarray(
            [
                max(float(row.get("depth_mm", row.get("precip_mm", 0.0))), 0.0)
                for row in ordered
            ]
        )
    )
    seasonal_phase = []
    antecedent: list[float | None] = []
    previous_end: datetime | None = None
    for row in ordered:
        started = event_time(row)
        phase = (
            started.timetuple().tm_yday
            - 1
            + (started.hour * 60 + started.minute) / 1440.0
        ) / 366.0
        seasonal_phase.append(phase)
        if "_antecedent_dry_hours" in row:
            stored_gap = row["_antecedent_dry_hours"]
            gap = None if stored_gap is None else float(stored_gap)
        elif previous_end is None:
            gap = None
        else:
            gap = max(0.0, (started - previous_end).total_seconds() / 3600.0)
        antecedent.append(None if gap is None else math.log1p(gap))
        previous_end = started + timedelta(minutes=float(row["duration_min"]))

    def quantiles(array: np.ndarray) -> list[float]:
        return [float(value) for value in np.quantile(array, [0.1, 0.5, 0.9])]

    retained = [index for index, value in enumerate(antecedent) if value is not None]
    if len(retained) < 3:
        raise ValueError(
            "group event estimator requires three uncensored antecedent gaps"
        )
    matrix = np.column_stack(
        (
            depth[retained],
            duration[retained],
            ttp[retained],
            peak[retained],
            np.asarray(seasonal_phase)[retained],
            np.asarray([antecedent[index] for index in retained], dtype=float),
        )
    )
    ranked = np.column_stack(
        [
            rankdata(matrix[:, index], method="average") / (len(matrix) + 1.0)
            for index in range(6)
        ]
    )
    correlation = np.corrcoef(ranked, rowvar=False)
    joint = [
        float(correlation[left, right])
        for left in range(6)
        for right in range(left + 1, 6)
    ]
    result = {
        "storm_duration": quantiles(duration),
        "storm_joint_dependence": joint,
        "storm_peak_ratio": quantiles(peak),
        "storm_time_to_peak": quantiles(ttp),
    }
    if not all(finite(values) for values in result.values()):
        raise ValueError("nonfinite grouped event estimator")
    return result


def mean_vectors(vectors: list[dict[str, list[float]]]) -> dict[str, list[float]]:
    if not vectors:
        raise ValueError("empty grouped vectors")
    result: dict[str, list[float]] = {}
    for objective in sorted(vectors[0]):
        matrix = np.asarray([row[objective] for row in vectors], dtype=float)
        result[objective] = [float(value) for value in matrix.mean(axis=0)]
    return result


def bootstrap_seed(replicate: int, station: str, draw: str) -> int:
    material = f"a9c3-grouped-bootstrap-v1\0{replicate}\0{station}\0{draw}".encode()
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


def event_year(row: dict[str, Any]) -> int:
    raw = row["start_lst"] if "start_lst" in row else row["date"]
    return int(raw[:4])


def station_year_resample(
    events: list[dict[str, Any]], horizon: int, replicate: int, station: str, draw: str
) -> list[dict[str, Any]]:
    chronological = sorted(
        events,
        key=lambda row: row["start_lst"] if "start_lst" in row else row["date"],
    )
    with_gaps = []
    previous_end: datetime | None = None
    for row in chronological:
        copied = dict(row)
        raw = row["start_lst"] if "start_lst" in row else row["date"]
        started = datetime.fromisoformat(raw)
        copied["_antecedent_dry_hours"] = (
            None
            if previous_end is None
            else max(0.0, (started - previous_end).total_seconds() / 3600.0)
        )
        with_gaps.append(copied)
        previous_end = started + timedelta(minutes=float(row["duration_min"]))
    blocks = by_key(with_gaps, event_year)
    available_years = sorted(blocks)
    generator = np.random.Generator(
        np.random.Philox(bootstrap_seed(replicate, station, draw))
    )
    selected = generator.choice(available_years, size=horizon, replace=True)
    output = []
    sequence = 0
    for selected_year in selected:
        rows = sorted(
            blocks[int(selected_year)],
            key=lambda row: row["start_lst"] if "start_lst" in row else row["date"],
        )
        for row in rows:
            copied = dict(row)
            copied["_sequence"] = sequence
            output.append(copied)
            sequence += 1
    return output


def null_seed(family: str, horizon: int, replicate: int) -> int:
    material = f"a9c3-null-v1\0{family}\0{horizon}\0{replicate}".encode()
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


def calibrate() -> None:
    started = time.monotonic()
    if CALIBRATION.exists():
        raise FileExistsError(CALIBRATION)
    for path in (FIT_EXECUTION, STRUCTURAL, EVALUATION, FREEZE):
        if path.exists():
            raise ValueError(f"candidate artifact exists before calibration: {path}")
    design = load(DESIGN)
    development = load_uscrn("development")
    panel_identity = verify_panels(load_daymet("development"), development)
    fit_events = load_uscrn("coefficient_fit")
    by_stratum: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for site, payload in development.items():
        by_stratum[payload["stratum"]][site] = payload["events"]
    if any(len(sites) != 2 for sites in by_stratum.values()) or len(by_stratum) != 6:
        raise ValueError("HOLD-A9C3-DATA-ROLE")

    threshold_rows = []
    threshold_identities = []
    blocks = observed_blocks()
    for family in (
        "occurrence_spell",
        "wet_amount",
        "aggregate",
        "extreme",
        "compound_context",
        "winter_proxy",
    ):
        family_floor = max(
            [
                float(row.get("absolute_floor", 0.0))
                for row in load(OBJECTIVES)["objectives"]
                if row["family"] == family
            ]
            or [1.0e-6]
        )
        for horizon in (30, 100):
            maxima = []
            identities = []
            for replicate in range(500):
                generator = np.random.Generator(
                    np.random.Philox(null_seed(family, horizon, replicate))
                )
                cell_maxima = []
                for _, raw in sorted(blocks[family].items()):
                    array = np.asarray(raw, dtype=float)
                    scale = np.maximum(np.std(array, axis=0, ddof=1), family_floor)
                    first = array[generator.integers(0, len(array), size=horizon)].mean(
                        axis=0
                    )
                    second = array[
                        generator.integers(0, len(array), size=horizon)
                    ].mean(axis=0)
                    cell_maxima.append(float(np.max(np.abs(first - second) / scale)))
                statistic = max(cell_maxima)
                maxima.append(statistic)
                identities.append(
                    sha256_bytes(
                        f"{family}:{horizon}:{replicate}:{statistic:.17g}".encode()
                    )
                )
            threshold_rows.append(
                {
                    "family": family,
                    "horizon_years": horizon,
                    "max_statistic_95": float(
                        np.quantile(maxima, 0.95, method="higher")
                    ),
                    "replicate_count": 500,
                    "replicate_identity_sha256": sha256_bytes(
                        canonical_bytes(identities)
                    ),
                }
            )
            threshold_identities.extend(identities)

    storm_scales: dict[str, dict[str, dict[str, list[float]]]] = {}
    for horizon in (30, 100):
        first_values: dict[tuple[str, str], list[list[float]]] = defaultdict(list)
        differences: list[dict[tuple[str, str], list[float]]] = []
        identities = []
        for replicate in range(500):
            replicate_differences: dict[tuple[str, str], list[float]] = {}
            for stratum, station_events in sorted(by_stratum.items()):
                draw_vectors = {}
                for draw in ("first", "second"):
                    station_vectors = [
                        event_vectors(
                            station_year_resample(
                                events,
                                horizon,
                                replicate,
                                site,
                                f"threshold-{horizon}-{draw}",
                            )
                        )
                        for site, events in sorted(station_events.items())
                    ]
                    draw_vectors[draw] = mean_vectors(station_vectors)
                for objective in sorted(draw_vectors["first"]):
                    first_values[(stratum, objective)].append(
                        draw_vectors["first"][objective]
                    )
                    replicate_differences[(stratum, objective)] = [
                        float(value)
                        for value in np.abs(
                            np.asarray(draw_vectors["first"][objective])
                            - np.asarray(draw_vectors["second"][objective])
                        )
                    ]
            differences.append(replicate_differences)
        scales = {
            key: [
                float(value)
                for value in np.maximum(
                    np.std(np.asarray(values), axis=0, ddof=1), 0.02
                )
            ]
            for key, values in first_values.items()
        }
        maxima = []
        for replicate, values in enumerate(differences):
            statistic = max(
                float(
                    np.sqrt(
                        np.mean((np.asarray(components) / np.asarray(scales[key])) ** 2)
                    )
                )
                for key, components in values.items()
            )
            maxima.append(statistic)
            identities.append(
                sha256_bytes(
                    f"storm_descriptor:{horizon}:{replicate}:{statistic:.17g}".encode()
                )
            )
        threshold_rows.append(
            {
                "family": "storm_descriptor",
                "horizon_years": horizon,
                "max_statistic_95": float(np.quantile(maxima, 0.95, method="higher")),
                "replicate_count": 500,
                "replicate_identity_sha256": sha256_bytes(canonical_bytes(identities)),
            }
        )
        threshold_identities.extend(identities)
        for (stratum, objective), values in scales.items():
            storm_scales.setdefault(stratum, {}).setdefault(str(horizon), {})[
                objective
            ] = values

    hot_sites = {site: development[site]["events"] for site in GROUP_SITES}
    central_by_site = {
        site: event_vectors(events) for site, events in hot_sites.items()
    }
    central = mean_vectors([central_by_site[site] for site in GROUP_SITES])
    replicate_count = int(design["precision_power_diagnostic"]["replicates"])
    bootstrap: dict[str, list[list[float]]] = {objective: [] for objective in central}
    for replicate in range(replicate_count):
        grouped = mean_vectors(
            [
                event_vectors(
                    station_year_resample(events, 7, replicate, site, "diagnostic")
                )
                for site, events in sorted(hot_sites.items())
            ]
        )
        for objective in sorted(central):
            bootstrap[objective].append(grouped[objective])

    diagnostics = []
    z = NormalDist().inv_cdf(0.975) + NormalDist().inv_cdf(0.80)
    all_finite = True
    for objective in sorted(central):
        samples = np.asarray(bootstrap[objective], dtype=float)
        for component, estimate in enumerate(central[objective]):
            values = samples[:, component]
            standard_error = float(np.std(values, ddof=1))
            interval = np.quantile(values, [0.025, 0.975])
            minimum_detectable = z * standard_error
            scale = max(float(np.std(values, ddof=1)), 0.02)
            row = {
                "bootstrap_ci_95": [float(interval[0]), float(interval[1])],
                "component": component,
                "estimate": float(estimate),
                "minimum_detectable_shift": minimum_detectable,
                "minimum_detectable_standardized_shift": minimum_detectable / scale,
                "objective_id": objective,
                "standard_error": standard_error,
            }
            all_finite = all_finite and finite(
                [
                    row["estimate"],
                    row["standard_error"],
                    row["minimum_detectable_shift"],
                    *row["bootstrap_ci_95"],
                ]
            )
            diagnostics.append(row)
    if not all_finite:
        raise ValueError("HOLD-A9C3-GROUP-ESTIMATOR")

    site_season = []
    for site, events in sorted(hot_sites.items()):
        for season in ("DJF", "MAM", "JJA", "SON"):
            selected = [
                row
                for row in events
                if SEASONS[
                    int((row["start_lst"] if "start_lst" in row else row["date"])[5:7])
                ]
                == season
            ]
            site_season.append(
                {
                    "event_count": len(selected),
                    "finite_summary": len(selected) >= 3,
                    "season": season,
                    "station_id": site,
                    "summary": event_vectors(selected) if len(selected) >= 3 else None,
                    "time_to_peak_clip_count": sum(
                        float(row["time_to_peak_fraction"]) <= 1.0e-6
                        or float(row["time_to_peak_fraction"]) >= 1.0 - 1.0e-6
                        for row in selected
                    ),
                }
            )
    removal = {
        site: {
            objective: [
                float(value)
                for value in np.asarray(central_by_site[other][objective])
                - np.asarray(central[objective])
            ]
            for objective in central
        }
        for site, other in (
            (GROUP_SITES[0], GROUP_SITES[1]),
            (GROUP_SITES[1], GROUP_SITES[0]),
        )
    }
    output = {
        "bootstrap_replicates": replicate_count,
        "candidate_inputs_accessed": False,
        "design_freeze_sha256": sha256_path(DESIGN),
        "diagnostics": diagnostics,
        "event_counts": {site: len(hot_sites[site]) for site in GROUP_SITES},
        "fit_event_counts": {
            site: len(fit_events[site]["events"]) for site in GROUP_SITES
        },
        "group_estimates": central,
        "grouped_objective_amendment_sha256": sha256_path(
            ARTIFACTS / "grouped-storm-objective-amendment-v1.json"
        ),
        "observed_object_hashes": {
            site: sha256_path(A9C / f"large/observed/uscrn/development/{site}.json.gz")
            for site in GROUP_SITES
        },
        "power_is_selection_gate": False,
        "resource": resource_snapshot("candidate_blind_calibration", started),
        "removal_sensitivity": removal,
        "schema_version": 1,
        "site_season_diagnostics": site_season,
        "site_estimates": central_by_site,
        "site_weights": {site: 0.5 for site in GROUP_SITES},
        "panel_identity": panel_identity,
        "storm_component_scales": storm_scales,
        "status": "finite_grouped_estimators",
        "threshold_identity_sha256": sha256_bytes(
            canonical_bytes(threshold_identities)
        ),
        "thresholds": sorted(
            threshold_rows, key=lambda row: (row["family"], row["horizon_years"])
        ),
    }
    write_once(CALIBRATION, output)
    print(
        f"calibrated two-site group from {sum(output['event_counts'].values())} actual events; "
        f"bootstrap={replicate_count}; thresholds={len(output['thresholds'])}; finite=yes"
    )


def detail_hash(value: dict[str, Any]) -> str:
    without = dict(value)
    without.pop("content_sha256", None)
    return sha256_bytes(canonical_bytes(without))


def deterministic_fit_identities(
    detail: dict[str, Any], config: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    return {
        "fit": {
            "identity_sha256": sha256_bytes(
                canonical_bytes(
                    {
                        "configuration": config,
                        "domain": "a9c3-fit-v1",
                        "sources": detail["sources"],
                    }
                )
            ),
            "stochastic": False,
        },
        "optimizer": {
            "identity_sha256": sha256_bytes(
                canonical_bytes(
                    {"configuration": config, "domain": "a9c3-optimizer-v1"}
                )
            ),
            "stochastic": False,
        },
        "parameter_member": {
            "identity_sha256": sha256_bytes(
                canonical_bytes(
                    {
                        "detail_content_sha256": detail["content_sha256"],
                        "domain": "a9c3-parameter-member-v1",
                    }
                )
            ),
            "stochastic": False,
        },
    }


def monthly_seed(fit_id: str, site: str, month: int, draw: str) -> int:
    material = (
        f"a9c3-monthly-reconciliation-v1\0{fit_id}\0{site}\0{month}\0{draw}"
    ).encode()
    return int.from_bytes(hashlib.sha256(material).digest(), "big")


def stationary_weights(transition: list[list[float]]) -> np.ndarray:
    matrix = np.asarray(transition, dtype=float)
    values, vectors = np.linalg.eig(matrix.T)
    index = int(np.argmin(np.abs(values - 1.0)))
    weights = np.abs(np.real(vectors[:, index]))
    weights /= weights.sum()
    return weights


def vector_pmf(
    generator: np.random.Generator, probabilities: list[float], count: int
) -> np.ndarray:
    return generator.choice(
        np.arange(1, len(probabilities) + 1),
        size=count,
        p=np.asarray(probabilities, dtype=float) / sum(probabilities),
    )


def vector_amount(
    parameters: dict[str, Any],
    generator: np.random.Generator,
    previous_log: np.ndarray,
    wet_mask: np.ndarray,
) -> np.ndarray:
    amount = np.zeros(len(previous_log), dtype=float)
    indices = np.flatnonzero(wet_mask)
    if not len(indices):
        return amount
    mean = float(parameters["mean"])
    sd = float(parameters["sd"])
    z = generator.standard_normal(len(indices))
    previous = previous_log[indices]
    prior = np.isfinite(previous)
    rho = float(parameters["amount_memory"])
    z[prior] = (
        rho * ((previous[prior] - mean) / sd)
        + math.sqrt(max(0.0, 1.0 - rho * rho)) * z[prior]
    )
    log_amount = mean + sd * z
    values = np.exp(log_amount)
    gate = generator.random(len(indices)) < float(parameters["tail_probability"])
    if np.any(gate):
        u = np.maximum(1.0 - generator.random(int(np.sum(gate))), 1.0e-12)
        shape = float(parameters["tail_shape"])
        scale = float(parameters["tail_scale"])
        excess = (
            -scale * np.log(u)
            if abs(shape) < 1.0e-8
            else scale * (u ** (-shape) - 1.0) / shape
        )
        values[gate] = np.maximum(
            values[gate], float(parameters["tail_threshold_mm"]) + excess
        )
    amount[indices] = values
    previous_log[indices] = np.log(values)
    return amount


def monthly_path_matrix(
    detail: dict[str, Any], site: str, month: int, path_count: int, draw: str
) -> np.ndarray:
    station = detail["stations"][site]
    generator = np.random.Generator(
        np.random.Philox(monthly_seed(detail["fit_id"], site, month, draw))
    )
    remaining = np.zeros(path_count, dtype=int)
    previous_log = np.full(path_count, np.nan)
    output = np.zeros((path_count, 31), dtype=float)
    burn_days = 120
    if detail["candidate_class"] == RENEWAL:
        parameters = station["months"][str(month)]
        wet = np.zeros(path_count, dtype=bool)
        for day_index in range(burn_days + 31):
            switching = remaining <= 0
            wet[switching] = ~wet[switching]
            for state, pmf_name in (
                (True, "wet_duration_pmf"),
                (False, "dry_duration_pmf"),
            ):
                selected = switching & (wet == state)
                remaining[selected] = vector_pmf(
                    generator, parameters[pmf_name], int(np.sum(selected))
                )
            amount_parameters = dict(parameters["variables"]["wet:log_amount"])
            amount_parameters.update(
                {
                    "amount_memory": parameters["amount_memory"],
                    "tail_probability": parameters["tail_probability"],
                    "tail_scale": parameters["tail_scale"],
                    "tail_shape": parameters["tail_shape"],
                    "tail_threshold_mm": parameters["tail_threshold_mm"],
                }
            )
            amount = vector_amount(amount_parameters, generator, previous_log, wet)
            previous_log[~wet] = np.nan
            remaining -= 1
            if day_index >= burn_days:
                output[:, day_index - burn_days] = amount
    else:
        transition = np.asarray(station["transition"], dtype=float)
        state = generator.choice(
            np.arange(len(transition)),
            size=path_count,
            p=stationary_weights(station["transition"]),
        )
        parameters = station["months"][str(month)]
        for day_index in range(burn_days + 31):
            switching = remaining <= 0
            for old_state in range(len(transition)):
                selected = switching & (state == old_state)
                state[selected] = generator.choice(
                    np.arange(len(transition)),
                    size=int(np.sum(selected)),
                    p=transition[old_state] / np.sum(transition[old_state]),
                )
            for current_state, emission in enumerate(parameters):
                selected = switching & (state == current_state)
                remaining[selected] = vector_pmf(
                    generator, emission["dwell_pmf"], int(np.sum(selected))
                )
            wet = np.zeros(path_count, dtype=bool)
            amount = np.zeros(path_count, dtype=float)
            for current_state, emission in enumerate(parameters):
                selected_state = state == current_state
                selected_indices = np.flatnonzero(selected_state)
                state_wet = generator.random(len(selected_indices)) < float(
                    emission["wet_probability"]
                )
                wet[selected_indices] = state_wet
                selected_wet = selected_state & wet
                amount_parameters = dict(emission["variables"]["log_amount"])
                amount_parameters.update(
                    {
                        "amount_memory": emission["amount_memory"],
                        "tail_probability": emission["tail_probability"],
                        "tail_scale": emission["tail_scale"],
                        "tail_shape": emission["tail_shape"],
                        "tail_threshold_mm": emission["tail_threshold_mm"],
                    }
                )
                state_amount = vector_amount(
                    amount_parameters, generator, previous_log, selected_wet
                )
                amount[selected_wet] = state_amount[selected_wet]
            previous_log[~wet] = np.nan
            remaining -= 1
            if day_index >= burn_days:
                output[:, day_index - burn_days] = amount
    return output


def reconcile_fit_monthlies(detail: dict[str, Any]) -> dict[str, Any]:
    requested_paths = 200_000
    cell_count = len(detail["stations"]) * 12
    paths_per_cell = math.ceil(requested_paths / cell_count)
    target_by_length: dict[int, list[np.ndarray]] = defaultdict(list)
    heldout_by_length: dict[int, list[np.ndarray]] = defaultdict(list)
    for site in sorted(detail["stations"]):
        for month in range(1, 13):
            target_paths = monthly_path_matrix(
                detail, site, month, paths_per_cell, "target"
            )
            heldout_paths = monthly_path_matrix(
                detail, site, month, paths_per_cell, "heldout"
            )
            for length in (28, 29, 30, 31):
                target_by_length[length].append(target_paths[:, :length])
                heldout_by_length[length].append(heldout_paths[:, :length])

    def variance_standard_error(values: np.ndarray) -> float:
        centered_values = values - np.mean(values)
        variance = float(np.var(values))
        fourth = float(np.mean(centered_values**4))
        return math.sqrt(max(0.0, (fourth - variance * variance) / len(values)))

    checks = []
    for length in (28, 29, 30, 31):
        target = np.concatenate(target_by_length[length], axis=0)
        heldout = np.concatenate(heldout_by_length[length], axis=0)
        column_means = np.mean(target, axis=0)
        centered = target - column_means
        daily_mean = float(np.mean(column_means))
        daily_variance = float(np.mean(np.mean(centered * centered, axis=0)))
        covariance = {
            lag: float(np.mean(np.mean(centered[:, :-lag] * centered[:, lag:], axis=0)))
            for lag in range(1, length)
        }
        analytic_target = monthly_moments(
            length,
            daily_mean,
            daily_variance,
            covariance,
        )
        target_totals = np.sum(target, axis=1)
        heldout_totals = np.sum(heldout, axis=1)
        target_variance = float(np.var(target_totals))
        heldout_mean = float(np.mean(heldout_totals))
        heldout_variance = float(np.var(heldout_totals))
        mean_standard_error = math.sqrt(
            target_variance / len(target_totals)
            + heldout_variance / len(heldout_totals)
        )
        variance_standard_error_combined = math.hypot(
            variance_standard_error(target_totals),
            variance_standard_error(heldout_totals),
        )
        mean_error = abs(analytic_target.total_mean - heldout_mean)
        variance_error = abs(analytic_target.total_variance - heldout_variance)
        mean_tolerance = max(
            1.0e-8,
            0.005 * max(abs(analytic_target.total_mean), 1.0e-12),
            3.290527 * mean_standard_error,
        )
        variance_tolerance = max(
            1.0e-8,
            0.005 * max(abs(analytic_target.total_variance), 1.0e-12),
            3.290527 * variance_standard_error_combined,
        )
        checks.append(
            {
                "analytic_target_mean": analytic_target.total_mean,
                "analytic_target_variance": analytic_target.total_variance,
                "heldout_mean": heldout_mean,
                "heldout_variance": heldout_variance,
                "mean_error": mean_error,
                "mean_standard_error": mean_standard_error,
                "mean_tolerance": mean_tolerance,
                "month_length_days": length,
                "status": (
                    "pass"
                    if mean_error <= mean_tolerance
                    and variance_error <= variance_tolerance
                    else "fail"
                ),
                "target_direct_mean": float(np.mean(target_totals)),
                "target_direct_variance": target_variance,
                "variance_error": variance_error,
                "variance_standard_error": variance_standard_error_combined,
                "variance_tolerance": variance_tolerance,
            }
        )
    maximum_absolute = max(
        max(row["mean_error"], row["variance_error"]) for row in checks
    )
    maximum_relative = max(
        max(
            row["mean_error"] / max(abs(row["analytic_target_mean"]), 1.0e-12),
            row["variance_error"] / max(abs(row["analytic_target_variance"]), 1.0e-12),
        )
        for row in checks
    )
    status = "pass" if all(row["status"] == "pass" for row in checks) else "fail"
    return {
        "check_count": len(checks),
        "full_process_path_count_per_fit_per_draw": paths_per_cell * cell_count,
        "independent_draws": ["target", "heldout"],
        "paths_per_station_month": paths_per_cell,
        "identity_sha256": sha256_bytes(canonical_bytes(checks)),
        "maximum_absolute_error": maximum_absolute,
        "maximum_relative_error": maximum_relative,
        "method": "a9c3_independent_full_process_path_mc_target_vs_heldout_v1",
        "status": status,
    }


def a9c3_structural_audit(fits: list[dict[str, Any]]) -> dict[str, Any]:
    renewal = [fit for fit in fits if fit["candidate_class"] == RENEWAL]
    latent = [fit for fit in fits if fit["candidate_class"] == LATENT]
    interior = all(
        0.0 < state["wet_probability"] < 1.0
        for fit in latent
        for station in fit["stations"].values()
        for month in station["months"].values()
        for state in month
    )
    latent_mixed = all(
        any(state["wet_probability"] < 0.5 for state in month)
        and any(state["wet_probability"] > 0.02 for state in month)
        for fit in latent
        for station in fit["stations"].values()
        for month in station["months"].values()
    )
    return {
        "candidate_classes": [RENEWAL, LATENT],
        "degenerate_intersection_entered": not interior,
        "factorization_bijection_exists": False,
        "latent_all_emissions_strictly_interior": interior,
        "latent_observed_spell_label_is_state": False,
        "latent_states_emit_mixed_occurrence": latent_mixed,
        "renewal_hidden_state_count": 0,
        "renewal_observable_spell_types_alternate": True,
        "status": (
            "pass" if renewal and latent and interior and latent_mixed else "fail"
        ),
    }


def count_spells(rows: list[dict[str, Any]]) -> tuple[int, int]:
    states = [float(row["precip_mm"]) > 0.0 for row in rows]
    if not states:
        return 0, 0
    wet_spells = int(states[0])
    dry_spells = int(not states[0])
    for previous, current in zip(states[:-1], states[1:]):
        if previous != current:
            wet_spells += int(current)
            dry_spells += int(not current)
    return wet_spells, dry_spells


def recovery_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**row, "prcp_mm": row["precip_mm"]} for row in rows]


def a9c3_synthetic_recovery(details: list[dict[str, Any]]) -> dict[str, Any]:
    recovery_rows_output = []
    for candidate in (RENEWAL, LATENT):
        fit_detail = next(
            value for value in details if value["candidate_class"] == candidate
        )
        generated = simulate(fit_detail, "id101022", burn=909091, years=30)
        adapted = recovery_rows(generated)
        wet_amounts = [row["precip_mm"] for row in generated if row["precip_mm"] > 0.0]
        wet_fraction = len(wet_amounts) / len(generated)
        amount_mean = float(np.mean(wet_amounts))
        if candidate == RENEWAL:
            wet_spells, dry_spells = count_spells(generated)
            hidden_state_count = 0
            mixed_state_count = None
            recovery_pass = (
                wet_spells >= 50
                and dry_spells >= 50
                and 0.01 < wet_fraction < 0.99
                and amount_mean > 0.0
            )
        else:
            refit = hmm_fit(
                adapted,
                int(fit_detail["configuration"]["hidden_states"]),
                iterations=10,
            )
            hidden_state_count = len(refit.wet_probability)
            mixed_state_count = sum(
                any(
                    row["latent_state"] == state and row["precip_mm"] > 0.0
                    for row in generated
                )
                and any(
                    row["latent_state"] == state and row["precip_mm"] == 0.0
                    for row in generated
                )
                for state in range(hidden_state_count)
            )
            recovery_pass = mixed_state_count == hidden_state_count and all(
                (refit.wet_probability > 0.0) & (refit.wet_probability < 1.0)
            )
            wet_spells = dry_spells = None
        recovery_rows_output.append(
            {
                "amount_mean_mm": amount_mean,
                "candidate_class": candidate,
                "dry_spell_count": dry_spells,
                "hidden_state_count": hidden_state_count,
                "mixed_emission_state_count": mixed_state_count,
                "recovery_status": "pass" if recovery_pass else "fail",
                "simulation_days": len(generated),
                "site": "id101022",
                "wet_fraction": wet_fraction,
                "wet_spell_count": wet_spells,
            }
        )
    renewal_fit = next(
        value for value in details if value["candidate_class"] == RENEWAL
    )
    latent_fit = next(value for value in details if value["candidate_class"] == LATENT)
    renewal_stream = simulate(renewal_fit, "id101022", burn=717171, years=30)
    latent_stream = simulate(latent_fit, "id101022", burn=717171, years=30)
    crossing_count = sum(
        latent_stream[index]["latent_state"] != latent_stream[index - 1]["latent_state"]
        and (latent_stream[index]["precip_mm"] > 0.0)
        == (latent_stream[index - 1]["precip_mm"] > 0.0)
        for index in range(1, len(latent_stream))
    )
    same_observable_bytes = canonical_bytes(
        [(row["date"], row["precip_mm"]) for row in renewal_stream]
    ) == canonical_bytes([(row["date"], row["precip_mm"]) for row in latent_stream])
    cross_pass = not same_observable_bytes and crossing_count > 0
    status = (
        all(row["recovery_status"] == "pass" for row in recovery_rows_output)
        and cross_pass
    )
    return {
        "cross_fit": {
            "exact_observable_law_identity": same_observable_bytes,
            "latent_boundaries_crossing_observed_spells": crossing_count,
            "same_state_probability_law_under_bijection": False,
            "status": "pass" if cross_pass else "fail",
        },
        "recovery": recovery_rows_output,
        "schema_version": 1,
        "status": "pass" if status else "fail",
    }


def close_fit_evidence(
    details: list[dict[str, Any]],
    records: list[dict[str, Any]],
    started: float,
    execution_mode: str,
) -> None:
    monthly_records = [
        {
            "configuration_id": row["configuration"]["configuration_id"],
            **row["monthly_reconciliation"],
        }
        for row in records
    ]
    static = a9c3_structural_audit(details)
    recovery = a9c3_synthetic_recovery(details)
    structural = {
        "candidate_classes": [RENEWAL, LATENT],
        "cross_fit_recovery": recovery,
        "design_freeze_sha256": sha256_path(DESIGN),
        "execution_mode": execution_mode,
        "schema_version": 1,
        "static_factorization": static,
        "monthly_reconciliation": {
            "absolute_tolerance": 1.0e-8,
            "configuration_results": monthly_records,
            "maximum_absolute_error": max(
                row["maximum_absolute_error"] for row in monthly_records
            ),
            "maximum_relative_error": max(
                row["maximum_relative_error"] for row in monthly_records
            ),
            "relative_tolerance": 0.005,
            "status": (
                "pass"
                if all(row["status"] == "pass" for row in monthly_records)
                else "fail"
            ),
        },
        "status": (
            "pass"
            if static["status"] == "pass" and recovery["status"] == "pass"
            else "fail"
        ),
    }
    write_once(STRUCTURAL, structural)
    resource_record = resource_snapshot("fit_and_structural", started)
    total_wall = sum(float(row["wall_seconds"]) for row in records) + float(
        resource_record["wall_seconds"]
    )
    if total_wall > float(load(DESIGN)["resource_limits"]["stage_wall_hours"]) * 3600.0:
        raise RuntimeError("HOLD-A9C3-RESOURCE-BOUND: fit stage wall")
    resource_record["wall_seconds"] = total_wall
    output = {
        "calibration_sha256": sha256_path(CALIBRATION),
        "configuration_count": len(records),
        "design_freeze_sha256": sha256_path(DESIGN),
        "execution_mode": execution_mode,
        "fits": records,
        "fresh_fit_count": len(records),
        "schema_version": 1,
        "structural_audit_sha256": sha256_path(STRUCTURAL),
        "valid_fit_count_by_class": {
            candidate: sum(
                row["fit_status"] == "fit_valid" and row["candidate_class"] == candidate
                for row in records
            )
            for candidate in (RENEWAL, LATENT)
        },
        "resource": resource_record,
        "wall_seconds": total_wall,
    }
    write_once(FIT_EXECUTION, output)
    print(
        f"fit {len(records)} fresh configurations; valid={output['valid_fit_count_by_class']}; "
        f"structural={structural['status']}; mode={execution_mode}"
    )


def fit() -> None:
    if not CALIBRATION.exists():
        raise ValueError("candidate-blind calibration must precede fit")
    if FIT_EXECUTION.exists() or STRUCTURAL.exists() or EVALUATION.exists():
        raise FileExistsError("fit/evaluation evidence exists")
    campaign = load(CONFIG_SOURCE)
    daymet = load_daymet("coefficient_fit")
    events = transformed_event_laws(load_uscrn("coefficient_fit"))
    details: list[dict[str, Any]] = []
    records = []
    started = time.monotonic()
    for config in campaign["configuration_grid"]:
        before = time.monotonic()
        if config["candidate_class"] == RENEWAL:
            detail = fit_renewal(config, daymet, events)
        elif config["candidate_class"] == LATENT:
            detail = fit_latent(config, daymet, events)
        else:
            raise ValueError(config["candidate_class"])
        detail["fit_id"] = f"a9c3-{config['configuration_id']}"
        detail["campaign_id"] = load(DESIGN)["campaign_id"]
        detail["content_sha256"] = detail_hash(detail)
        monthly = reconcile_fit_monthlies(detail)
        if monthly["status"] != "pass":
            raise RuntimeError("HOLD-A9C3-MONTHLY-RECONCILIATION")
        path = FIT_DETAILS / f"{config['configuration_id']}.json"
        write_once(path, detail)
        deterministic_identities = deterministic_fit_identities(detail, config)
        compact = {
            "candidate_class": detail["candidate_class"],
            "configuration": config,
            "content_sha256": detail["content_sha256"],
            "detail_path": str(path.relative_to(ROOT)),
            "detail_sha256": sha256_path(path),
            "effective_parameter_count": detail["effective_parameter_count"],
            "fit_id": detail["fit_id"],
            "fit_status": detail["fit_status"],
            "ineligible_stations": detail["ineligible_stations"],
            "model_source_sha256": sha256_path(ROOT / "research/a9c/models.py"),
            "monthly_reconciliation": monthly,
            "rng": {
                **deterministic_identities,
                "monthly_reconciliation": f"NumPy Philox a9c3-monthly-reconciliation-v1/{detail['fit_id']}/target|heldout",
                "simulation": f"A9 Philox4x32-10 random-field campaign a9c/{detail['fit_id']}",
            },
            "parent_identities": {
                "calibration_sha256": sha256_path(CALIBRATION),
                "campaign_freeze_sha256": sha256_path(CONFIG_SOURCE),
                "design_freeze_sha256": sha256_path(DESIGN),
                "objective_registry_sha256": sha256_path(OBJECTIVES),
                "source_inventory_sha256": sha256_bytes(
                    canonical_bytes(detail["sources"])
                ),
            },
            "source_count": len(detail["sources"]),
            "wall_seconds": time.monotonic() - before,
        }
        compact_path = FIT_RECORDS / f"{config['configuration_id']}.fit.json"
        write_once(compact_path, compact)
        compact["configuration_id"] = config["configuration_id"]
        compact["path"] = str(compact_path.relative_to(ROOT))
        compact["sha256"] = sha256_path(compact_path)
        records.append(compact)
        details.append(detail)

    close_fit_evidence(details, records, started, "single_process")


def resume_fit_closeout() -> None:
    if FIT_EXECUTION.exists() or STRUCTURAL.exists():
        raise FileExistsError("fit closeout evidence exists")
    if BASELINE.exists() or EVALUATION.exists() or FREEZE.exists():
        raise ValueError("candidate scoring exists before fit closeout")
    if not FIT_CORRECTION.is_file():
        raise FileNotFoundError(FIT_CORRECTION)
    started = time.monotonic()
    campaign = load(CONFIG_SOURCE)
    expected = {row["configuration_id"]: row for row in campaign["configuration_grid"]}
    actual_details = {path.stem: path for path in FIT_DETAILS.glob("*.json")}
    actual_compacts = {
        path.name.removesuffix(".fit.json"): path
        for path in FIT_RECORDS.glob("*.fit.json")
    }
    if set(actual_details) != set(expected) or set(actual_compacts) != set(expected):
        raise ValueError("HOLD-A9C3-PREDECESSOR-INTEGRITY: incomplete fit resume set")
    details = []
    records = []
    for identifier in expected:
        detail_path = actual_details[identifier]
        compact_path = actual_compacts[identifier]
        detail = load(detail_path)
        compact = load(compact_path)
        if (
            detail["configuration"] != expected[identifier]
            or detail_hash(detail) != detail["content_sha256"]
            or compact["configuration"] != expected[identifier]
            or compact["detail_sha256"] != sha256_path(detail_path)
            or compact["content_sha256"] != detail["content_sha256"]
            or compact["monthly_reconciliation"]["status"] != "pass"
        ):
            raise ValueError(
                f"HOLD-A9C3-PREDECESSOR-INTEGRITY: fit resume identity {identifier}"
            )
        compact["path"] = str(compact_path.relative_to(ROOT))
        compact["configuration_id"] = identifier
        compact["sha256"] = sha256_path(compact_path)
        details.append(detail)
        records.append(compact)
    close_fit_evidence(details, records, started, "pre_score_closeout_resume")


def years(rows: list[dict[str, Any]]) -> list[int]:
    return sorted({int(row["date"][:4]) for row in rows})


def by_key(rows: list[dict[str, Any]], key) -> dict[Any, list[dict[str, Any]]]:
    result: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[key(row)].append(row)
    return result


def precip(row: dict[str, Any]) -> float:
    return float(row.get("prcp_mm", row.get("precip_mm", 0.0)))


def tmean(row: dict[str, Any]) -> float:
    return (float(row["tmax_c"]) + float(row["tmin_c"])) / 2.0


def cv(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    return (
        float(np.std(array, ddof=1) / np.mean(array))
        if len(array) >= 2 and np.mean(array) > 0.0
        else 0.0
    )


def safe_corr(left: Iterable[float], right: Iterable[float]) -> float:
    x = np.asarray(list(left), dtype=float)
    y = np.asarray(list(right), dtype=float)
    if len(x) < 3 or np.std(x) == 0.0 or np.std(y) == 0.0:
        return 0.0
    value = float(np.corrcoef(x, y)[0, 1])
    return value if math.isfinite(value) else 0.0


def survival_features(
    rows: list[dict[str, Any]], wet: bool
) -> tuple[list[float], bool]:
    spells: dict[str, list[tuple[int, bool]]] = defaultdict(list)
    current: bool | None = None
    start_season = ""
    length = 0
    run_index = -1
    for row in rows:
        state = precip(row) >= 1.0
        if state == current:
            length += 1
            continue
        if current is not None and current == wet:
            spells[start_season].append((length, run_index == 0))
        current = state
        start_season = SEASONS[int(row["date"][5:7])]
        length = 1
        run_index += 1
    if current == wet:
        spells[start_season].append((length, True))
    limit = 30 if wet else 60
    values: list[float] = []
    available = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        sample = spells.get(season, [])
        complete = sum(not censored for _, censored in sample)
        available = available and complete >= 50
        survival = 1.0
        for duration in range(1, limit + 1):
            at_risk = sum(length >= duration for length, _ in sample)
            events = sum(
                length == duration and not censored for length, censored in sample
            )
            if at_risk:
                survival *= 1.0 - events / at_risk
            values.append(survival)
    return values, available


def triplet_features(rows: list[dict[str, Any]]) -> tuple[list[float], bool]:
    result = []
    available = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        windows = [
            [1 if precip(rows[index + offset]) >= 1.0 else 0 for offset in range(3)]
            for index in range(len(rows) - 2)
            if all(
                SEASONS[int(rows[index + offset]["date"][5:7])] == season
                for offset in range(3)
            )
            and (
                date.fromisoformat(rows[index + 1]["date"])
                - date.fromisoformat(rows[index]["date"])
            ).days
            == 1
            and (
                date.fromisoformat(rows[index + 2]["date"])
                - date.fromisoformat(rows[index + 1]["date"])
            ).days
            == 1
        ]
        available = available and len(windows) >= 500
        if not windows:
            result.extend([0.0] * 8)
            continue
        bits = [bit for window in windows for bit in window]
        p = float(np.mean(bits))
        transitions = np.zeros((2, 2), dtype=float)
        for window in windows:
            transitions[window[0], window[1]] += 1.0
            transitions[window[1], window[2]] += 1.0
        for state in (0, 1):
            total = float(np.sum(transitions[state]))
            transitions[state] = transitions[state] / total if total else [1.0 - p, p]
        for pattern in range(8):
            target = [(pattern >> shift) & 1 for shift in (2, 1, 0)]
            observed = sum(window == target for window in windows) / len(windows)
            expected = (
                (p if target[0] else 1.0 - p)
                * transitions[target[0], target[1]]
                * transitions[target[1], target[2]]
            )
            result.append(observed - expected)
    return result, available


def monthly_groups(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    return by_key(rows, lambda row: int(row["date"][5:7]))


def monthly_totals(rows: list[dict[str, Any]]) -> dict[tuple[int, int], float]:
    totals: dict[tuple[int, int], float] = defaultdict(float)
    for row in rows:
        totals[(int(row["date"][:4]), int(row["date"][5:7]))] += precip(row)
    return totals


def annual_totals(rows: list[dict[str, Any]]) -> dict[int, float]:
    totals: dict[int, float] = defaultdict(float)
    for row in rows:
        totals[int(row["date"][:4])] += precip(row)
    return totals


def objective_features(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    def add(identifier: str, values: Iterable[float], available: bool = True) -> None:
        vector = [float(value) for value in values]
        result[identifier] = {
            "available": bool(available and vector and finite(vector)),
            "values": vector,
        }

    monthly = monthly_groups(rows)
    wet_frequency = []
    wet_mean = []
    wet_cv = []
    wet_mean_available = True
    wet_cv_available = True
    for month in range(1, 13):
        amount = np.asarray([precip(row) for row in monthly.get(month, [])])
        positive = amount[amount > 0.0]
        wet_frequency.extend(
            [float(np.mean(amount > 0.0)), float(np.mean(amount >= 1.0))]
        )
        wet_mean.append(float(np.mean(positive)) if len(positive) else 0.0)
        wet_cv.append(cv(positive))
        wet_mean_available = wet_mean_available and len(positive) >= 25
        wet_cv_available = wet_cv_available and len(positive) >= 40
    add("occ_monthly_wet_frequency", wet_frequency, len(years(rows)) >= 12)
    values, available = survival_features(rows, True)
    add("occ_wet_spell_survival", values, available)
    values, available = survival_features(rows, False)
    add("occ_dry_spell_survival", values, available)
    values, available = triplet_features(rows)
    add("occ_higher_order_residual", values, available)
    add("amt_monthly_wet_mean", wet_mean, wet_mean_available)
    add("amt_monthly_wet_cv", wet_cv, wet_cv_available)

    adjacent_by_season: dict[str, list[tuple[float, float]]] = defaultdict(list)
    gap_bins: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    previous_row: dict[str, Any] | None = None
    gap = 0
    gap_known = False
    for row in rows:
        season = SEASONS[int(row["date"][5:7])]
        amount = precip(row)
        if previous_row is not None:
            consecutive = (
                date.fromisoformat(row["date"])
                - date.fromisoformat(previous_row["date"])
            ).days == 1
            if (
                consecutive
                and SEASONS[int(previous_row["date"][5:7])] == season
                and precip(previous_row) > 0.0
                and amount > 0.0
            ):
                adjacent_by_season[season].append((precip(previous_row), amount))
        if amount > 0.0:
            if gap_known:
                bin_id = 0 if gap <= 1 else 1 if gap <= 3 else 2 if gap <= 7 else 3
                gap_bins[season][bin_id].append(math.log(max(amount, 1.0e-6)))
            gap = 0
            gap_known = True
        elif gap_known:
            gap += 1
        previous_row = row

    adjacent = []
    upper = []
    dry_gap = []
    adjacent_available = True
    upper_available = True
    dry_gap_available = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        season_rows = [row for row in rows if SEASONS[int(row["date"][5:7])] == season]
        pairs = adjacent_by_season[season]
        adjacent_available = adjacent_available and len(pairs) >= 100
        correlation = (
            float(
                spearmanr(
                    [left for left, _ in pairs], [right for _, right in pairs]
                ).statistic
            )
            if len(pairs) >= 3
            else 0.0
        )
        adjacent.append(correlation if math.isfinite(correlation) else 0.0)
        positive = np.asarray([precip(row) for row in season_rows if precip(row) > 0.0])
        upper_available = (
            upper_available
            and len(positive) >= 300
            and sum(positive > np.quantile(positive, 0.9)) >= 30
            if len(positive)
            else False
        )
        if len(positive):
            quantiles = np.quantile(positive, [0.9, 0.95, 0.99])
            threshold = float(quantiles[0])
            exceedances = positive[positive > threshold] - threshold
            if len(exceedances) >= 30:
                shape, _, tail_scale = genpareto.fit(exceedances, floc=0.0)
            else:
                shape, tail_scale = 0.0, 0.0
            upper.extend(
                [
                    *(float(value) for value in quantiles),
                    float(shape),
                    float(tail_scale),
                ]
            )
        else:
            upper.extend([0.0] * 5)
        bins = gap_bins[season]
        dry_gap_available = dry_gap_available and all(
            len(bins[index]) >= 25 for index in range(4)
        )
        dry_gap.extend(
            float(np.mean(bins[index])) if bins[index] else 0.0 for index in range(4)
        )
    add("amt_adjacent_wet_dependence", adjacent, adjacent_available)
    add("amt_upper_tail", upper, upper_available)
    add("amt_dry_gap_memory", dry_gap, dry_gap_available)

    totals = monthly_totals(rows)
    years_present = years(rows)
    zero_frequency = []
    total_mean = []
    total_cv = []
    for month in range(1, 13):
        values = [totals.get((year, month), 0.0) for year in years_present]
        zero_frequency.append(sum(value == 0.0 for value in values) / len(values))
        total_mean.append(float(np.mean(values)))
        total_cv.append(cv(values))
    add("agg_zero_month_frequency", zero_frequency, len(years_present) >= 12)
    add("agg_monthly_total_mean", total_mean, len(years_present) >= 12)
    add("agg_monthly_total_cv", total_cv, len(years_present) >= 12 and any(total_mean))
    annual_matrix = np.asarray(
        [
            [totals.get((year, month), 0.0) for month in range(1, 13)]
            for year in years_present
        ]
    )
    covariance = (
        LedoitWolf().fit(annual_matrix).covariance_
        if len(years_present) >= 2
        else np.zeros((12, 12))
    )
    add("agg_cross_month_covariance", covariance.ravel(), len(years_present) >= 20)
    annual = [annual_totals(rows)[year] for year in years_present]
    add(
        "agg_annual_total_cv", [cv(annual)], len(annual) >= 12 and np.mean(annual) > 0.0
    )
    lag1 = safe_corr(annual[:-1], annual[1:])
    corrected_lag1 = float(
        np.clip(lag1 + (1.0 + 3.0 * lag1) / max(len(annual), 1), -0.999999, 0.999999)
    )
    add("agg_annual_lag1", [corrected_lag1], len(annual) >= 20)
    if len(annual) >= 4:
        detrended = np.asarray(annual, dtype=float)
        detrended -= np.polyval(
            np.polyfit(np.arange(len(detrended)), detrended, 1),
            np.arange(len(detrended)),
        )
        tapers = dpss(len(detrended), 2.5, Kmax=min(4, len(detrended) - 1))
        spectra = np.mean(
            [np.abs(np.fft.rfft(detrended * taper)) ** 2 for taper in tapers], axis=0
        )
        frequencies = np.fft.rfftfreq(len(detrended))[1:]
        periods = np.arange(2.0, 16.0)
        interpolated = np.interp(1.0 / periods, frequencies, spectra[1:])
        add("agg_low_frequency_spectrum", interpolated.tolist(), len(annual) >= 30)
    else:
        add("agg_low_frequency_spectrum", [0.0], False)

    extrema = []
    extrema_available = len(annual) >= 15
    for window in (1, 3, 5):
        annual_max = []
        for year, year_rows in by_key(rows, lambda row: int(row["date"][:4])).items():
            del year
            amount = np.asarray([precip(row) for row in year_rows])
            annual_max.append(
                float(np.convolve(amount, np.ones(window), mode="valid").max())
            )
        sample = np.sort(np.asarray(annual_max, dtype=float))
        count = len(sample)
        b0 = float(np.mean(sample))
        b1 = float(
            np.mean([index / (count - 1) * value for index, value in enumerate(sample)])
        )
        b2 = float(
            np.mean(
                [
                    index * (index - 1) / ((count - 1) * (count - 2)) * value
                    for index, value in enumerate(sample)
                ]
            )
        )
        l2 = 2.0 * b1 - b0
        l3 = 6.0 * b2 - 6.0 * b1 + b0
        l_skew = l3 / l2 if l2 > 0.0 else 0.0
        quantiles = np.quantile(sample, [0.5, 0.9])
        extrema.extend(
            [float(quantiles[0]), float(quantiles[1]), b0, l2, float(l_skew)]
        )
    add("ext_annual_1_3_5_day_maxima", extrema, extrema_available)

    temperature = []
    temperature_available = True
    for season in ("DJF", "MAM", "JJA", "SON"):
        season_rows = [row for row in rows if SEASONS[int(row["date"][5:7])] == season]
        wet = [row for row in season_rows if precip(row) > 0.0]
        dry = [row for row in season_rows if precip(row) == 0.0]
        temperature_available = (
            temperature_available and len(wet) >= 100 and len(dry) >= 100
        )
        for field in ("tmax_c", "tmin_c"):
            wet_values = np.asarray([float(row[field]) for row in wet])
            dry_values = np.asarray([float(row[field]) for row in dry])
            temperature.extend(
                [
                    (float(np.mean(wet_values)) if len(wet_values) else 0.0)
                    - (float(np.mean(dry_values)) if len(dry_values) else 0.0),
                    (float(np.std(wet_values, ddof=1)) if len(wet_values) >= 2 else 0.0)
                    - (
                        float(np.std(dry_values, ddof=1))
                        if len(dry_values) >= 2
                        else 0.0
                    ),
                ]
            )
    add("ctx_wet_dry_temperature", temperature, temperature_available)
    for identifier in (
        "ctx_wet_dry_humidity",
        "ctx_wet_dry_solar",
        "ctx_wet_event_wind_speed",
    ):
        add(identifier, [0.0], False)

    winter_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        month = int(row["date"][5:7])
        if month in (12, 1, 2):
            civil_year = int(row["date"][:4])
            winter_groups[civil_year + 1 if month == 12 else civil_year].append(row)
    complete_winter_groups = [
        group
        for _, group in sorted(winter_groups.items())
        if {int(row["date"][5:7]) for row in group} == {12, 1, 2}
    ]
    winter = [row for group in complete_winter_groups for row in group]
    winter_precip = np.asarray([precip(row) for row in winter])
    winter_temp = np.asarray([tmean(row) for row in winter])
    total_winter = float(np.sum(winter_precip))
    add(
        "winter_cold_wet_fraction",
        [
            (
                float(np.sum(winter_precip[winter_temp <= 0.0]) / total_winter)
                if total_winter > 0.0
                else 0.0
            )
        ],
        len(complete_winter_groups) >= 12 and total_winter > 0.0,
    )
    transitions = 0
    for group in complete_winter_groups:
        for previous, current in zip(group[:-1], group[1:]):
            if (
                date.fromisoformat(current["date"])
                - date.fromisoformat(previous["date"])
            ).days == 1:
                transitions += (tmean(previous) <= 0.0) != (tmean(current) <= 0.0)
    transitions /= max(len(complete_winter_groups), 1)
    add(
        "winter_freeze_transition_count",
        [float(transitions)],
        len(complete_winter_groups) >= 12,
    )
    wet_mask = winter_precip > 0.0
    winter_rank = (
        spearmanr(winter_precip[wet_mask], winter_temp[wet_mask]).statistic
        if int(np.sum(wet_mask)) >= 3
        else 0.0
    )
    add(
        "winter_precip_temperature_dependence",
        [float(winter_rank) if math.isfinite(float(winter_rank)) else 0.0],
        len(complete_winter_groups) >= 12 and int(np.sum(wet_mask)) >= 100,
    )
    return result


def fisher_z(values: np.ndarray) -> np.ndarray:
    return np.arctanh(np.clip(values, -1.0 + 1.0e-6, 1.0 - 1.0e-6))


def feature_distance(
    objective_id: str,
    simulated: dict[str, Any],
    observed: dict[str, Any],
    floor: float,
) -> float | None:
    if not simulated["available"] or not observed["available"]:
        return None
    left = np.asarray(simulated["values"], dtype=float)
    right = np.asarray(observed["values"], dtype=float)
    if left.shape != right.shape:
        raise ValueError(f"objective vector shape mismatch: {left.shape}/{right.shape}")
    epsilon = max(float(floor), 1.0e-6)
    if objective_id == "occ_monthly_wet_frequency":
        value = float(np.sqrt(np.mean((left - right) ** 2)))
    elif objective_id in {"occ_wet_spell_survival", "occ_dry_spell_survival"}:
        value = float(np.mean(np.abs(left - right)))
    elif objective_id == "occ_higher_order_residual":
        value = float(np.sqrt(np.mean((left - right) ** 2)))
    elif objective_id in {"amt_monthly_wet_mean", "agg_monthly_total_mean"}:
        value = float(
            np.mean(
                np.abs(np.log(np.maximum(left, epsilon) / np.maximum(right, epsilon)))
            )
        )
    elif objective_id in {
        "amt_monthly_wet_cv",
        "agg_monthly_total_cv",
        "agg_annual_total_cv",
    }:
        value = float(np.mean(np.abs(left - right)))
    elif objective_id in {
        "amt_adjacent_wet_dependence",
        "agg_annual_lag1",
        "winter_precip_temperature_dependence",
    }:
        value = float(np.mean(np.abs(fisher_z(left) - fisher_z(right))))
    elif objective_id == "amt_upper_tail":
        reshaped_left = left.reshape(-1, 5)
        reshaped_right = right.reshape(-1, 5)
        quantile = np.abs(reshaped_left[:, :3] - reshaped_right[:, :3]) / np.maximum(
            np.abs(reshaped_right[:, :3]), epsilon
        )
        shape = np.abs(reshaped_left[:, 3] - reshaped_right[:, 3])
        scale = np.abs(reshaped_left[:, 4] - reshaped_right[:, 4]) / np.maximum(
            np.abs(reshaped_right[:, 4]), epsilon
        )
        value = float(np.mean(np.concatenate([quantile.ravel(), shape, scale])))
    elif objective_id == "amt_dry_gap_memory":
        value = float(np.mean(np.abs(left - right)))
    elif objective_id == "agg_zero_month_frequency":
        value = float(np.mean(np.abs(left - right)))
    elif objective_id == "agg_cross_month_covariance":
        value = float(
            np.linalg.norm(left - right) / max(np.linalg.norm(right), epsilon)
        )
    elif objective_id == "agg_low_frequency_spectrum":
        value = float(
            np.mean(
                np.abs(
                    np.log(np.maximum(left, epsilon))
                    - np.log(np.maximum(right, epsilon))
                )
            )
        )
    elif objective_id == "ext_annual_1_3_5_day_maxima":
        reshaped_left = left.reshape(-1, 5)
        reshaped_right = right.reshape(-1, 5)
        magnitude = np.abs(reshaped_left[:, :4] - reshaped_right[:, :4]) / np.maximum(
            np.abs(reshaped_right[:, :4]), epsilon
        )
        l_skew = np.abs(reshaped_left[:, 4] - reshaped_right[:, 4])
        value = float(np.mean(np.concatenate([magnitude.ravel(), l_skew])))
    elif objective_id == "ctx_wet_dry_temperature":
        value = float(np.sqrt(np.mean(((left - right) / epsilon) ** 2)))
    elif objective_id in {"winter_cold_wet_fraction", "winter_freeze_transition_count"}:
        value = float(np.mean(np.abs(left - right)))
    else:
        raise ValueError(f"unregistered A9c3 distance: {objective_id}")
    return value if math.isfinite(value) else None


def predecessor_feature_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Adapt A9c3's canonical precipitation field for frozen A9c helpers."""
    return [{**row, "prcp_mm": precip(row)} for row in rows]


def family_vectors(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    blocks = daymet_year_features({"records": predecessor_feature_rows(rows)})
    result = {}
    for family in (
        "occurrence_spell",
        "wet_amount",
        "aggregate",
        "extreme",
        "compound_context",
        "winter_proxy",
    ):
        matrix = np.asarray([block[family] for block in blocks.values()], dtype=float)
        result[family] = [float(value) for value in matrix.mean(axis=0)]
    return result


def family_scale(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    blocks = daymet_year_features({"records": predecessor_feature_rows(rows)})
    floors = {
        row["family"]: max(
            float(row.get("absolute_floor", 0.0))
            for row in load(OBJECTIVES)["objectives"]
            if row["family"] == row["family"]
        )
        for row in []
    }
    del floors
    result = {}
    family_floor = {
        family: max(
            [
                float(row.get("absolute_floor", 0.0))
                for row in load(OBJECTIVES)["objectives"]
                if row["family"] == family
            ]
            or [1.0e-6]
        )
        for family in FAMILIES
    }
    for family in (
        "occurrence_spell",
        "wet_amount",
        "aggregate",
        "extreme",
        "compound_context",
        "winter_proxy",
    ):
        matrix = np.asarray([block[family] for block in blocks.values()], dtype=float)
        result[family] = [
            float(value)
            for value in np.maximum(
                np.std(matrix, axis=0, ddof=1), family_floor[family]
            )
        ]
    return result


def parse_cli(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            day, month, year = (int(fields[index]) for index in range(3))
            civil = date(year, month, day)
            values = [float(value) for value in fields[3:]]
        except ValueError:
            continue
        (
            precip_mm,
            duration_h,
            ttp,
            peak_ratio,
            tmax_c,
            tmin_c,
            solar,
            wind,
            direction,
            dew,
        ) = values
        row = {
            "date": civil.isoformat(),
            "precip_mm": precip_mm,
            "tmax_c": tmax_c,
            "tmin_c": tmin_c,
            "solar_radiation": solar,
            "wind_direction": direction,
            "wind_speed": wind,
            "dewpoint_c": dew,
        }
        if precip_mm > 0.0:
            row.update(
                {
                    "depth_mm": precip_mm,
                    "duration_min": duration_h * 60.0,
                    "peak_ratio": peak_ratio,
                    "time_to_peak_fraction": ttp,
                }
            )
        rows.append(row)
    if not rows:
        raise ValueError(f"no CLIGEN rows parsed: {path}")
    return rows


def faithful_rows(
    binary: Path,
    par: Path,
    site: str,
    burn: int,
    directory: Path,
    suffix: str = "primary",
) -> tuple[list[dict[str, Any]], str]:
    cli = directory / f"{site}-{burn}-{suffix}.cli"
    runspec = directory / f"{site}-{burn}-{suffix}.json"
    runspec.write_bytes(
        canonical_bytes(
            {
                "cligen_runspec": 1,
                "generation_profile": "faithful_5_32_3",
                "mode": "continuous",
                "output": {"cli": str(cli), "quality": False},
                "qc_filter": "faithful",
                "rng": {"burn": burn},
                "simulation": {"begin_year": 2001, "years": 100},
                "station": {"par": str(par)},
            }
        )
    )
    # CLIGEN intentionally refuses to overwrite output.  A replay uses the
    # identical temporary path so the path-bearing header is comparable.
    cli.unlink(missing_ok=True)
    subprocess.run(
        [str(binary), "run", str(runspec)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    digest = sha256_path(cli)
    return parse_cli(cli), digest


def validate_rows(
    rows: list[dict[str, Any]], start_year: int, year_count: int
) -> dict[str, Any]:
    expected_dates = [
        value.isoformat() for value in gregorian_dates(start_year, year_count)
    ]
    violations: list[str] = []
    actual_dates = [str(row.get("date", "")) for row in rows]
    if actual_dates != expected_dates:
        violations.append("gregorian_continuity")
    for index, row in enumerate(rows):
        required = ("precip_mm", "tmax_c", "tmin_c")
        if not all(
            field in row and math.isfinite(float(row[field])) for field in required
        ):
            violations.append(f"finite_required:{index}")
            continue
        if precip(row) < 0.0:
            violations.append(f"precipitation_support:{index}")
        if float(row["tmax_c"]) < float(row["tmin_c"]):
            violations.append(f"temperature_order:{index}")
        for field, value in row.items():
            if (
                field != "date"
                and isinstance(value, (int, float))
                and not math.isfinite(float(value))
            ):
                violations.append(f"nonfinite:{field}:{index}")
        for field in ("solar_radiation", "solar_radiation_w_m2"):
            if field in row and float(row[field]) < 0.0:
                violations.append(f"solar_support:{index}")
        for field in ("wind_speed", "wind_speed_1_5m_m_s"):
            if field in row and float(row[field]) < 0.0:
                violations.append(f"wind_speed_support:{index}")
        if "wind_direction" in row and not 0.0 <= float(row["wind_direction"]) <= 360.0:
            violations.append(f"wind_direction_support:{index}")
        if (
            "relative_humidity_pct" in row
            and not 0.0 <= float(row["relative_humidity_pct"]) <= 100.0
        ):
            violations.append(f"humidity_support:{index}")
        if precip(row) > 0.0:
            descriptors = ("duration_min", "time_to_peak_fraction", "peak_ratio")
            if not all(
                field in row and math.isfinite(float(row[field]))
                for field in descriptors
            ):
                violations.append(f"storm_descriptor_finite:{index}")
            elif not (
                float(row["duration_min"]) > 0.0
                and 0.0 <= float(row["time_to_peak_fraction"]) <= 1.0
                and float(row["peak_ratio"]) >= 1.0
            ):
                violations.append(f"storm_descriptor_support:{index}")
    return {
        "expected_row_count": len(expected_dates),
        "row_count": len(rows),
        "status": "pass" if not violations else "fail",
        "violation_count": len(violations),
        "violations": violations[:100],
    }


def prefix(rows: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    end_year = int(rows[0]["date"][:4]) + horizon
    return [row for row in rows if int(row["date"][:4]) < end_year]


def run_features(rows: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    selected = prefix(rows, horizon)
    events = [row for row in selected if precip(row) > 0.0 and "duration_min" in row]
    return {
        "family": family_vectors(selected),
        "objectives": objective_features(selected),
        "storm": event_vectors(events),
    }


def observed_context() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    daily = load_daymet("development")
    storms = load_uscrn("development")
    observed = {}
    scales = {}
    for site, payload in daily.items():
        observed[site] = {
            "family": family_vectors(payload["records"]),
            "objectives": objective_features(payload["records"]),
            "stratum": payload["stratum"],
        }
        scales[site] = family_scale(payload["records"])
    storm_by_stratum: dict[str, dict[str, Any]] = defaultdict(dict)
    for site, payload in storms.items():
        storm_by_stratum[payload["stratum"]][site] = event_vectors(payload["events"])
    grouped = {
        stratum: mean_vectors([vectors for _, vectors in sorted(sites.items())])
        for stratum, sites in storm_by_stratum.items()
    }
    return observed, scales, grouped


def thresholds() -> dict[tuple[str, int], float]:
    return {
        (row["family"], int(row["horizon_years"])): float(row["max_statistic_95"])
        for row in load(CALIBRATION)["thresholds"]
    }


def predecessor_hash(relative_path: str) -> str:
    records = {row["path"]: row["sha256"] for row in load(PREDECESSOR)["files"]}
    return records[relative_path]


def candidate_provenance_complete(
    detail: dict[str, Any], compact: dict[str, Any]
) -> bool:
    source_manifest = load(A9C / "observed-source-manifest-v1.json")
    expected_rows = [
        row
        for row in source_manifest["daymet_normalized_objects"]
        + source_manifest["uscrn_normalized_objects"]
        if row["role"] == "coefficient_fit"
    ]
    expected = {
        row["path"]: (
            row["logical_sha256"],
            row["object_sha256"],
            row["role"],
            row["station_id"],
        )
        for row in expected_rows
    }
    actual = {
        row["path"]: (
            row["logical_sha256"],
            row["object_sha256"],
            row["role"],
            row["station_id"],
        )
        for row in detail["sources"]
    }
    source_files_valid = expected == actual and all(
        (ROOT / relative).is_file() and sha256_path(ROOT / relative) == object_sha
        for relative, (_, object_sha, _, _) in actual.items()
    )
    parents = compact["parent_identities"]
    parent_valid = (
        parents["calibration_sha256"] == sha256_path(CALIBRATION)
        and parents["campaign_freeze_sha256"] == sha256_path(CONFIG_SOURCE)
        and parents["design_freeze_sha256"] == sha256_path(DESIGN)
        and parents["objective_registry_sha256"] == sha256_path(OBJECTIVES)
        and parents["source_inventory_sha256"]
        == sha256_bytes(canonical_bytes(detail["sources"]))
    )
    rng = compact["rng"]
    expected_rng = deterministic_fit_identities(detail, detail["configuration"])
    rng_valid = (
        rng["fit"] == expected_rng["fit"]
        and rng["optimizer"] == expected_rng["optimizer"]
        and rng["parameter_member"] == expected_rng["parameter_member"]
        and rng["monthly_reconciliation"]
        == f"NumPy Philox a9c3-monthly-reconciliation-v1/{detail['fit_id']}/target|heldout"
        and rng["simulation"]
        == f"A9 Philox4x32-10 random-field campaign a9c/{detail['fit_id']}"
    )
    return bool(
        detail_hash(detail) == detail["content_sha256"]
        and compact["content_sha256"] == detail["content_sha256"]
        and compact["model_source_sha256"] == predecessor_hash("research/a9c/models.py")
        and source_files_valid
        and parent_valid
        and rng_valid
    )


def storm_scale(stratum: str, horizon: int, objective: str) -> np.ndarray:
    return np.asarray(
        load(CALIBRATION)["storm_component_scales"][stratum][str(horizon)][objective],
        dtype=float,
    )


def aggregate_stage(
    configuration_id: str,
    candidate_class: str,
    run_cache: dict[tuple[str, int], dict[str, Any]],
    baseline_cache: dict[tuple[str, int], dict[str, Any]],
    sites: list[str],
    burns: list[int],
    horizons: list[int],
    observed: dict[str, Any],
    scales: dict[str, Any],
    storm_observed: dict[str, Any],
    engineering: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    registry = {row["id"]: row for row in load(OBJECTIVES)["objectives"]}
    threshold_map = thresholds()
    family_rows = []
    objective_rows = []
    strata_sites: dict[str, list[str]] = defaultdict(list)
    for site in sites:
        strata_sites[observed[site]["stratum"]].append(site)
    for horizon in horizons:
        for stratum, members in sorted(strata_sites.items()):
            for family in (
                "occurrence_spell",
                "wet_amount",
                "aggregate",
                "extreme",
                "compound_context",
                "winter_proxy",
            ):
                if family == "winter_proxy" and stratum != "cold":
                    continue
                candidate_distances = []
                baseline_distances = []
                for burn in burns:
                    for site in members:
                        reference = np.asarray(observed[site]["family"][family])
                        scale = np.asarray(scales[site][family])
                        candidate = np.asarray(
                            run_cache[(site, burn)][horizon]["family"][family]
                        )
                        baseline = np.asarray(
                            baseline_cache[(site, burn)][horizon]["family"][family]
                        )
                        candidate_distances.append(
                            float(np.max(np.abs(candidate - reference) / scale))
                        )
                        baseline_distances.append(
                            float(np.max(np.abs(baseline - reference) / scale))
                        )
                candidate_distance = float(np.median(candidate_distances))
                baseline_distance = float(np.median(baseline_distances))
                gate = threshold_map[(family, horizon)]
                family_rows.append(
                    {
                        "baseline_distance": baseline_distance,
                        "candidate_distance": candidate_distance,
                        "candidate_minus_baseline": candidate_distance
                        - baseline_distance,
                        "family": family,
                        "horizon_years": horizon,
                        "material_degradation": candidate_distance - baseline_distance
                        > gate,
                        "material_improvement": baseline_distance - candidate_distance
                        > gate,
                        "replicate_station_values": len(candidate_distances),
                        "stratum": stratum,
                        "threshold": gate,
                    }
                )

            candidate_storm: dict[str, list[float]] = defaultdict(list)
            baseline_storm: dict[str, list[float]] = defaultdict(list)
            for burn in burns:
                candidate_group = mean_vectors(
                    [run_cache[(site, burn)][horizon]["storm"] for site in members]
                )
                baseline_group = mean_vectors(
                    [baseline_cache[(site, burn)][horizon]["storm"] for site in members]
                )
                for objective in (
                    "storm_duration",
                    "storm_time_to_peak",
                    "storm_peak_ratio",
                    "storm_joint_dependence",
                ):
                    reference = np.asarray(storm_observed[stratum][objective])
                    scale = storm_scale(stratum, horizon, objective)
                    candidate_storm[objective].append(
                        float(
                            np.sqrt(
                                np.mean(
                                    (
                                        (
                                            np.asarray(candidate_group[objective])
                                            - reference
                                        )
                                        / scale
                                    )
                                    ** 2
                                )
                            )
                        )
                    )
                    baseline_storm[objective].append(
                        float(
                            np.sqrt(
                                np.mean(
                                    (
                                        (
                                            np.asarray(baseline_group[objective])
                                            - reference
                                        )
                                        / scale
                                    )
                                    ** 2
                                )
                            )
                        )
                    )
            candidate_distance = max(
                float(np.median(values)) for values in candidate_storm.values()
            )
            baseline_distance = max(
                float(np.median(values)) for values in baseline_storm.values()
            )
            gate = threshold_map[("storm_descriptor", horizon)]
            family_rows.append(
                {
                    "baseline_distance": baseline_distance,
                    "candidate_distance": candidate_distance,
                    "candidate_minus_baseline": candidate_distance - baseline_distance,
                    "family": "storm_descriptor",
                    "horizon_years": horizon,
                    "material_degradation": candidate_distance - baseline_distance
                    > gate,
                    "material_improvement": baseline_distance - candidate_distance
                    > gate,
                    "replicate_station_values": len(burns) * len(candidate_storm),
                    "stratum": stratum,
                    "threshold": gate,
                }
            )

            for objective_id, definition in registry.items():
                if definition["family"] in ("engineering", "storm_descriptor"):
                    continue
                if definition["family"] == "winter_proxy" and stratum != "cold":
                    continue
                candidate_values = []
                baseline_values = []
                available_sites = set()
                for site in members:
                    reference = observed[site]["objectives"][objective_id]
                    for burn in burns:
                        candidate_distance = feature_distance(
                            objective_id,
                            run_cache[(site, burn)][horizon]["objectives"][
                                objective_id
                            ],
                            reference,
                            float(definition.get("absolute_floor", 0.0)),
                        )
                        baseline_distance = feature_distance(
                            objective_id,
                            baseline_cache[(site, burn)][horizon]["objectives"][
                                objective_id
                            ],
                            reference,
                            float(definition.get("absolute_floor", 0.0)),
                        )
                        if (
                            candidate_distance is not None
                            and baseline_distance is not None
                        ):
                            available_sites.add(site)
                            candidate_values.append(candidate_distance)
                            baseline_values.append(baseline_distance)
                objective_rows.append(
                    {
                        "available_station_count": len(available_sites),
                        "baseline_distance": (
                            float(np.median(baseline_values))
                            if baseline_values
                            else None
                        ),
                        "candidate_distance": (
                            float(np.median(candidate_values))
                            if candidate_values
                            else None
                        ),
                        "horizon_years": horizon,
                        "objective_id": objective_id,
                        "selection_role": definition["selection_role"],
                        "status": (
                            "available" if len(available_sites) >= 2 else "unavailable"
                        ),
                        "stratum": stratum,
                    }
                )
            for objective_id in (
                "storm_duration",
                "storm_time_to_peak",
                "storm_peak_ratio",
                "storm_joint_dependence",
            ):
                candidate_values = []
                baseline_values = []
                reference = np.asarray(storm_observed[stratum][objective_id])
                scale = storm_scale(stratum, horizon, objective_id)
                for burn in burns:
                    candidate_group = mean_vectors(
                        [run_cache[(site, burn)][horizon]["storm"] for site in members]
                    )
                    baseline_group = mean_vectors(
                        [
                            baseline_cache[(site, burn)][horizon]["storm"]
                            for site in members
                        ]
                    )
                    candidate_values.append(
                        float(
                            np.sqrt(
                                np.mean(
                                    (
                                        (
                                            np.asarray(candidate_group[objective_id])
                                            - reference
                                        )
                                        / scale
                                    )
                                    ** 2
                                )
                            )
                        )
                    )
                    baseline_values.append(
                        float(
                            np.sqrt(
                                np.mean(
                                    (
                                        (
                                            np.asarray(baseline_group[objective_id])
                                            - reference
                                        )
                                        / scale
                                    )
                                    ** 2
                                )
                            )
                        )
                    )
                objective_rows.append(
                    {
                        "available_station_count": 2,
                        "baseline_distance": float(np.median(baseline_values)),
                        "candidate_distance": float(np.median(candidate_values)),
                        "horizon_years": horizon,
                        "objective_id": objective_id,
                        "selection_role": registry[objective_id]["selection_role"],
                        "status": "available",
                        "stratum": stratum,
                    }
                )

        selected_checks = [
            engineering[(site, burn)] for site in sites for burn in burns
        ]
        engineering_values = {
            "eng_deterministic_replay": sum(
                not row["deterministic_replay"] or not row["nested_30_year_prefix"]
                for row in selected_checks
            ),
            "eng_calendar_and_support": sum(
                int(row["calendar_and_support"]["violation_count"])
                for row in selected_checks
            ),
            "eng_provenance_completeness": sum(
                not row["provenance_complete"] for row in selected_checks
            ),
        }
        for objective_id, violations in engineering_values.items():
            objective_rows.append(
                {
                    "available_station_count": len(sites),
                    "baseline_distance": 0.0,
                    "candidate_distance": float(violations),
                    "horizon_years": horizon,
                    "objective_id": objective_id,
                    "selection_role": "hard_invariant",
                    "status": "available" if violations == 0 else "failed",
                    "stratum": "all",
                }
            )
    finite_family_rows = all(
        finite([row["baseline_distance"], row["candidate_distance"], row["threshold"]])
        for row in family_rows
    )
    degradations = [row for row in family_rows if row["material_degradation"]]
    degraded_families = {row["family"] for row in degradations}
    improvement_horizons: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in family_rows:
        if row["material_improvement"]:
            improvement_horizons[(row["family"], row["stratum"])].add(
                int(row["horizon_years"])
            )
    improved_families = {
        family
        for (family, _), family_horizons in improvement_horizons.items()
        if {30, 100} <= family_horizons and family not in degraded_families
    }
    mandatory_unavailable = [
        row
        for row in objective_rows
        if row["selection_role"] == "mandatory" and row["status"] != "available"
    ]
    hard_failures = [
        row
        for row in objective_rows
        if row["selection_role"] == "hard_invariant" and row["status"] != "available"
    ]
    candidate_distances = [row["candidate_distance"] for row in family_rows]
    baseline_distances = [row["baseline_distance"] for row in family_rows]
    standardized_improvements = [
        (row["baseline_distance"] - row["candidate_distance"]) / row["threshold"]
        for row in family_rows
    ]
    return {
        "candidate_class": candidate_class,
        "configuration_id": configuration_id,
        "family_rows": family_rows,
        "objective_rows": objective_rows,
        "summary": {
            "complete": finite_family_rows
            and not mandatory_unavailable
            and not hard_failures,
            "degradation_count": len(degradations),
            "effective_baseline_distance_median": float(np.median(baseline_distances)),
            "hard_failure_count": len(hard_failures),
            "improved_family_count": len(improved_families),
            "mandatory_unavailable_count": len(mandatory_unavailable),
            "median_normalized_distance": float(np.median(candidate_distances)),
            "worst_standardized_improvement": float(min(standardized_improvements)),
        },
    }


def evaluate() -> None:
    if (
        not CALIBRATION.exists()
        or not FIT_EXECUTION.exists()
        or not STRUCTURAL.exists()
    ):
        raise ValueError("calibration and complete fits must precede evaluation")
    if EVALUATION.exists() or BASELINE.exists() or FREEZE.exists():
        raise FileExistsError("evaluation evidence exists")
    structural = load(STRUCTURAL)
    if structural["status"] != "pass":
        raise ValueError("HOLD-A9C3-MODEL-CLASS-EQUIVALENCE")
    fit_evidence = load(FIT_EXECUTION)
    if any(value < 1 for value in fit_evidence["valid_fit_count_by_class"].values()):
        raise ValueError("HOLD-A9C3-FIT-APPLICABILITY")
    started = time.monotonic()
    development_daily = load_daymet("development")
    development_storm = load_uscrn("development")
    panel_verification = verify_panels(development_daily, development_storm)
    observed, scales, storm_observed = observed_context()
    sites = sorted(observed)
    strata_sites: dict[str, list[str]] = defaultdict(list)
    for site in sites:
        strata_sites[observed[site]["stratum"]].append(site)
    burns = load(DESIGN)["burns"]
    baseline_cache: dict[tuple[str, int], dict[int, dict[str, Any]]] = {}
    baseline_hashes = []
    baseline_engineering = []
    archive = ROOT / load(DESIGN)["baseline"]["parameter_archive"]
    source_tree_clean = (
        subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                SOURCE_COMMIT,
                "--",
                "Cargo.toml",
                "Cargo.lock",
                "crates",
            ],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0
    )
    build_directory = Path(tempfile.mkdtemp(prefix="a9c3-frozen-build-"))
    build_environment = {
        name: os.environ.get(name, "")
        for name in (
            "CARGO_BUILD_RUSTFLAGS",
            "CARGO_ENCODED_RUSTFLAGS",
            "RUSTFLAGS",
        )
    }
    if any("fast-math" in value for value in build_environment.values()):
        raise RuntimeError("HOLD-A9C3-PREDECESSOR-INTEGRITY: fast-math build flag")
    build_command = [
        "cargo",
        "build",
        "--release",
        "--locked",
        "--bin",
        "cligen",
        "--target-dir",
        str(build_directory),
    ]
    subprocess.run(build_command, cwd=ROOT, check=True)
    binary = build_directory / "release/cligen"
    if not binary.is_file():
        raise RuntimeError("HOLD-A9C3-PREDECESSOR-INTEGRITY: isolated build output")
    source_tree_receipt = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            SOURCE_COMMIT,
            "--",
            "Cargo.toml",
            "Cargo.lock",
            "crates",
        ],
        cwd=ROOT,
    )
    baseline_build_provenance = {
        "binary_sha256": sha256_path(binary),
        "build_command": [
            "cargo",
            "build",
            "--release",
            "--locked",
            "--bin",
            "cligen",
            "--target-dir",
            "<fresh-isolated-target>",
        ],
        "build_environment": build_environment,
        "build_profile": "Cargo default release profile; no repository override",
        "cargo_toml_sha256": sha256_path(ROOT / "Cargo.toml"),
        "cargo_lock_sha256": sha256_path(ROOT / "Cargo.lock"),
        "cargo_version": subprocess.check_output(
            ["cargo", "--version"], text=True
        ).strip(),
        "parameter_archive_sha256": sha256_path(archive),
        "rustc_version_verbose": subprocess.check_output(
            ["rustc", "--version", "--verbose"], text=True
        ).strip(),
        "source_tree_receipt_sha256": sha256_bytes(source_tree_receipt),
        "source_commit": SOURCE_COMMIT,
        "source_tree_matches_commit": source_tree_clean,
        "target_directory_was_fresh": True,
    }
    baseline_build_provenance["status"] = (
        "pass"
        if source_tree_clean
        and baseline_build_provenance["parameter_archive_sha256"]
        == predecessor_hash(str(archive.relative_to(ROOT)))
        else "fail"
    )
    if baseline_build_provenance["status"] != "pass":
        raise RuntimeError("HOLD-A9C3-PREDECESSOR-INTEGRITY: build provenance")
    with tempfile.TemporaryDirectory(prefix="a9c3-faithful-") as raw:
        directory = Path(raw)
        with tarfile.open(archive, "r:gz") as stream:
            stream.extractall(directory, filter="data")
        for site in sites:
            par = directory / f"station-parameters/{site}.par"
            for burn in burns:
                rows, digest = faithful_rows(binary, par, site, burn, directory)
                replay_rows, replay_digest = faithful_rows(
                    binary, par, site, burn, directory
                )
                validation = validate_rows(rows, 2001, 100)
                replay_ok = digest == replay_digest and canonical_bytes(
                    rows
                ) == canonical_bytes(replay_rows)
                provenance_ok = (
                    baseline_build_provenance["status"] == "pass"
                    and par.is_file()
                    and len(sha256_path(par)) == 64
                )
                check = {
                    "burn": burn,
                    "calendar_and_support": validation,
                    "deterministic_replay": replay_ok,
                    "provenance_complete": provenance_ok,
                    "site": site,
                }
                baseline_engineering.append(check)
                if validation["status"] != "pass" or not replay_ok or not provenance_ok:
                    raise RuntimeError(
                        "HOLD-A9C3-PREDECESSOR-INTEGRITY: faithful engineering invariant"
                    )
                baseline_hashes.append(
                    {
                        "burn": burn,
                        "cli_sha256": digest,
                        "par_sha256": sha256_path(par),
                        "site": site,
                    }
                )
                baseline_cache[(site, burn)] = {
                    horizon: run_features(rows, horizon) for horizon in (30, 100)
                }
    baseline_record = {
        "binary_sha256": sha256_path(binary),
        "build_provenance": baseline_build_provenance,
        "burn_count": len(burns),
        "design_freeze_sha256": sha256_path(DESIGN),
        "generation_profile": "faithful_5_32_3",
        "output_identities": baseline_hashes,
        "engineering_checks": baseline_engineering,
        "run_count": len(baseline_hashes),
        "schema_version": 1,
        "station_count": len(sites),
    }
    write_once(BASELINE, baseline_record)

    fits = []
    for row in fit_evidence["fits"]:
        if (
            sha256_path(ROOT / row["path"]) != row["sha256"]
            or sha256_path(ROOT / row["detail_path"]) != row["detail_sha256"]
        ):
            raise RuntimeError("HOLD-A9C3-PREDECESSOR-INTEGRITY: fit artifact identity")
    fit_compacts = {
        row["configuration_id"]: load(ROOT / row["path"])
        for row in fit_evidence["fits"]
    }
    for row in fit_evidence["fits"]:
        if row["fit_status"] == "fit_valid":
            fits.append(load(ROOT / row["detail_path"]))
    fit_provenance = {
        detail["configuration"]["configuration_id"]: candidate_provenance_complete(
            detail, fit_compacts[detail["configuration"]["configuration_id"]]
        )
        for detail in fits
    }

    candidate_streams: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    candidate_checks: dict[tuple[str, str, int], dict[str, Any]] = {}

    def candidate_cache(
        detail: dict[str, Any], selected_sites: list[str], selected_burns: list[int]
    ) -> tuple[
        dict[tuple[str, int], dict[int, dict[str, Any]]],
        dict[tuple[str, int], dict[str, Any]],
    ]:
        cache = {}
        checks = {}
        identifier = detail["configuration"]["configuration_id"]
        for site in selected_sites:
            for burn in selected_burns:
                key = (identifier, site, burn)
                if key not in candidate_streams:
                    rows = simulate(detail, site, burn=burn, years=100)
                    replay = simulate(detail, site, burn=burn, years=100)
                    thirty = simulate(detail, site, burn=burn, years=30)
                    validation = validate_rows(rows, 2001, 100)
                    candidate_streams[key] = rows
                    candidate_checks[key] = {
                        "calendar_and_support": validation,
                        "configuration_id": identifier,
                        "deterministic_replay": canonical_bytes(rows)
                        == canonical_bytes(replay),
                        "nested_30_year_prefix": canonical_bytes(thirty)
                        == canonical_bytes(prefix(rows, 30)),
                        "output_sha256": sha256_bytes(canonical_bytes(rows)),
                        "provenance_complete": fit_provenance[identifier],
                        "rng_identity": f"a9c/{detail['fit_id']}/{site}/{burn}",
                        "site": site,
                        "burn": burn,
                    }
                rows = candidate_streams[key]
                cache[(site, burn)] = {
                    horizon: run_features(rows, horizon) for horizon in (30, 100)
                }
                checks[(site, burn)] = candidate_checks[key]
        return cache, checks

    stages = []
    short_rows = []
    for detail in fits:
        cache, checks = candidate_cache(detail, sites, burns[:2])
        row = aggregate_stage(
            detail["configuration"]["configuration_id"],
            detail["candidate_class"],
            cache,
            baseline_cache,
            sites,
            burns[:2],
            [30],
            observed,
            scales,
            storm_observed,
            checks,
        )
        short_rows.append(row)
    stages.append(
        {
            "configuration_count": len(short_rows),
            "results": short_rows,
            "stage": "short_screen",
        }
    )

    full_ids = set()
    for candidate in (RENEWAL, LATENT):
        candidates = [
            row
            for row in short_rows
            if row["candidate_class"] == candidate
            and row["summary"]["hard_failure_count"] == 0
        ]
        candidates.sort(
            key=lambda row: (
                not row["summary"]["complete"],
                row["summary"]["median_normalized_distance"],
                row["configuration_id"],
            )
        )
        full_ids.update(row["configuration_id"] for row in candidates[:2])
    full_rows = []
    for detail in fits:
        if detail["configuration"]["configuration_id"] not in full_ids:
            continue
        cache, checks = candidate_cache(detail, sites, burns[:4])
        row = aggregate_stage(
            detail["configuration"]["configuration_id"],
            detail["candidate_class"],
            cache,
            baseline_cache,
            sites,
            burns[:4],
            [30, 100],
            observed,
            scales,
            storm_observed,
            checks,
        )
        full_rows.append(row)
    stages.append(
        {
            "configuration_count": len(full_rows),
            "results": full_rows,
            "stage": "full_development",
        }
    )

    replay_ids = set()
    for candidate in (RENEWAL, LATENT):
        candidates = [
            row
            for row in full_rows
            if row["candidate_class"] == candidate
            and row["summary"]["hard_failure_count"] == 0
        ]
        candidates.sort(
            key=lambda row: (
                not row["summary"]["complete"],
                row["summary"]["degradation_count"],
                row["summary"]["median_normalized_distance"],
                row["configuration_id"],
            )
        )
        if candidates:
            replay_ids.add(candidates[0]["configuration_id"])
    replay_rows = []
    for detail in fits:
        identifier = detail["configuration"]["configuration_id"]
        if identifier not in replay_ids:
            continue
        cache, checks = candidate_cache(detail, sites, burns)
        row = aggregate_stage(
            identifier,
            detail["candidate_class"],
            cache,
            baseline_cache,
            sites,
            burns,
            [30, 100],
            observed,
            scales,
            storm_observed,
            checks,
        )
        replay_rows.append(row)
    stages.append(
        {
            "configuration_count": len(replay_rows),
            "results": replay_rows,
            "stage": "pareto_replay",
        }
    )

    pareto_metric_ids = sorted(
        {
            f"{family_row['family']}:{family_row['stratum']}:{family_row['horizon_years']}"
            for row in replay_rows
            for family_row in row["family_rows"]
        }
    )
    pareto_items = [
        {
            "id": row["configuration_id"],
            "objectives": {
                f"{family_row['family']}:{family_row['stratum']}:{family_row['horizon_years']}": family_row[
                    "candidate_distance"
                ]
                for family_row in row["family_rows"]
            },
        }
        for row in replay_rows
    ]
    pareto_ids = pareto_frontier(pareto_items, pareto_metric_ids)

    summaries = []
    for row in replay_rows:
        fit_detail = next(
            detail
            for detail in fits
            if detail["configuration"]["configuration_id"] == row["configuration_id"]
        )
        summary = row["summary"]
        summaries.append(
            SelectionSummary(
                candidate_class=row["candidate_class"],
                feasible=summary["hard_failure_count"] == 0,
                complete=summary["complete"],
                degradation_count=summary["degradation_count"],
                worst_standardized_improvement=summary[
                    "worst_standardized_improvement"
                ],
                improved_families=summary["improved_family_count"],
                median_normalized_distance=summary["median_normalized_distance"],
                effective_parameter_count=int(fit_detail["effective_parameter_count"]),
            )
        )
    selected_class = None
    selection_error = None
    try:
        selected_class = select_candidate(summaries)
    except Exception as error:  # typed harness error is retained in the artifact
        selection_error = f"{type(error).__name__}: {error}"
    selected_configuration = None
    if selected_class is not None:
        selected_configuration = next(
            row["configuration_id"]
            for row in replay_rows
            if row["candidate_class"] == selected_class
        )

    replay_checks = [
        value for key, value in sorted(candidate_checks.items()) if key[0] in replay_ids
    ]
    terminal = (
        "CANDIDATE-FROZEN-READY-A9D"
        if selected_class
        else "HOLD-A9C3-NO-SELECTABLE-CANDIDATE"
    )
    evaluation_resource = resource_snapshot("evaluation", started)
    campaign_wall_seconds = (
        float(load(CALIBRATION)["resource"]["wall_seconds"])
        + float(fit_evidence["resource"]["wall_seconds"])
        + float(evaluation_resource["wall_seconds"])
    )
    campaign_limit_seconds = (
        float(load(DESIGN)["resource_limits"]["campaign_wall_hours"]) * 3600.0
    )
    if campaign_wall_seconds > campaign_limit_seconds:
        raise RuntimeError("HOLD-A9C3-RESOURCE-BOUND: campaign_wall_hours")
    output = {
        "baseline_sha256": sha256_path(BASELINE),
        "calibration_sha256": sha256_path(CALIBRATION),
        "campaign_resource": {
            "limit_seconds": campaign_limit_seconds,
            "status": "pass",
            "wall_seconds": campaign_wall_seconds,
        },
        "confirmation_series_accessed": False,
        "design_freeze_sha256": sha256_path(DESIGN),
        "engineering_attempt_inventory": [
            value for _, value in sorted(candidate_checks.items())
        ],
        "fit_execution_sha256": sha256_path(FIT_EXECUTION),
        "objective_registry_sha256": sha256_path(OBJECTIVES),
        "panel_verification": panel_verification,
        "pareto_trace": {
            "frontier_configuration_ids": pareto_ids,
            "item_count": len(pareto_items),
            "metric_count": len(pareto_metric_ids),
            "metric_ids": pareto_metric_ids,
        },
        "replay_checks": replay_checks,
        "schema_version": 1,
        "selected_candidate_class": selected_class,
        "selected_configuration_id": selected_configuration,
        "selection_error": selection_error,
        "selection_rule_id": "a9_lexicographic_pareto_v1",
        "stages": stages,
        "terminal": terminal,
        "two_site_generalization_limit": load(DESIGN)["two_site_generalization_limit"],
        "resource": evaluation_resource,
        "wall_seconds": time.monotonic() - started,
    }
    write_once(EVALUATION, output)
    if selected_class is not None:
        selected_detail = next(
            detail
            for detail in fits
            if detail["configuration"]["configuration_id"] == selected_configuration
        )
        freeze = {
            "candidate_class": selected_class,
            "configuration_id": selected_configuration,
            "confirmation_access_authorized": False,
            "detail_content_sha256": selected_detail["content_sha256"],
            "detail_path": next(
                row["detail_path"]
                for row in fit_evidence["fits"]
                if row["configuration_id"] == selected_configuration
            ),
            "evaluation_sha256": sha256_path(EVALUATION),
            "schema_version": 1,
            "status": "research_freeze_ready_for_separate_a9d_dispatch",
            "two_site_generalization_limit": load(DESIGN)[
                "two_site_generalization_limit"
            ],
        }
        write_once(FREEZE, freeze)
    shutil.rmtree(build_directory)
    print(
        f"evaluated short={len(short_rows)}, full={len(full_rows)}, replay={len(replay_rows)}; "
        f"terminal={terminal}; selected={selected_class}"
    )


def verify() -> None:
    design_hash = sha256_path(DESIGN)
    calibration = load(CALIBRATION)
    if (
        calibration["design_freeze_sha256"] != design_hash
        or calibration["candidate_inputs_accessed"] is not False
        or calibration["status"] != "finite_grouped_estimators"
        or calibration["bootstrap_replicates"] != 2000
        or len(calibration["thresholds"]) != 14
        or calibration["event_counts"]
        != {"az_yuma_27_ene": 136, "ca_stovepipe_wells_1_sw": 97}
    ):
        raise ValueError("calibration boundary")
    fit_evidence = load(FIT_EXECUTION)
    if fit_evidence["design_freeze_sha256"] != design_hash or fit_evidence[
        "calibration_sha256"
    ] != sha256_path(CALIBRATION):
        raise ValueError("fit boundary")
    for record in fit_evidence["fits"]:
        detail = ROOT / record["detail_path"]
        compact = ROOT / record["path"]
        if (
            sha256_path(detail) != record["detail_sha256"]
            or sha256_path(compact) != record["sha256"]
        ):
            raise ValueError("fit identity")
        value = load(detail)
        if detail_hash(value) != value["content_sha256"]:
            raise ValueError("fit content hash")
        if record["monthly_reconciliation"]["status"] != "pass":
            raise ValueError("monthly reconciliation")
    valid_fit_ids = {
        record["configuration_id"]
        for record in fit_evidence["fits"]
        if record["fit_status"] == "fit_valid"
    }
    if (
        fit_evidence["fresh_fit_count"] != 8
        or len(valid_fit_ids) != 6
        or fit_evidence["valid_fit_count_by_class"]
        != {
            "alternating_renewal_marked_v1": 4,
            "latent_regime_marked_v1": 2,
        }
    ):
        raise ValueError("fit inventory")
    if (
        sha256_path(STRUCTURAL) != fit_evidence["structural_audit_sha256"]
        or load(STRUCTURAL)["status"] != "pass"
    ):
        raise ValueError("structural evidence")
    evaluation = load(EVALUATION)
    baseline = load(BASELINE)
    baseline_checks = baseline["engineering_checks"]
    if (
        evaluation["baseline_sha256"] != sha256_path(BASELINE)
        or baseline["build_provenance"]["status"] != "pass"
        or baseline["run_count"] != 160
        or len(baseline_checks) != 160
        or any(
            row["calendar_and_support"]["status"] != "pass"
            or not row["deterministic_replay"]
            or not row["provenance_complete"]
            for row in baseline_checks
        )
    ):
        raise ValueError("faithful baseline")
    if (
        evaluation["confirmation_series_accessed"] is not False
        or evaluation["design_freeze_sha256"] != design_hash
        or evaluation["calibration_sha256"] != sha256_path(CALIBRATION)
        or evaluation["fit_execution_sha256"] != sha256_path(FIT_EXECUTION)
    ):
        raise ValueError("confirmation access")
    if any(
        not row["deterministic_replay"] or not row["nested_30_year_prefix"]
        for row in evaluation["replay_checks"]
    ):
        raise ValueError("replay invariant")
    if len(evaluation["stages"]) != 3:
        raise ValueError("stage count")
    for stage in evaluation["stages"]:
        if stage["configuration_count"] != len(stage["results"]):
            raise ValueError("stage configuration count")
        for row in stage["results"]:
            ids = {record["objective_id"] for record in row["objective_rows"]}
            if len(ids) != 31:
                raise ValueError(
                    f"objective coverage {row['configuration_id']}: {len(ids)}"
                )
    short_ids = {
        row["configuration_id"] for row in evaluation["stages"][0]["results"]
    }
    attempts = evaluation["engineering_attempt_inventory"]
    if short_ids != valid_fit_ids or len(attempts) != len(valid_fit_ids) * 20 * 2:
        raise ValueError("short-screen inventory")
    if any(
        not row["deterministic_replay"]
        or not row["nested_30_year_prefix"]
        or not row["provenance_complete"]
        for row in attempts
    ):
        raise ValueError("short-screen engineering identity")
    for row in evaluation["stages"][0]["results"]:
        failure = next(
            record
            for record in row["objective_rows"]
            if record["objective_id"] == "eng_calendar_and_support"
        )
        configuration_attempts = [
            attempt
            for attempt in attempts
            if attempt["configuration_id"] == row["configuration_id"]
        ]
        violation_count = sum(
            attempt["calendar_and_support"]["violation_count"]
            for attempt in configuration_attempts
        )
        if failure["candidate_distance"] != violation_count:
            raise ValueError(
                f"engineering violation count {row['configuration_id']}"
            )
    if evaluation["terminal"] == "CANDIDATE-FROZEN-READY-A9D":
        if not FREEZE.exists() or load(FREEZE)["evaluation_sha256"] != sha256_path(
            EVALUATION
        ):
            raise ValueError("candidate freeze")
    elif evaluation["terminal"] != "HOLD-A9C3-NO-SELECTABLE-CANDIDATE":
        raise ValueError("terminal")
    elif (
        FREEZE.exists()
        or evaluation["selected_candidate_class"] is not None
        or evaluation["selected_configuration_id"] is not None
        or evaluation["stages"][1]["configuration_count"] != 0
        or evaluation["stages"][2]["configuration_count"] != 0
    ):
        raise ValueError("hold closure")
    print(
        f"PASS: 2-site grouped calibration; {fit_evidence['fresh_fit_count']} fresh fits; "
        f"{len(short_ids)} short-screen configurations with 31-objective coverage; "
        f"terminal={evaluation['terminal']}; confirmation target series untouched"
    )


def main() -> None:
    import sys

    commands = {
        "calibrate": calibrate,
        "evaluate": evaluate,
        "fit": fit,
        "fit-closeout": resume_fit_closeout,
        "verify": verify,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit(
            "usage: python -m research.a9c3.experiment calibrate|fit|fit-closeout|evaluate|verify"
        )
    commands[sys.argv[1]]()


if __name__ == "__main__":
    main()
