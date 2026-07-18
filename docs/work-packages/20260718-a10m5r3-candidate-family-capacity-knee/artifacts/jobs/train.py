#!/usr/bin/env python3
"""Fit and export one frozen A10M5R3 row."""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import torch

import screen_core_v2 as core


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row-id", required=True)
    parser.add_argument("--family", choices=core.FAMILIES, required=True)
    parser.add_argument("--capacity", required=True)
    parser.add_argument("--seed", type=int, choices=core.SEEDS, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.capacity == "FAMILY": latent, width, depth = 64, 128, 2
    else: latent, width, depth = core.CAPACITIES[options.capacity]
    definition = {"latent_dim": latent, "width": width, "depth": depth, "amount_family": options.family}
    options.output.mkdir(parents=True, exist_ok=True); core.configure(options.seed)
    calibration = core.family_calibration(options.family); core.atomic_json(options.output / "family-calibration.json", calibration)
    if not calibration["valid"]: raise RuntimeError("family calibration failed")
    model, training, checkpoint = core.training(options, definition, options.output)
    export_model = core.StreamingExport(model.cpu().eval()).eval(); torch.cuda.empty_cache()
    export = options.output / "model-export.pt"
    traced = torch.jit.trace(export_model, (torch.zeros((1, 8, 13)), torch.tensor([export_model.validation_index]), torch.zeros((1, 1, export_model.transition.hidden_size))), strict=True); traced.save(str(export))
    model_record = {"schema_version": 2, "model_id": f"a10m5r3-{options.row_id}", "family_id": "neural_point_weather_state_space_v2", "amount_family": options.family, "pooling_class": "N0_complete", "configuration_id": "lemhi-a10-py311-l40-v1", "configuration_sha256": "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179", "parameter_count": training["parameter_count"], "architecture": {"latent_dim": latent, "width": width, "depth": depth, "amount_head_outputs": 5 if options.family == core.FAMILIES[2] else 2, "splice_threshold_mm": core.THRESHOLD if options.family == core.FAMILIES[2] else None}, "corpus_manifest_sha256": "9de18c4822397ae8a70f827a6a0fa7649bea0c4a8314f6363716fb9bd92f46c2", "normalization_sha256": "bbcfa7d21d484e61cf1540cef5bfecc9d2c920cd9b2f266f405b9aa754264c74", "training_seed": options.seed}
    core.atomic_json(options.output / "model-record.json", model_record)
    core.atomic_json(options.output / "export-metadata.json", {"schema_version": 2, "row_id": options.row_id, "family": options.family, "capacity_id": options.capacity, "training_seed": options.seed, "validation_index": export_model.validation_index, "hidden_size": export_model.transition.hidden_size, "parameter_count": training["parameter_count"], "validation_primary_nll": training["validation_primary_nll"], "validation_tail_score": training["validation_tail_score"], "validation_stability": training["validation_stability"], "gpu_fit_wall_seconds": training["wall_seconds"], "gpu_peak_bytes": training["gpu_peak_bytes"], "export_bytes": export.stat().st_size, "export_sha256": core.sha256(export), "checkpoint_record_sha256": core.sha256(options.output / "checkpoint-record.json"), "model_record_sha256": core.sha256(options.output / "model-record.json"), "trainer_pid": os.getpid(), "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat()})


if __name__ == "__main__": main()
