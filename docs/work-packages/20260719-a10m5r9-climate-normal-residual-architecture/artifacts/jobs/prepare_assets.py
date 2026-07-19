#!/usr/bin/env python3
"""Prepare immutable A10M5R9 Lemhi assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R3 = REPO / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee"
M8 = REPO / "docs/work-packages/20260719-a10m5r8-climate-statistics-objective"
RECONSTRUCTION = REPO / "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy/artifacts/reconstruction-contract.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise RuntimeError(f"required source absent: {source}")
    shutil.copyfile(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--canonical-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve()
    cache = options.canonical_cache.resolve()
    root.mkdir(parents=True, exist_ok=True)
    canonical = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar")
    for name in canonical:
        copy(cache / name, root / name)
    package_jobs = PACKAGE / "artifacts/jobs"
    generated = [
        "residual_core.py",
        "experiment.py",
        "run_experiment.sh",
        "job-climate-normal-residual.sh",
    ]
    for name in generated:
        copy(package_jobs / name, root / name)
    copy(M8 / "artifacts/jobs/climate_core.py", root / "climate_core.py")
    copy(R3 / "artifacts/jobs/screen_core_v2.py", root / "screen_core_v2.py")
    copy(R3 / "artifacts/jobs/train.py", root / "train.py")
    copy(
        REPO / "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py",
        root / "legacy_core.py",
    )
    copy(PACKAGE / "artifacts/architecture-contract.json", root / "architecture-contract.json")
    copy(RECONSTRUCTION, root / "reconstruction-contract.json")
    copy(
        REPO / "docs/specifications/a10-daymet-calendar-profile-v1.json",
        root / "a10-daymet-calendar-profile-v1.json",
    )
    generated.extend(
        [
            "climate_core.py",
            "screen_core_v2.py",
            "train.py",
            "legacy_core.py",
            "architecture-contract.json",
            "reconstruction-contract.json",
            "a10-daymet-calendar-profile-v1.json",
        ]
    )
    for source_name, target_name in (
        ("recover_job_local_v2.sh", "recover-job-local-v2.sh"),
        ("supervise_v2.sh", "supervise-v2.sh"),
    ):
        copy(REPO / "research/a10/lemhi_toolkit/remote" / source_name, root / target_name)
        generated.append(target_name)
    recovery = {"invoked": False, "reason": "the primary job owns supervised job-local cleanup"}
    (root / "recovery.json").write_text(
        json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    generated.append("recovery.json")
    for name in generated:
        if name.endswith((".sh", ".py")):
            (root / name).chmod(0o700)
    manifest = {
        "assets": {name: identity(root / name) for name in (*canonical, *generated)},
        "canonical_configuration_id": "lemhi-a10-py311-l40-v2-candidate",
        "canonical_configuration_semantic_sha256": "5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d",
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": options.source_commit,
    }
    (root / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
