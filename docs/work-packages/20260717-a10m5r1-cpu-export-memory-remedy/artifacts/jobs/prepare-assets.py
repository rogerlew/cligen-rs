#!/usr/bin/env python3
"""Prepare exact A10M5R1 assets around the attested canonical cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--canonical-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    cache = options.canonical_cache.resolve()
    canonical = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock")
    for name in canonical:
        source = cache / name
        if not source.is_file():
            raise RuntimeError(f"canonical cache asset absent: {name}")
    jobs = ("diagnose.py", "diagnose-job.sh", "job-memory-attribution.sh")
    for name in jobs:
        shutil.copyfile(PACKAGE / "artifacts/jobs" / name, root / name)
    for name in ("diagnose-job.sh", "job-memory-attribution.sh"):
        (root / name).chmod(0o700)
    for source_name, target_name in (
        ("recover_job_local_v2.sh", "recover-job-local-v2.sh"),
        ("supervise_v2.sh", "supervise-v2.sh"),
    ):
        shutil.copyfile(REPO / "research/a10/lemhi_toolkit/remote" / source_name, root / target_name)
        (root / target_name).chmod(0o700)
    assets = {name: identity(cache / name) for name in canonical}
    for name in (*jobs, "recover-job-local-v2.sh", "supervise-v2.sh"):
        assets[name] = identity(root / name)
    manifest = {
        "schema_version": 1,
        "source_commit": options.source_commit,
        "assets": assets,
        "canonical_configuration_sha256": "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179",
        "protected_roles_opened": [],
    }
    (root / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
