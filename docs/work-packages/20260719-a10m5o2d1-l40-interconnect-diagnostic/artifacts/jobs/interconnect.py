#!/usr/bin/env python3
"""Measure one NCCL group with deterministic resident tensors."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".promote")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-world", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()

    import torch
    import torch.distributed as dist

    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["WORLD_SIZE"])
    if world != options.expected_world or torch.cuda.device_count() != world:
        raise RuntimeError("world/visibility mismatch")
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    dist.init_process_group("nccl")
    try:
        names = [torch.cuda.get_device_name(index) for index in range(world)]
        scalar = torch.tensor(float(rank + 1), device=device)
        dist.all_reduce(scalar)
        collective_correct = float(scalar.item()) == float(world * (world + 1) // 2)
        peer_access = [
            bool(torch.cuda.can_device_access_peer(local_rank, other))
            if other != local_rank
            else True
            for other in range(world)
        ]
        local = {
            "binding": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
            "device_name": torch.cuda.get_device_name(local_rank),
            "local_rank": local_rank,
            "peer_access": peer_access,
            "rank": rank,
        }
        ranks: list[object] = [None] * world
        dist.all_gather_object(ranks, local)

        measurements = []
        for byte_count in (1 << 20, 16 << 20, 128 << 20):
            tensor = torch.zeros(byte_count // 4, dtype=torch.float32, device=device)
            for _ in range(3):
                dist.all_reduce(tensor)
            torch.cuda.synchronize(device)
            elapsed_values = []
            for _ in range(3):
                tensor.zero_()
                dist.barrier()
                started = time.perf_counter()
                for _ in range(10):
                    dist.all_reduce(tensor)
                torch.cuda.synchronize(device)
                elapsed = torch.tensor(time.perf_counter() - started, dtype=torch.float64, device=device)
                dist.all_reduce(elapsed, op=dist.ReduceOp.MAX)
                elapsed_values.append(float(elapsed.item()))
            median_seconds = statistics.median(elapsed_values)
            algorithm_gbps = byte_count * 10 / median_seconds / 1_000_000_000
            bus_gbps = algorithm_gbps * 2 * (world - 1) / world
            measurements.append(
                {
                    "algorithm_gbps": algorithm_gbps,
                    "bus_gbps": bus_gbps,
                    "bytes": byte_count,
                    "elapsed_seconds": elapsed_values,
                    "iterations": 10,
                    "median_seconds": median_seconds,
                }
            )
            del tensor
        if rank == 0:
            atomic_json(
                options.output / f"{options.label}.json",
                {
                    "collective_correct": collective_correct,
                    "cuda_runtime": torch.version.cuda,
                    "device_names": names,
                    "label": options.label,
                    "measurements": measurements,
                    "nccl_version": list(torch.cuda.nccl.version()),
                    "p2p_disabled": os.environ.get("NCCL_P2P_DISABLE") == "1",
                    "ranks": ranks,
                    "torch_version": torch.__version__,
                    "world_size": world,
                },
            )
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
