#!/usr/bin/env python3
"""Apply the frozen A5e0 H1-H3 arithmetic to the completed matrix."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable, Sequence

import numpy as np


STATIONS = ("ca042319", "co051660", "ms227840")
REGIMES = {"ca042319": "dry", "co051660": "cold", "ms227840": "wet"}
ARMS = ("research_baseline", "candidate")
HORIZONS = (30, 100)
REPLICATES = tuple(range(1, 9))
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_json(path: Path) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate key {key} in {path}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"nonfinite token {token} in {path}")
        ),
    )


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def conventional_median(values: Sequence[float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise RuntimeError("median input is empty")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def arithmetic_mean(values: Sequence[float]) -> float:
    if not values or any(not math.isfinite(value) for value in values):
        raise RuntimeError("required metric cell is missing or nonfinite")
    return math.fsum(values) / len(values)


def ratio(candidate: float, baseline: float) -> tuple[float | None, str]:
    if baseline == 0.0:
        return (1.0, "BOTH_ZERO") if candidate == 0.0 else (None, "UNBOUNDED")
    return candidate / baseline, "FINITE"


def get_path(root: Any, dotted: str) -> Any:
    value = root
    for part in dotted.split("."):
        value = value[part]
    return value


@dataclass
class LoadedReport:
    raw: dict[str, Any]
    vector: Any


def verify_artifact(root: Path, identity: dict[str, Any]) -> Path:
    path = root / identity["path"]
    if not path.is_file() or path.stat().st_size != identity["bytes"] or sha256(path) != identity["sha256"]:
        raise RuntimeError(f"artifact identity mismatch: {identity['path']}")
    return path


def load_reports(root: Path, matrix: dict[str, Any], helper: Any, bindings: list[Any]) -> dict[tuple[str, str, int, int], LoadedReport]:
    reports = {}
    for run in matrix["runs"]:
        station = run["station_id"]
        arm = run["arm"]
        replicate = run["replicate"]
        for horizon in HORIZONS:
            path = verify_artifact(root, run["products"][str(horizon)]["quality"])
            raw = strict_json(path)
            vector = helper.compress_report(raw, bindings)
            reports[(station, arm, replicate, horizon)] = LoadedReport(raw, vector)
    if len(reports) != 96:
        raise RuntimeError(f"loaded {len(reports)} reports, expected 96")
    return reports


def observed_target(helper: Any, corpus: dict[str, Any], binding: Any, station: str) -> tuple[float, Any]:
    target, count = helper.observed_cell(corpus, binding, station)
    numeric = helper.finite_number(target)
    if numeric is helper.MISSING or not helper.sufficient_count(binding, count):
        raise RuntimeError(f"required observed target is unavailable: {station}/{binding.cell_key}")
    return float(numeric), count


def cell_distance(helper: Any, corpus: dict[str, Any], binding: Any, station: str, report: LoadedReport) -> float:
    index = binding.report_index
    generated = float(report.vector.values[index])
    if not math.isfinite(generated) or not helper.sufficient_count(binding, report.vector.counts[index]):
        raise RuntimeError(f"generated cell is unavailable: {station}/{binding.cell_key}")
    if binding.surface_id == "report_embedded_station_parameter":
        target = float(report.vector.targets[index])
        count = report.vector.target_counts[index]
        if not math.isfinite(target) or not helper.sufficient_count(binding, count):
            raise RuntimeError(f"station target is unavailable: {station}/{binding.cell_key}")
        scale = float(report.vector.scales[index]) if binding.target_scale_path is not None else None
    else:
        target, _ = observed_target(helper, corpus, binding, station)
        scale = None
    return helper.distance_value(generated, target, binding, scale)


def distance_family(
    helper: Any,
    corpus: dict[str, Any],
    reports: dict[tuple[str, str, int, int], LoadedReport],
    bindings: Sequence[Any],
    station: str,
    arm: str,
    horizon: int,
) -> list[float]:
    if not bindings:
        raise RuntimeError("frozen metric family is empty")
    baseline_rows = [
        reports[(station, "research_baseline", replicate, horizon)].vector
        for replicate in REPLICATES
    ]
    eligible = [
        binding
        for binding in bindings
        if helper.baseline_eligible(corpus, binding, station, baseline_rows)
    ]
    if not eligible:
        raise RuntimeError(f"frozen metric family has no eligible cells: {station}/{horizon}")
    selected = [reports[(station, arm, replicate, horizon)].vector for replicate in REPLICATES]
    missing = [
        binding.cell_key
        for binding in eligible
        if not helper.candidate_defines(selected, binding)
    ]
    if missing:
        raise RuntimeError(
            f"required eligible cells are missing: {station}/{arm}/{horizon}/{len(missing)}"
        )
    return [
        arithmetic_mean(
            [
                cell_distance(helper, corpus, binding, station, reports[(station, arm, replicate, horizon)])
                for binding in eligible
            ]
        )
        for replicate in REPLICATES
    ]


def station_ratios(
    helper: Any,
    corpus: dict[str, Any],
    reports: dict[tuple[str, str, int, int], LoadedReport],
    family_bindings: dict[str, list[Any]],
    horizon: int,
    stations: Sequence[str] = STATIONS,
) -> list[dict[str, Any]]:
    rows = []
    for station in stations:
        arm_family = {}
        for arm in ARMS:
            arm_family[arm] = {
                family: {
                    "replicates": values,
                    "median": conventional_median(values),
                }
                for family, bindings in family_bindings.items()
                for values in [distance_family(helper, corpus, reports, bindings, station, arm, horizon)]
            }
        baseline_composite = arithmetic_mean([arm_family["research_baseline"][family]["median"] for family in family_bindings])
        candidate_composite = arithmetic_mean([arm_family["candidate"][family]["median"] for family in family_bindings])
        value, condition = ratio(candidate_composite, baseline_composite)
        rows.append(
            {
                "station_id": station,
                "regime": REGIMES[station],
                "baseline_composite": baseline_composite,
                "candidate_composite": candidate_composite,
                "ratio": value,
                "ratio_condition": condition,
                "families": arm_family,
            }
        )
    return rows


def summarize_ratio_gate(rows: list[dict[str, Any]], median_limit: float, station_limit: float) -> dict[str, Any]:
    if any(row["ratio"] is None for row in rows):
        median = None
        passed = False
    else:
        values = [float(row["ratio"]) for row in rows]
        median = conventional_median(values)
        passed = median <= median_limit and max(values) <= station_limit
    return {
        "status": "PASS" if passed else "FAIL",
        "three_station_median_ratio": median,
        "median_limit": median_limit,
        "station_limit": station_limit,
        "stations": rows,
    }


def h1_membership(bindings: list[Any]) -> dict[str, list[Any]]:
    result = {
        "annual_dispersion": [],
        "monthly_dispersion": [],
        "cross_month_dependence": [],
        "cross_variable_dependence": [],
    }
    for binding in bindings:
        if binding.gate_id != 1:
            continue
        if binding.template_id == "b_annual_nonnegative_dispersion" and binding.statistic in ("sd", "cv"):
            result["annual_dispersion"].append(binding)
        elif binding.template_id == "b_annual_temperature_dispersion" and binding.statistic == "sd":
            result["annual_dispersion"].append(binding)
        elif binding.template_id == "b_monthly_nonnegative_dispersion" and binding.statistic in ("sd", "cv"):
            result["monthly_dispersion"].append(binding)
        elif binding.template_id == "b_monthly_temperature_dispersion" and binding.statistic == "sd":
            result["monthly_dispersion"].append(binding)
        elif binding.template_id == "b_cross_month_dependence":
            result["cross_month_dependence"].append(binding)
        elif binding.template_id == "b_cross_variable_dependence":
            result["cross_variable_dependence"].append(binding)
    return result


def h2_memberships(bindings: list[Any]) -> dict[str, list[Any]]:
    return {
        "monthly_station_contract": [binding for binding in bindings if binding.gate_id == 3],
        "interannual_mean_contract": [
            binding
            for binding in bindings
            if binding.gate_id == 1
            and binding.template_id in ("b_annual_nonnegative_dispersion", "b_monthly_nonnegative_dispersion")
            and binding.statistic == "mean"
        ],
        "precipitation_structure": [binding for binding in bindings if binding.gate_id == 4],
        "winter_air_temperature_proxies": [binding for binding in bindings if binding.gate_id == 6],
    }


def daily_thermodynamic_target(corpus: dict[str, Any], station: str) -> float:
    source = next(row for row in corpus["stations"] if row["station_id"] == station)
    monthly = source["sources"]["daymet"]["periods"]["evaluation"]["monthly"]
    values = [
        days * (monthly[month]["tmax_mean_c"]["mean"] - monthly[month]["tmin_mean_c"]["mean"])
        for month, days in zip(MONTHS, MONTH_LENGTHS)
    ]
    return math.fsum(values) / 365.0


def daily_thermodynamic_error(report: dict[str, Any], range_target: float) -> float:
    generated_range = report["covariation"]["daily_range_mean_c"]["whole_run"]
    dew = report["par_convergence"]["dewpoint_mean_c"]
    counts = [dew[month]["n"] for month in MONTHS]
    generated_dew = math.fsum(dew[month]["generated"] * count for month, count in zip(MONTHS, counts)) / sum(counts)
    target_dew = math.fsum(dew[month]["target"] * count for month, count in zip(MONTHS, counts)) / sum(counts)
    return (abs(generated_range - range_target) + abs(generated_dew - target_dew)) / 2.0


def custom_error_ratios(
    reports: dict[tuple[str, str, int, int], LoadedReport],
    corpus: dict[str, Any],
    horizon: int,
    stations: Sequence[str],
    error: Callable[[dict[str, Any], str], float],
) -> list[dict[str, Any]]:
    rows = []
    for station in stations:
        values = {}
        for arm in ARMS:
            replicate_values = [error(reports[(station, arm, replicate, horizon)].raw, station) for replicate in REPLICATES]
            values[arm] = {"replicates": replicate_values, "median": conventional_median(replicate_values)}
        value, condition = ratio(values["candidate"]["median"], values["research_baseline"]["median"])
        rows.append({"station_id": station, "regime": REGIMES[station], "ratio": value, "ratio_condition": condition, "arms": values})
    return rows


def h3_descriptor_rows(reports: dict[tuple[str, str, int, int], LoadedReport], horizon: int) -> list[dict[str, Any]]:
    rows = []
    for station in STATIONS:
        replicate_scores = []
        subfamilies = []
        for replicate in REPLICATES:
            baseline = reports[(station, "research_baseline", replicate, horizon)].raw["tails"]["storm_descriptors"]
            candidate = reports[(station, "candidate", replicate, horizon)].raw["tails"]["storm_descriptors"]
            statistics = ("mean", "sd", "p50", "p90", "p95", "p99", "max")
            time_values = [
                abs(candidate["distributions"]["time_to_peak_fraction"][stat] - baseline["distributions"]["time_to_peak_fraction"][stat])
                for stat in statistics
            ]
            peak_values = []
            for stat in statistics:
                left = candidate["distributions"]["peak_intensity_ratio"][stat]
                right = baseline["distributions"]["peak_intensity_ratio"][stat]
                denominator = max(abs(left), abs(right))
                peak_values.append(0.0 if denominator == 0.0 else abs(left - right) / denominator)
            correlation_values = []
            for pair in ("depth_time_to_peak", "depth_peak_intensity_ratio", "duration_time_to_peak", "duration_peak_intensity_ratio", "time_to_peak_peak_intensity_ratio"):
                for statistic in ("pearson", "spearman"):
                    correlation_values.append(abs(candidate["dependence"][pair][statistic] - baseline["dependence"][pair][statistic]) / 2.0)
            three = {
                "time_to_peak": arithmetic_mean(time_values),
                "peak_intensity_ratio": arithmetic_mean(peak_values),
                "dependence": arithmetic_mean(correlation_values),
            }
            subfamilies.append(three)
            replicate_scores.append(arithmetic_mean(list(three.values())))
        rows.append(
            {
                "station_id": station,
                "regime": REGIMES[station],
                "replicates": replicate_scores,
                "replicate_subfamilies": subfamilies,
                "median": conventional_median(replicate_scores),
            }
        )
    return rows


def evaluate_horizon(helper: Any, corpus: dict[str, Any], reports: dict[tuple[str, str, int, int], LoadedReport], bindings: list[Any], horizon: int) -> dict[str, Any]:
    h1 = summarize_ratio_gate(
        station_ratios(helper, corpus, reports, h1_membership(bindings), horizon),
        0.90,
        1.25,
    )
    memberships = h2_memberships(bindings)
    h2_families = {}
    for family in ("monthly_station_contract", "interannual_mean_contract", "precipitation_structure"):
        h2_families[family] = summarize_ratio_gate(
            station_ratios(helper, corpus, reports, {family: memberships[family]}, horizon),
            1.10,
            1.25,
        )
    thermodynamic = custom_error_ratios(
        reports,
        corpus,
        horizon,
        STATIONS,
        lambda report, station: daily_thermodynamic_error(report, daily_thermodynamic_target(corpus, station)),
    )
    h2_families["daily_thermodynamic_contract"] = summarize_ratio_gate(thermodynamic, 1.25, 1.50)
    winter_rows = station_ratios(
        helper,
        corpus,
        reports,
        {"winter_air_temperature_proxies": memberships["winter_air_temperature_proxies"]},
        horizon,
        ("co051660",),
    )
    winter = winter_rows[0]
    h2_families["cold_winter"] = {
        "status": "PASS" if winter["ratio"] is not None and winter["ratio"] <= 1.25 else "FAIL",
        "limit": 1.25,
        "station": winter,
    }
    h2_status = "PASS" if all(value["status"] == "PASS" for value in h2_families.values()) else "FAIL"

    dependence_membership = {
        "annual_dependence": [binding for binding in bindings if binding.gate_id == 1 and binding.template_id == "b_annual_lag_one_dependence"],
        "low_frequency": [binding for binding in bindings if binding.gate_id == 1 and binding.template_id == "b_annual_low_frequency_fraction"],
    }
    h3_families = {
        family: summarize_ratio_gate(
            station_ratios(helper, corpus, reports, {family: membership}, horizon),
            2.0,
            3.0,
        )
        for family, membership in dependence_membership.items()
    }
    descriptor_rows = h3_descriptor_rows(reports, horizon)
    descriptor_median = conventional_median([row["median"] for row in descriptor_rows])
    descriptor_pass = descriptor_median <= 0.50 and max(row["median"] for row in descriptor_rows) <= 0.75
    h3_families["descriptor_guard"] = {
        "status": "PASS" if descriptor_pass else "FAIL",
        "three_station_median": descriptor_median,
        "median_limit": 0.50,
        "station_limit": 0.75,
        "stations": descriptor_rows,
    }
    h3_status = "PASS" if all(value["status"] == "PASS" for value in h3_families.values()) else "FAIL"
    return {
        "horizon_years": horizon,
        "h1": h1,
        "h2": {"status": h2_status, "families": h2_families},
        "h3": {"status": h3_status, "families": h3_families},
    }


def main() -> int:
    root = repo_root()
    package = root / "docs/work-packages/20260714-a5e0-direct-annual-state-pilot"
    matrix_path = root / "target/a5e0/matrix-index-v1.json"
    corpus_path = root / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/observed-target-corpus-v1.json"
    helper_path = root / "docs/work-packages/20260713-a5b-interannual-candidate-spike/artifacts/climate/analyze-a5b-v3.py"
    matrix = strict_json(matrix_path)
    corpus = strict_json(corpus_path)
    helper = load_module("a5b_analysis_helper_for_a5e0", helper_path)
    metric_helper, _bootstrap, _corpus, _target = helper.load_helpers()
    _manifest, bindings = helper.expand_bindings(metric_helper)
    reports = load_reports(root, matrix, helper, bindings)
    horizons = [evaluate_horizon(helper, corpus, reports, bindings, horizon) for horizon in HORIZONS]
    climate_pass = all(
        horizon[hypothesis]["status"] == "PASS"
        for horizon in horizons
        for hypothesis in ("h1", "h2", "h3")
    )
    result = {
        "analysis_schema": "a5e0_analysis_v1",
        "status": "complete",
        "identity": {
            "research_profile": "a5e0_direct_annual_state_v1",
            "matrix_index_sha256": sha256(matrix_path),
            "observed_target_sha256": sha256(corpus_path),
            "metric_manifest_sha256": sha256(root / "docs/specifications/a5-climate-gate-metrics-v1.json"),
            "metric_helper_sha256": sha256(helper_path),
            "analyzer_sha256": sha256(Path(__file__)),
        },
        "membership": {
            "h1": {family: len(rows) for family, rows in h1_membership(bindings).items()},
            "h2": {family: len(rows) for family, rows in h2_memberships(bindings).items()},
            "h3": {
                "annual_dependence": len([row for row in bindings if row.gate_id == 1 and row.template_id == "b_annual_lag_one_dependence"]),
                "low_frequency": len([row for row in bindings if row.gate_id == 1 and row.template_id == "b_annual_low_frequency_fraction"]),
                "descriptor_subfamilies": 3,
            },
        },
        "horizons": horizons,
        "climate_hypotheses_status": "PASS" if climate_pass else "FAIL",
        "climate_decision": "CONTINUE-A5E1" if climate_pass else "CLOSE-MECHANISM",
    }
    output = package / "artifacts/a5e0-analysis-v1.json"
    write_json(output, result)
    print(json.dumps({"status": result["climate_hypotheses_status"], "decision": result["climate_decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
