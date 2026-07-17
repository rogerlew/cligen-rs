#!/usr/bin/env python3
"""Build private, content-addressed A10M4 assets on rmm."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
M1 = REPO / "docs/work-packages/20260717-a10m1-corpus-role-freeze/artifacts"
SMOKE_BUILDER = REPO / (
    "docs/work-packages/20260717-a10-lemhi-python311-smoke/"
    "artifacts/environment/build_assets.py"
)
CARGO = {
    "filename": "cargo-1.92.0-x86_64-unknown-linux-gnu.tar.xz",
    "bytes": 10_788_340,
    "sha256": "e5e12be2c7126a7036c8adf573078a28b92611f5767cc9bd0a6f7c83081df103",
    "url": (
        "https://static.rust-lang.org/dist/2025-12-11/"
        "cargo-1.92.0-x86_64-unknown-linux-gnu.tar.xz"
    ),
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def valid(path: Path, expected: dict[str, object]) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == expected["bytes"]
        and digest(path) == expected["sha256"]
    )


def download(expected: dict[str, object], destination: Path) -> None:
    if valid(destination, expected):
        return
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        str(expected["url"]), headers={"User-Agent": "cligen-rs-a10m4-assets/1"}
    )
    with urllib.request.urlopen(request, timeout=180) as source, partial.open("wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    if not valid(partial, expected):
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"download identity mismatch: {destination.name}")
    os.replace(partial, destination)


def tar_info(path: Path, arcname: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(arcname)
    info.size = path.stat().st_size
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    return info


def build_corpus(destination: Path) -> None:
    transfer = json.loads((M1 / "offline-transfer-manifest-v1.json").read_text())
    partial = destination.with_suffix(".tar.part")
    with tarfile.open(partial, "w", format=tarfile.PAX_FORMAT) as archive:
        for record in transfer["objects"]:
            source = REPO / record["path"]
            if identity(source) != {"bytes": record["bytes"], "sha256": record["sha256"]}:
                raise RuntimeError(f"corpus identity mismatch: {record['path']}")
            with source.open("rb") as stream:
                archive.addfile(tar_info(source, f"corpus/{record['path']}"), stream)
        for name in (
            "offline-transfer-manifest-v1.json",
            "normalized-manifest-v1.json",
            "normalization-statistics-v1.json",
        ):
            source = M1 / name
            with source.open("rb") as stream:
                archive.addfile(tar_info(source, f"corpus/artifacts/{name}"), stream)
    os.replace(partial, destination)


def build_source(commit: str, destination: Path) -> None:
    partial = destination.with_suffix(".tar.gz.part")
    with partial.open("wb") as stream:
        subprocess.run(
            ["git", "archive", "--format=tar.gz", "--prefix=source/", commit],
            cwd=REPO,
            check=True,
            stdout=stream,
        )
    os.replace(partial, destination)


def build_vendor(destination: Path) -> None:
    partial = destination.with_suffix(".tar.gz.part")
    with tempfile.TemporaryDirectory(prefix="a10m4-vendor-") as temporary:
        vendor = Path(temporary) / "vendor"
        subprocess.run(
            ["cargo", "vendor", "--locked", "--versioned-dirs", str(vendor)],
            cwd=REPO,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        with tarfile.open(partial, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for source in sorted(vendor.rglob("*"), key=lambda item: item.as_posix()):
                relative = source.relative_to(vendor)
                info = archive.gettarinfo(str(source), f"vendor/{relative.as_posix()}")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                if info.isfile():
                    with source.open("rb") as stream:
                        archive.addfile(info, stream)
                else:
                    archive.addfile(info)
    os.replace(partial, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--pip-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "python3", str(SMOKE_BUILDER), "--asset-root", str(root),
            "--pip-cache", str(options.pip_cache.resolve()), "--repo", str(REPO),
        ],
        check=True,
    )

    cargo = root / CARGO["filename"]
    download(CARGO, cargo)
    corpus = root / "corpus.tar"
    build_corpus(corpus)
    source = root / "source.tar.gz"
    build_source(options.source_commit, source)
    vendor = root / "cargo-vendor.tar.gz"
    build_vendor(vendor)
    parameters = root / "selected-parameters-v1.tar.gz"
    shutil.copyfile(
        REPO / (
            "docs/work-packages/20260715-a8a-dry-regime-applicability/"
            "artifacts/selected-parameters-v1.tar.gz"
        ),
        parameters,
    )

    for name, source_path in (
        ("qualify.py", PACKAGE / "artifacts/jobs/qualify.py"),
        ("qualify.sh", PACKAGE / "artifacts/jobs/qualify.sh"),
        ("evidence.schema.json", PACKAGE / "artifacts/jobs/evidence.schema.json"),
    ):
        shutil.copyfile(source_path, root / name)

    names = [
        "runtime.tar.gz", "wheelhouse.tar", "requirements.lock",
        CARGO["filename"], "corpus.tar", "source.tar.gz",
        "cargo-vendor.tar.gz", "selected-parameters-v1.tar.gz",
        "qualify.py", "qualify.sh", "evidence.schema.json",
    ]
    manifest = {
        "schema_version": 1,
        "source_commit": options.source_commit,
        "assets": {name: identity(root / name) for name in names},
    }
    (root / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
