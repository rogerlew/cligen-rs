#!/usr/bin/env python3
"""Verify frozen R0 science dependencies at source and after materialization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
MANIFEST = PACKAGE / "artifacts/science-dependency-identities.json"
MANIFEST_BYTES = 3428
MANIFEST_SHA256 = "4c5669c87aa4263fd16c76e20044ae3d865df6665f86d2c2b40868d68788d887"
DEPENDENCY_NAMES = {
    "a10-daymet-calendar-profile-v1.json",
    "candidate_experiment.py",
    "climate_core.py",
    "legacy_core.py",
    "materialize_controls.py",
    "portfolio-contract.json",
    "portfolio_core.py",
    "reconstruction-contract.json",
    "residual_core.py",
    "screen_core_v2.py",
    "select_portfolio.py",
    "train.py",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"required identity target absent: {path}")
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def load_manifest() -> dict[str, Any]:
    if identity(MANIFEST) != {"bytes": MANIFEST_BYTES, "sha256": MANIFEST_SHA256}:
        raise RuntimeError("science dependency identity manifest byte drift")
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (
        document.get("schema_version") != 1
        or document.get("package_id")
        != "20260719-a10m5r10r1-candidate-job-local-capacity-remedy"
        or document.get("predecessor_package_id")
        != "20260719-a10m5r10-parallel-architecture-portfolio"
        or document.get("predecessor_source_commit")
        != "cbf73d781df09f466d66e31d2569ca19ffaa0faf"
        or set(document.get("dependencies", {})) != DEPENDENCY_NAMES
    ):
        raise RuntimeError("science dependency identity manifest semantic drift")
    return document


def verify_expected(actual: dict[str, Any], expected: dict[str, Any], name: str) -> None:
    frozen = {"bytes": expected["bytes"], "sha256": expected["sha256"]}
    if actual != frozen:
        raise RuntimeError(f"science dependency byte drift: {name}: {actual}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path)
    options = parser.parse_args()
    document = load_manifest()
    repo_root = REPO.resolve()
    source_results = {}
    for name, expected in document["dependencies"].items():
        source = (REPO / expected["source_path"]).resolve()
        if not source.is_relative_to(repo_root):
            raise RuntimeError(f"science source escapes repository: {name}")
        actual = identity(source)
        verify_expected(actual, expected, name)
        source_results[name] = actual

    asset_results = None
    if options.asset_root is not None:
        root = options.asset_root.resolve()
        copied_manifest = identity(root / MANIFEST.name)
        verify_expected(
            copied_manifest,
            {"bytes": MANIFEST_BYTES, "sha256": MANIFEST_SHA256},
            MANIFEST.name,
        )
        copied_document = json.loads(
            (root / MANIFEST.name).read_text(encoding="utf-8")
        )
        if copied_document != document:
            raise RuntimeError("copied science dependency manifest semantic drift")
        asset_results = {}
        for name, expected in document["dependencies"].items():
            actual = identity(root / name)
            verify_expected(actual, expected, name)
            asset_results[name] = actual
        asset_manifest = json.loads(
            (root / "asset-manifest.json").read_text(encoding="utf-8")
        )
        for name, actual in {**asset_results, MANIFEST.name: copied_manifest}.items():
            if asset_manifest.get("assets", {}).get(name) != actual:
                raise RuntimeError(f"asset manifest science identity drift: {name}")
        recorded = asset_manifest.get("science_dependency_identities")
        if recorded != {
            "dependencies": document["dependencies"],
            "manifest": copied_manifest,
        }:
            raise RuntimeError("asset manifest science dependency record drift")

    print(json.dumps({
        "asset_root_verified": options.asset_root is not None,
        "dependency_count": len(source_results),
        "manifest": {"bytes": MANIFEST_BYTES, "sha256": MANIFEST_SHA256},
        "predecessor_source_commit": document["predecessor_source_commit"],
        "schema_version": 1,
        "valid": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
