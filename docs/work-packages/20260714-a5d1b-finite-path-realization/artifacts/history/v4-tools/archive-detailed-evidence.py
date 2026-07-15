#!/usr/bin/env python3
"""Create a deterministic archive of A5d1b count and ordered-path records."""

from __future__ import annotations

import gzip
import io
import sys
import tarfile

from a5d1b_common import ARTIFACTS, COUNT_DIR, PATH_DIR, freeze_identity, sha256, write_json


ARCHIVE = ARTIFACTS / "detailed-evidence-v1.tar.gz"
MANIFEST = ARTIFACTS / "detailed-evidence-manifest-v1.json"


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: archive-detailed-evidence.py")
    freeze_sha256 = freeze_identity()
    files = sorted(COUNT_DIR.glob("*.json")) + sorted(PATH_DIR.glob("*.json"))
    if len(list(COUNT_DIR.glob("*.json"))) != 17:
        raise ValueError("count certificate set does not close")
    tar_buffer = io.BytesIO()
    members = []
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            prefix = "counts" if path.parent == COUNT_DIR else "paths"
            name = f"{prefix}/{path.name}"
            payload = path.read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(payload))
            members.append({"member": name, "bytes": len(payload), "sha256": sha256(path)})
    with ARCHIVE.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(tar_buffer.getvalue())
    value = {
        "detailed_evidence_manifest_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "member_count": len(members),
        "members": members,
        "archive": {"path": ARCHIVE.name, "bytes": ARCHIVE.stat().st_size, "sha256": sha256(ARCHIVE)},
    }
    write_json(MANIFEST, value)
    print(f"A5d1b detailed evidence: {len(members)} members; {value['archive']['sha256']}")


if __name__ == "__main__":
    main()

