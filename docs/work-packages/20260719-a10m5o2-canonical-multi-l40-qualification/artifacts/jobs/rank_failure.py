#!/usr/bin/env python3
"""Inject one bounded distributed-rank failure and publish its marker."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    import torch
    import torch.distributed as dist

    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["WORLD_SIZE"])
    if world != 2 or torch.cuda.device_count() != 2:
        raise RuntimeError("controlled failure requires exactly two visible GPUs")
    torch.cuda.set_device(local_rank)
    options.output.mkdir(parents=True, exist_ok=True)
    dist.init_process_group("nccl")
    dist.barrier()
    if rank == 1:
        marker = options.output / "rank-one-failure.json"
        marker.write_text(
            json.dumps({"injected_exit": 7, "rank": 1, "world_size": world}, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    dist.barrier()
    marker = options.output / "rank-one-failure.json"
    ready = options.output / "rank-zero-ready"
    if rank == 0:
        evidence = {
            "classification": "a10m5o2-controlled-rank-failure",
            "gates": {
                "canonical_cuda": torch.version.cuda == "12.8",
                "canonical_torch": torch.__version__ == "2.7.1+cu128",
                "exact_two_devices": torch.cuda.device_count() == 2,
                "failure_injected": marker.exists(),
                "homogeneous_l40": all(
                    "L40" in torch.cuda.get_device_name(index).upper() for index in range(2)
                ),
                "rank_zero_observed_marker": marker.exists(),
                "world_size_two": world == 2,
            },
            "world_size": world,
        }
        temporary = options.output / "evidence.json.part.promote"
        temporary.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, options.output / "evidence.json.part")
        ready.write_text("ready\n", encoding="utf-8")
        time.sleep(30)
        raise RuntimeError("rank one did not terminate the launcher")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not ready.exists():
        time.sleep(0.1)
    os._exit(7 if ready.exists() else 8)


if __name__ == "__main__":
    main()
