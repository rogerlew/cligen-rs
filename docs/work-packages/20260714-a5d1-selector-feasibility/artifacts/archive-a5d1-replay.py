#!/usr/bin/env python3
"""Retain a deterministic post-result replay snapshot before target restore."""

from __future__ import annotations

import gzip
import os
import tarfile

from a5d1_common import PACKAGE, PATH_DIR, PATH_RESULTS, freeze_identity, relative, sha256, write_json


ARCHIVE = PACKAGE / "replay-evidence-v1.tar.gz"
MANIFEST = PACKAGE / "replay-evidence-manifest-v1.json"


def main() -> None:
    freeze_sha256 = freeze_identity()
    sources = [(f"paths/{path.name}", path) for path in sorted(PATH_DIR.glob("*.json"))]
    sources.append(("path-results-v1.json", PATH_RESULTS))
    if len(sources) != 307:
        raise ValueError(f"expected 307 replay records, found {len(sources)}")
    temporary = ARCHIVE.with_suffix(ARCHIVE.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for name, source in sources:
                    info = tarfile.TarInfo(name)
                    info.size = source.stat().st_size
                    info.mtime = 0
                    info.mode = 0o644
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)
    os.replace(temporary, ARCHIVE)
    value = {
        "replay_evidence_manifest_schema_version": 1,
        "post_result_closure_evidence": True,
        "freeze_sha256": freeze_sha256,
        "archive": {
            "path": relative(ARCHIVE),
            "bytes": ARCHIVE.stat().st_size,
            "sha256": sha256(ARCHIVE),
            "format": "deterministic-ustar+gzip",
        },
        "member_count": len(sources),
        "members": [
            {"member": name, "bytes": source.stat().st_size, "sha256": sha256(source)}
            for name, source in sources
        ],
    }
    write_json(MANIFEST, value)
    print(f"A5d1 replay archive: PASS ({len(sources)} records; {ARCHIVE.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
