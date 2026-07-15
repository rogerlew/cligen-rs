#!/usr/bin/env python3
"""Create or safely restore the deterministic A8c retained-stream archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
EVIDENCE = ARTIFACTS / "execution-evidence-v1.json"
ARCHIVE = ARTIFACTS / "a8c-retained-streams-v1.tar.gz"
MANIFEST = ARTIFACTS / "retained-streams-manifest-v1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def expected_members() -> list[dict[str, Any]]:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    members = []
    for cell in evidence["cells"]:
        for variant in ("candidate", "faithful"):
            entry = cell[variant]
            for path_key, hash_key in (
                ("cli_path", "cli_sha256"),
                ("provenance_path", "provenance_sha256"),
            ):
                members.append(
                    {
                        "path": entry[path_key],
                        "sha256": entry[hash_key],
                    }
                )
    members.sort(key=lambda row: row["path"])
    if len(members) != 96 or len({row["path"] for row in members}) != 96:
        raise ValueError("expected 96 unique retained stream files")
    return members


def create() -> None:
    members = expected_members()
    for member in members:
        path = ROOT / member["path"]
        if sha256(path) != member["sha256"]:
            raise ValueError(f"retained stream hash mismatch: {path}")
        member["bytes"] = path.stat().st_size
    with ARCHIVE.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for member in members:
                    path = ROOT / member["path"]
                    info = archive.gettarinfo(str(path), arcname=member["path"])
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    info.mode = 0o644
                    with path.open("rb") as stream:
                        archive.addfile(info, stream)
    canonical_json(
        MANIFEST,
        {
            "archive": str(ARCHIVE.relative_to(ROOT)),
            "archive_bytes": ARCHIVE.stat().st_size,
            "archive_sha256": sha256(ARCHIVE),
            "execution_evidence_sha256": sha256(EVIDENCE),
            "members": members,
            "schema_version": 1,
        },
    )
    print(sha256(ARCHIVE))


def restore() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(ARCHIVE) != manifest["archive_sha256"]:
        raise ValueError("archive hash mismatch")
    expected = {row["path"]: row for row in manifest["members"]}
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        actual = {member.name: member for member in archive.getmembers()}
        if set(actual) != set(expected):
            raise ValueError("archive member set mismatch")
        for name in sorted(expected):
            member = actual[name]
            if not member.isfile() or member.name.startswith("/") or ".." in Path(name).parts:
                raise ValueError(f"unsafe archive member: {name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"missing archive member body: {name}")
            data = stream.read()
            if hashlib.sha256(data).hexdigest() != expected[name]["sha256"]:
                raise ValueError(f"archive member hash mismatch: {name}")
            destination = ROOT / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    print(f"restored {len(expected)} files")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    restore() if args.restore else create()


if __name__ == "__main__":
    main()
