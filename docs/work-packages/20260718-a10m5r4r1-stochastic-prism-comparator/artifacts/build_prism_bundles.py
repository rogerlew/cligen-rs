#!/usr/bin/env python3
"""Build deterministic source and runtime PRISM Norm91m bundles."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.io import MemoryFile


ACCESS_DATE = "2026-07-18"
BUNDLE_VERSION = "2026.07"
VARIABLES = (("ppt", "M4", "millimetres/month"),
             ("tmax", "M5", "degrees Celsius"),
             ("tmin", "M5", "degrees Celsius"))
ATTRIBUTION = """# PRISM attribution and terms

PRISM Group, Oregon State University, https://prism.oregonstate.edu,
data accessed 2026-07-18.

Source terms: https://prism.oregonstate.edu/terms/
Normals documentation: https://prism.oregonstate.edu/normals/

PRISM supplies only the registered monthly grid values. The localized CLIGEN
outputs are not official PRISM products.
"""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_bytes(value)
    partial.replace(path)


def parse_info(raw: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            result[key.strip()] = value.strip()
    return result


def expected_name(variable: str, month: int) -> str:
    return f"prism_{variable}_us_25m_2020{month:02d}_avg_30y.zip"


def official_url(variable: str, name: str) -> str:
    return f"https://data.prism.oregonstate.edu/normals/us/4km/{variable}/monthly/{name}"


def read_grid(
    archive: Path,
    variable: str,
    month: int,
    release: str,
    units: str,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], tuple[Any, ...]]:
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        tif_names = [name for name in names if name.endswith(".tif")]
        info_names = [name for name in names if name.endswith(".info.txt")]
        if len(tif_names) != 1 or len(info_names) != 1:
            raise RuntimeError(f"{archive.name}: expected one TIFF and one info member")
        tif_name = tif_names[0]
        info_name = info_names[0]
        tif_raw = zipped.read(tif_name)
        info_raw = zipped.read(info_name)
    info = parse_info(info_raw)
    if info.get("PRISM_DATASET_VERSION") != release:
        raise RuntimeError(f"{archive.name}: expected release {release}")
    if "normals/9120" not in info.get("PRISM_DATASET_TYPE", ""):
        raise RuntimeError(f"{archive.name}: not a 1991-2020 normal")
    with MemoryFile(tif_raw) as memory:
        with memory.open() as dataset:
            if dataset.count != 1 or dataset.dtypes != ("float32",):
                raise RuntimeError(f"{archive.name}: expected one float32 band")
            if str(dataset.crs) != "EPSG:4269" or dataset.nodata != -9999.0:
                raise RuntimeError(f"{archive.name}: unexpected CRS or nodata")
            values = dataset.read(1)
            valid = dataset.read_masks(1) != 0
            identity = (
                dataset.width,
                dataset.height,
                str(dataset.crs),
                tuple(float(item) for item in dataset.transform),
                float(dataset.nodata),
            )
            raster = {
                "width": dataset.width,
                "height": dataset.height,
                "crs": str(dataset.crs),
                "transform": list(tuple(float(item) for item in dataset.transform)),
                "dtype": "float32",
                "nodata": float(dataset.nodata),
            }
    record = {
        "variable": variable,
        "month": month,
        "units": units,
        "release": release,
        "archive": archive.name,
        "official_url": official_url(variable, archive.name),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "tiff_member": tif_name,
        "tiff_bytes": len(tif_raw),
        "tiff_sha256": sha256_bytes(tif_raw),
        "info_member": info_name,
        "info_sha256": sha256_bytes(info_raw),
        "dataset_create_date": info["PRISM_DATASET_CREATE_DATE"],
        "dataset_type": info["PRISM_DATASET_TYPE"],
        "dataset_version": info["PRISM_DATASET_VERSION"],
        "raster": raster,
    }
    return values, valid, record, identity


def deterministic_tar_gz(source: Path, destination: Path) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    with partial.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
                    relative = path.relative_to(source).as_posix()
                    info = archive.gettarinfo(str(path), arcname=relative)
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    info.mode = 0o755 if path.is_dir() else 0o644
                    if path.is_file():
                        with path.open("rb") as content:
                            archive.addfile(info, content)
                    else:
                        archive.addfile(info)
    partial.replace(destination)


def build(source_root: Path, output_root: Path) -> dict[str, Any]:
    source_tree = output_root / "source-tree"
    runtime_tree = output_root / "runtime-tree"
    for tree in (source_tree, runtime_tree):
        if tree.exists():
            shutil.rmtree(tree)
        tree.mkdir(parents=True)
    (source_tree / "archives").mkdir()
    grids: list[dict[str, Any]] = []
    arrays: list[np.ndarray] = []
    validity: np.ndarray | None = None
    grid_identity: tuple[Any, ...] | None = None
    for variable, release, units in VARIABLES:
        for month in range(1, 13):
            name = expected_name(variable, month)
            archive = source_root / name
            if not archive.is_file():
                raise RuntimeError(f"missing source archive {name}")
            values, valid, record, identity = read_grid(
                archive, variable, month, release, units
            )
            if grid_identity is None:
                grid_identity = identity
                validity = valid.copy()
            elif identity != grid_identity:
                raise RuntimeError(f"{name}: grid identity differs")
            else:
                assert validity is not None
                validity &= valid
            arrays.append(values)
            grids.append(record)
            shutil.copyfile(archive, source_tree / "archives" / name)
    assert grid_identity is not None and validity is not None
    width, height, crs, transform, nodata = grid_identity
    source_manifest = {
        "schema_version": 1,
        "dataset": "PRISM Norm91m",
        "period": "1991-2020",
        "resolution": "4km (2.5 arc-minute)",
        "coverage": "CONUS",
        "access_date": ACCESS_DATE,
        "attribution": (
            "PRISM Group, Oregon State University, "
            "https://prism.oregonstate.edu, data accessed 2026-07-18."
        ),
        "grids": grids,
    }
    source_manifest_raw = canonical_bytes(source_manifest)
    write_bytes(source_tree / "source-manifest.json", source_manifest_raw)
    write_bytes(runtime_tree / "source-manifest.json", source_manifest_raw)
    write_bytes(source_tree / "ATTRIBUTION.md", ATTRIBUTION.encode("utf-8"))
    write_bytes(runtime_tree / "ATTRIBUTION.md", ATTRIBUTION.encode("utf-8"))

    stack = np.stack(arrays, axis=-1).astype("<f4", copy=False)
    normals_path = runtime_tree / "normals.f32le"
    stack.tofile(normals_path)
    mask_path = runtime_tree / "validity-mask.bin"
    packed_mask = np.packbits(validity.reshape(-1), bitorder="little")
    packed_mask.tofile(mask_path)
    grid_manifest = {
        "schema_version": 1,
        "bundle_id": "prism_norm91m_9120_4km_m4_m5_v1",
        "bundle_version": BUNDLE_VERSION,
        "source_manifest_sha256": sha256_bytes(source_manifest_raw),
        "width": width,
        "height": height,
        "crs": crs,
        "transform": list(transform),
        "source_nodata": nodata,
        "layout": "cell-major",
        "byte_order": "little-endian",
        "scalar_type": "float32",
        "layers": [
            {
                "index": variable_index * 12 + month - 1,
                "variable": variable,
                "month": month,
                "units": units,
            }
            for variable_index, (variable, _release, units) in enumerate(VARIABLES)
            for month in range(1, 13)
        ],
        "validity": "one little-endian bit per cell; set iff all 36 layers are valid",
        "valid_cell_count": int(validity.sum()),
        "normals": {
            "path": "normals.f32le",
            "bytes": normals_path.stat().st_size,
            "sha256": sha256_file(normals_path),
        },
        "validity_mask": {
            "path": "validity-mask.bin",
            "bytes": mask_path.stat().st_size,
            "sha256": sha256_file(mask_path),
        },
    }
    grid_manifest_raw = canonical_bytes(grid_manifest)
    write_bytes(runtime_tree / "grid-manifest.json", grid_manifest_raw)
    script_path = Path(__file__).resolve()
    receipt = {
        "schema_version": 1,
        "producer": "A10M5R4R1 build_prism_bundles.py",
        "producer_sha256": sha256_file(script_path),
        "build_date": ACCESS_DATE,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "rasterio": rasterio.__version__,
        "source_manifest_sha256": sha256_bytes(source_manifest_raw),
        "grid_manifest_sha256": sha256_bytes(grid_manifest_raw),
    }
    write_bytes(runtime_tree / "BUILD-RECEIPT.json", canonical_bytes(receipt))

    source_archive = output_root / f"prism-normals-source-{BUNDLE_VERSION}.tar.gz"
    runtime_archive = output_root / f"prism-normals-runtime-{BUNDLE_VERSION}.tar.gz"
    deterministic_tar_gz(source_tree, source_archive)
    deterministic_tar_gz(runtime_tree, runtime_archive)
    result = {
        "schema_version": 1,
        "bundle_version": BUNDLE_VERSION,
        "source_manifest_sha256": sha256_bytes(source_manifest_raw),
        "grid_manifest_sha256": sha256_bytes(grid_manifest_raw),
        "source_archive": {
            "path": source_archive.name,
            "bytes": source_archive.stat().st_size,
            "sha256": sha256_file(source_archive),
        },
        "runtime_archive": {
            "path": runtime_archive.name,
            "bytes": runtime_archive.stat().st_size,
            "sha256": sha256_file(runtime_archive),
        },
    }
    write_bytes(output_root / "bundle-build.json", canonical_bytes(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    options = parser.parse_args()
    options.output_root.mkdir(parents=True, exist_ok=True)
    result = build(options.source_root.resolve(), options.output_root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
