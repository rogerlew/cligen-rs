import argparse
import hashlib
import json
import os
import shutil
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

MIB = 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(MIB):
            digest.update(block)
    return digest.hexdigest()


def add_file(archive: tarfile.TarFile, path: Path, arcname: str) -> None:
    info = archive.gettarinfo(str(path), arcname)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    with path.open("rb") as handle:
        archive.addfile(info, handle)


def wheel_metadata(path: Path) -> tuple[str, str, list[str], list[str]]:
    with zipfile.ZipFile(path) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
    return (
        metadata["Name"],
        metadata["Version"],
        metadata.get_all("License") or [],
        metadata.get_all("License-File") or [],
    )


def build_corpus(manifest_path: Path, output: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    objects = manifest["objects"]
    for entry in objects:
        path = Path(entry["path"])
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise RuntimeError(f"A10M1 object verification failed: {path}")
    if len(objects) != 98 or sum(entry["bytes"] for entry in objects) != 223_799_545:
        raise RuntimeError("A10M1 aggregate differs from accepted manifest")
    with tarfile.open(output, "w", format=tarfile.PAX_FORMAT) as archive:
        for entry in sorted(objects, key=lambda item: item["path"]):
            add_file(archive, Path(entry["path"]), entry["path"])
    return {"bytes": output.stat().st_size, "sha256": sha256(output)}


def build_wheelhouse(wheel_dir: Path, output_dir: Path, output: Path) -> None:
    records = []
    requirements = []
    licenses = []
    wheels = sorted(wheel_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError("wheelhouse is empty")
    with tarfile.open(output, "w", format=tarfile.PAX_FORMAT) as archive:
        for wheel in wheels:
            digest = sha256(wheel)
            name, version, license_values, license_files = wheel_metadata(wheel)
            records.append(
                {
                    "bytes": wheel.stat().st_size,
                    "filename": wheel.name,
                    "name": name,
                    "sha256": digest,
                    "version": version,
                }
            )
            requirements.append(f"{name}=={version} --hash=sha256:{digest}")
            licenses.append(
                {
                    "filename": wheel.name,
                    "license_files_embedded_in_wheel": license_files,
                    "license_metadata": license_values,
                    "name": name,
                }
            )
            add_file(archive, wheel, f"wheelhouse/{wheel.name}")
    (output_dir / "requirements.lock").write_text(
        "\n".join(sorted(requirements, key=str.casefold)) + "\n", encoding="utf-8"
    )
    (output_dir / "wheelhouse-manifest.json").write_text(
        json.dumps(
            {
                "archive_bytes": output.stat().st_size,
                "archive_sha256": sha256(output),
                "resolver_sources": [
                    "https://download.pytorch.org/whl/cu128",
                    "https://pypi.org/simple",
                ],
                "platform": "CPython 3.11 / manylinux x86_64",
                "wheels": records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "license-metadata.json").write_text(
        json.dumps(licenses, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--environment-dir", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument("--platform-label", required=True)
    parser.add_argument("--pytorch-index", required=True)
    args = parser.parse_args()
    args.environment_dir.mkdir(parents=True, exist_ok=True)
    args.asset_dir.mkdir(parents=True, exist_ok=True)

    corpus = args.asset_dir / "a10m1-corpus.tar"
    wheelhouse = args.asset_dir / "wheelhouse.tar"
    corpus_record = build_corpus(args.manifest, corpus)
    shutil.copyfile(
        args.manifest, args.environment_dir / "a10m1-transfer-manifest.json"
    )
    build_wheelhouse(args.wheel_dir, args.environment_dir, wheelhouse)
    wheel_manifest_path = args.environment_dir / "wheelhouse-manifest.json"
    wheel_manifest = json.loads(wheel_manifest_path.read_text(encoding="utf-8"))
    wheel_manifest["platform"] = args.platform_label
    wheel_manifest["resolver_sources"][0] = args.pytorch_index
    wheel_manifest_path.write_text(
        json.dumps(wheel_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    wheel_record = {
        "bytes": wheelhouse.stat().st_size,
        "sha256": sha256(wheelhouse),
    }
    (args.environment_dir / "asset-manifest.json").write_text(
        json.dumps(
            {"a10m1-corpus.tar": corpus_record, "wheelhouse.tar": wheel_record},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
