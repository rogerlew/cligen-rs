#!/usr/bin/env python3
"""Join trainer and fresh-worker evidence after external RSS measurement."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


RSS_LIMIT = 2_147_483_648
EXPORT_LIMIT = 262_144_000


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def external_rss(path: Path) -> int:
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, raw = line.strip().partition(": ")
        if separator and key == "Maximum resident set size (kbytes)":
            return int(raw) * 1024
    raise RuntimeError("external maximum RSS absent")


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".promote")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-predecessors", type=Path, required=True)
    parser.add_argument("--time-v", type=Path, required=True)
    options = parser.parse_args()

    training = json.loads((options.output / "training.json").read_text())
    worker = json.loads((options.output / "worker.json").read_text())
    metadata = json.loads((options.output / "export-metadata.json").read_text())
    model = json.loads((options.output / "model-record.json").read_text())
    checkpoint = json.loads((options.output / "checkpoint-record.json").read_text())
    expected = json.loads(options.expected_predecessors.read_text(encoding="utf-8"))[
        options.config_id
    ]
    time_v_rss = external_rss(options.time_v)
    peak_rss = max(int(worker["vmhwm_bytes"]), time_v_rss)
    score_keys = (
        "validation_primary_nll",
        "validation_tail_score",
        "validation_stability",
    )
    fit_identity = (
        training["parameter_count"] == expected["parameter_count"]
        and all(training[key] == expected[key] for key in score_keys)
    )
    ratios = float(worker["runtime_ratio_max"])
    gates = {
        "all_98_objects_verified": training["object_count"] == 98
        and training["aggregate_bytes"] == 223_799_545,
        "canonical_scientific_record": model["configuration_sha256"]
        == "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179",
        "candidate_fit_only": training["fit_role"] == "candidate_fit"
        and training["normalization_role"] == "candidate_fit",
        "fit_validation_gradient_free": training["validation_used_for_gradient"] is False,
        "finite_scores": all(math.isfinite(float(training[key])) for key in score_keys),
        "fit_identity_exact": fit_identity,
        "parameter_ceiling": training["parameter_count"] <= 50_000_000,
        "checkpoint_complete": checkpoint["state"]
        == {key: True for key in ("model", "optimizer", "scheduler", "scaler", "rng", "sampler")},
        "export_identity": sha256(options.output / "model-export.pt")
        == metadata["export_sha256"],
        "trainer_exited_before_worker": worker["trainer_exited_before_worker"] is True,
        **worker["gates"],
        "own_vmhwm": int(worker["vmhwm_bytes"]) <= RSS_LIMIT,
        "external_maximum_rss": time_v_rss <= RSS_LIMIT,
        "absolute_safeguards": metadata["export_bytes"] <= EXPORT_LIMIT
        and peak_rss <= RSS_LIMIT
        and float(worker["cold_start_seconds"]) <= 15.0
        and worker["gates"]["warm_absolute"],
    }
    evidence = {
        "schema_version": 1,
        "classification": "a10m5r2-development-only-corrected-cpu-export-screen",
        "configuration_id": options.config_id,
        "pooling_class": model["pooling_class"],
        "valid": all(gates.values()),
        "validation_primary_nll": training["validation_primary_nll"],
        "validation_tail_score": training["validation_tail_score"],
        "validation_stability": training["validation_stability"],
        "parameter_count": training["parameter_count"],
        "runtime_ratio_max": ratios,
        "runtime_class_max": worker["runtime_class_max"],
        "checkpoint_record_sha256": sha256(options.output / "checkpoint-record.json"),
        "model_record_sha256": sha256(options.output / "model-record.json"),
        "export_bytes": metadata["export_bytes"],
        "cold_start_seconds": worker["cold_start_seconds"],
        "worker_vmrss_bytes": worker["vmrss_bytes"],
        "worker_vmhwm_bytes": worker["vmhwm_bytes"],
        "external_maximum_rss_bytes": time_v_rss,
        "peak_rss_bytes": peak_rss,
        "gpu_peak_bytes": training["gpu_peak_bytes"],
        "cpu_export_recipe": "trainer exits; shell launches fresh one-core TorchScript worker under /usr/bin/time -v; /proc VmHWM and VmRSS recorded",
        "predecessor_configuration_evidence_sha256": expected["evidence_sha256"],
        "predecessor_benchmark_sha256": expected["benchmark_sha256"],
        "gates": gates,
        "verdict": "PASS" if all(gates.values()) else "FAIL",
    }
    atomic_json(options.output / "evidence.json.part", evidence)
    if not evidence["valid"]:
        raise RuntimeError("A10M5R2 configuration gate failure")


if __name__ == "__main__":
    main()
