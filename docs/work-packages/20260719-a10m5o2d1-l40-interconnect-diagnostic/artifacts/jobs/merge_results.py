#!/usr/bin/env python3
"""Merge topology and NCCL group results into the authenticated gate receipt."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    labels = [
        *(f"pair-{left}{right}-{mode}" for left, right in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)) for mode in ("default", "p2p-disabled")),
        "quad-default",
        "quad-p2p-disabled",
    ]
    results = [json.loads((options.input / f"{label}.json").read_text(encoding="utf-8")) for label in labels]
    topology = (options.input / "topology.txt").read_text(encoding="utf-8")
    p2p_read = (options.input / "p2p-read.txt").read_text(encoding="utf-8")
    p2p_write = (options.input / "p2p-write.txt").read_text(encoding="utf-8")
    p2p_read_status = int((options.input / "p2p-read.status").read_text(encoding="utf-8"))
    p2p_write_status = int((options.input / "p2p-write.status").read_text(encoding="utf-8"))
    inventory = (options.input / "gpu-inventory.csv").read_text(encoding="utf-8")
    finite_positive = all(
        math.isfinite(measurement["bus_gbps"]) and measurement["bus_gbps"] > 0
        for result in results
        for measurement in result["measurements"]
    )
    gates = {
        "all_collectives_correct": all(result["collective_correct"] for result in results),
        "all_groups_complete": len(results) == 14,
        "canonical_cuda": all(result["cuda_runtime"] == "12.8" for result in results),
        "canonical_torch": all(result["torch_version"] == "2.7.1+cu128" for result in results),
        "finite_positive_bandwidth": finite_positive,
        "homogeneous_l40": all(all("L40" in name.upper() for name in result["device_names"]) for result in results),
        "p2p_controls_complete": sum(result["p2p_disabled"] for result in results) == 7,
        "p2p_matrices_captured": p2p_read_status == 0 and p2p_write_status == 0,
        "pair_matrix_complete": sum(result["world_size"] == 2 for result in results) == 12,
        "quad_matrix_complete": sum(result["world_size"] == 4 for result in results) == 2,
        "topology_captured": "GPU0" in topology and "CPU Affinity" in topology,
    }
    value = {
        "classification": "a10m5o2d1-l40-interconnect-diagnostic",
        "gates": gates,
        "gpu_inventory": inventory,
        "p2p_read_matrix": p2p_read,
        "p2p_write_matrix": p2p_write,
        "results": results,
        "topology_matrix": topology,
    }
    options.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = options.output.with_suffix(options.output.suffix + ".promote")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, options.output)
    if not gates or not all(gates.values()):
        raise SystemExit("diagnostic gate failure")


if __name__ == "__main__":
    main()
