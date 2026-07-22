#!/usr/bin/env python3
"""Bind the R14 experiment writer to A10M5R15R2 conditioning semantics."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import sys
from pathlib import Path

import continuous_core as continuous
import portfolio_core as portfolio
import torch


SOURCE = Path(__file__).resolve().with_name("inherited_r15_candidate_experiment.py")
spec = importlib.util.spec_from_file_location("inherited_r15_candidate_experiment", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited candidate experiment")
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)


def argument(name: str) -> str:
    try:
        return sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as error:
        raise RuntimeError(f"required argument missing: {name}") from error


candidate = argument("--candidate")
run_root = Path(argument("--run-root"))
output_root = Path(argument("--output"))
controls_root = Path(argument("--controls"))
uses_normals = candidate in (continuous.CANDIDATES[1], continuous.CANDIDATES[3])
if uses_normals:
    continuous.load_conditioning(run_root)


base_backbone_capacity = portfolio.backbone_capacity


def backbone_capacity(contract, capacity):
    if candidate in continuous.CANDIDATES[2:]:
        return "NONE"
    return base_backbone_capacity(contract, capacity)


portfolio.backbone_capacity = backbone_capacity
base_find_control = parent.find_control


def find_control(summary, capacity, seed):
    if capacity != "NONE":
        return base_find_control(summary, capacity, seed)
    row = dict(base_find_control(summary, "P2", seed))
    row["capacity_id"] = "NONE"
    row["parameter_count"] = 0
    return row


parent.find_control = find_control
base_generate = parent.generate_site_streams


def generate_site_streams(model, control, hidden_size, site, seed, generation, device):
    original_forward = portfolio.forward_control
    if model.uses_normals:
        continuous.set_generation_point(site["point_id"])
    if not model.uses_p2:
        portfolio.forward_control = lambda frozen, features, station, width: None
    try:
        return base_generate(model, control, hidden_size, site, seed, generation, device)
    finally:
        portfolio.forward_control = original_forward
        if model.uses_normals:
            continuous.set_generation_point(None)


parent.generate_site_streams = generate_site_streams


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping_hash(checkpoint: Path) -> str | None:
    if candidate not in (continuous.CANDIDATES[1], continuous.CANDIDATES[3]):
        return None
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    selected = {
        name: value
        for name, value in state.items()
        if any(
            token in name
            for token in (
                "climatology_heads",
                "descriptor_baseline",
                "nonlocation_baseline",
                "location_baseline",
            )
        )
    }
    if not selected:
        raise RuntimeError("conditioned mapping weights absent from checkpoint")
    value = hashlib.sha256()
    for name, tensor in sorted(selected.items()):
        array = tensor.detach().cpu().contiguous().numpy()
        value.update(name.encode("utf-8") + b"\0")
        value.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
        value.update(str(array.dtype).encode("ascii") + b"\0")
        value.update(array.tobytes())
    return value.hexdigest()


def provenance(seed: int | None, fitted_mapping_sha256: str | None) -> dict:
    contract = json.loads((run_root / "execution-contract.json").read_text(encoding="utf-8"))
    arm = next(row for row in contract["arms"] if row["candidate"] == candidate)
    calendar_path = output_root / "calendar-preflight.json"
    conditioning = dict(contract["conditioning"]) if uses_normals else None
    return {
        "calendar": {
            "preflight_sha256": digest(calendar_path),
            "profile_id": "daymet_official_365_v1",
        },
        "corpus": contract["corpus"],
        "mapping_sha256": fitted_mapping_sha256,
        "model": {
            "arm": arm["arm"],
            "candidate": candidate,
            "role": arm["role"],
        },
        "normals_bundle": conditioning,
        "normals_excluded": not uses_normals,
        "normals_window_limitation": (
            "PRISM Norm91m 1991-2020 monthly normals are fixed climatological "
            "conditioning covariates and do not represent conditions outside that window."
            if uses_normals
            else "No normals were requested, loaded, appended, or consumed by this control arm."
        ),
        "runtime_classification": "PENDING-NORMATIVE-ADR-0006-BENCHMARK",
        "seed": seed,
    }


def publish_provenance() -> None:
    contract = json.loads((run_root / "execution-contract.json").read_text(encoding="utf-8"))
    arm = next(row for row in contract["arms"] if row["candidate"] == candidate)
    if arm["uses_normals"] is not uses_normals:
        raise RuntimeError("candidate conditioning role drift")
    if arm["parameter_count"] > (340_000 if arm["uses_p2"] else 330_000):
        raise RuntimeError("per-arm parameter ceiling exceeded")
    mapping_by_seed = {
        seed: mapping_hash(output_root / "seed-work" / str(seed) / "checkpoint.pt")
        for seed in (147031, 271828, 314159)
    }
    if arm["uses_p2"]:
        control_summary = json.loads(
            (controls_root / "control-summary.json").read_text(encoding="utf-8")
        )
        for seed in (147031, 271828, 314159):
            row = next(
                item
                for item in control_summary["models"]
                if item["capacity_id"] == "P2" and item["training_seed"] == seed
            )
            source = controls_root / row["model_directory"] / "model-export.pt"
            target = output_root / "seed-work" / str(seed) / "control-export.pt"
            shutil.copy2(source, target)
            if digest(target) != row["export_sha256"]:
                raise RuntimeError("portable P2 control export identity drift")
    for seed, fitted_mapping_sha256 in mapping_by_seed.items():
        path = output_root / "seeds" / f"{seed}.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["provenance"] = provenance(seed, fitted_mapping_sha256)
        portfolio.atomic_json(path, value)
    training_path = output_root / "training.json"
    training = json.loads(training_path.read_text(encoding="utf-8"))
    for row in training["seeds"]:
        row["provenance"] = provenance(row["seed"], mapping_by_seed[row["seed"]])
        row["portable_control_export_sha256"] = (
            digest(output_root / "seed-work" / str(row["seed"]) / "control-export.pt")
            if arm["uses_p2"]
            else None
        )
    training["provenance_contract"] = "SPEC-A10-EXTERNAL-NORMAL-CONDITIONING-rev2"
    portfolio.atomic_json(training_path, training)
    streams_path = output_root / "streams.json"
    streams = json.loads(streams_path.read_text(encoding="utf-8"))
    streams["configuration_id"] = arm["configuration_id"]
    for row in streams["streams"]:
        row["provenance"] = provenance(
            row["training_seed"], mapping_by_seed[row["training_seed"]]
        )
    streams["provenance_contract"] = "SPEC-A10-EXTERNAL-NORMAL-CONDITIONING-rev2"
    portfolio.atomic_json(streams_path, streams)
    summary_path = output_root / "candidate-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["configuration_id"] = arm["configuration_id"]
    summary["provenance"] = provenance(None, None)
    portfolio.atomic_json(summary_path, summary)
    part_path = output_root / "evidence.json.part"
    evidence = json.loads(part_path.read_text(encoding="utf-8"))
    evidence["gates"]["rev2_provenance_complete"] = True
    evidence["provenance"] = provenance(None, None)
    evidence["runtime_classification_pending"] = True
    portfolio.atomic_json(part_path, evidence)


if __name__ == "__main__":
    parent.main()
    publish_provenance()
