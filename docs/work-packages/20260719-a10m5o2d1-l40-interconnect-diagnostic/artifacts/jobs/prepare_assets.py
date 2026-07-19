#!/usr/bin/env python3
"""Prepare immutable A10M5O2D1 canonical topology assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]


def identity(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


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
    root.mkdir(parents=True, exist_ok=True)
    canonical = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock")
    for name in canonical:
        copy(options.canonical_cache.resolve() / name, root / name)
    generated = ["interconnect.py", "merge_results.py", "run-diagnostic.sh", "job-common.sh"]
    for name in generated:
        copy(PACKAGE / "artifacts/jobs" / name, root / name)
    for source_name, target_name in (
        ("recover_job_local_v2.sh", "recover-job-local-v2.sh"),
        ("supervise_v2.sh", "supervise-v2.sh"),
    ):
        copy(REPO / "research/a10/lemhi_toolkit/remote" / source_name, root / target_name)
        generated.append(target_name)
    (root / "job-interconnect-diagnostic.sh").write_text(
        "#!/bin/sh\nset -eu\nexec ./job-common.sh\n", encoding="utf-8"
    )
    generated.append("job-interconnect-diagnostic.sh")
    (root / "recovery.json").write_text(
        json.dumps({"invoked": False, "reason": "primary supervisor owns job-local cleanup"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
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
