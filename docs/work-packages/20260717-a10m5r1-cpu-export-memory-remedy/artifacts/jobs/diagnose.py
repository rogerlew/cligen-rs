#!/usr/bin/env python3
"""Phase-resolved, synthetic A10M5 CPU export memory diagnostic."""

from __future__ import annotations

import argparse
import ctypes
import gc
import hashlib
import json
import os
import re
import resource
import time
from pathlib import Path


RSS_LIMIT = 2_147_483_648
SEED = 147031
VARIANTS = (
    "import-only",
    "load-only",
    "eager",
    "jit-default",
    "jit-unoptimized",
    "jit-mkldnn-off",
    "jit-frozen",
)


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def status() -> dict[str, int]:
    wanted = {"VmRSS", "VmHWM", "VmData", "VmStk", "VmExe", "VmLib", "Threads"}
    values: dict[str, int] = {}
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        key, _, remainder = line.partition(":")
        if key not in wanted:
            continue
        fields = remainder.split()
        values[key] = int(fields[0]) * (1024 if len(fields) > 1 and fields[1] == "kB" else 1)
    return values


def rollup() -> dict[str, int]:
    path = Path("/proc/self/smaps_rollup")
    if not path.is_file():
        return {}
    wanted = {"Rss", "Pss", "Pss_Anon", "Pss_File", "Private_Clean", "Private_Dirty", "Shared_Clean", "Shared_Dirty"}
    values: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, remainder = line.partition(":")
        if key in wanted:
            values[key] = int(remainder.split()[0]) * 1024
    return values


def mapped_rss() -> dict[str, int]:
    path = Path("/proc/self/smaps")
    if not path.is_file():
        return {}
    header = re.compile(r"^[0-9a-f]+-[0-9a-f]+\s")
    categories: dict[str, int] = {}
    category = "anonymous"
    for line in path.read_text(encoding="utf-8").splitlines():
        if header.match(line):
            fields = line.split(None, 5)
            name = fields[5] if len(fields) == 6 else ""
            lowered = name.lower()
            if "site-packages/torch" in lowered:
                category = "torch"
            elif any(token in lowered for token in ("nvidia", "cuda", "cudnn", "cublas")):
                category = "cuda_nvidia"
            elif "site-packages/numpy" in lowered:
                category = "numpy"
            elif name == "[heap]":
                category = "heap"
            elif name.startswith("[stack"):
                category = "stack"
            elif name.startswith("/"):
                category = "other_file"
            else:
                category = "anonymous_other"
        elif line.startswith("Rss:"):
            categories[category] = categories.get(category, 0) + int(line.split()[1]) * 1024
    return categories


def snapshot(phase: str, tensor_bytes: int = 0, output_bytes: int = 0) -> dict[str, object]:
    return {
        "phase": phase,
        "monotonic_seconds": time.perf_counter(),
        "ru_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "status": status(),
        "smaps_rollup": rollup(),
        "mapped_rss_bytes": mapped_rss(),
        "live_tensor_bytes": tensor_bytes,
        "retained_output_bytes": output_bytes,
    }


def configure_torch(torch: object) -> None:
    affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {affinity[0]})
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)


