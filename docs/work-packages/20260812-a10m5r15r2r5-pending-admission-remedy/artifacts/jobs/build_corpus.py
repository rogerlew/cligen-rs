#!/usr/bin/env python3
"""Build the deterministic A10M5R15R1 offline corpus archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
R1 = PACKAGE.parent / "20260721-a10m5r15r1-prism-eligible-cohort"
CONTRACT = PACKAGE / "artifacts/execution-contract.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def tar_info(path: Path, name: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = path.stat().st_size
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    return info


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    options = parser.parse_args()
    if options.output.exists() or options.receipt.exists():
        raise RuntimeError("fresh corpus archive and receipt paths required")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    pins = contract["corpus"]
    paths = {
        "build_receipt_sha256": R1 / "artifacts/cohort-build-receipt.json",
        "normalized_manifest_sha256": R1 / "artifacts/normalized-manifest-v1.json",
        "normalization_statistics_sha256": R1 / "artifacts/normalization-statistics-v1.json",
        "selection_sha256": R1 / "artifacts/cohort-selection.json",
        "transfer_manifest_sha256": R1 / "artifacts/offline-transfer-manifest-v1.json",
    }
    if any(digest(path) != pins[name] for name, path in paths.items()):
        raise RuntimeError("A10M5R15R1 corpus input identity drift")
    transfer = json.loads(paths["transfer_manifest_sha256"].read_text(encoding="utf-8"))
    if len(transfer["objects"]) != pins["object_count"] or transfer["aggregate_bytes"] != pins["aggregate_bytes"]:
        raise RuntimeError("successor transfer aggregate drift")
    options.output.parent.mkdir(parents=True, exist_ok=True)
    partial = options.output.with_suffix(options.output.suffix + ".part")
    with tarfile.open(partial, "w", format=tarfile.PAX_FORMAT) as archive:
        for record in transfer["objects"]:
            source = REPO / record["path"]
            if source.stat().st_size != record["bytes"] or digest(source) != record["sha256"]:
                raise RuntimeError(f"successor transfer object drift: {record['path']}")
            with source.open("rb") as stream:
                archive.addfile(tar_info(source, f"corpus/{record['path']}"), stream)
        for name in (
            "offline-transfer-manifest-v1.json",
            "normalized-manifest-v1.json",
            "normalization-statistics-v1.json",
        ):
            source = R1 / "artifacts" / name
            with source.open("rb") as stream:
                archive.addfile(tar_info(source, f"corpus/artifacts/{name}"), stream)
    os.replace(partial, options.output)
    receipt = {
        "bytes": options.output.stat().st_size,
        "corpus_terminal": pins["terminal"],
        "member_count": len(transfer["objects"]) + 3,
        "package_id": contract["package_id"],
        "schema_version": "a10m5r15r2-corpus-archive-1",
        "sha256": digest(options.output),
        "valid": True,
    }
    options.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = options.receipt.with_suffix(options.receipt.suffix + ".part")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, options.receipt)
    print(f"A10M5R15R2-CORPUS-ARCHIVE-BUILT {receipt['sha256']}")


if __name__ == "__main__":
    main()
