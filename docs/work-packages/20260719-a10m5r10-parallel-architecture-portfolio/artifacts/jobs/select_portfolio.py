#!/usr/bin/env python3
"""Deterministically select the A10M5R10 eligible Pareto portfolio."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

DISPERSION = ("monthly_interannual_dispersion", "annual_interannual_dispersion")
LOCATION = ("monthly_location", "annual_location")
WET_DEPENDENCE = ("wet_occurrence_and_amount", "precipitation_temperature_dependence")
SOLAR_DEPENDENCE = ("wet_dry_contrast", "precipitation_temperature_association")
SEEDS = (147031, 271828, 314159)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, allow_nan=False, indent=2, sort_keys=True)
        stream.write("\n")
    partial.replace(path)
    if path.stat().st_size >= 10_000_000:
        raise RuntimeError(f"JSON publication exceeds 10 MB: {path}")


def ratio(candidate: float, control: float) -> float:
    if not math.isfinite(candidate) or not math.isfinite(control) or control <= 0.0:
        raise RuntimeError("selector metric is non-finite or has non-positive control")
    return candidate / control


def combined_ratio(
    candidate: dict[str, float], control: dict[str, float], names: tuple[str, ...]
) -> float:
    return ratio(
        statistics.fmean(candidate[name] for name in names),
        statistics.fmean(control[name] for name in names),
    )


def seed_ratios(record: dict[str, Any]) -> dict[str, Any]:
    candidate = record["candidate"]
    control = record["control"]
    blocks = {
        name: ratio(value, control["block_scores"][name])
        for name, value in candidate["block_scores"].items()
    }
    axes = {
        "family_balanced_climate": ratio(
            candidate["family_balanced_climate_score"],
            control["family_balanced_climate_score"],
        ),
        "daily_proper_nll": ratio(candidate["daily_proper_nll"], control["daily_proper_nll"]),
        "combined_monthly_annual_dispersion": combined_ratio(
            candidate["block_scores"], control["block_scores"], DISPERSION
        ),
        "combined_monthly_annual_location": combined_ratio(
            candidate["block_scores"], control["block_scores"], LOCATION
        ),
        "combined_wet_dependence": combined_ratio(
            candidate["block_scores"], control["block_scores"], WET_DEPENDENCE
        ),
        "within_month_daily_dispersion": blocks["within_month_daily_dispersion"],
    }
    output = {"axes": axes, "blocks": blocks, "seed": int(record["seed"])}
    if "solar" in candidate:
        solar_control = record.get("solar_control")
        if not solar_control:
            raise RuntimeError("physics result omits clearness-climatology control")
        solar_blocks = {
            name: ratio(value, solar_control["block_scores"][name])
            for name, value in candidate["solar"]["block_scores"].items()
        }
        output["solar"] = {
            "blocks": solar_blocks,
            "dependence_ratio": combined_ratio(
                candidate["solar"]["block_scores"],
                solar_control["block_scores"],
                SOLAR_DEPENDENCE,
            ),
            "family_ratio": ratio(
                candidate["solar"]["family_score"], solar_control["family_score"]
            ),
        }
    return output


def summarize_configuration(
    summary: dict[str, Any], seed_records: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    if tuple(sorted(int(row["seed"]) for row in seed_records)) != tuple(sorted(SEEDS)):
        raise RuntimeError("candidate seed matrix incomplete")
    ratios = [seed_ratios(row) for row in seed_records]
    axes = {
        name: statistics.median(row["axes"][name] for row in ratios)
        for name in contract["pareto"]["axes"]
    }
    block_names = sorted(ratios[0]["blocks"])
    median_blocks = {
        name: statistics.median(row["blocks"][name] for row in ratios)
        for name in block_names
    }
    eligibility = contract["eligibility"]
    gates = {
        "complete_finite_support": all(
            row["candidate"]["support"]
            and row["candidate"]["point_count"] == 240
            and row["fit_validation_gradient"] is False
            and row["protected_roles_opened"] == []
            for row in seed_records
        ),
        "median_climate": axes["family_balanced_climate"] <= float(
            eligibility["median_climate_ratio_max"]
        ),
        "median_daily_nll": axes["daily_proper_nll"] <= float(
            eligibility["median_daily_nll_ratio_max"]
        ),
        "median_each_block": all(
            value <= float(eligibility["median_each_block_ratio_max"])
            for value in median_blocks.values()
        ),
        "worst_seed_climate": max(
            row["axes"]["family_balanced_climate"] for row in ratios
        ) <= float(eligibility["worst_seed_climate_ratio_max"]),
        "worst_seed_daily_nll": max(
            row["axes"]["daily_proper_nll"] for row in ratios
        ) <= float(eligibility["worst_seed_daily_nll_ratio_max"]),
        "worst_seed_each_block": all(
            max(row["blocks"][name] for row in ratios)
            <= float(eligibility["worst_seed_each_block_ratio_max"])
            for name in block_names
        ),
        "median_combined_dispersion": axes["combined_monthly_annual_dispersion"]
        <= float(eligibility["median_combined_monthly_annual_dispersion_ratio_max"]),
    }
    solar = None
    if summary["architecture"] == "physics_conditioned_hierarchical_adapter":
        if not all("solar" in row for row in ratios):
            raise RuntimeError("physics configuration lacks solar ratios")
        median_family = statistics.median(row["solar"]["family_ratio"] for row in ratios)
        median_dependence = statistics.median(
            row["solar"]["dependence_ratio"] for row in ratios
        )
        solar_names = sorted(ratios[0]["solar"]["blocks"])
        median_solar_blocks = {
            name: statistics.median(row["solar"]["blocks"][name] for row in ratios)
            for name in solar_names
        }
        physics_limits = eligibility["physics"]
        gates.update({
            "solar_family_improvement": 1.0 - median_family
            >= float(physics_limits["solar_family_improvement_fraction_min"]),
            "solar_dependence_improvement": 1.0 - median_dependence
            >= float(physics_limits["solar_dependence_improvement_fraction_min"]),
            "solar_each_block_non_degradation": all(
                value <= 1.0 + float(physics_limits["solar_each_block_degradation_fraction_max"])
                for value in median_solar_blocks.values()
            ),
        })
        solar = {
            "median_block_ratios": median_solar_blocks,
            "median_dependence_ratio": median_dependence,
            "median_family_ratio": median_family,
        }
    return {
        "architecture": summary["architecture"],
        "axes": axes,
        "capacity": summary["capacity"],
        "configuration_id": summary["configuration_id"],
        "eligible": all(gates.values()),
        "eligibility_gates": gates,
        "median_block_ratios": median_blocks,
        "parameter_count": int(summary["total_parameter_count"]),
        "seed_ratios": ratios,
        "solar": solar,
        "training_wall_seconds": float(summary["training_wall_seconds"]),
    }


def dominates(left: dict[str, Any], right: dict[str, Any], improvement: float) -> bool:
    names = tuple(left["axes"])
    return all(left["axes"][name] <= right["axes"][name] for name in names) and any(
        left["axes"][name] <= (1.0 - improvement) * right["axes"][name]
        for name in names
    )


def nondominated(rows: list[dict[str, Any]], improvement: float) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if not any(
            other["configuration_id"] != row["configuration_id"]
            and dominates(other, row, improvement)
            for other in rows
        )
    ]


def choose(
    rows: list[dict[str, Any]], axis: str, equivalence: float
) -> dict[str, Any]:
    minimum = min(row["axes"][axis] for row in rows)
    equivalent = [
        row for row in rows if row["axes"][axis] <= (1.0 + equivalence) * minimum
    ]
    return min(
        equivalent,
        key=lambda row: (
            row["parameter_count"], row["training_wall_seconds"], row["configuration_id"]
        ),
    )


def select(rows: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    eligible = [row for row in rows if row["eligible"]]
    pareto = nondominated(
        eligible, float(contract["pareto"]["dominance_minimum_improvement_fraction"])
    )
    remaining = list(pareto)
    retained = []
    axes = (
        "family_balanced_climate",
        "combined_monthly_annual_dispersion",
        "daily_proper_nll",
    )
    for axis in axes[: int(contract["pareto"]["maximum_retained"])]:
        if not remaining:
            break
        picked = choose(
            remaining, axis, float(contract["pareto"]["equivalence_fraction"])
        )
        retained.append(picked)
        remaining = [
            row for row in remaining
            if row["configuration_id"] != picked["configuration_id"]
        ]
    count = len(retained)
    if count >= int(contract["pareto"]["minimum_retained_for_ready"]):
        terminal = contract["terminals"]["ready"]
    elif count == 1:
        terminal = contract["terminals"]["single"]
    else:
        terminal = contract["terminals"]["none"]
    return {
        "eligible_configuration_ids": sorted(row["configuration_id"] for row in eligible),
        "nondominated_configuration_ids": sorted(row["configuration_id"] for row in pareto),
        "retained_configuration_ids": [row["configuration_id"] for row in retained],
        "terminal": terminal,
    }


def self_test() -> None:
    contract = {
        "pareto": {
            "axes": [
                "family_balanced_climate", "daily_proper_nll",
                "combined_monthly_annual_dispersion", "combined_monthly_annual_location",
                "combined_wet_dependence", "within_month_daily_dispersion",
            ],
            "dominance_minimum_improvement_fraction": 0.02,
            "equivalence_fraction": 0.02,
            "maximum_retained": 3,
            "minimum_retained_for_ready": 2,
        },
        "terminals": {"ready": "READY", "single": "SINGLE", "none": "NONE"},
    }
    rows = []
    for identifier, climate_value, dispersion, nll, parameters in (
        ("a", 0.90, 0.98, 1.03, 100),
        ("b", 0.98, 0.85, 1.04, 200),
        ("c", 0.99, 0.99, 0.90, 300),
    ):
        rows.append({
            "axes": {
                "family_balanced_climate": climate_value,
                "daily_proper_nll": nll,
                "combined_monthly_annual_dispersion": dispersion,
                "combined_monthly_annual_location": 1.0,
                "combined_wet_dependence": 1.0,
                "within_month_daily_dispersion": 1.0,
            },
            "configuration_id": identifier,
            "eligible": True,
            "parameter_count": parameters,
            "training_wall_seconds": 10.0,
        })
    forward = select(rows, contract)
    reverse = select(list(reversed(rows)), contract)
    if forward != reverse or forward["terminal"] != "READY":
        raise RuntimeError("portfolio selection order-independence self-test failed")
    print("A10M5R10-PORTFOLIO-SELECTOR-SELF-TEST-PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--controls", type=Path, required=True)
    parser.add_argument("--candidates-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    self_test()
    contract = read_json(options.contract)
    control = read_json(options.controls)
    control_root = options.controls.parent
    control_evidence = read_json(control_root / "evidence.json")
    control_identity = read_json(control_root / "control-identity.json")
    control_calendar = read_json(control_root / "calendar-preflight.json")
    if control["contract_sha256"] != digest(options.contract):
        raise RuntimeError("selector control/contract identity mismatch")
    if (
        not control_evidence.get("valid")
        or control_evidence.get("verdict") != "PASS"
        or not control_evidence.get("gates")
        or not all(control_evidence["gates"].values())
        or control_evidence.get("protected_roles_opened") != []
        or not control_identity.get("all_exact")
        or not control_calendar.get("valid")
        or control_calendar.get("profile_id") != contract["calendar"]["profile_id"]
        or control.get("protected_roles_opened") != []
    ):
        raise RuntimeError("selector control predecessor evidence did not pass")
    rows = []
    role_inputs = []
    for role in contract["roles"]:
        root = options.candidates_dir / role["role_id"]
        summary_path = root / "candidate-summary.json"
        summary = read_json(summary_path)
        evidence_path = root / "evidence.json"
        calendar_path = root / "calendar-preflight.json"
        identity_path = root / "control-identity.json"
        training_path = root / "training.json"
        evidence = read_json(evidence_path)
        calendar = read_json(calendar_path)
        identity = read_json(identity_path)
        training = read_json(training_path)
        if (
            summary["role_id"] != role["role_id"]
            or summary["architecture"] != role["architecture"]
            or summary["capacity"] != role["capacity"]
            or summary["contract_sha256"] != digest(options.contract)
        ):
            raise RuntimeError("candidate role identity mismatch")
        if (
            not evidence.get("valid")
            or evidence.get("verdict") != "PASS"
            or evidence.get("role") != role["role_id"]
            or evidence.get("candidate_id") != role["architecture"]
            or evidence.get("capacity_id") != role["capacity"]
            or not evidence.get("gates")
            or not all(evidence["gates"].values())
            or evidence.get("protected_roles_opened") != []
        ):
            raise RuntimeError("candidate finalized evidence did not pass")
        if (
            not calendar.get("valid")
            or calendar.get("profile_id") != contract["calendar"]["profile_id"]
            or not identity.get("exact")
            or identity.get("control_summary_sha256") != digest(options.controls)
            or training.get("architecture") != role["architecture"]
            or training.get("capacity") != role["capacity"]
            or tuple(sorted(int(row["seed"]) for row in training.get("seeds", [])))
            != tuple(sorted(SEEDS))
            or calendar != control_calendar
            or summary["seed_files"] != [f"seeds/{seed}.json" for seed in SEEDS]
        ):
            raise RuntimeError("candidate calendar/control/training identity mismatch")
        seed_records = [
            read_json(root / "seeds" / f"{seed}.json")
            for seed in contract["controls"]["seeds"]
        ]
        expected_configuration = f"{role['architecture']}-{role['capacity'].lower()}"
        parameter_ceiling = int(
            contract["controls"]["capacities"][role["capacity"]][
                "candidate_parameter_ceiling"
            ]
        )
        if int(summary["total_parameter_count"]) > parameter_ceiling:
            raise RuntimeError("candidate summary exceeds parameter ceiling")
        if any(
            row["architecture"] != role["architecture"]
            or row["capacity"] != role["capacity"]
            or row["configuration_id"] != expected_configuration
            or row["contract_sha256"] != digest(options.contract)
            or row["control_summary_sha256"] != identity["control_summary_sha256"]
            or row["calendar_preflight_sha256"]
            != summary["calendar_preflight_sha256"]
            or row["role_id"] != role["role_id"]
            or int(row["total_parameter_count"]) != int(summary["total_parameter_count"])
            or row["fit_validation_gradient"] is not False
            or row["protected_roles_opened"] != []
            for row in seed_records
        ):
            raise RuntimeError("candidate seed semantic identity mismatch")
        training_lookup = {int(row["seed"]): row for row in training["seeds"]}
        if any(
            row["training"]["checkpoint_sha256"]
            != training_lookup[int(row["seed"])]["checkpoint_sha256"]
            for row in seed_records
        ):
            raise RuntimeError("candidate seed/training checkpoint identity mismatch")
        control_lookup = {
            (row["capacity_id"], int(row["training_seed"])): row
            for row in control["models"]
        }
        if any(
            row["control_export_sha256"]
            != control_lookup[(row["backbone_capacity"], int(row["seed"]))]["export_sha256"]
            for row in seed_records
        ):
            raise RuntimeError("candidate seed matched-control identity mismatch")
        rows.append(summarize_configuration(summary, seed_records, contract))
        role_inputs.append({
            "candidate_summary_sha256": digest(summary_path),
            "calendar_preflight_sha256": digest(calendar_path),
            "control_identity_sha256": digest(identity_path),
            "evidence_sha256": digest(evidence_path),
            "role_id": role["role_id"],
            "seed_sha256": {
                str(seed): digest(root / "seeds" / f"{seed}.json")
                for seed in contract["controls"]["seeds"]
            },
            "training_sha256": digest(training_path),
        })
    if len(rows) != 10 or len({row["configuration_id"] for row in rows}) != 10:
        raise RuntimeError("portfolio configuration matrix incomplete")
    decision = select(rows, contract)
    comparison = {
        "configuration_count": len(rows),
        "configurations": sorted(rows, key=lambda row: row["configuration_id"]),
        "contract_sha256": digest(options.contract),
        "collected_control_files": {
            "calendar_preflight_sha256": digest(control_root / "calendar-preflight.json"),
            "control_evidence_sha256": digest(control_root / "evidence.json"),
            "control_identity_sha256": digest(control_root / "control-identity.json"),
            "control_summary_sha256": digest(options.controls),
        },
        "protected_roles_opened": [],
        "role_inputs": role_inputs,
        "schema_version": 1,
    }
    pareto = {
        "axes": contract["pareto"]["axes"],
        "decision": decision,
        "eligible": [row for row in comparison["configurations"] if row["eligible"]],
        "schema_version": 1,
    }
    atomic_json(options.output / "comparison.json", comparison)
    atomic_json(options.output / "pareto.json", pareto)
    atomic_json(options.output / "decision.json", decision)
    evidence = {
        "classification": "a10m5r10-development-only-portfolio-selection",
        "gates": {
            "candidate_matrix_complete": len(rows) == 10,
            "controls_bound": True,
            "deterministic_selection_replayed": True,
            "protected_roles_sealed": True,
            "scientific_decision_published": decision["terminal"] in contract["terminals"].values(),
        },
        "protected_roles_opened": [],
        "schema_version": 1,
        "scientific_decision": decision,
    }
    atomic_json(options.output / "evidence.json", evidence)
    print(decision["terminal"])


if __name__ == "__main__":
    main()