def model_types(torch: object) -> tuple[type, type]:
    nn = torch.nn

    class StateSpace(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(13, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()
            )
            self.transition = nn.GRU(128, 32, batch_first=True)
            self.head = nn.Linear(32, 15)

        def forward(self, features: object, station: object, hidden: object) -> tuple[object, object]:
            del station
            states, next_hidden = self.transition(self.encoder(features).float(), hidden)
            return self.head(states), next_hidden

    class StreamingExport(nn.Module):
        def __init__(self, model: object) -> None:
            super().__init__()
            self.encoder = model.encoder
            self.transition = model.transition
            self.head = model.head

        def forward(self, features: object, station: object, hidden: object) -> tuple[object, object]:
            del station
            states, next_hidden = self.transition(self.encoder(features).float(), hidden)
            return self.head(states), next_hidden

    return StateSpace, StreamingExport


def tensors(torch: object) -> tuple[object, object, object]:
    days = 36_525
    index = torch.arange(days * 13, dtype=torch.float32).reshape(1, days, 13)
    features = torch.sin(index * 0.00017) + torch.cos(index * 0.000031)
    return features, torch.tensor([98]), torch.zeros((1, 1, 32))


def parameter_bytes(model: object) -> int:
    return sum(value.numel() * value.element_size() for value in model.parameters())


def stream(torch: object, model: object, features: object, station: object, hidden: object, optimized: bool) -> tuple[str, int, float, dict[str, object]]:
    digest = hashlib.sha256()
    output_bytes = 0
    first: dict[str, object] = {}
    started = time.perf_counter()
    context = torch.jit.optimized_execution(optimized)
    with torch.inference_mode(), context:
        for offset in range(0, features.shape[1], 365):
            heads, hidden = model(features[:, offset : offset + 365], station, hidden)
            raw = heads.contiguous().numpy().tobytes()
            digest.update(raw)
            output_bytes += len(raw)
            if offset == 0:
                live = features.numel() * features.element_size() + hidden.numel() * hidden.element_size() + heads.numel() * heads.element_size()
                first = snapshot("first-inference", live, output_bytes)
    return digest.hexdigest(), output_bytes, time.perf_counter() - started, first


def build(work: Path) -> None:
    phases = [snapshot("python-start")]
    import torch

    configure_torch(torch)
    phases.append(snapshot("torch-imported"))
    StateSpace, StreamingExport = model_types(torch)
    model = StreamingExport(StateSpace().eval()).eval()
    state_path = work / "state.pt"
    torch.save(model.state_dict(), state_path)
    example = (torch.zeros((1, 8, 13)), torch.tensor([98]), torch.zeros((1, 1, 32)))
    traced = torch.jit.trace(model, example, strict=True)
    export = work / "model-export.pt"
    traced.save(str(export))
    features, station, hidden = tensors(torch)
    phases.append(snapshot("model-and-input-ready", parameter_bytes(model) + features.numel() * features.element_size()))
    digest, output_bytes, warm, first = stream(torch, model, features, station, hidden, True)
    phases.extend((first, snapshot("steady-inference", parameter_bytes(model) + features.numel() * features.element_size(), output_bytes)))
    atomic_json(work / "reference.json", {
        "classification": "a10m5r1-synthetic-development-only",
        "digest_sha256": digest,
        "export_bytes": export.stat().st_size,
        "output_bytes": output_bytes,
        "phases": phases,
        "state_bytes": state_path.stat().st_size,
        "warm_seconds": warm,
    })


def worker(work: Path, variant: str, result: Path) -> None:
    phases = [snapshot("python-start")]
    import torch

    configure_torch(torch)
    if variant == "jit-mkldnn-off":
        torch.backends.mkldnn.enabled = False
    phases.append(snapshot("torch-imported"))
    record: dict[str, object] = {
        "classification": "a10m5r1-synthetic-development-only",
        "variant": variant,
        "mkldnn_enabled": bool(torch.backends.mkldnn.enabled),
        "phases": phases,
    }
    if variant == "import-only":
        atomic_json(result, record)
        return
    if variant.startswith("jit") or variant == "load-only":
        model = torch.jit.load(str(work / "model-export.pt"), map_location="cpu").eval()
        if variant == "jit-frozen":
            model = torch.jit.freeze(model)
    else:
        StateSpace, StreamingExport = model_types(torch)
        model = StreamingExport(StateSpace().eval()).eval()
        model.load_state_dict(torch.load(work / "state.pt", map_location="cpu", weights_only=True))
    model_size = sum(value.numel() * value.element_size() for value in model.parameters())
    phases.append(snapshot("model-loaded", model_size))
    record["model_tensor_bytes"] = model_size
    if variant == "load-only":
        atomic_json(result, record)
        return
    features, station, hidden = tensors(torch)
    optimized = variant != "jit-unoptimized"
    digest, output_bytes, warm, first = stream(torch, model, features, station, hidden, optimized)
    phases.extend((first, snapshot("steady-inference", model_size + features.numel() * features.element_size(), output_bytes)))
    del features, station, hidden, model
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (AttributeError, OSError):
        pass
    phases.append(snapshot("teardown"))
    reference = json.loads((work / "reference.json").read_text(encoding="utf-8"))
    record.update({
        "digest_sha256": digest,
        "exact_reference_identity": digest == reference["digest_sha256"],
        "output_bytes": output_bytes,
        "warm_seconds": warm,
    })
    atomic_json(result, record)


def time_record(path: Path) -> dict[str, object]:
    values: dict[str, object] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, raw = line.strip().partition(": ")
        if not separator:
            continue
        if key == "Maximum resident set size (kbytes)":
            values["maximum_resident_set_bytes"] = int(raw) * 1024
        elif key in {"Elapsed (wall clock) time (h:mm:ss or m:ss)", "Major (requiring I/O) page faults", "Minor (reclaiming a frame) page faults", "Voluntary context switches", "Involuntary context switches"}:
            values[key] = raw
    return values


def aggregate(work: Path, output: Path) -> None:
    reference = json.loads((work / "reference.json").read_text(encoding="utf-8"))
    variants = []
    for variant in VARIANTS:
        record = json.loads((work / f"{variant}.json").read_text(encoding="utf-8"))
        record["time_v"] = time_record(work / f"{variant}.time-v.txt")
        peak = int(record["time_v"]["maximum_resident_set_bytes"])
        record["rss_limit_pass"] = peak <= RSS_LIMIT
        variants.append(record)
    exact_remedies = [
        value["variant"] for value in variants
        if value.get("exact_reference_identity") is True and value["rss_limit_pass"]
    ]
    atomic_json(output, {
        "schema_version": 1,
        "classification": "a10m5r1-synthetic-development-only",
        "reference": reference,
        "variants": variants,
        "exact_remedy_candidates": exact_remedies,
        "rss_limit_bytes": RSS_LIMIT,
        "diagnostic_complete": len(variants) == len(VARIANTS),
        "verdict": "REMEDY-CANDIDATE" if exact_remedies else "NO-REMEDY",
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "worker", "aggregate"):
        child = subparsers.add_parser(command)
        child.add_argument("--work", type=Path, required=True)
        if command == "worker":
            child.add_argument("--variant", choices=VARIANTS, required=True)
            child.add_argument("--result", type=Path, required=True)
        if command == "aggregate":
            child.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    options.work.mkdir(parents=True, exist_ok=True)
    if options.command == "build":
        build(options.work)
    elif options.command == "worker":
        worker(options.work, options.variant, options.result)
    else:
        aggregate(options.work, options.output)


if __name__ == "__main__":
    main()
