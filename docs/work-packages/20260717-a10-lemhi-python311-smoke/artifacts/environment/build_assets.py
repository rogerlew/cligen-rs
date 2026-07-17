#!/usr/bin/env python3
"""Build the private, content-addressed CPython 3.11 smoke assets on rmm."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

PREDECESSOR = "8b7e751"
MANIFEST_OBJECT = "docs/work-packages/20260717-a10m2-completion/artifacts/environment/wheelhouse-manifest.json"
LOCK_OBJECT = "docs/work-packages/20260717-a10m2-completion/artifacts/environment/requirements.lock"
RUNTIME = {
    "bytes": 48850850,
    "filename": "runtime.tar.gz",
    "sha256": "14b5843a3492925dab6fdb7cca7d09af83ddf1fe2851f72cf9b1edc8ed2b1db7",
    "url": "https://github.com/astral-sh/python-build-standalone/releases/download/20260510/cpython-3.11.15%2B20260510-x86_64-unknown-linux-gnu-install_only.tar.gz",
}
NUMPY = {
    "bytes": 16821570,
    "filename": "numpy-2.2.6-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    "name": "numpy",
    "sha256": "ba10f8411898fc418a521833e014a77d3ca01c15b0c6cdcce6a0d2897e6dbbdf",
    "version": "2.2.6",
    "url": "https://files.pythonhosted.org/packages/b3/dd/2238b898e51bd6d389b7389ffb20d7f4c10066d80351187ec8e303a5a475/numpy-2.2.6-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
}
DIRECT_URLS = {
    "filelock-3.29.0-py3-none-any.whl": "https://files.pythonhosted.org/packages/81/47/dd9a212ef6e343a6857485ffe25bba537304f1913bdbed446a23f7f592e1/filelock-3.29.0-py3-none-any.whl",
    "fsspec-2026.4.0-py3-none-any.whl": "https://files.pythonhosted.org/packages/d5/0c/043d5e551459da400957a1395e0febbf771446ff34291afcbe3d8be2a279/fsspec-2026.4.0-py3-none-any.whl",
    "markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl": "https://files.pythonhosted.org/packages/30/ac/0273f6fcb5f42e314c6d8cd99effae6a5354604d461b8d392b5ec9530a54/markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl",
    "networkx-3.6.1-py3-none-any.whl": "https://files.pythonhosted.org/packages/9e/c9/b2622292ea83fbb4ec318f5b9ab867d0a28ab43c5717bb85b0a5f6b3b0a4/networkx-3.6.1-py3-none-any.whl",
    "sympy-1.14.0-py3-none-any.whl": "https://files.pythonhosted.org/packages/a2/09/77d55d46fd61b4a135c444fc97158ef34a095e5681d0a6c10b75bf356191/sympy-1.14.0-py3-none-any.whl",
    "torch-2.7.1+cu128-cp311-cp311-manylinux_2_28_x86_64.whl": "https://download-r2.pytorch.org/whl/cu128/torch-2.7.1%2Bcu128-cp311-cp311-manylinux_2_28_x86_64.whl",
    "typing_extensions-4.15.0-py3-none-any.whl": "https://files.pythonhosted.org/packages/18/67/36e9267722cc04a6b9f15c7f3441c2363321a3ea07da7ae0c0707beb2a9c/typing_extensions-4.15.0-py3-none-any.whl",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def valid(path: Path, record: dict) -> bool:
    return path.is_file() and path.stat().st_size == record["bytes"] and digest(path) == record["sha256"]


def download(record: dict, destination: Path) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(record["url"], headers={"User-Agent": "cligen-rs-a10-asset-builder/1"})
    with urllib.request.urlopen(request, timeout=120) as source, partial.open("wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    if not valid(partial, record):
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"identity mismatch: {record['filename']}")
    os.replace(partial, destination)


def cached_wheels(cache: Path, records: list[dict]) -> dict[str, Path]:
    sizes = {item["bytes"] for item in records}
    wanted = {item["sha256"] for item in records}
    found: dict[str, Path] = {}
    for root, _, files in os.walk(cache):
        for name in files:
            candidate = Path(root) / name
            try:
                if candidate.stat().st_size not in sizes:
                    continue
            except OSError:
                continue
            identity = digest(candidate)
            if identity in wanted:
                found[identity] = candidate
    return found


def safe_runtime_archive(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if not members or any(member.name.startswith("/") or ".." in Path(member.name).parts for member in members):
            raise RuntimeError("unsafe runtime archive path")
        if any(member.isdev() or member.mode & 0o6000 for member in members):
            raise RuntimeError("unsafe runtime archive member")
        for member in members:
            if member.issym() or member.islnk():
                base = posixpath.dirname(member.name) if member.issym() else ""
                target = posixpath.normpath(posixpath.join(base, member.linkname))
                if member.linkname.startswith("/") or target == ".." or target.startswith("../"):
                    raise RuntimeError("unsafe runtime archive link")
        if not any(member.name == "python/bin/python3" for member in members):
            raise RuntimeError("runtime entry point absent")


def deterministic_wheel_tar(wheel_dir: Path, destination: Path) -> None:
    partial = destination.with_suffix(".tar.part")
    with tarfile.open(partial, "w", format=tarfile.USTAR_FORMAT) as archive:
        directory = tarfile.TarInfo("wheelhouse")
        directory.type = tarfile.DIRTYPE
        directory.mode = 0o755
        directory.uid = directory.gid = 0
        directory.mtime = 0
        archive.addfile(directory)
        for path in sorted(wheel_dir.iterdir(), key=lambda item: item.name):
            info = tarfile.TarInfo(f"wheelhouse/{path.name}")
            info.size = path.stat().st_size
            info.mode = 0o644
            info.uid = info.gid = 0
            info.mtime = 0
            with path.open("rb") as stream:
                archive.addfile(info, stream)
    os.replace(partial, destination)


def git_object(repo: Path, object_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{PREDECESSOR}:{object_path}"],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--pip-cache", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve()
    wheels = root / "wheels"
    wheels.mkdir(parents=True, exist_ok=True)
    prior = json.loads(git_object(options.repo, MANIFEST_OBJECT))
    records = prior["wheels"] + [NUMPY]
    cache = cached_wheels(options.pip_cache.resolve(), records)
    for record in records:
        destination = wheels / record["filename"]
        if valid(destination, record):
            continue
        source = cache.get(record["sha256"])
        if source is not None:
            shutil.copyfile(source, destination)
        else:
            url = DIRECT_URLS.get(record["filename"], record.get("url"))
            if url is None:
                raise RuntimeError(f"wheel missing from retained cache: {record['filename']}")
            download({**record, "url": url}, destination)
        if not valid(destination, record):
            raise RuntimeError(f"wheel identity mismatch: {record['filename']}")
    runtime = root / RUNTIME["filename"]
    if not valid(runtime, RUNTIME):
        download(RUNTIME, runtime)
    safe_runtime_archive(runtime)
    lock = git_object(options.repo, LOCK_OBJECT).decode("utf-8")
    lock += f"numpy==2.2.6 --hash=sha256:{NUMPY['sha256']}\n"
    (root / "requirements.lock").write_text(lock, encoding="utf-8")
    wheel_tar = root / "wheelhouse.tar"
    deterministic_wheel_tar(wheels, wheel_tar)
    manifest = {
        "archive_bytes": wheel_tar.stat().st_size,
        "archive_sha256": digest(wheel_tar),
        "platform": "CPython 3.11 / manylinux x86_64",
        "wheels": sorted(records, key=lambda item: item["filename"]),
    }
    (root / "wheel-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assets = [runtime, wheel_tar, root / "requirements.lock", root / "wheel-manifest.json"]
    print(json.dumps({path.name: {"bytes": path.stat().st_size, "sha256": digest(path)} for path in assets}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
