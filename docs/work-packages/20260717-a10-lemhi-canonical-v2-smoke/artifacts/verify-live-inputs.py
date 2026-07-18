#!/usr/bin/env python3
"""Fail closed on canonical-v2 smoke inputs before remote staging."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath


EXPECTED = {
    "runtime.tar.gz": (48_850_850, "14b5843a3492925dab6fdb7cca7d09af83ddf1fe2851f72cf9b1edc8ed2b1db7"),
    "wheelhouse.tar": (3_865_978_880, "30344178212946f5a37df03a6ccdc82025d198c07467adf55d87b9d5918e730e"),
    "requirements.lock": (2_676, "87dcc51e95945d1b152174a592bdb76d57fbe8cae0eb95ed5fdf9045c8fe6647"),
    "wheel-manifest.json": (7_267, "f70271b551bde1544167eaaa8513ee2d37907deba0109021ba1dcee2c74347cb"),
    "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz": (192_171_372, "d2ccef59dd9f7439f2c694948069f789a044dc1addcc0803613232af8f88ee0c"),
    "cargo-vendor.tar.gz": (35_822_885, "13d7f41f3e0d8b45254a1e6070db5b814d54327e9201ccbe22a57269168f0d3c"),
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify_archive(path: Path) -> None:
    with tarfile.open(path, "r:*") as archive:
        for member in archive:
            pure = PurePosixPath(member.name)
            if pure.is_absolute() or ".." in pure.parts:
                raise SystemExit(f"unsafe archive member: {path.name}")
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise SystemExit(f"unsupported archive member: {path.name}")
            if member.mode & 0o6000:
                raise SystemExit(f"setid archive member: {path.name}")
            if member.issym() or member.islnk():
                target = PurePosixPath(member.linkname)
                if target.is_absolute():
                    raise SystemExit(f"absolute archive link: {path.name}")
                parts: list[str] = []
                for part in (pure.parent / target).parts:
                    if part in ("", "."):
                        continue
                    if part == "..":
                        if not parts:
                            raise SystemExit(f"escaping archive link: {path.name}")
                        parts.pop()
                    else:
                        parts.append(part)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    options = parser.parse_args()
    for name, (size, sha256) in EXPECTED.items():
        path = options.asset_root / name
        if not path.is_file() or path.stat().st_size != size or digest(path) != sha256:
            raise SystemExit(f"canonical-v2 live input mismatch: {name}")
        if name.endswith((".tar", ".tar.gz", ".tar.xz")):
            verify_archive(path)
    print("canonical-v2 live inputs: PASS")


if __name__ == "__main__":
    main()
