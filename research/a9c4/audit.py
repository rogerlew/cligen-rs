"""Freeze A9c4 evidence availability before corrected candidate output."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.a9c.models import load_daymet, simulate
from research.a9c3.experiment import (
    faithful_rows,
    objective_features,
    prefix,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/work-packages/20260715-a9c4-context-support-completeness"
ARTIFACTS = PACKAGE / "artifacts"
DESIGN = ARTIFACTS / "design-freeze-v1.json"
PREDECESSOR = ARTIFACTS / "predecessor-manifest-v1.json"
AUDIT = ARTIFACTS / "availability-audit-v1.json"
MASK = ARTIFACTS / "evidence-mask-v1.json"
A9A = ROOT / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts"
A9C3 = ROOT / "docs/work-packages/20260715-a9c3-two-site-grouped-observed-comparison/artifacts"
OBJECTIVES = A9A / "objective-registry-v1.json"
A9C3_EVALUATION = A9C3 / "evaluation-v1.json"
A9C3_FITS = A9C3 / "fit-execution-v1.json"
ARCHIVE = (
    ROOT
    / "docs/work-packages/20260715-a8a-dry-regime-applicability/artifacts/selected-parameters-v1.tar.gz"
)
A9C3_SOURCE_COMMIT = "a0e24f0866f4536c168bfd809cb957d91e6d8bf3"


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(canonical_bytes(value))


def verify_predecessors() -> None:
    for row in load(PREDECESSOR)["files"]:
        path = ROOT / row["path"]
        if not path.is_file() or sha256(path) != row["sha256"]:
            raise RuntimeError(f"HOLD-A9C4-PREDECESSOR-INTEGRITY: {row['path']}")
    if subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            A9C3_SOURCE_COMMIT,
            "--",
            "Cargo.toml",
            "Cargo.lock",
            "crates",
        ],
        cwd=ROOT,
        check=False,
    ).returncode:
        raise RuntimeError("HOLD-A9C4-PREDECESSOR-INTEGRITY: faithful source drift")


def applicable_cells() -> tuple[list[dict[str, str]], dict[str, dict[str, Any]]]:
    registry = {
        row["id"]: row
        for row in load(OBJECTIVES)["objectives"]
        if row["selection_role"] == "mandatory"
    }
    design = load(A9C3 / "design-freeze-v1.json")
    strata_sites: dict[str, list[str]] = defaultdict(list)
    for stratum, sites in design["grouped_storm_amendment"][
        "generated_contributors"
    ].items():
        strata_sites[stratum].extend(sites)
    cells = []
    for objective_id, definition in registry.items():
        for stratum in sorted(strata_sites):
            if definition["family"] == "winter_proxy" and stratum != "cold":
                continue
            cells.append(
                {
                    "family": definition["family"],
                    "objective_id": objective_id,
                    "stratum": stratum,
                }
            )
    return cells, dict(strata_sites)


def available(features: dict[str, dict[str, Any]], objective_id: str) -> bool:
    row = features[objective_id]
    return bool(row["available"])


def historical_expected() -> dict[tuple[str, str, str], str]:
    short = next(
        row
        for row in load(A9C3_EVALUATION)["stages"]
        if row["stage"] == "short_screen"
    )
    return {
        (
            result["configuration_id"],
            row["objective_id"],
            row["stratum"],
        ): row["status"]
        for result in short["results"]
        for row in result["objective_rows"]
        if row["selection_role"] == "mandatory"
    }


def build_faithful() -> tuple[Path, Path, dict[str, Any]]:
    target = Path(tempfile.mkdtemp(prefix="a9c4-audit-build-"))
    command = [
        "cargo",
        "build",
        "--release",
        "--locked",
        "--bin",
        "cligen",
        "--target-dir",
        str(target),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    binary = target / "release/cligen"
    if not binary.is_file():
        raise RuntimeError("HOLD-A9C4-PREDECESSOR-INTEGRITY: missing binary")
    provenance = {
        "binary_sha256": sha256(binary),
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
        "cargo_version": subprocess.check_output(
            ["cargo", "--version"], text=True
        ).strip(),
        "rustc_version": subprocess.check_output(
            ["rustc", "--version"], text=True
        ).strip(),
        "source_commit": A9C3_SOURCE_COMMIT,
        "source_tree_matches_commit": True,
    }
    return binary, target, provenance


def nonstorm_availability(
    cells: list[dict[str, str]], strata_sites: dict[str, list[str]]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    design = load(DESIGN)
    burns = design["evidence_completeness"]["audit_burns"]
    horizon = int(design["evidence_completeness"]["audit_horizon_years"])
    observed_payload = load_daymet("development")
    observed = {
        site: objective_features(payload["records"])
        for site, payload in observed_payload.items()
    }
    binary, target, provenance = build_faithful()
    faithful: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="a9c4-audit-faithful-") as raw:
            directory = Path(raw)
            with tarfile.open(ARCHIVE, "r:gz") as stream:
                stream.extractall(directory, filter="data")
            for sites in strata_sites.values():
                for site in sites:
                    par = directory / f"station-parameters/{site}.par"
                    for burn in burns:
                        rows, _ = faithful_rows(
                            binary, par, site, int(burn), directory, suffix="audit"
                        )
                        faithful[(site, int(burn))] = objective_features(
                            prefix(rows, horizon)
                        )
    finally:
        shutil.rmtree(target)

    fits = [
        load(ROOT / row["detail_path"])
        for row in load(A9C3_FITS)["fits"]
        if row["fit_status"] == "fit_valid"
    ]
    candidate: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = {}
    for fit in fits:
        identifier = fit["configuration"]["configuration_id"]
        for sites in strata_sites.values():
            for site in sites:
                for burn in burns:
                    rows = simulate(fit, site, int(burn), years=horizon)
                    candidate[(identifier, site, int(burn))] = objective_features(rows)
    return observed, faithful, {
        "features": candidate,
        "fit_ids": [fit["configuration"]["configuration_id"] for fit in fits],
        "faithful_build": provenance,
    }


def write_mask(rows: list[dict[str, Any]]) -> dict[str, Any]:
    retained = [row for row in rows if row["retained_in_candidate_blind_mask"]]
    excluded = [row for row in rows if not row["retained_in_candidate_blind_mask"]]
    applicable_family_strata = {
        (row["family"], row["stratum"]) for row in rows
    }
    retained_family_strata = {
        (row["family"], row["stratum"]) for row in retained
    }
    missing_breadth = sorted(applicable_family_strata - retained_family_strata)
    design = load(DESIGN)
    mask = {
        "audit_sha256": sha256(AUDIT),
        "breadth_guard": {
            "missing_family_strata": [
                {"family": family, "stratum": stratum}
                for family, stratum in missing_breadth
            ],
            "status": "pass" if not missing_breadth else "fail",
        },
        "candidate_inputs_used": False,
        "excluded_cells": [
            {
                "family": row["family"],
                "horizon_years": row["horizon_years"],
                "objective_id": row["objective_id"],
                "role": row["prospective_role"],
                "stratum": row["stratum"],
            }
            for row in excluded
        ],
        "mask_rule": design["evidence_completeness"]["prospective_mask_rule"],
        "retained_cells": [
            {
                "family": row["family"],
                "horizon_years": row["horizon_years"],
                "objective_id": row["objective_id"],
                "role": row["prospective_role"],
                "stratum": row["stratum"],
            }
            for row in retained
        ],
        "schema_version": 1,
        "status": "pass" if not missing_breadth else "hold",
        "terminal_if_hold": (
            None if not missing_breadth else "HOLD-A9C4-COMPLETENESS-SURFACE"
        ),
    }
    write_once(MASK, mask)
    return mask


def main() -> None:
    if MASK.exists():
        raise FileExistsError("A9c4 evidence mask already exists")
    if AUDIT.exists():
        audit = load(AUDIT)
        mask = write_mask(audit["cells"])
        print(
            f"A9c4 audit closeout: {audit['source_specific_cell_count']} mandatory "
            f"cells; {audit['retained_cell_count']} retained; "
            f"{audit['excluded_cell_count']} report-only; "
            f"breadth={mask['breadth_guard']['status']}"
        )
        return
    started = time.monotonic()
    verify_predecessors()
    cells, strata_sites = applicable_cells()
    observed, faithful, historical = nonstorm_availability(cells, strata_sites)
    candidate = historical.pop("features")
    expected = historical_expected()
    design = load(DESIGN)
    burns = [int(value) for value in design["evidence_completeness"]["audit_burns"]]
    horizon = int(design["evidence_completeness"]["audit_horizon_years"])
    rows = []
    mismatch = []
    for cell in cells:
        objective_id = cell["objective_id"]
        stratum = cell["stratum"]
        sites = sorted(strata_sites[stratum])
        if cell["family"] == "storm_descriptor":
            observed_sites = sorted(
                load(A9C3 / "design-freeze-v1.json")["grouped_storm_amendment"]
                ["observed_contributors"][stratum]
            )
            faithful_sites = sites
            historical_counts = {
                identifier: len(sites) for identifier in historical["fit_ids"]
            }
            expected_statuses = {
                identifier: expected[(identifier, objective_id, stratum)]
                for identifier in historical["fit_ids"]
            }
        else:
            observed_sites = [
                site for site in sites if available(observed[site], objective_id)
            ]
            faithful_sites = [
                site
                for site in sites
                if site in observed_sites
                and all(
                    available(faithful[(site, burn)], objective_id) for burn in burns
                )
            ]
            historical_counts = {}
            expected_statuses = {}
            for identifier in historical["fit_ids"]:
                joint_sites = {
                    site
                    for site in sites
                    for burn in burns
                    if site in observed_sites
                    and available(faithful[(site, burn)], objective_id)
                    and available(candidate[(identifier, site, burn)], objective_id)
                }
                historical_counts[identifier] = len(joint_sites)
                reproduced = "available" if len(joint_sites) >= 2 else "unavailable"
                expected_statuses[identifier] = expected[
                    (identifier, objective_id, stratum)
                ]
                if reproduced != expected_statuses[identifier]:
                    mismatch.append(
                        {
                            "configuration_id": identifier,
                            "expected": expected_statuses[identifier],
                            "objective_id": objective_id,
                            "reproduced": reproduced,
                            "stratum": stratum,
                        }
                    )
        retained = len(faithful_sites) >= int(
            design["evidence_completeness"]["minimum_common_station_contributors"]
        )
        rows.append(
            {
                **cell,
                "historical_a9c3_joint_available_station_count": historical_counts,
                "historical_a9c3_status": expected_statuses,
                "horizon_years": horizon,
                "observed_available_station_count": len(observed_sites),
                "observed_available_stations": observed_sites,
                "prospective_role": "mandatory" if retained else "report_only_not_evaluated",
                "retained_in_candidate_blind_mask": retained,
                "faithful_all_burn_available_station_count": len(faithful_sites),
                "faithful_all_burn_available_stations": faithful_sites,
            }
        )

    retained = [row for row in rows if row["retained_in_candidate_blind_mask"]]
    excluded = [row for row in rows if not row["retained_in_candidate_blind_mask"]]
    applicable_family_strata = {
        (row["family"], row["stratum"]) for row in rows
    }
    retained_family_strata = {
        (row["family"], row["stratum"]) for row in retained
    }
    missing_breadth = sorted(applicable_family_strata - retained_family_strata)
    if mismatch:
        raise RuntimeError(
            f"HOLD-A9C4-PREDECESSOR-INTEGRITY: {len(mismatch)} A9c3 status mismatches"
        )
    audit = {
        "a9c3_status_reproduction": {
            "mismatch_count": 0,
            "status": "pass",
        },
        "candidate_blind_mask_inputs": ["observed", "faithful"],
        "cells": rows,
        "design_freeze_sha256": sha256(DESIGN),
        "excluded_cell_count": len(excluded),
        "historical_candidate_count": len(historical["fit_ids"]),
        "historical_candidate_role": "diagnostic_only",
        "predecessor_manifest_sha256": sha256(PREDECESSOR),
        "retained_cell_count": len(retained),
        "schema_version": 1,
        "source_specific_cell_count": len(rows),
        "wall_seconds": time.monotonic() - started,
        **historical,
    }
    write_once(AUDIT, audit)
    mask = write_mask(rows)
    print(
        f"A9c4 audit: {len(rows)} mandatory cells; {len(retained)} retained; "
        f"{len(excluded)} report-only; breadth={mask['breadth_guard']['status']}"
    )


if __name__ == "__main__":
    main()
