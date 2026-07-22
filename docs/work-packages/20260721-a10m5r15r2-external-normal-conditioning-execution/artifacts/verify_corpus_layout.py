#!/usr/bin/env python3
"""Verify the exact A10M5R15R1 successor archive and extraction layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
PIN_PATH = PACKAGE / "artifacts/corpus-layout-pin.json"
PIN_BYTES = 866
PIN_SHA256 = "93045d7727a5c0718579ed2222397fb514633f54bec20afd919b61bd6944bc44"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"corpus archive must be a regular nonsymlink file: {path}")
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def load_pin(path: Path = PIN_PATH) -> dict[str, Any]:
    if identity(path) != {"bytes": PIN_BYTES, "sha256": PIN_SHA256}:
        raise RuntimeError("corpus layout pin byte identity drift")
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_layout(archive: Path) -> dict[str, Any]:
    with tarfile.open(archive, "r:") as stream:
        members = stream.getmembers()
    names = [member.name for member in members]
    if len(names) != len(set(names)):
        raise RuntimeError("corpus archive contains duplicate member paths")
    paths = [PurePosixPath(name) for name in names]
    return {
        "member_count": len(members),
        "accepted_object_count": len(members) - 3,
        "all_members_regular": all(member.isfile() for member in members),
        "sole_top_level_prefix": (
            next(iter({path.parts[0] for path in paths}))
            if paths and len({path.parts[0] for path in paths}) == 1
            else None
        ),
        "absolute_paths_allowed": any(path.is_absolute() for path in paths),
        "parent_components_allowed": any(".." in path.parts for path in paths),
        "required_members": sorted(
            name for name in names if name.startswith("corpus/artifacts/")
        ),
    }


def write_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".promote")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--asset-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    pin = load_pin()
    archive_identity = identity(options.archive)
    manifest = json.loads(options.asset_manifest.read_text(encoding="utf-8"))
    layout = inspect_layout(options.archive)
    gates = {
        "archive_identity": archive_identity == pin["archive"],
        "asset_manifest_identity": manifest.get("assets", {}).get("corpus.tar") == pin["archive"],
        "layout_identity": layout == pin["layout"],
        "package_identity": manifest.get("package_id") == pin["package_id"],
    }
    receipt = {
        "archive": archive_identity,
        "gates": gates,
        "layout": layout,
        "package_id": pin["package_id"],
        "schema_version": 1,
        "valid": all(gates.values()),
    }
    if options.output is not None:
        write_atomic(options.output, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    if not receipt["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
