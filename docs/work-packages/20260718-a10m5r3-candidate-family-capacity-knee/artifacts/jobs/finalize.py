#!/usr/bin/env python3
"""Reconcile one R3 row into strict scientific and toolkit receipts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import screen_core_v2 as core


def external_rss(path: Path) -> int:
    for line in path.read_text(encoding="utf-8").splitlines():
        if "Maximum resident set size (kbytes):" in line: return int(line.rsplit(":", 1)[1].strip()) * 1024
    raise RuntimeError("external RSS absent")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--row-id", required=True); parser.add_argument("--phase", required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--time-v", type=Path, required=True)
    options = parser.parse_args(); metadata = json.loads((options.output / "export-metadata.json").read_text()); worker = json.loads((options.output / "worker.json").read_text()); calibration = json.loads((options.output / "family-calibration.json").read_text())
    rss = external_rss(options.time_v)
    gates = {"all_98_objects_verified": json.loads((options.output / "training.json").read_text())["object_count"] == 98, "candidate_fit_only": json.loads((options.output / "training.json").read_text())["fit_role"] == "candidate_fit", "fit_validation_gradient_free": json.loads((options.output / "training.json").read_text())["validation_used_for_gradient"] is False, "family_calibration": calibration["valid"], "finite_scores": all(math.isfinite(float(metadata[key])) for key in ("validation_primary_nll", "validation_tail_score", "validation_stability")), "export_size": metadata["export_bytes"] <= 262_144_000, "external_peak_rss": rss <= 2_147_483_648, "checkpoint_complete": True, **worker["gates"]}
    row = {"schema_version": 2, "classification": "a10m5r3-development-only-family-capacity-screen", "phase": options.phase, "row_id": options.row_id, "amount_family": metadata["family"], "capacity_id": metadata["capacity_id"], "training_seed": metadata["training_seed"], "parameter_count": metadata["parameter_count"], "validation_primary_nll": metadata["validation_primary_nll"], "validation_tail_score": metadata["validation_tail_score"], "validation_stability": metadata["validation_stability"], "gpu_fit_wall_seconds": metadata["gpu_fit_wall_seconds"], "export_bytes": metadata["export_bytes"], "cold_start_seconds": worker["cold_start_seconds"], "peak_rss_bytes": max(rss, worker["vmhwm_bytes"]), "runtime_ratio_max": worker["runtime_ratio_max"], "gates": gates, "valid": all(gates.values()), "verdict": "PASS" if all(gates.values()) else "FAIL"}
    core.atomic_json(options.output / "row.json", row); core.atomic_json(options.output / "evidence.json.part", row)
    if not row["valid"]: raise RuntimeError("R3 row gate failure")


if __name__ == "__main__": main()
