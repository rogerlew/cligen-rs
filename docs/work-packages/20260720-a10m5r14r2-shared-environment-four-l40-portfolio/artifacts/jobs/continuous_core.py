#!/usr/bin/env python3
"""R14R2 interface wrapper around the byte-identical inherited R14 core."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().with_name("inherited_r14_continuous_core.py")
ACCOUNTING = Path(__file__).resolve().with_name("parameter_accounting.py")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load authenticated R14R2 dependency: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inherited = load("inherited_r14_continuous_core", SOURCE)
accounting = load("r14r2_parameter_accounting", ACCOUNTING)
for exported_name in dir(inherited):
    if not exported_name.startswith("_"):
        globals()[exported_name] = getattr(inherited, exported_name)


def train_candidate(contract, candidate, *args, **kwargs):
    model, result = inherited.train_candidate(contract, candidate, *args, **kwargs)
    adapter_count = sum(parameter.numel() for parameter in model.parameters())
    return model, accounting.repair(result, candidate, adapter_count)
