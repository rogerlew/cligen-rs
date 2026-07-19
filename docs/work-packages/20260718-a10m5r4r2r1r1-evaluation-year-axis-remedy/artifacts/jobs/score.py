#!/usr/bin/env python3
"""Score the exact retained R2R1 matrix with valid synthetic year labels."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_SCRIPT = REPO / "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy/artifacts/jobs/evaluate.py"
EXPECTED_TREE = "c4d7bf9c2b8441b89ceda42ec1ef5e7976ee533f998eff473bece2f967154607"


def tree_identity(root: Path) -> tuple[int, int, str]:
    value = hashlib.sha256()
    files = 0
    byte_count = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        item_hash = hashlib.sha256(payload).hexdigest()
        relative = str(path.relative_to(root))
        value.update(relative.encode())
        value.update(b"\0")
        value.update(str(len(payload)).encode())
        value.update(b"\0")
        value.update(item_hash.encode())
        value.update(b"\n")
        files += 1
        byte_count += len(payload)
    return files, byte_count, value.hexdigest()


def load_parent() -> Any:
    spec = importlib.util.spec_from_file_location("a10m5r4r2r1_parent_evaluate", PARENT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load parent evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corrected_resample(module: Any, blocks: list[dict[str, Any]], indices: np.ndarray) -> dict[str, float]:
    dates: list[dt.date] = []
    precipitation: list[np.ndarray] = []
    tmax: list[np.ndarray] = []
    tmin: list[np.ndarray] = []
    for position, index in enumerate(indices):
        block = blocks[int(index)]
        leap = any(date.month == 2 and date.day == 29 for date in block["dates"])
        target_year = 2400 + 8 * position + (0 if leap else 1)
        dates.extend(date.replace(year=target_year) for date in block["dates"])
        precipitation.append(block["precipitation"])
        tmax.append(block["tmax"])
        tmin.append(block["tmin"])
    return module.realized_metrics(dates, np.concatenate(precipitation), np.concatenate(tmax), np.concatenate(tmin))


def retained_comparators(module: Any, scratch: Path, site: dict[str, Any], burns: list[int]) -> tuple[dict[str, list[dict[str, float]]], dict[str, Any]]:
    localize = scratch / "localization" / site["point_id"]
    arms: dict[str, list[dict[str, float]]] = defaultdict(list)
    for arm in ("faithful", "stochastic_prism_localized_par_v1"):
        for member, _ in enumerate(burns):
            cli = scratch / "runs" / site["point_id"] / arm / f"member-{member}" / "climate.cli"
            arms[arm].append(module.realized_metrics(*module.parse_cli(cli)))
    provenance = {
        "artifact_manifest_sha256": module.digest(localize / "artifact-manifest.json"),
        "localization_sha256": module.digest(localize / "localization.json"),
        "normals_sha256": module.digest(localize / "prism-normals.json"),
        "source_station_sha256": module.digest(localize / "source-station.par"),
        "localized_station_sha256": module.digest(localize / "localized.par"),
        "station_selection_sha256": module.digest(localize / "station-selection.json"),
    }
    return dict(arms), provenance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("parent_arguments", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    if tree_identity(options.scratch) != (354, 280551300, EXPECTED_TREE):
        raise RuntimeError("retained comparator tree identity mismatch")
    module = load_parent()
    module.resampled_observation = lambda blocks, indices: corrected_resample(module, blocks, indices)
    module.comparator_streams = lambda binary, data_root, scratch, site, years, burns: retained_comparators(module, scratch, site, burns)
    arguments = list(options.parent_arguments)
    if arguments and arguments[0] == "--":
        arguments.pop(0)
    sys.argv = [str(PARENT_SCRIPT), *arguments]
    module.main()


if __name__ == "__main__":
    main()
