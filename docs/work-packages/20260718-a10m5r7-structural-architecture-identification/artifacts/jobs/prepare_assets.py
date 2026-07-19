#!/usr/bin/env python3
"""Prepare immutable A10M5R7 Lemhi assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R3 = REPO / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee"
R4 = REPO / "docs/work-packages/20260718-a10m5r4r2-realized-temporal-adjudication"
R4_REMEDY = REPO / "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy"


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
        if not (cache / name).is_file():
            raise RuntimeError(f"canonical asset absent: {name}")

    package_jobs = PACKAGE / "artifacts/jobs"
    generated = [
        "probe.py",
        "run_probe.sh",
        "job-architecture-probe.sh",
    ]
    for name in generated:
        copy(package_jobs / name, root / name)
    copy(R3 / "artifacts/jobs/screen_core_v2.py", root / "screen_core_v2.py")
    copy(R3 / "artifacts/jobs/train.py", root / "train.py")
    copy(
        REPO / "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py",
        root / "legacy_core.py",
    )
    copy(R4 / "artifacts/jobs/temporal_metrics.py", root / "temporal_metrics.py")
    copy(R4 / "artifacts/sites.json", root / "sites.json")
    copy(
        R4_REMEDY / "artifacts/reconstruction-contract.json",
        root / "reconstruction-contract.json",
    )
    copy(PACKAGE / "artifacts/diagnostic-contract.json", root / "diagnostic-contract.json")
    for source_name, target_name in (
        ("recover_job_local_v2.sh", "recover-job-local-v2.sh"),
        ("supervise_v2.sh", "supervise-v2.sh"),
    ):
        copy(REPO / "research/a10/lemhi_toolkit/remote" / source_name, root / target_name)

    recovery = {
        "invoked": False,
        "reason": "the primary job owns supervised job-local cleanup",
    }
    (root / "recovery.json").write_text(
        json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    generated.extend(
        [
            "screen_core_v2.py",
            "train.py",
            "legacy_core.py",
            "temporal_metrics.py",
            "sites.json",
            "reconstruction-contract.json",
            "diagnostic-contract.json",
            "recover-job-local-v2.sh",
            "supervise-v2.sh",
            "recovery.json",
        ]
    )
    for name in generated:
        if name.endswith((".sh", ".py")):
            (root / name).chmod(0o700)

    assets = {name: identity(cache / name) for name in canonical}
    assets.update({name: identity(root / name) for name in generated})
    manifest = {
        "assets": assets,
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
