#!/usr/bin/env python3
"""Bind the bounded UTF-8 source-parser amendment before daily station access."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
PRIOR_FREEZE_SHA256 = "dd22e50d90db1c49cafa53ad3d54d0fdee486fe7f67e3227685a5881cb9031d5"
STATION_LIST_ARCHIVE_SHA256 = "047a5de7be283a324a0709dbf7a6184a28b5bf5af8c0c446ae1bc33bce7d220b"
STATION_LIST_SOURCE_SHA256 = "fedc8bbe92f9b1eee0a57f8886e5e022965a542efa60710c01b47a838120b18d"
OUTCOMES = (
    "source-manifest-v1.json",
    "a8a-analysis-v1.json",
    "a8a-decision-v1.json",
    "findings.md",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def main() -> None:
    output = ARTIFACTS / "pre-analysis-freeze-v2.json"
    if output.exists() or any((ARTIFACTS / name).exists() for name in OUTCOMES):
        raise SystemExit("refusing to amend after successor freeze or outcome access")
    prior_path = ARTIFACTS / "pre-analysis-freeze-v1.json"
    if sha256(prior_path.read_bytes()) != PRIOR_FREEZE_SHA256:
        raise SystemExit("prior freeze identity mismatch")
    prior = load_json(prior_path)
    amendment_path = ARTIFACTS / "pre-analysis-amendment-001.json"
    amendment = load_json(amendment_path)
    for relative, identities in amendment["amended_files"].items():
        if prior["frozen_files_sha256"][relative] != identities["original_sha256"]:
            raise SystemExit(f"original frozen identity mismatch: {relative}")
        if sha256((REPO / relative).read_bytes()) != identities["amended_sha256"]:
            raise SystemExit(f"amended identity mismatch: {relative}")
    archive_root = REPO / "references/observed/a8a-v1"
    metadata_path = archive_root / "metadata/ghcnd-stations.txt.gz"
    archive = metadata_path.read_bytes()
    source = gzip.decompress(archive)
    if sha256(archive) != STATION_LIST_ARCHIVE_SHA256:
        raise SystemExit("GHCN station-list archive mismatch")
    if sha256(source) != STATION_LIST_SOURCE_SHA256:
        raise SystemExit("GHCN station-list source mismatch")
    source.decode("utf-8")
    for directory in (archive_root / "daymet", archive_root / "ghcn"):
        if directory.exists() and any(directory.glob("*.gz")):
            raise SystemExit("daily station archive existed before amendment")
    contract = load_json(ARTIFACTS / "analysis-contract-v1.json")
    for entry in contract["inputs"].values():
        if sha256((REPO / entry["path"]).read_bytes()) != entry["sha256"]:
            raise SystemExit(f"input mismatch: {entry['path']}")
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=REPO,
            check=False,
        ).returncode
        != 0
    ):
        raise SystemExit("production crates changed after source boundary")
    frozen_paths = set(prior["frozen_files_sha256"])
    frozen_paths.update(
        {
            prior_path.relative_to(REPO).as_posix(),
            amendment_path.relative_to(REPO).as_posix(),
            Path(__file__).resolve().relative_to(REPO).as_posix(),
        }
    )
    value = {
        "amendments": [amendment["amendment_id"]],
        "daily_station_source_files_present_at_freeze": False,
        "freeze_id": "a8a_pre_analysis_freeze_v2",
        "frozen_files_sha256": {
            relative: sha256((REPO / relative).read_bytes())
            for relative in sorted(frozen_paths)
        },
        "method_boundary": (
            "The v1 panel and scientific decision contract remain unchanged; only strict "
            "UTF-8 station-list decoding and successor-freeze provenance are amended."
        ),
        "prior_freeze": {
            "path": prior_path.relative_to(REPO).as_posix(),
            "sha256": PRIOR_FREEZE_SHA256,
        },
        "schema_version": 2,
        "source_commit": contract["source_commit"],
        "station_list_metadata_accessed_before_amendment": {
            "archive_sha256": STATION_LIST_ARCHIVE_SHA256,
            "source_sha256": STATION_LIST_SOURCE_SHA256,
        },
        "status": "FROZEN-BEFORE-NEW-DAILY-DATA",
    }
    output.write_bytes(canonical_json_bytes(value))
    print(sha256(output.read_bytes()))


if __name__ == "__main__":
    main()
