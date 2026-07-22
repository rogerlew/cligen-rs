#!/usr/bin/env python3
"""Verify the immutable A10M5R15 pre-reservation HOLD evidence."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
SOURCE_COMMIT = "679755627cc19e579dc0d704e11c910df9904a83"
SOURCE = PACKAGE / "artifacts/jobs/build_normal_conditioning.py"
FAILURE = PACKAGE / "artifacts/preflight/normal-conditioning-preflight-failure.json"
TERMINAL = "HOLD-A10M5R15-ENGINEERING-INCOMPLETE"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    published = subprocess.run(
        ("git", "show", f"{SOURCE_COMMIT}:{SOURCE.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    require(SOURCE.read_bytes() == published, "preflight source differs from its published commit")
    value = json.loads(FAILURE.read_text(encoding="utf-8"))
    require(value["schema_version"] == "a10m5r15-normal-conditioning-preflight-failure-1", "failure schema drift")
    require(value["source_commit"] == SOURCE_COMMIT, "failure source commit drift")
    require(value["terminal"] == TERMINAL and value["valid"] is False, "terminal drift")
    require(value["resource_reserved"] is False, "failure record claims resource use")
    require(value["calendar_points_validated"] == 1440, "calendar count drift")
    require(value["corpus_query_count"] == 1440, "corpus query count drift")
    require(value["failure_count"] == 74 == len(value["failures"]), "failure count drift")
    require(value["failed_by_role"] == {"candidate_fit": 60, "fit_validation": 14, "temporal_site": 0}, "role failure counts drift")
    require(
        value["failed_by_regime_role"]
        == {
            "cold/candidate_fit": 19,
            "cold/fit_validation": 3,
            "hot_arid/candidate_fit": 41,
            "hot_arid/fit_validation": 11,
        },
        "regime failure counts drift",
    )
    require(
        value["gates"]
        == {
            "all_calendar_surfaces_valid": True,
            "all_corpus_queries_valid": False,
            "all_temporal_queries_valid": True,
            "containing_cell_only": True,
            "fallback_or_interpolation_used": False,
            "pre_reservation": True,
        },
        "preflight gate matrix drift",
    )
    rows = value["failures"]
    require(len({row["point_id"] for row in rows}) == 74, "failure points are not unique")
    require(
        all(
            row["role"] in ("candidate_fit", "fit_validation")
            and row["regime"] in ("cold", "hot_arid")
            and math.isfinite(row["latitude"])
            and math.isfinite(row["longitude"])
            and "masked PRISM cell" in row["error"]
            for row in rows
        ),
        "failure row semantic drift",
    )
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    disposition = (PACKAGE / "preflight-disposition.md").read_text(encoding="utf-8")
    roadmap = (REPO / "docs/ROADMAP.md").read_text(encoding="utf-8")
    catalog = (REPO / "docs/work-packages/README.md").read_text(encoding="utf-8")
    require(all(TERMINAL in text for text in (package, disposition, roadmap, catalog)), "terminal is not reconciled")
    print("A10M5R15-PREFLIGHT-HOLD-VERIFIED")


if __name__ == "__main__":
    main()
