#!/usr/bin/env python3
"""Verify the committed A10M5R10R1R4 portfolio result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
EXPECTED_RETAINED = [
    "annual_monthly_residual_adapter-k1",
    "monthly_residual_adapter-k2",
    "annual_monthly_residual_adapter-k2",
]
EXPECTED_ELIGIBLE = {
    "annual_monthly_residual_adapter-k1",
    "annual_monthly_residual_adapter-k2",
    "hierarchical_joint_factor_adapter-k2",
    "monthly_residual_adapter-k2",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    artifacts = PACKAGE / "artifacts"
    summary = read_json(artifacts / "operational-summary.json")
    comparison = read_json(artifacts / "portfolio-summary.json")
    decision = read_json(artifacts / "portfolio-decision.json")
    pareto = read_json(artifacts / "portfolio-pareto.json")
    selection_evidence = read_json(artifacts / "portfolio-selection-evidence.json")
    collection = read_json(artifacts / "toolkit-recovered" / "collection.json")
    cleanup = read_json(artifacts / "toolkit-recovered" / "cleanup.json")
    terminal = read_json(artifacts / "toolkit-recovered" / "terminal.json")

    require(summary["terminal"] == "A10M5R10-PORTFOLIO-READY", "terminal drift")
    require(comparison["configuration_count"] == 10, "configuration count drift")
    require(comparison["protected_roles_opened"] == [], "protected role opened")
    require(decision["retained_configuration_ids"] == EXPECTED_RETAINED, "retained set drift")
    require(set(decision["eligible_configuration_ids"]) == EXPECTED_ELIGIBLE, "eligible set drift")
    require(decision["eligible_configuration_ids"] == decision["nondominated_configuration_ids"], "Pareto drift")
    require(pareto["decision"] == decision, "Pareto decision mismatch")
    require(selection_evidence["scientific_decision"] == decision, "selection evidence mismatch")
    require(all(selection_evidence["gates"].values()), "selection gate failed")
    require(selection_evidence["protected_roles_opened"] == [], "selection opened protected role")

    rows = {row["configuration_id"]: row for row in comparison["configurations"]}
    require(
        {name.replace("_", "-") for name in rows}
        == {row["role_id"] for row in comparison["role_inputs"]},
        "role matrix drift",
    )
    require(all(rows[name]["eligible"] for name in EXPECTED_ELIGIBLE), "eligible row drift")
    require(not rows["physics_conditioned_hierarchical_adapter-k1"]["eligible"], "physics K1 drift")
    require(not rows["physics_conditioned_hierarchical_adapter-k2"]["eligible"], "physics K2 drift")
    require(
        rows["physics_conditioned_hierarchical_adapter-k1"]["eligibility_gates"]["solar_each_block_non_degradation"] is False,
        "physics K1 solar guard drift",
    )
    require(
        rows["physics_conditioned_hierarchical_adapter-k2"]["eligibility_gates"]["solar_each_block_non_degradation"] is False,
        "physics K2 solar guard drift",
    )
    require(sum(job["actual_gpu_minutes"] for job in summary["execution"]["jobs"]) == 396, "accounting drift")
    require(len(summary["execution"]["jobs"]) == 11, "attempt count drift")
    require(summary["confirmation"]["protected_roles_opened"] == [], "confirmation firewall drift")

    hashes = summary["science"]["selector_output_sha256"]
    for filename, expected in hashes.items():
        require(digest(artifacts / filename) == expected, f"{filename} identity drift")
    require(collection["sha256"] == summary["preserved_evidence"]["archive_sha256"], "archive drift")
    require(len(collection["present"]) == 153 and collection["absent"] == [], "collection completeness drift")
    require(cleanup["remote_absent"] is True, "remote root remains")
    require(cleanup["job_local_cleanup"] == "verified_absent", "job-local cleanup drift")
    require(terminal["terminal"] == "LEMHI-TOOLKIT-RUN-CLOSED", "toolkit not closed")
    require(terminal["attempt_count"] == 11, "terminal attempt count drift")
    print("A10M5R10R1R4-PORTFOLIO-RESULT-VERIFIED")


if __name__ == "__main__":
    main()
