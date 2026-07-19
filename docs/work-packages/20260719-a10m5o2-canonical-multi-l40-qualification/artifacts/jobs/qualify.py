#!/usr/bin/env python3
"""Canonical single-node NCCL/DDP correctness and bounded scaling probe."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import sysconfig
import time
from pathlib import Path


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".promote")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def benchmark(torch, dist, ddp_type, device, local_rank: int, world: int, local_batch: int) -> dict[str, object]:
    dimension = 4096
    model = torch.nn.Sequential(
        torch.nn.Linear(dimension, dimension, bias=False),
        torch.nn.GELU(),
        torch.nn.Linear(dimension, dimension, bias=False),
    ).to(device)
    model = ddp_type(model, device_ids=[local_rank])
    optimizer = torch.optim.SGD(model.parameters(), lr=0.0001)
    generator = torch.Generator(device=device).manual_seed(1729 + local_rank)
    features = torch.randn((local_batch, dimension), generator=generator, device=device)
    target = torch.randn((local_batch, dimension), generator=generator, device=device)

    def step() -> None:
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(model(features), target)
        loss.backward()
        optimizer.step()

    for _ in range(2):
        step()
    torch.cuda.synchronize(device)
    throughputs: list[float] = []
    elapsed_values: list[float] = []
    for _ in range(3):
        dist.barrier()
        started = time.perf_counter()
        for _ in range(5):
            step()
        torch.cuda.synchronize(device)
        elapsed = torch.tensor(time.perf_counter() - started, dtype=torch.float64, device=device)
        dist.all_reduce(elapsed, op=dist.ReduceOp.MAX)
        seconds = float(elapsed.item())
        elapsed_values.append(seconds)
        throughputs.append(float(local_batch * world * 5) / seconds)
    return {
        "elapsed_seconds": elapsed_values,
        "examples_per_second": throughputs,
        "median_examples_per_second": statistics.median(throughputs),
        "local_batch": local_batch,
        "global_batch": local_batch * world,
        "measured_steps": 5,
        "repetitions": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-world", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--role", required=True)
    options = parser.parse_args()

    import numpy as np
    import torch
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel

    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["WORLD_SIZE"])
    options.output.mkdir(parents=True, exist_ok=True)
    if world != options.expected_world:
        raise RuntimeError(f"world mismatch: {world} != {options.expected_world}")
    if torch.cuda.device_count() != world:
        raise RuntimeError(f"visible device mismatch: {torch.cuda.device_count()} != {world}")
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    names = [torch.cuda.get_device_name(index) for index in range(world)]
    if any("L40" not in name.upper() for name in names):
        raise RuntimeError(f"non-L40 device: {names}")

    torch.manual_seed(20260719)
    torch.cuda.manual_seed_all(20260719)
    torch.use_deterministic_algorithms(True)
    dist.init_process_group("nccl")
    try:
        collective = torch.tensor(float(rank + 1), device=device)
        dist.all_reduce(collective)
        expected_sum = float(world * (world + 1) // 2)
        broadcast = torch.tensor(-1.0 if rank else 42.0, device=device)
        dist.broadcast(broadcast, src=0)
        dist.barrier()

        torch.manual_seed(314159)
        correctness = DistributedDataParallel(
            torch.nn.Linear(4, 2).to(device), device_ids=[local_rank]
        )
        optimizer = torch.optim.SGD(correctness.parameters(), lr=0.01)
        features = torch.tensor(
            [[1.0 + rank, 2.0, 3.0, 4.0], [2.0, 3.0 + rank, 4.0, 5.0]],
            device=device,
        )
        target = torch.tensor([[1.0, 0.0], [0.0, 1.0]], device=device)
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(correctness(features), target)
        loss.backward()
        optimizer.step()
        flat = torch.cat(
            [parameter.detach().flatten() for parameter in correctness.module.parameters()]
        )
        gathered = [torch.empty_like(flat) for _ in range(world)]
        dist.all_gather(gathered, flat)
        parameters_synchronized = all(torch.equal(gathered[0], value) for value in gathered[1:])

        checkpoint = options.output / "checkpoint.pt"
        if rank == 0:
            torch.save({"parameters": flat.cpu(), "world": world}, checkpoint)
        dist.barrier()
        restored = torch.load(checkpoint, map_location="cpu", weights_only=True)
        checkpoint_reload = restored["world"] == world and torch.equal(restored["parameters"], flat.cpu())
        dist.barrier()
        if rank == 0:
            checkpoint.unlink()

        strong = benchmark(
            torch,
            dist,
            DistributedDataParallel,
            device,
            local_rank,
            world,
            512 // world,
        )
        weak = benchmark(
            torch,
            dist,
            DistributedDataParallel,
            device,
            local_rank,
            world,
            256,
        )
        torch.cuda.synchronize(device)
        visible = [item for item in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if item]
        binding = visible[local_rank] if len(visible) == world else str(local_rank)
        rank_record = {
            "binding": binding,
            "device_name": torch.cuda.get_device_name(local_rank),
            "hostname": os.uname().nodename,
            "local_rank": local_rank,
            "max_memory_allocated": torch.cuda.max_memory_allocated(device),
            "rank": rank,
        }
        atomic_json(options.output / f"rank-{rank}.json", rank_record)
        dist.barrier()

        if rank == 0:
            rank_records = [
                json.loads((options.output / f"rank-{index}.json").read_text(encoding="utf-8"))
                for index in range(world)
            ]
            bindings = [record["binding"] for record in rank_records]
            gates = {
                "all_reduce_correct": float(collective.item()) == expected_sum,
                "broadcast_correct": float(broadcast.item()) == 42.0,
                "canonical_cuda": torch.version.cuda == "12.8",
                "canonical_numpy": np.__version__ == "2.2.6",
                "canonical_python": sys.version_info[:3] == (3, 11, 15)
                and str(sysconfig.get_config_var("SOABI")).startswith("cpython-311"),
                "canonical_torch": torch.__version__ == "2.7.1+cu128",
                "checkpoint_reload": checkpoint_reload,
                "ddp_parameters_synchronized": parameters_synchronized,
                "homogeneous_l40": len(names) == world
                and all("L40" in name.upper() for name in names),
                "nccl_backend": dist.get_backend() == "nccl",
                "one_process_per_gpu": len(rank_records) == world
                and sorted(record["local_rank"] for record in rank_records) == list(range(world)),
                "single_node": len({record["hostname"] for record in rank_records}) == 1,
                "unique_device_bindings": len(set(bindings)) == world,
                "world_size": world == options.expected_world,
            }
            evidence = {
                "classification": "a10m5o2-canonical-single-node-multi-l40",
                "cuda_runtime": torch.version.cuda,
                "device_names": names,
                "gates": gates,
                "nccl_version": list(torch.cuda.nccl.version()),
                "numpy_version": np.__version__,
                "rank_records": rank_records,
                "role": options.role,
                "scaling": {"fixed_global_work": strong, "fixed_per_gpu_work": weak},
                "torch_version": torch.__version__,
                "world_size": world,
            }
            atomic_json(options.output / "evidence.json.part", evidence)
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
