import json
import os

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel


def main() -> None:
    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ["WORLD_SIZE"])
    if world_size != 2 or torch.cuda.device_count() != 2:
        raise RuntimeError(
            f"expected world/device count 2, got {world_size}/{torch.cuda.device_count()}"
        )
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    if "L40" not in torch.cuda.get_device_name(local_rank).upper():
        raise RuntimeError(f"rank {rank} expected L40")

    dist.init_process_group("nccl")
    collective = torch.tensor(float(rank + 1), device=device)
    dist.all_reduce(collective)
    if float(collective.item()) != 3.0:
        raise RuntimeError(f"all-reduce mismatch: {collective.item()}")

    torch.manual_seed(20260716)
    model = DistributedDataParallel(torch.nn.Linear(3, 1).to(device), device_ids=[local_rank])
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    features = torch.tensor([[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]], device=device)
    target = torch.tensor([[1.0], [2.0]], device=device)
    optimizer.zero_grad(set_to_none=True)
    loss = torch.nn.functional.mse_loss(model(features), target)
    loss.backward()
    optimizer.step()

    flat = torch.cat([parameter.detach().flatten() for parameter in model.module.parameters()])
    gathered = [torch.empty_like(flat) for _ in range(world_size)]
    dist.all_gather(gathered, flat)
    parameter_max_error = float((gathered[0] - gathered[1]).abs().max().item())
    if parameter_max_error != 0.0:
        raise RuntimeError(f"DDP parameter mismatch: {parameter_max_error}")
    dist.barrier()
    if rank == 0:
        print(
            json.dumps(
                {
                    "all_reduce": 3.0,
                    "backend": dist.get_backend(),
                    "ddp_update": "pass",
                    "device_count": torch.cuda.device_count(),
                    "device_names": [torch.cuda.get_device_name(index) for index in range(2)],
                    "j3": "pass",
                    "parameter_max_error": parameter_max_error,
                    "world_size": world_size,
                },
                sort_keys=True,
            )
        )
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
