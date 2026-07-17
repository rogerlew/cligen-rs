import json
import os
from pathlib import Path

import torch


def main() -> None:
    if torch.cuda.device_count() != 1:
        raise RuntimeError(f"expected one CUDA device, got {torch.cuda.device_count()}")
    device_name = torch.cuda.get_device_name(0)
    if "L40" not in device_name.upper():
        raise RuntimeError(f"expected L40, got {device_name}")

    torch.manual_seed(20260717)
    torch.cuda.manual_seed_all(20260717)
    device = torch.device("cuda:0")
    model = torch.nn.Linear(4, 2).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
    features = torch.arange(32, dtype=torch.float32, device=device).reshape(8, 4) / 31.0
    target = torch.stack((features.sum(dim=1), features[:, 0] - features[:, 3]), dim=1)

    optimizer.zero_grad(set_to_none=True)
    loss_before = torch.nn.functional.mse_loss(model(features), target)
    loss_before.backward()
    optimizer.step()
    with torch.no_grad():
        loss_after = torch.nn.functional.mse_loss(model(features), target)
    if not torch.isfinite(loss_before) or not torch.isfinite(loss_after):
        raise RuntimeError("non-finite loss")
    if not float(loss_after) < float(loss_before):
        raise RuntimeError("one optimizer step did not lower loss")

    checkpoint = Path(os.environ["A10M2_CHECKPOINT"])
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict()}, checkpoint)
    reloaded = torch.nn.Linear(4, 2).to(device)
    payload = torch.load(checkpoint, map_location=device, weights_only=True)
    reloaded.load_state_dict(payload["model"])
    for expected, actual in zip(model.parameters(), reloaded.parameters(), strict=True):
        if not torch.equal(expected, actual):
            raise RuntimeError("checkpoint reload differs")

    print(
        json.dumps(
            {
                "cuda_runtime": torch.version.cuda,
                "cudnn": torch.backends.cudnn.version(),
                "device_count": torch.cuda.device_count(),
                "device_name": device_name,
                "loss_after": float(loss_after),
                "loss_before": float(loss_before),
                "pytorch": torch.__version__,
                "smoke": "pass",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
