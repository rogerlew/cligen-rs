"""Execute A9d development on the accepted A9c4 evidence surface.

The implementation reuses the accepted A9c3 evaluator while changing only
the prospectively frozen A9d seams: bounded event-context marginals, monthly
occurrence/amount calibration, the 92-cell selection surface, and campaign
identity. It does not modify production Rust generation.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
import math
import shutil
import subprocess
import tarfile
import tempfile
import time
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from research.a9c.models import (
    LATENT,
    RENEWAL,
    fit_latent,
    fit_renewal,
    load_daymet,
    load_uscrn,
    transformed_event_laws,
)
from research.a9c3 import experiment as base


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/work-packages/20260715-a9d-successor-development-confirmation"
ARTIFACTS = PACKAGE / "artifacts"
DESIGN = ARTIFACTS / "design-freeze-v1.json"
FIT_AMENDMENT = ARTIFACTS / "pre-output-fit-amendment.md"
RUNTIME_DESIGN = ARTIFACTS / "development-runtime-v1.json"
DISPATCH = ARTIFACTS / "execution-dispatch-v1.json"
PREDECESSOR = ARTIFACTS / "predecessor-manifest-v1.json"
CALIBRATION = ARTIFACTS / "calibration-v1.json"
CROSSWALK = ARTIFACTS / "confirmation-baseline-crosswalk-v1.json"
PARAMETERS = ARTIFACTS / "confirmation-baseline-parameters-v1.tar.gz"
FIT_EXECUTION = ARTIFACTS / "fit-execution-v1.json"
STRUCTURAL = ARTIFACTS / "structural-audit-v1.json"
BASELINE = ARTIFACTS / "development-faithful-baseline-v1.json"
EVALUATION = ARTIFACTS / "development-evaluation-v1.json"
FREEZE = ARTIFACTS / "candidate-freeze-v1.json"
DEVELOPMENT_RESULT = ARTIFACTS / "development-result-v1.json"
FIT_DETAILS = ARTIFACTS / "fits/detail"
FIT_RECORDS = ARTIFACTS / "fits"

A9A = ROOT / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts"
A9C = ROOT / "docs/work-packages/20260715-a9c-observed-development/artifacts"
A9C3 = ROOT / "docs/work-packages/20260715-a9c3-two-site-grouped-observed-comparison/artifacts"
A9C4 = ROOT / "docs/work-packages/20260715-a9c4-context-support-completeness/artifacts"
OBJECTIVES = A9A / "objective-registry-v1.json"
MASK = A9C4 / "evidence-mask-v1.json"
SOURCE_COMMIT = "1d0350eed8549067eca41047c0eef43949822c69"

_ORIGINAL_SIMULATE = base.simulate
_ORIGINAL_AGGREGATE = base.aggregate_stage


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def replace_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value))
    temporary.replace(path)


def predecessor_paths() -> list[Path]:
    return [
        ROOT / "docs/decisions/0002-quality-metrics-authority.md",
        A9A / "data-and-evaluation-plan.md",
        A9A / "model-family-envelope.md",
        A9A / "tuning-harness-contract.md",
        A9A / "objective-registry-v1.json",
        A9A / "confirmation-metadata-selection-v1.json",
        A9C / "campaign-freeze-v1.json",
        A9C / "data-role-freeze-v1.json",
        A9C / "observed-source-manifest-v1.json",
        A9C3 / "design-freeze-v1.json",
        A9C3 / "grouped-calibration-v1.json",
        A9C3 / "objective-evaluator-freeze-v1.json",
        A9C3 / "evaluation-v1.json",
        A9C4 / "design-freeze-v1.json",
        A9C4 / "availability-audit-v1.json",
        A9C4 / "evidence-mask-v1.json",
        ROOT / "docs/reports/a9c4-context-support-completeness-report.md",
        ROOT / "docs/reports/a9c4-context-support-completeness-report.manifest.json",
        ROOT / "research/a9c/models.py",
        ROOT / "research/a9c3/experiment.py",
        ROOT / "research/a9c4/audit.py",
    ]


def verify_predecessors() -> None:
    manifest = load(PREDECESSOR)
    for row in manifest["files"]:
        path = ROOT / row["path"]
        if not path.is_file() or sha256_path(path) != row["sha256"]:
            raise ValueError(f"HOLD-A9D-PREDECESSOR-INTEGRITY: {row['path']}")
    if manifest["design_freeze_sha256"] != sha256_path(DESIGN):
        raise ValueError("HOLD-A9D-PREDECESSOR-INTEGRITY: design")


def station_source_name(station: dict[str, Any]) -> str:
    words = station["station_name"].split()
    state = words[0]
    location = station["station_name"][3:]
    return f"{state}_{location.replace(' ', '_')}"


def deterministic_parameter_archive(rows: list[dict[str, Any]]) -> None:
    if PARAMETERS.exists():
        raise FileExistsError(PARAMETERS)
    with PARAMETERS.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as archive:
                for row in sorted(rows, key=lambda item: item["station_id"]):
                    data = Path(row.pop("_source_path")).read_bytes()
                    info = tarfile.TarInfo(
                        f"station-parameters/{row['station_id']}.par"
                    )
                    info.size = len(data)
                    info.mode = 0o644
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(data))


def build_confirmation_crosswalk() -> None:
    roster = load(A9A / "confirmation-metadata-selection-v1.json")
    subprocess.run(
        ["cargo", "build", "--quiet", "--locked", "--bin", "cligen"],
        cwd=ROOT,
        check=True,
    )
    binary = ROOT / "target/debug/cligen"
    rows = []
    for station in roster["stations"]:
        output = subprocess.check_output(
            [
                str(binary),
                "stations",
                "nearest",
                "--lat",
                str(station["latitude"]),
                "--lon",
                str(station["longitude"]),
                "--collection",
                "us-2015",
                "-n",
                "1",
                "--min-years",
                "30",
                "--json",
            ],
            text=True,
        )
        nearest = json.loads(output)
        if len(nearest) != 1:
            raise ValueError("HOLD-A9D-PREDECESSOR-INTEGRITY: nearest parameter")
        selected = nearest[0]
        source = Path(selected["path"])
        if not source.is_file():
            raise FileNotFoundError(source)
        rows.append(
            {
                "_source_path": str(source),
                "distance_km": float(selected["distance_km"]),
                "parameter_description": selected["desc"],
                "parameter_id": selected["id"],
                "parameter_latitude": float(selected["latitude"]),
                "parameter_longitude": float(selected["longitude"]),
                "parameter_sha256": sha256_path(source),
                "parameter_years": float(selected["years"]),
                "primary_stratum": station["primary_stratum"],
                "source_name": station_source_name(station),
                "station_id": station["station_id"],
                "target_latitude": float(station["latitude"]),
                "target_longitude": float(station["longitude"]),
            }
        )
    deterministic_parameter_archive(rows)
    public_rows = [{key: value for key, value in row.items() if key != "_source_path"} for row in rows]
    write_once(
        CROSSWALK,
        {
            "collection": "us-2015",
            "collection_archive_sha256": load(DESIGN)["baseline"][
                "parameter_collection_archive_sha256"
            ],
            "collection_version": "2026.07",
            "design_freeze_sha256": sha256_path(DESIGN),
            "maximum_distance_km": max(row["distance_km"] for row in public_rows),
            "parameter_archive_path": str(PARAMETERS.relative_to(ROOT)),
            "parameter_archive_sha256": sha256_path(PARAMETERS),
            "rule": load(DESIGN)["baseline"]["parameter_rule"],
            "schema_version": 1,
            "station_count": len(public_rows),
            "stations": public_rows,
        },
    )


def prepare() -> None:
    for path in (PREDECESSOR, CALIBRATION, CROSSWALK, PARAMETERS, RUNTIME_DESIGN):
        if path.exists():
            raise FileExistsError(path)
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != SOURCE_COMMIT:
        raise ValueError("HOLD-A9D-PREDECESSOR-INTEGRITY: dispatch commit")
    predecessor = {
        "design_freeze_sha256": sha256_path(DESIGN),
        "dispatch_sha256": sha256_path(DISPATCH),
        "files": [
            {
                "bytes": path.stat().st_size,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256_path(path),
            }
            for path in predecessor_paths()
        ],
        "latest_predecessor_terminal": "HOLD-A9C4-COMPLETENESS-SURFACE",
        "manifest_id": "a9d-predecessor-v1",
        "schema_version": 1,
    }
    write_once(PREDECESSOR, predecessor)

    inherited = load(A9C3 / "grouped-calibration-v1.json")
    inherited["a9d_design_freeze_sha256"] = sha256_path(DESIGN)
    inherited["inherited_source_path"] = str(
        (A9C3 / "grouped-calibration-v1.json").relative_to(ROOT)
    )
    inherited["inherited_source_sha256"] = sha256_path(
        A9C3 / "grouped-calibration-v1.json"
    )
    inherited["status"] = "inherited_candidate_blind_calibration"
    write_once(CALIBRATION, inherited)

    runtime = load(A9C3 / "design-freeze-v1.json")
    design = load(DESIGN)
    runtime["campaign_id"] = design["campaign_id"]
    runtime["source_commit"] = SOURCE_COMMIT
    runtime["burns"] = design["burns"]["development"]
    runtime["resource_limits"].update(
        {
            "campaign_wall_hours": design["resource_limits"][
                "development_wall_hours"
            ],
            "memory_gib": design["resource_limits"]["memory_gib"],
            "retained_gib": design["resource_limits"]["retained_gib"],
            "workers": design["resource_limits"]["workers"],
        }
    )
    runtime["a9d_design_freeze_sha256"] = sha256_path(DESIGN)
    runtime["evidence_mask_sha256"] = sha256_path(MASK)
    write_once(RUNTIME_DESIGN, runtime)
    build_confirmation_crosswalk()
    verify_predecessors()
    print("prepared A9d: 21 predecessor files, inherited calibration, 18-site baseline crosswalk")


def transform_context(value: float, index: int, epsilon: float) -> float:
    if index == 0:
        return value
    if index in (1, 3):
        return math.log(max(value, epsilon))
    fraction = min(1.0 - epsilon, max(epsilon, value / 100.0))
    return math.log(fraction / (1.0 - fraction))


def bounded_event_laws(uscrn: dict[str, dict[str, Any]]) -> dict[str, Any]:
    laws = transformed_event_laws(uscrn)
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for payload in uscrn.values():
        by_stratum[payload["stratum"]].extend(payload["events"])
    all_events = [row for values in by_stratum.values() for row in values]
    epsilon = float(load(DESIGN)["context_laws"]["boundary_epsilon"])
    names = (
        "air_temperature_c",
        "solar_radiation_w_m2",
        "relative_humidity_pct",
        "wind_speed_1_5m_m_s",
    )
    law_names = ("Gaussian", "lognormal", "logit-normal", "lognormal")

    def statistics(events: list[dict[str, Any]], index: int) -> tuple[float, float, int]:
        values = [
            transform_context(float(row[names[index]]), index, epsilon)
            for row in events
            if row.get(names[index]) is not None
        ]
        if not values:
            raise ValueError(f"HOLD-A9D-FIT-APPLICABILITY: {names[index]}")
        return float(np.mean(values)), max(float(np.std(values)), 1.0e-4), len(values)

    global_context = [statistics(all_events, index) for index in range(4)]
    for stratum, events in by_stratum.items():
        weight = len(events) / (len(events) + 150.0)
        local_context = [statistics(events, index) for index in range(4)]
        context = []
        for index, (local, global_) in enumerate(zip(local_context, global_context)):
            context.append(
                {
                    "fit_space": (
                        "identity"
                        if index == 0
                        else "log"
                        if index in (1, 3)
                        else "logit_fraction"
                    ),
                    "law": law_names[index],
                    "mean": weight * local[0] + (1.0 - weight) * global_[0],
                    "n": local[2],
                    "sd": max(
                        weight * local[1] + (1.0 - weight) * global_[1], 1.0e-4
                    ),
                    "variable": names[index],
                }
            )
        laws[stratum]["context"] = context
        laws[stratum]["context_transform_epsilon"] = epsilon
    return laws


def inverse_logistic(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def simulate_bounded(
    fit: dict[str, Any],
    site: str,
    burn: int,
    years: int = 100,
    start_year: int = 2001,
) -> list[dict[str, Any]]:
    rows = _ORIGINAL_SIMULATE(fit, site, burn, years, start_year)
    for row in rows:
        if float(row["precip_mm"]) <= 0.0:
            continue
        row["solar_radiation_w_m2"] = math.exp(
            float(row["solar_radiation_w_m2"])
        )
        row["relative_humidity_pct"] = 100.0 * inverse_logistic(
            float(row["relative_humidity_pct"])
        )
        row["wind_speed_1_5m_m_s"] = math.exp(
            float(row["wind_speed_1_5m_m_s"])
        )
    return rows


def expected_duration(pmf: list[float]) -> float:
    return sum((index + 1) * value for index, value in enumerate(pmf))


def tilt_pmf(pmf: list[float], value: float) -> list[float]:
    support = np.arange(1, len(pmf) + 1, dtype=float)
    centered = (support - np.mean(support)) / max(float(len(pmf)), 1.0)
    weights = np.asarray(pmf, dtype=float) * np.exp(value * centered)
    weights /= weights.sum()
    return [float(item) for item in weights]


def renewal_occurrence_calibration(parameters: dict[str, Any], target: float) -> float:
    def wet_fraction(value: float) -> float:
        wet = expected_duration(tilt_pmf(parameters["wet_duration_pmf"], value))
        dry = expected_duration(tilt_pmf(parameters["dry_duration_pmf"], -value))
        return wet / (wet + dry)

    low, high = -40.0, 40.0
    if not wet_fraction(low) <= target <= wet_fraction(high):
        raise ValueError("HOLD-A9D-MONTHLY-RECONCILIATION: renewal wet fraction")
    for _ in range(80):
        middle = (low + high) / 2.0
        if wet_fraction(middle) < target:
            low = middle
        else:
            high = middle
    value = (low + high) / 2.0
    parameters["wet_duration_pmf"] = tilt_pmf(
        parameters["wet_duration_pmf"], value
    )
    parameters["dry_duration_pmf"] = tilt_pmf(
        parameters["dry_duration_pmf"], -value
    )
    wet = expected_duration(parameters["wet_duration_pmf"])
    dry = expected_duration(parameters["dry_duration_pmf"])
    return wet / (wet + dry)


def logit(value: float) -> float:
    return math.log(value / (1.0 - value))


def latent_occurrence_calibration(
    station: dict[str, Any], emissions: list[dict[str, Any]], target: float
) -> tuple[np.ndarray, float]:
    embedded = base.stationary_weights(station["transition"])
    dwell = np.asarray(
        [expected_duration(row["dwell_pmf"]) for row in emissions], dtype=float
    )
    weights = embedded * dwell
    weights /= weights.sum()
    original = np.asarray([float(row["wet_probability"]) for row in emissions])

    def wet_fraction(offset: float) -> float:
        probabilities = np.asarray(
            [inverse_logistic(logit(value) + offset) for value in original]
        )
        return float(weights @ probabilities)

    low, high = -40.0, 40.0
    for _ in range(80):
        middle = (low + high) / 2.0
        if wet_fraction(middle) < target:
            low = middle
        else:
            high = middle
    offset = (low + high) / 2.0
    for row in emissions:
        row["wet_probability"] = inverse_logistic(
            logit(float(row["wet_probability"])) + offset
        )
    return weights, wet_fraction(offset)


_MC_NORMAL = np.random.Generator(np.random.Philox(903_771)).standard_normal(8192)
_MC_GATE = np.random.Generator(np.random.Philox(903_772)).random(8192)
_MC_EXCESS = np.random.Generator(np.random.Philox(903_773)).random(8192)


@lru_cache(maxsize=None)
def amount_component_mean(
    mean: float,
    sd: float,
    tail_probability: float,
    tail_shape: float,
    tail_scale: float,
    tail_threshold: float,
) -> float:
    values = np.exp(mean + sd * _MC_NORMAL)
    selected = _MC_GATE < tail_probability
    if np.any(selected):
        u = np.maximum(1.0 - _MC_EXCESS[selected], 1.0e-12)
        excess = (
            -tail_scale * np.log(u)
            if abs(tail_shape) < 1.0e-8
            else tail_scale * (u ** (-tail_shape) - 1.0) / tail_shape
        )
        values[selected] = np.maximum(values[selected], tail_threshold + excess)
    return float(np.mean(values))


def scale_amount(parameters: dict[str, Any], variable: dict[str, Any], factor: float) -> None:
    if not math.isfinite(factor) or factor <= 0.0:
        raise ValueError("HOLD-A9D-MONTHLY-RECONCILIATION: amount scale")
    variable["mean"] = float(variable["mean"]) + math.log(factor)
    parameters["tail_scale"] = float(parameters["tail_scale"]) * factor
    parameters["tail_threshold_mm"] = (
        float(parameters["tail_threshold_mm"]) * factor
    )


def component_mean(parameters: dict[str, Any], variable: dict[str, Any]) -> float:
    return amount_component_mean(
        float(variable["mean"]),
        float(variable["sd"]),
        float(parameters["tail_probability"]),
        float(parameters["tail_shape"]),
        float(parameters["tail_scale"]),
        float(parameters["tail_threshold_mm"]),
    )


def calibrate_monthly_fit(
    detail: dict[str, Any], daymet: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    rows = []
    for site, station in detail["stations"].items():
        observed = daymet[site]["records"]
        for month in range(1, 13):
            values = [
                float(row["prcp_mm"])
                for row in observed
                if int(row["date"][5:7]) == month
            ]
            positive = [value for value in values if value > 0.0]
            target_wet = len(positive) / len(values)
            if detail["candidate_class"] == RENEWAL:
                parameters = station["months"][str(month)]
                wet_duration = expected_duration(parameters["wet_duration_pmf"])
                dry_duration = expected_duration(parameters["dry_duration_pmf"])
                realized_wet = wet_duration / (wet_duration + dry_duration)
                variable = parameters["variables"]["wet:log_amount"]
                components = [(1.0, parameters, variable)]
            else:
                emissions = station["months"][str(month)]
                embedded = base.stationary_weights(station["transition"])
                dwell = np.asarray(
                    [expected_duration(row["dwell_pmf"]) for row in emissions],
                    dtype=float,
                )
                weights = embedded * dwell
                weights /= weights.sum()
                realized_wet = float(
                    weights
                    @ np.asarray(
                        [float(row["wet_probability"]) for row in emissions]
                    )
                )
                positive_weights = np.asarray(
                    [
                        weights[index] * float(emission["wet_probability"])
                        for index, emission in enumerate(emissions)
                    ]
                )
                positive_weights /= positive_weights.sum()
                components = [
                    (float(positive_weights[index]), emission, emission["variables"]["log_amount"])
                    for index, emission in enumerate(emissions)
                ]
            if positive:
                target_amount = float(np.mean(positive))
                before = sum(
                    weight * component_mean(parameters, variable)
                    for weight, parameters, variable in components
                )
                factor = target_amount / before
                for _, parameters, variable in components:
                    scale_amount(parameters, variable, factor)
                realized_amount = sum(
                    weight * component_mean(parameters, variable)
                    for weight, parameters, variable in components
                )
                amount_error = abs(realized_amount - target_amount) / target_amount
                amount_status = "calibrated"
            else:
                target_amount = None
                realized_amount = None
                factor = 1.0
                amount_error = 0.0
                amount_status = "structural_zero_wet_target_unaltered"
            rows.append(
                {
                    "amount_mean_relative_error": amount_error,
                    "amount_scale_factor": factor,
                    "amount_status": amount_status,
                    "month": month,
                    "observed_positive_amount_mean_mm": target_amount,
                    "observed_wet_fraction": target_wet,
                    "realized_positive_amount_mean_mm": realized_amount,
                    "realized_wet_fraction": realized_wet,
                    "site": site,
                    "wet_fraction_absolute_error": abs(realized_wet - target_wet),
                }
            )
    result = {
        "maximum_amount_mean_relative_error": max(
            row["amount_mean_relative_error"] for row in rows
        ),
        "maximum_wet_fraction_absolute_error": max(
            row["wet_fraction_absolute_error"] for row in rows
        ),
        "record_count": len(rows),
        "records": rows,
        "occurrence_calibration": "none; inherited fitted occurrence retained",
        "pre_output_amendment_sha256": sha256_path(FIT_AMENDMENT),
        "rule_id": "a9d_positive_amount_mean_v1",
        "status": "pass",
    }
    if (
        result["maximum_amount_mean_relative_error"] > 5.0e-4
    ):
        result["status"] = "fail"
        raise ValueError("HOLD-A9D-MONTHLY-RECONCILIATION: calibration")
    return result


def candidate_provenance_complete(
    detail: dict[str, Any], compact: dict[str, Any]
) -> bool:
    try:
        expected_sources = {
            row["path"]: (row["logical_sha256"], row["object_sha256"])
            for row in load(A9C / "observed-source-manifest-v1.json")[
                "daymet_normalized_objects"
            ]
            + load(A9C / "observed-source-manifest-v1.json")[
                "uscrn_normalized_objects"
            ]
            if row["role"] == "coefficient_fit"
        }
        actual_sources = {
            row["path"]: (row["logical_sha256"], row["object_sha256"])
            for row in detail["sources"]
        }
        parents = compact["parent_identities"]
        return bool(
            base.detail_hash(detail) == detail["content_sha256"]
            and compact["content_sha256"] == detail["content_sha256"]
            and compact["extension_source_sha256"] == sha256_path(Path(__file__))
            and parents["calibration_sha256"] == sha256_path(CALIBRATION)
            and parents["design_freeze_sha256"] == sha256_path(DESIGN)
            and parents["fit_amendment_sha256"] == sha256_path(FIT_AMENDMENT)
            and parents["evidence_mask_sha256"] == sha256_path(MASK)
            and expected_sources == actual_sources
            and all(
                (ROOT / path).is_file()
                and sha256_path(ROOT / path) == identity[1]
                for path, identity in actual_sources.items()
            )
        )
    except (KeyError, OSError, ValueError):
        return False


def configure_base() -> None:
    base.PACKAGE = PACKAGE
    base.ARTIFACTS = ARTIFACTS
    base.DESIGN = RUNTIME_DESIGN
    base.PREDECESSOR = PREDECESSOR
    base.CALIBRATION = CALIBRATION
    base.FIT_EXECUTION = FIT_EXECUTION
    base.STRUCTURAL = STRUCTURAL
    base.BASELINE = BASELINE
    base.EVALUATION = EVALUATION
    base.FREEZE = FREEZE
    base.FIT_DETAILS = FIT_DETAILS
    base.FIT_RECORDS = FIT_RECORDS
    base.SOURCE_COMMIT = SOURCE_COMMIT
    base.simulate = simulate_bounded
    base.aggregate_stage = aggregate_stage_masked
    base.candidate_provenance_complete = candidate_provenance_complete


def fit() -> None:
    configure_base()
    verify_predecessors()
    if not all(path.is_file() for path in (CALIBRATION, RUNTIME_DESIGN, CROSSWALK)):
        raise ValueError("HOLD-A9D-PREDECESSOR-INTEGRITY: preparation")
    if any(path.exists() for path in (FIT_EXECUTION, STRUCTURAL, EVALUATION, FREEZE)):
        raise FileExistsError("A9d fit/evaluation evidence exists")
    daymet = load_daymet("coefficient_fit")
    event_laws = bounded_event_laws(load_uscrn("coefficient_fit"))
    details = []
    records = []
    started = time.monotonic()
    for config in load(DESIGN)["development"]["configuration_grid"]:
        before = time.monotonic()
        if config["candidate_class"] == RENEWAL:
            detail = fit_renewal(config, daymet, event_laws)
        elif config["candidate_class"] == LATENT:
            detail = fit_latent(config, daymet, event_laws)
        else:
            raise ValueError(config["candidate_class"])
        detail["fit_id"] = f"a9d-{config['configuration_id']}"
        detail["campaign_id"] = load(DESIGN)["campaign_id"]
        detail["monthly_calibration"] = calibrate_monthly_fit(detail, daymet)
        detail["content_sha256"] = base.detail_hash(detail)
        monthly = base.reconcile_fit_monthlies(detail)
        if monthly["status"] != "pass":
            raise RuntimeError("HOLD-A9D-MONTHLY-RECONCILIATION")
        detail_path = FIT_DETAILS / f"{config['configuration_id']}.json"
        write_once(detail_path, detail)
        deterministic = base.deterministic_fit_identities(detail, config)
        compact = {
            "candidate_class": detail["candidate_class"],
            "configuration": config,
            "content_sha256": detail["content_sha256"],
            "detail_path": str(detail_path.relative_to(ROOT)),
            "detail_sha256": sha256_path(detail_path),
            "effective_parameter_count": detail["effective_parameter_count"],
            "extension_source_sha256": sha256_path(Path(__file__)),
            "fit_id": detail["fit_id"],
            "fit_status": detail["fit_status"],
            "ineligible_stations": detail["ineligible_stations"],
            "model_source_sha256": sha256_path(ROOT / "research/a9c/models.py"),
            "monthly_calibration": {
                key: value
                for key, value in detail["monthly_calibration"].items()
                if key != "records"
            },
            "monthly_reconciliation": monthly,
            "parent_identities": {
                "calibration_sha256": sha256_path(CALIBRATION),
                "design_freeze_sha256": sha256_path(DESIGN),
                "evidence_mask_sha256": sha256_path(MASK),
                "fit_amendment_sha256": sha256_path(FIT_AMENDMENT),
                "objective_registry_sha256": sha256_path(OBJECTIVES),
                "source_inventory_sha256": sha256_bytes(
                    canonical_bytes(detail["sources"])
                ),
            },
            "rng": {
                **deterministic,
                "monthly_reconciliation": f"NumPy Philox a9c3-monthly-reconciliation-v1/{detail['fit_id']}/target|heldout",
                "simulation": f"A9 Philox4x32-10 random-field campaign a9c/{detail['fit_id']}",
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
    base.close_fit_evidence(details, records, started, "a9d_single_process")


def retained_surface() -> tuple[set[tuple[str, str]], set[tuple[str, str, str]]]:
    cells = load(MASK)["retained_cells"]
    families = {(row["family"], row["stratum"]) for row in cells}
    objectives = {
        (row["objective_id"], row["family"], row["stratum"]) for row in cells
    }
    return families, objectives


def aggregate_stage_masked(*args: Any, **kwargs: Any) -> dict[str, Any]:
    raw = _ORIGINAL_AGGREGATE(*args, **kwargs)
    family_surface, objective_surface = retained_surface()
    family_rows = [
        row
        for row in raw["family_rows"]
        if (row["family"], row["stratum"]) in family_surface
    ]
    selected_objectives = []
    report_only = []
    registry = {
        row["id"]: row for row in load(OBJECTIVES)["objectives"]
    }
    for row in raw["objective_rows"]:
        role = row["selection_role"]
        if role == "hard_invariant":
            selected_objectives.append(row)
            continue
        definition = registry[row["objective_id"]]
        key = (row["objective_id"], definition["family"], row["stratum"])
        if role == "mandatory" and key in objective_surface:
            selected_objectives.append(row)
        else:
            report_only.append(
                {
                    **row,
                    "original_selection_role": role,
                    "selection_role": "report_only_not_evaluated",
                }
            )
    degradations = [row for row in family_rows if row["material_degradation"]]
    degraded_families = {row["family"] for row in degradations}
    improvement_horizons: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in family_rows:
        if row["material_improvement"]:
            improvement_horizons[(row["family"], row["stratum"])].add(
                int(row["horizon_years"])
            )
    improved = {
        family
        for (family, _), horizons in improvement_horizons.items()
        if {30, 100} <= horizons and family not in degraded_families
    }
    mandatory_unavailable = [
        row
        for row in selected_objectives
        if row["selection_role"] == "mandatory" and row["status"] != "available"
    ]
    hard_failures = [
        row
        for row in selected_objectives
        if row["selection_role"] == "hard_invariant"
        and row["status"] != "available"
    ]
    candidate_distances = [float(row["candidate_distance"]) for row in family_rows]
    baseline_distances = [float(row["baseline_distance"]) for row in family_rows]
    standardized = [
        (float(row["baseline_distance"]) - float(row["candidate_distance"]))
        / float(row["threshold"])
        for row in family_rows
    ]
    raw["family_rows"] = family_rows
    raw["objective_rows"] = selected_objectives
    raw["report_only_objective_rows"] = report_only
    raw["summary"] = {
        "complete": bool(
            family_rows
            and all(
                math.isfinite(float(row[key]))
                for row in family_rows
                for key in ("baseline_distance", "candidate_distance", "threshold")
            )
            and not mandatory_unavailable
            and not hard_failures
        ),
        "degradation_count": len(degradations),
        "effective_baseline_distance_median": float(np.median(baseline_distances)),
        "hard_failure_count": len(hard_failures),
        "improved_family_count": len(improved),
        "mandatory_unavailable_count": len(mandatory_unavailable),
        "median_normalized_distance": float(np.median(candidate_distances)),
        "worst_standardized_improvement": float(min(standardized)),
    }
    return raw


def support_audit(detail: dict[str, Any]) -> dict[str, Any]:
    violations = []
    streams = 0
    for site in sorted(detail["stations"]):
        for burn in load(DESIGN)["burns"]["development"][:2]:
            rows = simulate_bounded(detail, site, burn, years=30)
            streams += 1
            for index, row in enumerate(rows):
                if float(row["precip_mm"]) <= 0.0:
                    continue
                if not float(row["solar_radiation_w_m2"]) > 0.0:
                    violations.append(f"solar:{site}:{burn}:{index}")
                if not float(row["wind_speed_1_5m_m_s"]) > 0.0:
                    violations.append(f"wind:{site}:{burn}:{index}")
                if not 0.0 < float(row["relative_humidity_pct"]) < 100.0:
                    violations.append(f"humidity:{site}:{burn}:{index}")
    return {
        "checked_streams": streams,
        "realized_output_clipping_or_repair": False,
        "status": "pass" if not violations else "fail",
        "violation_count": len(violations),
        "violations": violations[:100],
    }


def evaluate() -> None:
    configure_base()
    verify_predecessors()
    base.evaluate()
    evaluation = load(EVALUATION)
    if evaluation["terminal"] == "HOLD-A9C3-NO-SELECTABLE-CANDIDATE":
        evaluation["terminal"] = "HOLD-A9D-NO-SELECTABLE-CANDIDATE"
    evaluation["a9d_design_freeze_sha256"] = sha256_path(DESIGN)
    evaluation["evidence_mask_sha256"] = sha256_path(MASK)
    evaluation["accepted_retained_cells_per_horizon"] = 92
    evaluation["report_only_cells_per_horizon"] = 19
    fits = load(FIT_EXECUTION)
    audits = {}
    for row in fits["fits"]:
        if row["fit_status"] == "fit_valid":
            detail = load(ROOT / row["detail_path"])
            audits[row["configuration_id"]] = support_audit(detail)
    support = {
        "configurations": audits,
        "status": (
            "pass"
            if audits and all(row["status"] == "pass" for row in audits.values())
            else "fail"
        ),
        "total_violation_count": sum(
            row["violation_count"] for row in audits.values()
        ),
    }
    evaluation["context_support_audit"] = support
    if support["status"] != "pass":
        evaluation["selected_candidate_class"] = None
        evaluation["selected_configuration_id"] = None
        evaluation["terminal"] = "HOLD-A9D-CONTEXT-SUPPORT"
        FREEZE.unlink(missing_ok=True)
    replace_json(EVALUATION, evaluation)

    if FREEZE.exists():
        freeze = load(FREEZE)
        freeze.update(
            {
                "a9d_design_freeze_sha256": sha256_path(DESIGN),
                "calibration_sha256": sha256_path(CALIBRATION),
                "confirmation_access_authorized": True,
                "confirmation_burns": load(DESIGN)["burns"]["confirmation"],
                "evidence_mask_sha256": sha256_path(MASK),
                "evaluation_sha256": sha256_path(EVALUATION),
                "objective_registry_sha256": sha256_path(OBJECTIVES),
                "status": "development_candidate_sealed_for_same_package_confirmation",
            }
        )
        freeze["content_sha256"] = sha256_bytes(
            canonical_bytes({key: value for key, value in freeze.items() if key != "content_sha256"})
        )
        replace_json(FREEZE, freeze)
    result = {
        "candidate_freeze_count": int(FREEZE.exists()),
        "confirmation_series_accessed": False,
        "context_support_status": support["status"],
        "evaluation_sha256": sha256_path(EVALUATION),
        "report_only_cells_per_horizon": 19,
        "retained_cells_per_horizon": 92,
        "selected_candidate_class": evaluation["selected_candidate_class"],
        "selected_configuration_id": evaluation["selected_configuration_id"],
        "terminal": evaluation["terminal"],
    }
    write_once(DEVELOPMENT_RESULT, result)
    print(
        f"A9d development terminal={result['terminal']}; "
        f"selected={result['selected_configuration_id']}; support={support['status']}"
    )


def verify_development() -> None:
    configure_base()
    verify_predecessors()
    for path in (
        CALIBRATION,
        RUNTIME_DESIGN,
        CROSSWALK,
        PARAMETERS,
        FIT_EXECUTION,
        STRUCTURAL,
        BASELINE,
        EVALUATION,
        DEVELOPMENT_RESULT,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if sha256_path(MASK) != load(RUNTIME_DESIGN)["evidence_mask_sha256"]:
        raise ValueError("mask identity")
    fit_execution = load(FIT_EXECUTION)
    if fit_execution["configuration_count"] != 18:
        raise ValueError("fit count")
    if any(value < 1 for value in fit_execution["valid_fit_count_by_class"].values()):
        raise ValueError("fit class availability")
    for row in fit_execution["fits"]:
        if sha256_path(ROOT / row["path"]) != row["sha256"]:
            raise ValueError(f"compact fit identity: {row['configuration_id']}")
        if sha256_path(ROOT / row["detail_path"]) != row["detail_sha256"]:
            raise ValueError(f"detail fit identity: {row['configuration_id']}")
    evaluation = load(EVALUATION)
    for stage in evaluation["stages"]:
        for row in stage["results"]:
            if any(
                item["selection_role"] == "mandatory"
                and (
                    item["objective_id"],
                    load(OBJECTIVES)["objectives"][
                        next(
                            index
                            for index, value in enumerate(load(OBJECTIVES)["objectives"])
                            if value["id"] == item["objective_id"]
                        )
                    ]["family"],
                    item["stratum"],
                )
                not in retained_surface()[1]
                for item in row["objective_rows"]
            ):
                raise ValueError("selection surface leak")
            if any(
                item["selection_role"] != "report_only_not_evaluated"
                for item in row["report_only_objective_rows"]
            ):
                raise ValueError("report-only role")
    if evaluation["context_support_audit"]["total_violation_count"] != 0:
        raise ValueError("context support")
    result = load(DEVELOPMENT_RESULT)
    if result["candidate_freeze_count"] != int(FREEZE.exists()):
        raise ValueError("freeze count")
    if FREEZE.exists():
        freeze = load(FREEZE)
        expected = sha256_bytes(
            canonical_bytes({key: value for key, value in freeze.items() if key != "content_sha256"})
        )
        if freeze["content_sha256"] != expected:
            raise ValueError("candidate freeze content")
        if result["terminal"] != "CANDIDATE-FROZEN-READY-A9D":
            raise ValueError("candidate terminal")
    elif result["terminal"] != "HOLD-A9D-NO-SELECTABLE-CANDIDATE":
        raise ValueError("development hold terminal")
    print(
        f"PASS: 18 fits; {sum(stage['configuration_count'] for stage in evaluation['stages'])} staged evaluations; "
        f"92 retained/19 report-only cells per horizon; terminal={result['terminal']}"
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("prepare", "fit", "evaluate", "verify-development")
    )
    args = parser.parse_args(argv)
    if args.command == "prepare":
        prepare()
    elif args.command == "fit":
        fit()
    elif args.command == "evaluate":
        evaluate()
    else:
        verify_development()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
