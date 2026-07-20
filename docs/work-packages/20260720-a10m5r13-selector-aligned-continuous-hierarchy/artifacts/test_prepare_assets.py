#!/usr/bin/env python3
"""Reject parent asset roster and byte drift before any R13 overlay."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

package = Path(__file__).resolve().parents[1]
repo = package.parents[2]
path = package / "artifacts/jobs/prepare_assets.py"
spec = importlib.util.spec_from_file_location("r13_prepare", path)
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

parent_jobs = repo / "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/jobs"
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    assets = {}
    for name in prepare.EXPECTED:
        shutil.copy2(parent_jobs / name, root / name)
        assets[name] = prepare.identity(root / name)
    manifest = {
        "assets": assets,
        "canonical_configuration_id": "fixture",
        "canonical_configuration_semantic_sha256": "0" * 64,
        "package_id": "20260719-a10m5r12r1-admission-materialization-remedy",
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": "87d38996e1f46ddb47b80c16c9625c16beaede9b",
    }
    (root / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    prepare.verify_parent_assets(root)
    (root / "continuous_core.py").write_bytes(b"drift")
    try:
        prepare.verify_parent_assets(root)
    except RuntimeError:
        pass
    else:
        raise RuntimeError("parent byte drift was accepted")
    (root / "continuous_core.py").unlink()
    try:
        prepare.verify_parent_assets(root)
    except RuntimeError:
        pass
    else:
        raise RuntimeError("parent roster drift was accepted")

source = path.read_text(encoding="utf-8")
if "committed_write(repo, args.source_commit" not in source:
    raise RuntimeError("R13 overlays are not sourced from published git bytes")
if "temporal_select.py" in prepare.EXPECTED:
    raise RuntimeError("selector was incorrectly required from the R12R1 asset tree")
if (
    'source_paths["temporal_select.py"] = parent_selector_relative' not in source
    or 'raise RuntimeError("inherited temporal selector drift")' not in source
):
    raise RuntimeError("published predecessor selector is not authenticated and staged")
print("A10M5R13-PREPARE-ASSETS-TEST-PASS")
