#!/usr/bin/env python3
"""Finalize the frozen A5d1b aggregate result and machine decision."""

from __future__ import annotations

import sys

from a5d1b_common import (
    ARTIFACTS,
    CONTRACT,
    COUNT_RESULTS,
    DIAGNOSTIC_RESULTS,
    PATH_RESULTS,
    ROOT,
    freeze_identity,
    load_json,
    sha256,
    write_json,
)


RESULTS = ARTIFACTS / "a5d1b-results-v1.json"
DECISION = ARTIFACTS / "a5d1b-decision-v1.json"
DETAILED_ARCHIVE = ARTIFACTS / "detailed-evidence-v1.tar.gz"
DETAILED_MANIFEST = ARTIFACTS / "detailed-evidence-manifest-v1.json"


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: finalize-a5d1b.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    diagnostics = load_json(DIAGNOSTIC_RESULTS)
    counts = load_json(COUNT_RESULTS)
    paths = load_json(PATH_RESULTS)
    manifest = load_json(DETAILED_MANIFEST)
    if not all(isinstance(value, dict) for value in (contract, diagnostics, counts, paths, manifest)):
        raise ValueError("invalid finalization input")
    if counts["count_pass_count"] == 17:
        if not paths["executed"] or paths["actual_cells"] != 51:
            raise ValueError("ordered path matrix missing after complete count gate")
        if paths["pass_count"] == 51:
            terminal = "EXECUTED-COMPLETE-STRUCTURAL-SELECTOR"
            structural = "STRUCTURALLY-FEASIBLE"
            first_action = "Proceed only after A5d2 and A5d3 close; then bind this structural selector in A5d4."
        elif paths.get("resource_exhausted_count", 0) > 0:
            terminal = "EXECUTED-HOLD-RESOURCE"
            structural = "HOLD"
            first_action = "Profile the frozen ordering search and prospectively justify a resource-only successor without changing climate tolerances."
        else:
            terminal = "EXECUTED-HOLD-ORDERING-SEARCH-BOUNDED"
            structural = "HOLD"
            first_action = "Diagnose the first common order-dependent gate under the exact count witnesses before freezing another ordering search."
    else:
        separate_both = 0
        for row in counts["records"]:
            if row["count_pass"]:
                continue
            certificate = load_json(ROOT / row["certificate"]["path"])
            separate = certificate.get("separate_horizon_diagnostics")
            if separate and all(separate[str(horizon)]["exact_pass"] for horizon in (30, 100)):
                separate_both += 1
        failing = 17 - counts["count_pass_count"]
        if failing > 0 and separate_both == failing:
            terminal = "EXECUTED-HOLD-COMMON-PREFIX-SEARCH-BOUNDED"
            first_action = "Diagnose joint-prefix construction under the separate exact 30-/100-year witnesses; do not relax the frozen climate rules."
        else:
            terminal = "EXECUTED-HOLD-COUNT-SEARCH-BOUNDED"
            first_action = "Diagnose the first common exact count-replay obstruction and separate MILP linear status from bounded nonlinear construction failure."
        structural = "HOLD"
    results = {
        "a5d1b_results_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "terminal_status": terminal,
        "structural_decision": structural,
        "station_count": 17,
        "inherited_diagnostic_cells": diagnostics["actual_cells"],
        "inherited_count_only_both_pass": diagnostics["count_only_both_horizons_pass"],
        "count_pass_count": counts["count_pass_count"],
        "ordered_execution": paths["executed"],
        "ordered_path_pass_count": paths["pass_count"],
        "ordered_path_actual_cells": paths["actual_cells"],
        "selected_algorithm": contract["algorithm"]["ordering_id"] if structural == "STRUCTURALLY-FEASIBLE" else None,
        "first_corrective_action": first_action,
        "evidence": {
            "contract_sha256": sha256(CONTRACT),
            "diagnostics_sha256": sha256(DIAGNOSTIC_RESULTS),
            "count_results_sha256": sha256(COUNT_RESULTS),
            "path_results_sha256": sha256(PATH_RESULTS),
            "detailed_manifest_sha256": sha256(DETAILED_MANIFEST),
            "detailed_archive_sha256": sha256(DETAILED_ARCHIVE),
        },
    }
    write_json(RESULTS, results)
    decision = {
        "a5d1b_decision_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "results_sha256": sha256(RESULTS),
        "terminal_status": terminal,
        "decision": structural,
        "selected_structural_algorithm": results["selected_algorithm"],
        "public_candidate_authorized": False,
        "confirmation_authorized": False,
        "a5d2_required": True,
        "a5d3_required": True,
        "a5d4_authorized": structural == "STRUCTURALLY-FEASIBLE",
        "first_corrective_action": first_action,
    }
    write_json(DECISION, decision)
    print(f"A5d1b terminal: {terminal}; count={counts['count_pass_count']}/17; paths={paths['pass_count']}/{paths['actual_cells']}")


if __name__ == "__main__":
    main()
