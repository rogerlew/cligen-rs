#!/usr/bin/env python3
"""Publish deterministic, checkout-auditable A5d1 detailed evidence."""

from __future__ import annotations

import gzip
import os
import shutil
import tarfile

from a5d1_common import (
    CERTIFICATE_DIR,
    MARGINAL_RESULTS,
    PACKAGE,
    PATH_DIR,
    PATH_RESULTS,
    freeze_identity,
    relative,
    sha256,
    write_json,
)


ARCHIVE = PACKAGE / "detailed-evidence-v1.tar.gz"
MANIFEST = PACKAGE / "detailed-evidence-manifest-v1.json"
PUBLISHED_MARGINAL = PACKAGE / "marginal-results-v1.json"
PUBLISHED_PATH = PACKAGE / "path-results-v1.json"


def main() -> None:
    freeze_sha256 = freeze_identity()
    sources = []
    for directory, prefix in ((CERTIFICATE_DIR, "certificates"), (PATH_DIR, "paths")):
        for path in sorted(directory.glob("*.json")):
            sources.append((f"{prefix}/{path.name}", path))
    if len(sources) != 340:
        raise ValueError(f"expected 340 detailed records, found {len(sources)}")
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
    shutil.copyfile(MARGINAL_RESULTS, PUBLISHED_MARGINAL)
    shutil.copyfile(PATH_RESULTS, PUBLISHED_PATH)
    records = [
        {
            "member": name,
            "bytes": source.stat().st_size,
            "sha256": sha256(source),
        }
        for name, source in sources
    ]
    value = {
        "detailed_evidence_manifest_schema_version": 1,
        "development_only": True,
        "freeze_sha256": freeze_sha256,
        "archive": {
            "path": relative(ARCHIVE),
            "bytes": ARCHIVE.stat().st_size,
            "sha256": sha256(ARCHIVE),
            "format": "deterministic-ustar+gzip",
        },
        "member_count": len(records),
        "members": records,
        "published_aggregates": [
            {
                "path": relative(PUBLISHED_MARGINAL),
                "sha256": sha256(PUBLISHED_MARGINAL),
                "bytes": PUBLISHED_MARGINAL.stat().st_size,
            },
            {
                "path": relative(PUBLISHED_PATH),
                "sha256": sha256(PUBLISHED_PATH),
                "bytes": PUBLISHED_PATH.stat().st_size,
            },
        ],
    }
    write_json(MANIFEST, value)
    print(
        f"A5d1 detailed evidence archive: PASS ({len(records)} records; "
        f"{ARCHIVE.stat().st_size} bytes)"
    )


if __name__ == "__main__":
    main()
