#!/usr/bin/env python3
"""Fresh-address-space A10M5R2 CPU export and benchmark worker."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import torch

import screen_core as core


class ExportAdapter:
    """Expose the attributes used by the frozen generation helper."""

    def __init__(self, module: Any, validation_index: int, hidden_size: int) -> None:
        self.module = module
        self.validation_index = validation_index
        self.transition = SimpleNamespace(hidden_size=hidden_size)

    def __call__(
        self, features: torch.Tensor, station: torch.Tensor, hidden: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        return self.module(features, station, hidden)


def process_status() -> dict[str, int]:
    wanted = {"VmRSS", "VmHWM", "Threads"}
    values: dict[str, int] = {}
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        key, separator, remainder = line.partition(":")
        if separator and key in wanted:
            fields = remainder.split()
            multiplier = 1024 if len(fields) > 1 and fields[1] == "kB" else 1
            values[key] = int(fields[0]) * multiplier
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--faithful-binary", type=Path, required=True)
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--expected-predecessors", type=Path, required=True)
    parser.add_argument("--trainer-exited-marker", type=Path, required=True)
    options = parser.parse_args()

    if not options.trainer_exited_marker.is_file():
        raise RuntimeError("trainer exit marker absent")
    if torch.cuda.is_available() or torch.cuda.device_count() != 0:
        raise RuntimeError("GPU must be hidden from the CPU export worker")
    affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {affinity[0]})
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)

    metadata = json.loads((options.output / "export-metadata.json").read_text())
    if metadata["configuration_id"] != options.config_id:
        raise RuntimeError("export metadata configuration mismatch")
    cold_started = time.perf_counter()
    module = torch.jit.load(str(options.output / "model-export.pt"), map_location="cpu").eval()
    cold_seconds = time.perf_counter() - cold_started
    model = ExportAdapter(
        module, int(metadata["validation_index"]), int(metadata["hidden_size"])
    )

    smoke = core.candidate_stream(model, metadata["tail_head"], core.STATIONS[0], 1)
    streams = {
        station[1]: core.candidate_stream(model, metadata["tail_head"], station, 100)
        for station in core.STATIONS
    }
    prefix_days = core.days_for_years(30)
    prefix_exact = all(
        core.candidate_stream(model, metadata["tail_head"], station, 30)[1]
        == streams[station[1]][1][: prefix_days * 8 * 4]
        for station in core.STATIONS
    )
    reverse = {
        station[1]: core.candidate_stream(model, metadata["tail_head"], station, 100)[0]
        for station in reversed(core.STATIONS)
    }
    order_exact = all(streams[key][0] == reverse[key] for key in streams)
    benchmark = core.benchmark(
        model,
        metadata["tail_head"],
        options.faithful_binary,
        options.parameters,
        options.output / "benchmark-work",
    )
    core.atomic_json(options.output / "benchmark.json", benchmark)

    expected = json.loads(options.expected_predecessors.read_text(encoding="utf-8"))[
        options.config_id
    ]
    observed_identities = [
        {key: row[key] for key in ("station_id", "horizon_years", "candidate_identity")}
        for row in benchmark["rows"]
    ]
    ratios = [float(row["ratio"]) for row in benchmark["rows"]]
    warm_absolute = all(
        row["candidate_median_seconds"]
        <= (10.0 if row["horizon_years"] == 30 else 30.0)
        for row in benchmark["rows"]
    )
    status = process_status()
    worker = {
        "schema_version": 1,
        "classification": "a10m5r2-clean-cpu-export-worker",
        "configuration_id": options.config_id,
        "worker_pid": os.getpid(),
        "worker_parent_pid": os.getppid(),
        "trainer_pid": metadata["trainer_pid"],
        "trainer_exited_before_worker": options.trainer_exited_marker.is_file(),
        "cuda_hidden": not torch.cuda.is_available() and torch.cuda.device_count() == 0,
        "affinity": sorted(os.sched_getaffinity(0)),
        "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "cold_start_seconds": cold_seconds,
        "vmrss_bytes": status["VmRSS"],
        "vmhwm_bytes": status["VmHWM"],
        "threads_at_exit": status["Threads"],
        "runtime_ratio_max": max(ratios),
        "runtime_class_max": (
            "PASS" if max(ratios) < 5.0 else "WARN" if max(ratios) < 10.0 else "FAIL"
        ),
        "candidate_mad_over_median_max": max(
            float(row["candidate_mad_over_median"]) for row in benchmark["rows"]
        ),
        "faithful_mad_over_median_max": max(
            float(row["faithful_mad_over_median"]) for row in benchmark["rows"]
        ),
        "candidate_identity_exact": observed_identities == expected["identities"],
        "observed_identities": observed_identities,
        "gates": {
            "trainer_exited_before_worker": options.trainer_exited_marker.is_file(),
            "cuda_hidden": not torch.cuda.is_available() and torch.cuda.device_count() == 0,
            "one_core": len(os.sched_getaffinity(0)) == 1,
            "one_thread": torch.get_num_threads() == 1
            and torch.get_num_interop_threads() == 1,
            "generation_support": smoke[2] and all(value[2] for value in streams.values()),
            "generation_prefix_exact": prefix_exact,
            "generation_order_independent": order_exact,
            "benchmark_complete": len(benchmark["rows"]) == 12
            and all(row["complete"] for row in benchmark["rows"]),
            "benchmark_dispersion": all(
                row["candidate_mad_over_median"] <= 0.10
                and row["faithful_mad_over_median"] <= 0.10
                for row in benchmark["rows"]
            ),
            "candidate_identity_exact": observed_identities == expected["identities"],
            "warm_absolute": warm_absolute,
        },
        "candidate_median_seconds_max": max(
            float(row["candidate_median_seconds"]) for row in benchmark["rows"]
        ),
        "candidate_median_seconds_median": statistics.median(
            float(row["candidate_median_seconds"]) for row in benchmark["rows"]
        ),
    }
    core.atomic_json(options.output / "worker.json", worker)
    if not all(worker["gates"].values()):
        raise RuntimeError("clean CPU worker scientific gate failure")
    print(f"A10M5R2-CPU-WORKER-COMPLETE {options.config_id}")


if __name__ == "__main__":
    main()
