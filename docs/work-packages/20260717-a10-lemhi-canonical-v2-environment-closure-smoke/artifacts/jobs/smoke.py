#!/usr/bin/env python3
"""Compute-side CPython, NumPy, and one-L40 canonical-v2 smoke."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import multiprocessing
import os
import sqlite3
import ssl
import subprocess
import sys
import tempfile
from pathlib import Path


CANDIDATE_SHA256 = "5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--configuration-sha256", required=True)
    options = parser.parse_args()

    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("deterministic CUDA environment was not established")
    if any(name in os.environ for name in ("PYTHONPATH", "PYTHONHOME", "LD_LIBRARY_PATH")):
        raise RuntimeError("prohibited ambient Python or loader state")

    import numpy as np
    import torch

    array = np.arange(12, dtype=np.float32).reshape(3, 4)
    bridged = torch.from_numpy(array)
    device_ok = torch.cuda.is_available() and torch.cuda.device_count() == 1 and "L40" in torch.cuda.get_device_name(0)
    if not device_ok:
        raise RuntimeError("exactly one L40 is required")

    torch.manual_seed(147031)
    torch.cuda.manual_seed_all(147031)
    torch.use_deterministic_algorithms(True)
    layer = torch.nn.Linear(4, 2).cuda()
    value = bridged.cuda().requires_grad_(True)
    loss = layer(value).square().mean()
    loss.backward()
    if not bool(torch.isfinite(value.grad).all()):
        raise RuntimeError("non-finite CUDA autograd result")

    with tempfile.TemporaryDirectory() as temporary:
        checkpoint = Path(temporary) / "checkpoint.pt"
        torch.save({"model": layer.state_dict(), "seed": 147031}, checkpoint)
        restored = torch.load(checkpoint, map_location="cpu", weights_only=True)
        checkpoint_ok = restored["seed"] == 147031 and set(restored["model"]) == set(layer.state_dict())
        checkpoint_hash = sha256(checkpoint)

    subprocess.run([sys.executable, "-c", "import ssl,sqlite3,ctypes,multiprocessing"], check=True)
    process = multiprocessing.get_context("spawn").Process(target=str, args=("smoke",))
    process.start()
    process.join(30)

    gates = {
        "canonical_candidate": options.configuration_sha256 == CANDIDATE_SHA256,
        "cpython_3_11_15": sys.version_info[:3] == (3, 11, 15),
        "stdlib_native_modules": bool(ssl.OPENSSL_VERSION) and sqlite3.sqlite_version_info > (3, 0, 0) and bool(ctypes.sizeof(ctypes.c_void_p)),
        "subprocess": True,
        "multiprocessing": process.exitcode == 0,
        "numpy_2_2_6": np.__version__ == "2.2.6" and np.array_equal(bridged.numpy(), array),
        "torch_2_7_1_cu128": torch.__version__ == "2.7.1+cu128" and torch.version.cuda == "12.8",
        "one_l40": device_ok,
        "cuda_tensor_autograd": bool(torch.isfinite(loss).item()) and bool(torch.isfinite(value.grad).all()),
        "checkpoint_roundtrip": checkpoint_ok and len(checkpoint_hash) == 64,
        "offline_environment": os.environ.get("PIP_NO_INDEX") == "1" and os.environ.get("CARGO_NET_OFFLINE") == "true",
        "environment_closed": os.environ.get("PYTHONNOUSERSITE") == "1",
    }
    result = {
        "configuration_semantic_sha256": options.configuration_sha256,
        "gates": gates,
        "numpy_version": np.__version__,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "torch_cuda_version": torch.version.cuda,
        "torch_version": torch.__version__,
    }
    temporary = options.output.with_suffix(".json.part")
    temporary.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, options.output)
    if not all(gates.values()):
        raise RuntimeError("one or more compute smoke gates failed")


if __name__ == "__main__":
    main()
