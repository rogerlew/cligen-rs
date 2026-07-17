#!/usr/bin/env python3
"""Bounded CPython/NumPy/PyTorch validation; emits sanitized JSON only."""

from __future__ import annotations

import argparse
import ctypes
import json
import multiprocessing
import os
import sqlite3
import ssl
import subprocess
import sys
import sysconfig
import venv
from pathlib import Path


def child(queue: multiprocessing.Queue) -> None:
    queue.put((sys.version_info[:2], 6 * 7))


def linked_without_missing(path: Path) -> bool:
    result = subprocess.run(["ldd", str(path)], check=False, capture_output=True, text=True)
    return result.returncode == 0 and "not found" not in result.stdout and "not found" not in result.stderr


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()

    import numpy as np
    import torch

    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=child, args=(queue,))
    process.start()
    child_result = queue.get(timeout=10)
    process.join(timeout=10)
    native_paths = [Path(np._core._multiarray_umath.__file__)]

    array = np.arange(9, dtype=np.float32).reshape(3, 3)
    product = array @ array.T
    shared = torch.from_numpy(array)
    shared[0, 0] = 11.0

    device = torch.device("cuda:0")
    parameter = torch.tensor([3.0], device=device, requires_grad=True)
    optimizer = torch.optim.SGD([parameter], lr=0.1)
    initial = float((parameter.square()).detach().cpu())
    optimizer.zero_grad()
    parameter.square().backward()
    optimizer.step()
    final = float((parameter.square()).detach().cpu())
    options.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"parameter": parameter.detach().cpu(), "numpy_sum": float(product.sum())}, options.checkpoint)
    restored = torch.load(options.checkpoint, map_location="cpu", weights_only=True)

    gates = {
        "abi_cp311": sysconfig.get_config_var("SOABI").startswith("cpython-311"),
        "autograd_update": final < initial,
        "checkpoint_reload": float(restored["parameter"][0]) == float(parameter.detach().cpu()[0]),
        "cuda_available": torch.cuda.is_available(),
        "ctypes": ctypes.sizeof(ctypes.c_void_p) == 8,
        "exact_python": sys.version_info[:3] == (3, 11, 15),
        "isolated_environment": not os.environ.get("PYTHONPATH") and not os.environ.get("PYTHONHOME") and not os.environ.get("LD_LIBRARY_PATH"),
        "multiprocessing_spawn": process.exitcode == 0 and child_result == ((3, 11), 42),
        "native_linkage": all(linked_without_missing(path) for path in native_paths),
        "numpy": np.__version__ == "2.2.6" and float(product[0, 0]) == 5.0,
        "numpy_torch_interop": float(array[0, 0]) == 11.0 and float(shared[0, 0]) == 11.0,
        "one_l40": torch.cuda.device_count() == 1 and "L40" in torch.cuda.get_device_name(0),
        "ssl": bool(ssl.OPENSSL_VERSION),
        "sqlite": sqlite3.connect(":memory:").execute("select 42").fetchone()[0] == 42,
        "subprocess": subprocess.run([sys.executable, "-c", "raise SystemExit(0)"], check=False).returncode == 0,
        "torch_cuda_tensor": torch.__version__ == "2.7.1+cu128" and parameter.is_cuda,
        "venv": isinstance(venv.EnvBuilder(with_pip=True), venv.EnvBuilder),
    }
    evidence = {
        "classification": "development-only",
        "cuda_runtime": torch.version.cuda,
        "gates": gates,
        "numpy_version": np.__version__,
        "python_implementation": sys.implementation.name,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "torch_version": torch.__version__,
        "verdict": "PASS" if all(gates.values()) else "FAIL",
    }
    options.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not all(gates.values()):
        raise SystemExit("smoke gate failed")


if __name__ == "__main__":
    main()
