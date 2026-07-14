#!/usr/bin/env python3
"""Apply the frozen cross-station selection rule and publish A5d1 results."""

from __future__ import annotations

import collections
import sys

from a5d1_common import (
    CONTRACT,
    FEATURE_MANIFEST,
    LIBRARY_MANIFEST,
    MARGINAL_RESULTS,
    PACKAGE,
    PATH_RESULTS,
    freeze_identity,
    load_json,
    sha256,
    station_records,
    write_json,
)


RESULTS = PACKAGE / "selector-feasibility-results-v1.json"
DECISION = PACKAGE / "a5d1-decision-v1.json"
REPORT = PACKAGE / "feasibility-report.md"


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: finalize-a5d1.py")
    freeze_sha256 = freeze_identity()
    contract = load_json(CONTRACT)
    marginal = load_json(MARGINAL_RESULTS)
    paths = load_json(PATH_RESULTS)
    stations = [row["station_id"] for row in station_records()]
    summaries = []
    selected = None
    for pool_size in contract["pool_sizes"]:
        for algorithm in contract["algorithms"]:
            rows = [
                row
                for row in paths["records"]
                if row["pool_size"] == pool_size and row["algorithm"] == algorithm
            ]
            required = len(stations) * len(contract["path"]["path_seeds"])
            passed = len(rows) == required and all(row["path_pass"] for row in rows)
            summaries.append(
                {
                    "pool_size": pool_size,
                    "algorithm": algorithm,
                    "required_cells": required,
                    "actual_cells": len(rows),
                    "pass_cells": sum(row["path_pass"] for row in rows),
                    "all_station_seed_pass": passed,
                    "failure_counts": dict(
                        sorted(collections.Counter(row["first_failed_criterion"] for row in rows if not row["path_pass"]).items())
                    ),
                }
            )
            if selected is None and passed:
                selected = {"pool_size": pool_size, "algorithm": algorithm}
    marginal_by_pool = []
    for pool_size in contract["pool_sizes"]:
        rows = [row for row in marginal["records"] if row["pool_size"] == pool_size]
        marginal_by_pool.append(
            {
                "pool_size": pool_size,
                "station_count": len(rows),
                "pass_count": sum(row["marginal_pass"] for row in rows),
                "all_station_pass": len(rows) == len(stations) and all(row["marginal_pass"] for row in rows),
                "failure_counts": dict(
                    sorted(collections.Counter(row["first_failed_criterion"] for row in rows if not row["marginal_pass"]).items())
                ),
            }
        )
    if selected is not None:
        terminal_status = "EXECUTED-COMPLETE"
        structural_decision = "STRUCTURALLY-FEASIBLE"
        first_corrective_action = None
    elif not any(row["all_station_pass"] for row in marginal_by_pool):
        terminal_status = "EXECUTED-HOLD-STRUCTURAL-INFEASIBILITY"
        structural_decision = "HOLD"
        first_corrective_action = (
            "A5d1a must diagnose which frozen station-surface or annual-marginal constraints "
            "exclude a common pool before any selector-family expansion or tolerance change."
        )
    else:
        terminal_status = "EXECUTED-HOLD-PATH-INFEASIBILITY"
        structural_decision = "HOLD"
        first_corrective_action = (
            "A5d1b must diagnose the first common finite-path failure under the frozen "
            "marginal weights before introducing another path algorithm."
        )
    results = {
        "selector_feasibility_results_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "station_count": len(stations),
        "station_ids": stations,
        "expected_matrix_cells": 306,
        "actual_matrix_cells": paths["actual_cell_count"],
        "unique_matrix_cells": paths["unique_cell_count"],
        "marginal_by_pool": marginal_by_pool,
        "path_by_global_contract": summaries,
        "selected_global_contract": selected,
        "terminal_status": terminal_status,
        "structural_decision": structural_decision,
        "first_corrective_action": first_corrective_action,
        "evidence": {
            "contract_sha256": sha256(CONTRACT),
            "library_manifest_sha256": sha256(LIBRARY_MANIFEST),
            "feature_manifest_sha256": sha256(FEATURE_MANIFEST),
            "marginal_results_sha256": sha256(MARGINAL_RESULTS),
            "path_results_sha256": sha256(PATH_RESULTS),
        },
    }
    write_json(RESULTS, results)
    decision = {
        "a5d1_decision_schema_version": 1,
        "decision": structural_decision,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "terminal_status": terminal_status,
        "selected_global_contract": selected,
        "first_corrective_action": first_corrective_action,
        "confirmation_authorized": False,
        "public_candidate_authorized": False,
        "a5d2_required": True,
        "a5d3_required": True,
        "a5d4_required": True,
        "results_sha256": sha256(RESULTS),
    }
    write_json(DECISION, decision)
    lines = [
        "# A5d1 Selector Feasibility Report",
        "",
        f"Decision: `{structural_decision}`  ",
        f"Terminal status: `{terminal_status}`",
        "",
        "## Question and boundary",
        "",
        "This development-only experiment asked whether one prospectively frozen, bounded complete-year selector contract can satisfy the marginal and finite-path requirements at all 17 exposed stations. It did not inspect confirmation data, mutate daily physical values, change faithful generation, or authorize a public candidate.",
        "",
        "## Methods",
        "",
        "A single burn-0 256-year `faithful_5_32_3 + qc_filter: off` library was regenerated twice per station. Nested 128- and 256-year prefixes supplied complete blocks. Binary64 HiGHS linear programs selected nonnegative weights under fitted monthly and uniform-library preservation constraints while fixing annual means and minimizing normalized distance to six centered detrended-Daymet variance/covariance targets. Three bounded path algorithms and three fixed seeds constructed 100-year paths; every 30-year result was its exact prefix. Finite-prefix preservation combines realized January 1 transition pairs with within-block January counts; dependence, calendar, reuse/cooldown, directional boundary/spell behavior, physical-row identity, and resource invariants were replayed independently.",
        "",
        "## Marginal results",
        "",
        "| Pool | Passing stations | All 17 |",
        "|---:|---:|:---:|",
    ]
    for row in marginal_by_pool:
        lines.append(f"| {row['pool_size']} | {row['pass_count']}/17 | {'yes' if row['all_station_pass'] else 'no'} |")
    lines.extend(
        [
            "",
            "## Finite-path results",
            "",
            "| Pool | Algorithm | Passing station-seed cells | All 51 |",
            "|---:|---|---:|:---:|",
        ]
    )
    for row in summaries:
        lines.append(
            f"| {row['pool_size']} | `{row['algorithm']}` | {row['pass_cells']}/{row['required_cells']} | "
            f"{'yes' if row['all_station_seed_pass'] else 'no'} |"
        )
    lines.extend(["", "## Conclusion", ""])
    if selected:
        lines.append(
            f"The first globally eligible contract is pool {selected['pool_size']} with `{selected['algorithm']}`. This is structural development evidence only; A5d2, A5d3, and A5d4 remain mandatory."
        )
    else:
        lines.append(
            f"No global contract passed. {first_corrective_action} The frozen rules were not relaxed after outcomes were opened."
        )
    lines.extend(
        [
            "",
            "## Evidence identities",
            "",
            f"- Pre-solver freeze: `{freeze_sha256}`",
            f"- Result record: `{sha256(RESULTS)}`",
            f"- Full path matrix: `{sha256(PATH_RESULTS)}` (published aggregate; detailed records retained in the LFS evidence archive)",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"A5d1 decision: {terminal_status} / {structural_decision}")


if __name__ == "__main__":
    main()
