#!/usr/bin/env python3
"""Bind live assets to the immutable canonical-v2 candidate."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from research.a10.lemhi_toolkit.core import canonical_bytes, read_json, sha256_bytes, sha256_file


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"exact candidate asset firewall: FAIL: {detail}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    options = parser.parse_args()
    candidate = read_json(ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json")
    semantic = candidate.pop("configuration_semantic_sha256")
    require(semantic == sha256_bytes(canonical_bytes(candidate)), "semantic hash")
    expected = {
        "runtime.tar.gz": (candidate["runtime"]["artifact_bytes"], candidate["runtime"]["artifact_sha256"]),
        "wheelhouse.tar": (candidate["framework"]["wheelhouse_bytes"], candidate["framework"]["wheelhouse_sha256"]),
        "requirements.lock": (2676, candidate["framework"]["requirements_lock_sha256"]),
        "wheel-manifest.json": (7267, candidate["framework"]["wheel_manifest_sha256"]),
        "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz": (candidate["toolchain"]["rust_archive_bytes"], candidate["toolchain"]["rust_archive_sha256"]),
        "cargo-vendor.tar.gz": (candidate["toolchain"]["vendor_archive_bytes"], candidate["toolchain"]["vendor_archive_sha256"]),
    }
    for name, (size, digest) in expected.items():
        path = options.asset_root / name
        require(path.is_file() and path.stat().st_size == size, f"{name} bytes")
        require(sha256_file(path) == digest, f"{name} sha256")
    print(f"exact candidate asset firewall: PASS candidate={semantic}")


if __name__ == "__main__":
    main()
