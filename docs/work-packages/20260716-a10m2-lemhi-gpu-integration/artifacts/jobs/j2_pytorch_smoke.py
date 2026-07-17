import json
import math
import os
from pathlib import Path

import torch


def main() -> None:
    if torch.cuda.device_count() != 1:
        raise RuntimeError(f"expected one CUDA device, got {torch.cuda.device_count()}")
    if "L40" not in torch.cuda.get_device_name(0).upper():
        raise RuntimeError(f"expected L40, got {torch.cuda.get_device_name(0)}")

    torch.manual_seed(20260716)
    torch.cuda.manual_seed_all(20260716)
    device = torch.device("cuda:0")
    model = torch.nn.Linear(4, 2).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
    features = torch.arange(32, dtype=torch.float32, device=device).reshape(8, 4) / 31.0
    target = torch.stack((features.sum(dim=1), features[:, 0] - features[:, 3]), dim=1)

    optimizer.zero_grad(set_to_none=True)
    loss_before = torch.nn.functional.mse_loss(model(features), target)
    loss_before.backward()
    gradient_norm = math.sqrt(
        sum(float(parameter.grad.detach().square().sum().item()) for parameter in model.parameters())
    )
    optimizer.step()
    loss_after = torch.nn.functional.mse_loss(model(features), target)
    if not all(math.isfinite(value) for value in (float(loss_before), float(loss_after), gradient_norm)):
        raise RuntimeError("nonfinite training diagnostic")
    if not float(loss_after) < float(loss_before):
        raise RuntimeError("optimizer step did not decrease the registered loss")

    checkpoint = Path(os.environ["A10M2_CHECKPOINT"])
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict()}, checkpoint)
    reloaded = torch.nn.Linear(4, 2).to(device)
    payload = torch.load(checkpoint, map_location=device, weights_only=True)
    reloaded.load_state_dict(payload["model"])
    max_reload_error = max(
        float((left - right).abs().max().item())
        for left, right in zip(model.parameters(), reloaded.parameters(), strict=True)
    )
    if max_reload_error != 0.0:
        raise RuntimeError(f"checkpoint reload mismatch: {max_reload_error}")

    print(
        json.dumps(
            {
                "checkpoint_reload": "pass",
                "cuda_runtime": torch.version.cuda,
                "cudnn": torch.backends.cudnn.version(),
                "device_count": torch.cuda.device_count(),
                "device_name": torch.cuda.get_device_name(0),
                "gradient_norm": gradient_norm,
                "j2": "pass",
                "loss_after": float(loss_after),
                "loss_before": float(loss_before),
                "pytorch": torch.__version__,
                "reload_max_error": max_reload_error,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
