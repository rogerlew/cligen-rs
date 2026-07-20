#!/usr/bin/env python3
"""Behavioral preparation tests including fresh controller materialization."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

package = Path(__file__).resolve().parents[1]
path = package / "artifacts/jobs/prepare_assets.py"
spec = importlib.util.spec_from_file_location("r13r1_prepare", path)
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

operational = (
    "admission_checker.py", "setup_diagnostics.py",
    "job-control-materialization.sh", "job-common-candidate.sh",
    "run_temporal_candidate.sh", "run_control.sh", "temporal_select.py",
    "continuous_candidate_experiment.py",
)
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    parent, output = root / "parent", root / "output"
    parent.mkdir()
    for name in operational:
        (parent / name).write_text(
            "20260720-a10m5r13-selector-aligned-continuous-hierarchy\n"
            "a10m5r13-selector-aligned-continuous-hierarchy-r0\n"
            "a10m5r13-submission-admission\n"
            "A10M5R13-TEMPORAL-READY\n",
            encoding="utf-8",
        )
    (parent / "science.bin").write_bytes(b"identical-r13-science")
    admissions = parent / "controller-admissions"
    admissions.mkdir()
    (admissions / "stale.json").write_text("{}", encoding="utf-8")
    assets = {
        item.name: prepare.identity(item)
        for item in parent.iterdir() if item.is_file()
    }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": "fixture",
        "canonical_configuration_semantic_sha256": "0" * 64,
        "package_id": prepare.PARENT_PACKAGE,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": prepare.PARENT_SOURCE_COMMIT,
    }
    manifest_path = parent / "asset-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest_sha = prepare.digest(manifest_path)
    result = prepare.prepare(
        parent, package, "f" * 40, output, require_published=False,
        expected_parent_manifest_sha256=manifest_sha,
    )
    if any((output / "controller-admissions").iterdir()):
        raise RuntimeError("copied controller admissions survived preparation")
    if (output / "science.bin").read_bytes() != b"identical-r13-science":
        raise RuntimeError("R13 science changed during operational preparation")
    transformed = (output / "admission_checker.py").read_text(encoding="utf-8")
    if (
        prepare.PACKAGE_ID not in transformed
        or prepare.RUN_ID not in transformed
        or "a10m5r13r1-submission-admission" not in transformed
        or "A10M5R13-TEMPORAL-READY" not in transformed
    ):
        raise RuntimeError("R13R1 operational transform/science terminal drift")
    if result["package_id"] != prepare.PACKAGE_ID or result["source_commit"] != "f" * 40:
        raise RuntimeError("R13R1 prepared manifest identity drift")
    if result["assets"]["materialize_admission.py"].get("source_path") is None:
        raise RuntimeError("committed R13R1 controller provenance missing")

    (parent / "science.bin").write_bytes(b"drift")
    try:
        prepare.verify_parent_assets(
            parent, expected_manifest_sha256=manifest_sha
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("real-parent byte drift was accepted")

print("A10M5R13R1-PREPARE-ASSETS-TEST-PASS")
