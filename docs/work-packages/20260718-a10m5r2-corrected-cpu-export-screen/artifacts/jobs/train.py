#!/usr/bin/env python3
"""Frozen A10M5 trainer phase; persist the CPU export and then exit."""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import torch

import screen_core as core


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    definition = core.configuration(options.config_id)
    if (
        definition["width"] != 128
        or definition["latent_dim"] not in {32, 64}
        or definition["depth"] not in {2, 3}
        or definition["tail_head"] not in {"lognormal", "gpd"}
    ):
        raise RuntimeError("configuration ID outside frozen grid")

    options.output.mkdir(parents=True, exist_ok=True)
    core.configure(147031)
    model, training, checkpoint = core.training(options, definition, options.output)
    model = core.StreamingExport(model.cpu().eval()).eval()
    torch.cuda.empty_cache()
    export = options.output / "model-export.pt"
    traced = torch.jit.trace(
        model,
        (
            torch.zeros((1, 8, 13)),
            torch.tensor([model.validation_index]),
            torch.zeros((1, 1, model.transition.hidden_size)),
        ),
        strict=True,
    )
    traced.save(str(export))

    model_record = {
        "schema_version": 1,
        "model_id": f"a10m5-{options.config_id}-seed147031",
        "family_id": "neural_point_weather_state_space_v1",
        "pooling_class": definition["pooling_class"],
        "configuration_id": "lemhi-a10-py311-l40-v1",
        "configuration_sha256": "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179",
        "parameter_count": training["parameter_count"],
        "architecture": {
            key: definition[key]
            for key in ("latent_dim", "width", "depth", "tail_head")
        },
        "corpus_manifest_sha256": "9de18c4822397ae8a70f827a6a0fa7649bea0c4a8314f6363716fb9bd92f46c2",
        "normalization_sha256": "bbcfa7d21d484e61cf1540cef5bfecc9d2c920cd9b2f266f405b9aa754264c74",
    }
    core.atomic_json(options.output / "model-record.json", model_record)
    core.atomic_json(
        options.output / "export-metadata.json",
        {
            "schema_version": 1,
            "configuration_id": options.config_id,
            "pooling_class": definition["pooling_class"],
            "tail_head": definition["tail_head"],
            "validation_index": model.validation_index,
            "hidden_size": model.transition.hidden_size,
            "export_bytes": export.stat().st_size,
            "export_sha256": core.sha256(export),
            "model_record_sha256": core.sha256(options.output / "model-record.json"),
            "checkpoint_record_sha256": core.sha256(options.output / "checkpoint-record.json"),
            "checkpoint_payload_sha256": checkpoint["payload_sha256"],
            "trainer_pid": os.getpid(),
            "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
    )
    print(f"A10M5R2-TRAINER-COMPLETE {options.config_id}")


if __name__ == "__main__":
    main()
