#!/usr/bin/env python3
"""Analyze the frozen A8c routed-daily pilot without modifying output."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
CONTRACT_PATH = ARTIFACTS / "pilot-contract-v1.json"
EXECUTION_FREEZE_PATH = ARTIFACTS / "pre-execution-freeze-v1.json"
FREEZE_PATH = ARTIFACTS / "pre-analysis-freeze-v2.json"
EXECUTION_PATH = ARTIFACTS / "execution-evidence-v1.json"
ANALYSIS_PATH = ARTIFACTS / "a8c-analysis-v1.json"
DECISION_PATH = ARTIFACTS / "a8c-decision-v1.json"
FINDINGS_PATH = ARTIFACTS / "findings.md"
FAMILIES = ("spell_structure", "higher_order_occurrence")
EPSILON = 1.0e-12
CLOSURE_OWNED = {
    "crates/cligen/src/runspec.rs",
    "crates/cligen/tests/a8c_routed_daily.rs",
    "docs/specifications/SPEC-A8C-ROUTED-DAILY.md",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/package.md",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/analyze-a8c.py",
    "docs/work-packages/20260715-a8c-routed-daily-pilot/artifacts/verify-a8c.py",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def median(values: Iterable[float]) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    center = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[center]
    return (ordered[center - 1] + ordered[center]) / 2.0


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def sample_variance(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    center = mean(values)
    assert center is not None
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def relative_error(actual: float | None, expected: float) -> float | None:
    if actual is None or expected <= 0.0:
        return None
    return abs(actual - expected) / expected


def legacy_target_dimensionless_variance(cell: dict[str, Any]) -> float:
    legacy = cell["legacy"]
    days = int(cell["days"])
    pww = float(legacy["pww"])
    pwd = float(legacy["pwd"])
    wet_fraction = pwd / (1.0 - pww + pwd)
    correlation = pww - pwd
    wet_count_variance = days * wet_fraction * (1.0 - wet_fraction)
    wet_count_variance += 2.0 * wet_fraction * (1.0 - wet_fraction) * sum(
        (days - lag) * correlation**lag for lag in range(1, days)
    )
    wet_mean = float(legacy["wet_mean_mm"])
    wet_sd = float(legacy["wet_sd_mm"])
    reconstructed = wet_count_variance + days * wet_fraction * (wet_sd / wet_mean) ** 2
    reported = cell.get("budget", {}).get("legacy_target_dimensionless_variance")
    if reported is not None:
        if not math.isclose(
            reconstructed, float(reported), rel_tol=1.0e-12, abs_tol=1.0e-12
        ):
            raise ValueError("reported and reconstructed legacy variance targets differ")
        return float(reported)
    return reconstructed


def full_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 13:
            continue
        try:
            day, month, year = map(int, fields[:3])
            values = [float(token) for token in fields[3:]]
        except ValueError:
            continue
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"non-finite climate row: {path}")
        rows.append(
            {
                "date": (year, month, day),
                "precipitation": values[0],
                "duration": values[1],
                "time_to_peak": values[2],
                "normalized_peak": values[3],
                "tmax": values[4],
                "tmin": values[5],
                "radiation": values[6],
                "wind_speed": values[7],
                "wind_direction": values[8],
                "dew_point": values[9],
            }
        )
    if not rows:
        raise ValueError(f"no rows: {path}")
    return rows


def check_frozen_inputs(contract: dict[str, Any]) -> dict[str, str]:
    freeze = load_json(FREEZE_PATH)
    if freeze["status"] != "FROZEN-POST-GENERATION-BEFORE-OUTCOME":
        raise ValueError("inactive A8c freeze")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if relative in CLOSURE_OWNED:
            continue
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"frozen file changed: {relative}")
    checked = {}
    for name, entry in contract["inputs"].items():
        actual = sha256(ROOT / entry["path"])
        if actual != entry["sha256"]:
            raise ValueError(f"input changed: {name}")
        checked[name] = actual
    return checked


def load_streams(execution: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    result = {}
    for cell in execution["cells"]:
        candidate_path = ROOT / cell["candidate"]["cli_path"]
        faithful_path = ROOT / cell["faithful"]["cli_path"]
        if sha256(candidate_path) != cell["candidate"]["cli_sha256"]:
            raise ValueError(f"candidate stream changed: {candidate_path}")
        if sha256(faithful_path) != cell["faithful"]["cli_sha256"]:
            raise ValueError(f"faithful stream changed: {faithful_path}")
        result[(cell["station_id"], cell["burn"])] = {
            "candidate": full_rows(candidate_path),
            "faithful": full_rows(faithful_path),
            "evidence": cell,
        }
    return result


def observed_metrics(
    contract: dict[str, Any], a7a: Any, a7a_contract: dict[str, Any]
) -> dict[str, dict[str, dict[str, float]]]:
    corpus_path = ROOT / contract["inputs"]["corpus_common"]["path"]
    corpus = load_module(corpus_path, "a8c_corpus_common")
    panel = load_json(ROOT / contract["inputs"]["a8a_panel"]["path"])
    manifest = load_json(ROOT / contract["inputs"]["a8a_source_manifest"]["path"])
    panel_by_id = {row["station_id"]: row for row in panel["stations"]}
    source_by_id = {row["station_id"]: row["sources"]["daymet"] for row in manifest["stations"]}
    start, end = contract["execution"]["observed_period"]
    result = {}
    for station in contract["stations"]:
        station_id = station["station_id"]
        metadata = source_by_id[station_id]
        path = ROOT / metadata["archive_path"]
        records, checked = corpus.archive_records(path, "daymet", panel_by_id[station_id])
        for field in ("archive_sha256", "source_sha256", "calendar"):
            if checked[field] != metadata[field]:
                raise ValueError(f"{station_id}: observed {field} mismatch")
        rows = [
            (date, values["prcp"])
            for date, values in sorted(records.items())
            if start <= date[0] <= end and "prcp" in values
        ]
        metrics, _ = a7a.metric_bundle(rows, metadata["calendar"], a7a_contract)
        result[station_id] = metrics
    return result


def daily_evaluation(
    contract: dict[str, Any],
    streams: dict[tuple[str, int], dict[str, Any]],
    observed: dict[str, dict[str, dict[str, float]]],
    a7a: Any,
    a7a_contract: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    distances = []
    summaries = []
    burns = contract["execution"]["burns"]
    for station in contract["stations"]:
        station_id = station["station_id"]
        for horizon in contract["execution"]["horizons_years"]:
            by_family: dict[str, dict[str, list[float]]] = {
                family: {"candidate": [], "faithful": []} for family in FAMILIES
            }
            for burn in burns:
                for variant in ("candidate", "faithful"):
                    rows = streams[(station_id, burn)][variant]
                    precipitation = [
                        (row["date"], row["precipitation"])
                        for row in rows
                        if row["date"][0] <= horizon
                    ]
                    metrics, _ = a7a.metric_bundle(
                        precipitation, "proleptic_gregorian", a7a_contract
                    )
                    for family in FAMILIES:
                        distance, count, _ = a7a.family_distance(
                            metrics[family], observed[station_id][family], family, a7a_contract
                        )
                        distances.append(
                            {
                                "burn": burn,
                                "common_components": count,
                                "distance": distance,
                                "family": family,
                                "horizon_years": horizon,
                                "station_id": station_id,
                                "variant": variant,
                            }
                        )
                        if distance is not None:
                            by_family[family][variant].append(distance)
            for family in FAMILIES:
                candidate = median(by_family[family]["candidate"])
                faithful = median(by_family[family]["faithful"])
                improvement = None
                if candidate is not None and faithful is not None:
                    if faithful > EPSILON:
                        improvement = (faithful - candidate) / faithful
                    elif candidate <= EPSILON:
                        improvement = 0.0
                summaries.append(
                    {
                        "candidate_median_distance": candidate,
                        "faithful_median_distance": faithful,
                        "family": family,
                        "horizon_years": horizon,
                        "relative_improvement": improvement,
                        "station_id": station_id,
                    }
                )
    gates = []
    threshold = contract["daily_target_gates"]
    for family in FAMILIES:
        for horizon in contract["execution"]["horizons_years"]:
            values = [
                row["relative_improvement"]
                for row in summaries
                if row["family"] == family
                and row["horizon_years"] == horizon
                and row["relative_improvement"] is not None
            ]
            center = median(values)
            fraction = sum(value >= -EPSILON for value in values) / len(values) if values else 0.0
            passed = bool(
                center is not None
                and center + EPSILON
                >= threshold["required_median_relative_improvement_each_family_horizon"]
                and fraction + EPSILON
                >= threshold["required_nonworse_station_horizon_fraction"]
            )
            gates.append(
                {
                    "available_stations": len(values),
                    "family": family,
                    "horizon_years": horizon,
                    "median_relative_improvement": center,
                    "nonworse_fraction": fraction,
                    "pass": passed,
                }
            )
    return distances, summaries + gates, all(row["pass"] for row in gates)


def monthly_evaluation(
    contract: dict[str, Any], streams: dict[tuple[str, int], dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    a8a = load_json(ROOT / contract["inputs"]["a8a_analysis"]["path"])
    targets = {
        row["station_id"]: {cell["month"]: cell for cell in row["full_record"]["cells"]}
        for row in a8a["station_results"]
    }
    threshold = contract["execution"]["wet_day_threshold_mm"]
    cells = []
    for station in contract["stations"]:
        station_id = station["station_id"]
        for horizon in contract["execution"]["horizons_years"]:
            for month in range(1, 13):
                daily = []
                totals = []
                for burn in contract["execution"]["burns"]:
                    selected = [
                        row["precipitation"]
                        for row in streams[(station_id, burn)]["candidate"]
                        if row["date"][0] <= horizon and row["date"][1] == month
                    ]
                    daily.extend(selected)
                    by_year: dict[int, float] = defaultdict(float)
                    for row in streams[(station_id, burn)]["candidate"]:
                        if row["date"][0] <= horizon and row["date"][1] == month:
                            by_year[row["date"][0]] += row["precipitation"]
                    totals.extend(by_year.values())
                wet = [value for value in daily if value >= threshold]
                actual_wet_fraction = len(wet) / len(daily)
                actual_wet_mean = mean(wet)
                actual_total_mean = mean(totals)
                actual_total_variance = sample_variance(totals)
                source = targets[station_id][month]
                wet_fraction = source["legacy"]["stationary_wet_fraction"]
                wet_mean = source["legacy"]["wet_mean_mm"]
                expected_total_mean = source["days"] * wet_fraction * wet_mean
                expected_total_variance = (
                    legacy_target_dimensionless_variance(source) * wet_mean * wet_mean
                )
                cells.append(
                    {
                        "errors": {
                            "monthly_total_mean": relative_error(actual_total_mean, expected_total_mean),
                            "monthly_total_variance": relative_error(
                                actual_total_variance, expected_total_variance
                            ),
                            "wet_amount_mean": relative_error(actual_wet_mean, wet_mean),
                            "wet_fraction": abs(actual_wet_fraction - wet_fraction),
                        },
                        "horizon_years": horizon,
                        "month": month,
                        "station_id": station_id,
                    }
                )
    names = {
        "wet_fraction": "wet_fraction_absolute_error_max",
        "wet_amount_mean": "wet_amount_mean_relative_error_max",
        "monthly_total_mean": "monthly_total_mean_relative_error_max",
        "monthly_total_variance": "monthly_total_variance_relative_error_max",
    }
    gates = []
    rules = contract["monthly_moment_gates"]
    for horizon in contract["execution"]["horizons_years"]:
        key = str(horizon)
        for metric, threshold_name in names.items():
            selected = [
                row["errors"][metric]
                for row in cells
                if row["horizon_years"] == horizon and row["errors"][metric] is not None
            ]
            passing = sum(value <= rules[threshold_name][key] + EPSILON for value in selected)
            fraction = passing / 72.0
            gates.append(
                {
                    "available_cells": len(selected),
                    "horizon_years": horizon,
                    "metric": metric,
                    "pass": len(selected) == 72
                    and fraction + EPSILON >= rules["required_station_month_fraction"][key],
                    "passing_fraction": fraction,
                    "threshold": rules[threshold_name][key],
                }
            )
    return cells, gates, all(row["pass"] for row in gates)


def descriptor_log_ratio(candidate: float | None, faithful: float | None) -> float | None:
    if candidate is None or faithful is None:
        return None
    if candidate == 0.0 and faithful == 0.0:
        return 0.0
    if candidate == 0.0 or faithful == 0.0:
        return None
    return abs(math.log(candidate / faithful))


def guard_evaluation(
    contract: dict[str, Any], streams: dict[tuple[str, int], dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    descriptors = []
    finite_and_bounds = True
    cold_wet_count = 0
    cold_wet_exact = True
    for station in contract["stations"]:
        station_id = station["station_id"]
        for horizon in contract["execution"]["horizons_years"]:
            pooled = {variant: defaultdict(list) for variant in ("candidate", "faithful")}
            for burn in contract["execution"]["burns"]:
                for variant in ("candidate", "faithful"):
                    for row in streams[(station_id, burn)][variant]:
                        if row["date"][0] > horizon or row["precipitation"] <= 0.0:
                            continue
                        if not (
                            0.0 <= row["duration"] <= 24.0
                            and 0.0 <= row["time_to_peak"] <= 0.99
                            and row["normalized_peak"] >= 1.01 - EPSILON
                        ):
                            finite_and_bounds = False
                        if variant == "candidate" and row["tmax"] <= 0.0:
                            cold_wet_count += 1
                            cold_wet_exact &= abs(row["normalized_peak"] - 1.01) <= EPSILON
                        for name in ("duration", "time_to_peak", "normalized_peak"):
                            pooled[variant][name].append(row[name])
            for name in ("duration", "time_to_peak", "normalized_peak"):
                candidate = median(pooled["candidate"][name])
                faithful = median(pooled["faithful"][name])
                ratio = descriptor_log_ratio(candidate, faithful)
                descriptors.append(
                    {
                        "candidate_median": candidate,
                        "descriptor": name,
                        "faithful_median": faithful,
                        "horizon_years": horizon,
                        "log_ratio": ratio,
                        "station_id": station_id,
                    }
                )
    ratio_gate = all(
        row["log_ratio"] is not None
        and row["log_ratio"] <= contract["guard_gates"]["storm_descriptor_median_log_ratio_max"] + EPSILON
        for row in descriptors
    )
    summary = {
        "cold_wet_count": cold_wet_count,
        "cold_wet_normalized_peak_exact": cold_wet_count > 0 and cold_wet_exact,
        "storm_descriptor_gate": ratio_gate,
        "storm_finite_and_bounds": finite_and_bounds,
    }
    return descriptors, summary, all(summary.values())


def engineering_evaluation(execution: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    cells = execution["cells"]
    checks = {
        "candidate_byte_replay": all(row["candidate_byte_replay"] for row in cells),
        "candidate_30_year_row_prefix": all(row["candidate_30_year_row_prefix"] for row in cells),
        "cross_variable_exact": all(
            row["cross_variable_exact"] is True
            for row in cells
            if row["route"] == "integrated_daily"
        ),
        "fallback_typed_row_identity": all(
            row["fallback_typed_row_identity"] is True
            for row in cells
            if row["route"] == "legacy_daily_fallback"
        ),
        "profile_station_rng_provenance": all(
            row["provenance"]["profile"] == "a8c_routed_daily_v1"
            and row["provenance"]["input_schema_version"] == 2
            and row["provenance"]["rng_scheme"]
            == "cligen_randn_5_32_3_plus_splitmix64_daily_v1"
            for row in cells
        ),
    }
    return checks, all(checks.values())


def findings_text(decision: dict[str, Any]) -> str:
    failed = decision["failed_gate_groups"]
    return "\n".join(
        [
            "# A8c findings",
            "",
            f"Terminal: `{decision['terminal_decision']}`.",
            "",
            f"Engineering output gates: {'pass' if decision['gate_groups']['engineering'] else 'fail'}.",
            f"Monthly moment gates: {'pass' if decision['gate_groups']['monthly_moments'] else 'fail'}.",
            f"Daily target gates: {'pass' if decision['gate_groups']['daily_targets'] else 'fail'}.",
            f"Storm/winter guards: {'pass' if decision['gate_groups']['storm_winter'] else 'fail'}.",
            "",
            "Failed gate groups: " + (", ".join(failed) if failed else "none"),
            "",
            "The pilot cannot promote a public default. A confirmation study is only a recommendation when every frozen gate passes.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution", type=Path, default=EXECUTION_PATH)
    parser.add_argument("--output-dir", type=Path, default=ARTIFACTS)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    contract = load_json(CONTRACT_PATH)
    checked_inputs = check_frozen_inputs(contract)
    execution = load_json(args.execution.resolve())
    if execution["contract_sha256"] != sha256(CONTRACT_PATH):
        raise ValueError("execution used a different contract")
    if execution["freeze_sha256"] != sha256(EXECUTION_FREEZE_PATH):
        raise ValueError("execution used a different pre-generation freeze")
    streams = load_streams(execution)
    if len(streams) != 24:
        raise ValueError("expected 24 station/burn cells")

    a7a_path = ROOT / contract["inputs"]["a7a_analyzer"]["path"]
    a7a = load_module(a7a_path, "a8c_a7a_measurement")
    a7a_contract = load_json(ROOT / contract["inputs"]["a7a_measurement_contract"]["path"])
    observed = observed_metrics(contract, a7a, a7a_contract)
    daily_distances, daily_summaries, daily_pass = daily_evaluation(
        contract, streams, observed, a7a, a7a_contract
    )
    monthly_cells, monthly_gates, monthly_pass = monthly_evaluation(contract, streams)
    descriptors, guard_summary, guard_pass = guard_evaluation(contract, streams)
    engineering, engineering_pass = engineering_evaluation(execution)
    gate_groups = {
        "daily_targets": daily_pass,
        "engineering": engineering_pass,
        "monthly_moments": monthly_pass,
        "storm_winter": guard_pass,
    }
    terminal = (
        "RECOMMEND-A8D-CONFIRMATION"
        if all(gate_groups.values())
        else "STOP-A8-ROUTED-DAILY"
    )
    analysis = {
        "analysis_id": contract["analysis_id"],
        "contract_sha256": sha256(CONTRACT_PATH),
        "daily_distances": daily_distances,
        "daily_summaries_and_gates": daily_summaries,
        "engineering_gates": engineering,
        "execution_evidence_sha256": sha256(args.execution.resolve()),
        "pre_analysis_freeze_sha256": sha256(FREEZE_PATH),
        "guard_summary": guard_summary,
        "input_hashes": checked_inputs,
        "monthly_cells": monthly_cells,
        "monthly_gates": monthly_gates,
        "schema_version": 1,
        "source_commit": contract["source_commit"],
        "storm_descriptor_comparisons": descriptors,
    }
    decision = {
        "analysis_id": contract["analysis_id"],
        "analysis_sha256": "computed-after-write",
        "failed_gate_groups": sorted(name for name, passed in gate_groups.items() if not passed),
        "gate_groups": gate_groups,
        "schema_version": 1,
        "source_commit": contract["source_commit"],
        "terminal_decision": terminal,
    }
    analysis_path = output_dir / ANALYSIS_PATH.name
    decision_path = output_dir / DECISION_PATH.name
    findings_path = output_dir / FINDINGS_PATH.name
    write_json(analysis_path, analysis)
    decision["analysis_sha256"] = sha256(analysis_path)
    write_json(decision_path, decision)
    findings_path.write_text(findings_text(decision), encoding="utf-8")
    print(terminal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
