#!/usr/bin/env python3
"""Exercise exact R14 inheritance and published R14R1 overlays."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

package = Path(__file__).resolve().parents[1]
path = package / "artifacts/jobs/prepare_assets.py"
spec = importlib.util.spec_from_file_location("r14r1_prepare", path)
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

operational = (
    "admission_checker.py",
    "setup_diagnostics.py",
    "job-control-materialization.sh",
    "job-common-candidate.sh",
    "run_temporal_candidate.sh",
    "run_control.sh",
    "temporal_select.py",
    "continuous_candidate_experiment.py",
)
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    parent, output = root / "parent", root / "output"
    parent.mkdir()
    for name in operational:
        (parent / name).write_text(
            prepare.PARENT_PACKAGE
            + "\n"
            + "a10m5r14-continuous-distribution-head-factorial-r0\n"
            + "a10m5r14-submission-admission\n",
            encoding="utf-8",
        )
    (parent / "science.bin").write_bytes(b"byte-identical-r14-science")
    admissions = parent / "controller-admissions"
    admissions.mkdir()
    (admissions / "stale.json").write_text("{}", encoding="utf-8")
    assets = {
        item.name: prepare.identity(item)
        for item in parent.iterdir()
        if item.is_file()
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
    result = prepare.prepare(
        parent,
        package,
        "f" * 40,
        output,
        require_published=False,
        expected_parent_manifest_sha256=prepare.digest(manifest_path),
    )
    if any((output / "controller-admissions").iterdir()):
        raise RuntimeError("copied R14 admissions survived preparation")
    if (output / "science.bin").read_bytes() != b"byte-identical-r14-science":
        raise RuntimeError("R14 science changed during operational preparation")
    published_checker = package / "artifacts/jobs/admission_checker.py"
    if (output / "admission_checker.py").read_bytes() != published_checker.read_bytes():
        raise RuntimeError("prepared checker differs from published R14R1 source")
    for name in operational[1:]:
        text = (output / name).read_text(encoding="utf-8")
        if prepare.PACKAGE_ID not in text or prepare.RUN_ID not in text:
            raise RuntimeError(f"fresh operational identity absent: {name}")
    if result["package_id"] != prepare.PACKAGE_ID or result["source_commit"] != "f" * 40:
        raise RuntimeError("fresh prepared manifest identity drift")
    for name in (
        "admission_checker.py",
        "build_control_records.py",
        "job-local-capacity-contract.json",
        "materialize_admission.py",
    ):
        if not isinstance(result["assets"][name].get("source_path"), str):
            raise RuntimeError(f"published overlay source mapping absent: {name}")

    (parent / "science.bin").write_bytes(b"drift")
    try:
        prepare.verify_parent_assets(
            parent, expected_manifest_sha256=prepare.digest(manifest_path)
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("R14 parent byte drift was accepted")

print("A10M5R14R1-PREPARE-ASSETS-TEST-PASS")
