#!/usr/bin/env python3
"""Independent identity, invariant, decision, and reproduction checks for A8a."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
INTEGRATED = "integrated_daily"
FALLBACK = "legacy_daily_fallback"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(path)
    return value


def close(left: float, right: float, tolerance: float = 2e-9) -> None:
    if not math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"numeric mismatch: {left} != {right}")


def check_freeze(contract: dict[str, Any]) -> None:
    freeze_path = ARTIFACTS / "pre-analysis-freeze-v2.json"
    freeze = load_json(freeze_path)
    if freeze["status"] != "FROZEN-BEFORE-NEW-DAILY-DATA":
        raise AssertionError("freeze status mismatch")
    for relative, expected in freeze["frozen_files_sha256"].items():
        if sha256((REPO / relative).read_bytes()) != expected:
            raise AssertionError(f"frozen file mismatch: {relative}")
    for entry in contract["inputs"].values():
        if sha256((REPO / entry["path"]).read_bytes()) != entry["sha256"]:
            raise AssertionError(f"input mismatch: {entry['path']}")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", contract["source_commit"], "HEAD"],
        cwd=REPO,
        check=True,
    )
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=REPO,
            check=False,
        ).returncode
        != 0
    ):
        raise AssertionError("production crates changed after source boundary")


def verify_sources(contract: dict[str, Any]) -> None:
    manifest = load_json(ARTIFACTS / "source-manifest-v1.json")
    if manifest["analysis_contract_sha256"] != sha256(
        (ARTIFACTS / "analysis-contract-v1.json").read_bytes()
    ):
        raise AssertionError("source manifest contract mismatch")
    if manifest["pre_analysis_freeze_sha256"] != sha256(
        (ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes()
    ):
        raise AssertionError("source manifest freeze mismatch")
    if len(manifest["stations"]) != 20:
        raise AssertionError("source station count mismatch")
    station_list = manifest["ghcn_station_list"]
    if sha256((REPO / station_list["archive_path"]).read_bytes()) != station_list["archive_sha256"]:
        raise AssertionError("GHCN station-list archive mismatch")
    for entry in manifest["stations"]:
        daymet = entry["sources"]["daymet"]
        if daymet["availability"] != "available":
            raise AssertionError("primary Daymet source unavailable")
        if daymet["fixed_window_record_count"] != contract["sources"]["daymet_expected_record_count"]:
            raise AssertionError("Daymet record-count mismatch")
        if sha256((REPO / daymet["archive_path"]).read_bytes()) != daymet["archive_sha256"]:
            raise AssertionError("Daymet archive identity mismatch")
        ghcn = entry["sources"]["ghcn"]
        if ghcn["availability"] == "available":
            if not ghcn["station_identifier"].startswith("USC"):
                raise AssertionError("non-U.S.-Cooperative GHCN source")
            if ghcn["coordinate_separation_km"] > contract["sources"]["ghcn_coordinate_tolerance_km"]:
                raise AssertionError("GHCN coordinate tolerance violated")
            if sha256((REPO / ghcn["archive_path"]).read_bytes()) != ghcn["archive_sha256"]:
                raise AssertionError("GHCN archive identity mismatch")


def verify() -> None:
    contract = load_json(ARTIFACTS / "analysis-contract-v1.json")
    analysis = load_json(ARTIFACTS / "a8a-analysis-v1.json")
    decision = load_json(ARTIFACTS / "a8a-decision-v1.json")
    check_freeze(contract)
    verify_sources(contract)
    if analysis["pre_analysis_freeze_sha256"] != sha256(
        (ARTIFACTS / "pre-analysis-freeze-v2.json").read_bytes()
    ):
        raise AssertionError("analysis freeze mismatch")
    expected_counts = {
        "confirmation_stations": 20,
        "development_stations": 8,
        "full_record_cells": 336,
        "shortened_station_windows": 80,
    }
    if analysis["execution_counts"] != expected_counts:
        raise AssertionError("execution cardinality mismatch")
    if len(analysis["station_results"]) != 28:
        raise AssertionError("station-result cardinality mismatch")
    confirmation = [entry for entry in analysis["station_results"] if entry["confirmation"]]
    development = [entry for entry in analysis["station_results"] if not entry["confirmation"]]
    for entry in analysis["station_results"]:
        full = entry["full_record"]
        analytic_pass = bool(
            full["feasible_cell_count"] == 12
            and all(cell["feasible"] for cell in full["cells"])
        )
        if analytic_pass != full["analytic_pass"]:
            raise AssertionError("station analytic disposition mismatch")
        bootstrap_pass = all(
            season["bootstrap_lower_pass"] and season["point_fit_pass"]
            for season in entry["bootstrap_support"]["seasons"].values()
        )
        if bootstrap_pass != entry["bootstrap_support"]["all_seasons_pass"]:
            raise AssertionError("bootstrap disposition mismatch")
        expected_class = INTEGRATED if analytic_pass and bootstrap_pass else FALLBACK
        if entry["classification"] != expected_class:
            raise AssertionError("station classification mismatch")
        for cell in full["cells"]:
            if not cell["feasible"]:
                if not cell["infeasibility_reasons"]:
                    raise AssertionError("infeasible cell lacks reason")
                continue
            matrix = np.asarray(cell["kernel"]["transition_matrix"])
            pi = np.asarray(cell["kernel"]["stationary_distribution"])
            if np.max(np.abs(np.sum(matrix, axis=1) - 1.0)) > 2e-12:
                raise AssertionError("transition row sum mismatch")
            if np.max(np.abs(pi @ matrix - pi)) > 2e-9:
                raise AssertionError("stored stationary distribution mismatch")
            close(
                cell["kernel"]["stationary_wet_fraction"],
                cell["legacy"]["stationary_wet_fraction"],
            )
            budget = cell["budget"]
            if budget["monthly_variance_relative_error"] > 1e-8:
                raise AssertionError("monthly budget error")
            if budget["wet_amount_variance_retention"] < 0.25:
                raise AssertionError("variance retention error")
            if budget["tail_log_error_max"] > 0.7:
                raise AssertionError("tail gate error")
            if budget["budget_dispersion"] > budget["legacy_dispersion"] + 1e-12:
                raise AssertionError("wet-amount variance increase")
    development_actual = {entry["station_id"]: entry["classification"] for entry in development}
    if development_actual != contract["decision"]["expected_development_classes"]:
        raise AssertionError("development reproduction mismatch")
    dry = [entry for entry in confirmation if entry["stratum"] != "negative_control"]
    controls = [entry for entry in confirmation if entry["stratum"] == "negative_control"]
    comparisons = [
        entry["classification"] == window["classification"]
        for entry in confirmation
        for window in entry["shortened_windows"]
    ]
    shortened_agreement = sum(comparisons) / len(comparisons)
    close(shortened_agreement, decision["shortened_window_agreement"])

    def instability(entries: list[dict[str, Any]]) -> float:
        values = [
            entry["classification"] != window["classification"]
            for entry in entries
            for window in entry["shortened_windows"]
        ]
        return sum(values) / len(values)

    monsoon = [entry for entry in confirmation if entry["stratum"] == "monsoonal_transition"]
    other = [
        entry
        for entry in confirmation
        if entry["stratum"] in contract["stability"]["other_dry_groups"]
    ]
    monsoon_rate = instability(monsoon)
    other_rate = instability(other)
    close(monsoon_rate, decision["monsoonal_instability_rate"])
    close(other_rate, decision["other_dry_instability_rate"])
    guards = {
        "confirmation_cardinality": len(confirmation) == 20,
        "development_reproduced": True,
        "dry_fallback_breadth": sum(x["classification"] == FALLBACK for x in dry)
        >= contract["decision"]["dry_fallback_min"],
        "dry_integrated_breadth": sum(x["classification"] == INTEGRATED for x in dry)
        >= contract["decision"]["dry_integrated_min"],
        "integrated_analytic_pass": all(
            x["full_record"]["analytic_pass"]
            for x in confirmation
            if x["classification"] == INTEGRATED
        ),
        "monsoonal_shared_boundary": monsoon_rate - other_rate
        <= contract["decision"]["monsoonal_instability_excess_max"],
        "negative_controls_integrated": sum(x["classification"] == INTEGRATED for x in controls)
        == contract["decision"]["negative_control_integrated_required"],
        "shortened_window_agreement": shortened_agreement
        >= contract["decision"]["shortened_window_agreement_min"],
    }
    if guards != decision["guards"]:
        raise AssertionError("decision guard mismatch")
    terminal = (
        contract["decision"]["pass_terminal"]
        if all(guards.values())
        else contract["decision"]["stop_terminal"]
    )
    if terminal != decision["terminal"] or terminal != analysis["terminal"]:
        raise AssertionError("terminal mismatch")


def reproduce() -> None:
    with tempfile.TemporaryDirectory(prefix="a8a-reproduce-") as temporary:
        root = Path(temporary)
        output = root / "analysis.json"
        decision = root / "decision.json"
        findings = root / "findings.md"
        subprocess.run(
            [
                sys.executable,
                str(ARTIFACTS / "analyze-a8a.py"),
                "--output",
                str(output),
                "--decision",
                str(decision),
                "--findings",
                str(findings),
            ],
            cwd=REPO,
            check=True,
        )
        for generated, canonical in (
            (output, ARTIFACTS / "a8a-analysis-v1.json"),
            (decision, ARTIFACTS / "a8a-decision-v1.json"),
            (findings, ARTIFACTS / "findings.md"),
        ):
            if generated.read_bytes() != canonical.read_bytes():
                raise AssertionError(f"non-reproducible artifact: {canonical.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    verify()
    if args.reproduce:
        reproduce()
    print("A8a independent verification: PASS")


if __name__ == "__main__":
    main()
