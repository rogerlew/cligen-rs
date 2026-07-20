#!/usr/bin/env python3
"""Authenticate the exact real prepared R13 parent tree."""

from __future__ import annotations

import argparse
import importlib.util
import tempfile
from pathlib import Path

package = Path(__file__).resolve().parents[1]
path = package / "artifacts/jobs/prepare_assets.py"
spec = importlib.util.spec_from_file_location("r13r1_prepare_real", path)
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

parser = argparse.ArgumentParser()
parser.add_argument("--parent-assets", type=Path, required=True)
options = parser.parse_args()
manifest = prepare.verify_parent_assets(options.parent_assets)
if len(manifest["assets"]) != 46:
    raise RuntimeError("real R13 parent asset count drift")
with tempfile.TemporaryDirectory() as scratch:
    output = Path(scratch) / "r13r1-assets"
    prepared = prepare.prepare(
        options.parent_assets, package, "f" * 40, output,
        require_published=False,
    )
    if (
        prepared["package_id"] != prepare.PACKAGE_ID
        or prepared["parent_asset_manifest_sha256"]
        != prepare.PARENT_MANIFEST_SHA256
        or any((output / "controller-admissions").iterdir())
    ):
        raise RuntimeError("real-parent R13R1 preparation identity drift")
    for name in (
        "continuous_core.py", "selector_loss.py", "climate_core.py",
        "portfolio-contract.json", "temporal-contract.json",
    ):
        if prepare.identity(output / name) != {
            key: manifest["assets"][name][key] for key in ("bytes", "sha256")
        }:
            raise RuntimeError(f"real-parent science changed: {name}")
    if (output / "materialize_admission.py").read_bytes() != (
        package / "artifacts/jobs/materialize_admission.py"
    ).read_bytes():
        raise RuntimeError("committed R13R1 admission wrapper was not staged exactly")
print("A10M5R13R1-REAL-PARENT-ASSETS-TEST-PASS")
