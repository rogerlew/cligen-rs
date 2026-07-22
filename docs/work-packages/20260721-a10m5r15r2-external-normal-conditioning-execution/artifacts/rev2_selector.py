#!/usr/bin/env python3
"""Run the frozen selector while retaining its candidate bootstrap sequences."""

from __future__ import annotations

import json
import shutil
import sys
import tarfile
from pathlib import Path

TWO_ARM_DIAGNOSTIC = '''        left, right = configurations
        left_values = np.asarray(values[left])
        right_values = np.asarray(values[right])
        annual_diagnostics[family] = {
            "configurations": summaries,
            "probability_medium_lower_error": float(np.mean(left_values < right_values)),
            "selection_gating": False,
        }
'''
FOUR_ARM_DIAGNOSTIC = '''        pairwise = {}
        for left_index, left in enumerate(configurations):
            for right in configurations[left_index + 1:]:
                left_values = np.asarray(values[left])
                right_values = np.asarray(values[right])
                pairwise[f"{left}__vs__{right}"] = {
                    "probability_left_lower_error": float(np.mean(left_values < right_values))
                }
        annual_diagnostics[family] = {
            "configurations": summaries,
            "pairwise_probabilities": pairwise,
            "selection_gating": False,
        }
'''


def four_arm_source(source: str) -> str:
    if source.count(TWO_ARM_DIAGNOSTIC) != 1:
        raise RuntimeError("frozen two-arm diagnostic source identity drift")
    transformed = source.replace(TWO_ARM_DIAGNOSTIC, FOUR_ARM_DIAGNOSTIC)
    compile(transformed, "temporal_select_rev2.py", "exec")
    return transformed


def digest(path: Path) -> str:
    import hashlib

    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def extract_observations(corpus: Path, output: Path, sites: list[dict]) -> None:
    wanted = {site["daymet_shard"]: site["daymet_shard_sha256"] for site in sites}
    output.mkdir(mode=0o700)
    with tarfile.open(corpus, "r:") as archive:
        for member in archive:
            name = Path(member.name).name
            if name not in wanted:
                continue
            if not member.isfile() or member.uid != 0 or member.gid != 0:
                raise RuntimeError("unsafe observation archive member")
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("unreadable observation archive member")
            target = output / name
            with source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination)
            if digest(target) != wanted[name]:
                raise RuntimeError("observation shard identity drift")
    if {path.name for path in output.iterdir()} != set(wanted):
        raise RuntimeError("observation shard roster incomplete")


def run_selector(
    *,
    asset_root: Path,
    binary: Path,
    data_root: Path,
    evidence_root: Path,
    observations: Path,
    output_root: Path,
    bootstrap_seed: int,
) -> tuple[dict, dict[str, list[float]]]:
    import numpy as np

    source = asset_root / "temporal_select.py"
    module_name = f"rev2_temporal_select_{bootstrap_seed}_{output_root.name}"
    module = __import__("types").ModuleType(module_name)
    module.__file__ = str(source)
    exec(compile(four_arm_source(source.read_text(encoding="utf-8")), str(source), "exec"), module.__dict__)
    contract = json.loads((asset_root / "temporal-contract.json").read_text(encoding="utf-8"))
    configurations = [row["configuration_id"] for row in contract["roles"]]
    replicates = int(contract["scoring"]["bootstrap"]["replicates"])
    captured: list[list[float]] = []
    original_rng = np.random.default_rng
    original_quantile = np.quantile

    def selected_rng(seed=None):
        return original_rng(bootstrap_seed if seed == 410542 else seed)

    def observed_quantile(values, q, *args, **kwargs):
        array = np.asarray(values)
        if array.ndim == 1 and array.size == replicates and float(q) == 0.90:
            captured.append([float(value) for value in array])
        return original_quantile(values, q, *args, **kwargs)

    result_path = output_root / "temporal-result.json"
    output_root.mkdir(mode=0o700)
    arguments = [
        str(source),
        "--binary", str(binary),
        "--data-root", str(data_root),
        "--observation-shards", str(observations),
        "--neural-root", str(evidence_root),
        "--scratch", str(output_root / "scratch"),
        "--output", str(result_path),
        "--contract", str(asset_root / "temporal-contract.json"),
        "--portfolio-contract", str(asset_root / "portfolio-contract.json"),
        "--calendar-control-expectation", str(asset_root / "calendar-control-expectation.json"),
        "--sites", str(asset_root / "sites.json"),
    ]
    old_argv = sys.argv
    np.random.default_rng = selected_rng
    np.quantile = observed_quantile
    try:
        sys.argv = arguments
        module.main()
    finally:
        sys.argv = old_argv
        np.random.default_rng = original_rng
        np.quantile = original_quantile
    if len(captured) < len(configurations):
        raise RuntimeError("candidate bootstrap sequences were not captured")
    return (
        json.loads(result_path.read_text(encoding="utf-8")),
        dict(zip(configurations, captured[: len(configurations)])),
    )
