#!/usr/bin/env python3
"""Fail-closed structural verifier for executed A10M5R4R1 evidence."""

from __future__ import annotations

import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]


def load(name: str) -> dict:
    return json.loads((PACKAGE / "artifacts" / name).read_text(encoding="utf-8"))


def main() -> None:
    package = (PACKAGE / "package.md").read_text(encoding="utf-8")
    assert "Status: `EXECUTED-COMPLETE`" in package
    assert "A10M5R4R1-STOCHASTIC-PRISM-READY" in package

    bundle = load("prism-bundle-manifest.json")
    embedded = json.loads(
        (REPO / "crates/cligen/src/prism/distribution.json").read_text(encoding="utf-8")
    )
    assert bundle["bundle_id"] == embedded["bundle_id"]
    assert bundle["version"] == embedded["version"]
    assert bundle["runtime"]["sha256"] == embedded["runtime_archive"]["sha256"]
    assert bundle["source"]["sha256"] == embedded["source_archive"]["sha256"]
    assert bundle["runtime"]["grid_manifest_sha256"] == embedded["grid_manifest_sha256"]
    assert bundle["source"]["source_manifest_sha256"] == embedded["source_manifest_sha256"]
    assert bundle["source"]["official_archive_count"] == 36
    assert bundle["reproducibility"]["independent_second_build_byte_identical"] is True

    contract = load("monte-carlo-contract.json")
    result = load("monte-carlo-result.json")
    assert contract["frozen_before_execution"] is True
    assert result["decision"] == "PASS"
    assert result["maxima"]["precipitation_relative_error"] <= contract["gates"]["each_month_precipitation_relative_error_max"]
    assert result["maxima"]["tmax_absolute_error_c"] <= contract["gates"]["each_month_tmax_absolute_error_c_max"]
    assert result["maxima"]["tmin_absolute_error_c"] <= contract["gates"]["each_month_tmin_absolute_error_c_max"]

    for module in ("grid.rs", "localize.rs", "run.rs", "sync.rs"):
        assert (REPO / "crates/cligen/src/prism" / module).is_file()
    cli = (REPO / "crates/cligen/src/bin/cligen.rs").read_text(encoding="utf-8")
    for command in ("PrismCommand::Sync", "PrismCommand::Query", "PrismCommand::Run"):
        assert command in cli
    print("A10M5R4R1-STOCHASTIC-PRISM-READY")


if __name__ == "__main__":
    main()
