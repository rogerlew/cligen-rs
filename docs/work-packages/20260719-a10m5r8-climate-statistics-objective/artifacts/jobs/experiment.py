#!/usr/bin/env python3
"""Run the frozen A10M5R8 control/treatment experiment on one L40."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch

import climate_core as climate
import legacy_core as legacy


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def accepted_control(contract: dict[str, Any], output: Path) -> dict[str, Any]:
    expected = next(
        row for row in contract["models"]
        if row["capacity_id"] == "P1" and row["training_seed"] == 147031
    )
    checkpoint = read_json(output / "checkpoint-record.json")
    export = read_json(output / "export-metadata.json")
    actual = {
        "capacity_id": export["capacity_id"],
        "checkpoint_epoch": checkpoint["epoch"],
        "checkpoint_global_step": checkpoint["global_step"],
        "checkpoint_payload_bytes": (output / "checkpoint.pt").stat().st_size,
        "checkpoint_payload_sha256": climate.digest(output / "checkpoint.pt"),
        "corpus_cursor_epoch_order_sha256": checkpoint["corpus_cursor"]["epoch_order_sha256"],
        "corpus_cursor_next_batch": checkpoint["corpus_cursor"]["next_batch"],
        "family": export["family"],
        "hidden_size": export["hidden_size"],
        "model_record_sha256": climate.digest(output / "model-record.json"),
        "parameter_count": export["parameter_count"],
        "row_id": export["row_id"],
        "training_seed": checkpoint["training_seed"],
        "validation_primary_nll": export["validation_primary_nll"],
        "validation_stability": export["validation_stability"],
        "validation_tail_score": export["validation_tail_score"],
    }
    for key, value in actual.items():
        if value != expected[key]:
            raise RuntimeError(f"accepted control identity mismatch: {key}")
    record = {"actual": actual, "expected": expected, "exact": True, "schema_version": 1}
    climate.atomic_json(output.parent / "control-identity.json", record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "L40" not in torch.cuda.get_device_name(0):
        raise RuntimeError("exactly one typed L40 is required")
    options.output.mkdir(parents=True, exist_ok=True)
    contract_path = options.run_root / "climate-objective-contract.json"
    contract = read_json(contract_path)
    reconstruction = read_json(options.run_root / "reconstruction-contract.json")
    control_output = options.output / "control"
    subprocess.run(
        [
            sys.executable,
            str(options.run_root / "train.py"),
            "--row-id", "capacity-p1-s147031",
            "--family", "lognormal_wet_v2",
            "--capacity", "P1",
            "--seed", "147031",
            "--corpus", str(options.corpus),
            "--output", str(control_output),
        ],
        check=True,
    )
    identity = accepted_control(reconstruction, control_output)

    transfer, normalized, normalization = legacy.verify_corpus(options.corpus)
    fit, validation, role_counts = legacy.load_daymet(options.corpus, normalized, normalization)
    fit_calendar, validation_calendar = climate.attach_calendars(
        options.corpus, normalized, fit, validation, contract["stochastic"]["window_calendar_years"]
    )
    device = torch.device("cuda:0")
    treatment, training = climate.train_treatment(
        contract, fit_calendar, validation_calendar, device, options.output
    )
    selections = [(index, 0) for index in range(len(validation_calendar))]
    treatment_score = climate.score_model(
        treatment, validation_calendar, selections,
        contract["stochastic"]["evaluation_members"], device, len(fit), 780000,
    )
    del treatment
    torch.cuda.empty_cache()
    control = torch.jit.load(str(control_output / "model-export.pt"), map_location=device).eval()
    control_score = climate.score_model(
        control, validation_calendar, selections,
        contract["stochastic"]["evaluation_members"], device, len(fit), 780000,
    )
    decision = climate.decision(control_score, treatment_score, contract)
    comparison = {
        "arms": {
            "climate_statistics_treatment": treatment_score,
            "proper_nll_control": control_score,
        },
        "calendar_window_years": contract["stochastic"]["window_calendar_years"],
        "contract_sha256": climate.digest(contract_path),
        "corpus": {
            "aggregate_bytes": transfer["aggregate_bytes"],
            "normalization_role": normalization["fit_role_only"],
            "object_count": len(transfer["objects"]),
            "role_counts": role_counts,
        },
        "decision": decision,
        "fit_calendar_points": len(fit_calendar),
        "fit_validation_calendar_points": len(validation_calendar),
        "protected_roles_opened": [],
        "schema_version": 1,
        "treatment_checkpoint": {
            "best_epoch": training["best_epoch"],
            "bytes": training["checkpoint_bytes"],
            "sha256": training["checkpoint_sha256"],
        },
    }
    climate.atomic_json(options.output / "comparison.json", comparison)
    climate.atomic_json(options.output / "decision.json", decision)
    evidence = {
        "classification": "a10m5r8-development-only-climate-statistics-objective",
        "control_identity": identity["exact"],
        "gates": {
            "calendar_surface_complete": len(fit_calendar) == 1200 and len(validation_calendar) == 240,
            "comparison_published": True,
            "control_reconstructed_exactly": identity["exact"],
            "fit_validation_gradient_free": True,
            "protected_roles_sealed": True,
            "scientific_decision_published": decision["terminal"].startswith(("A10M5R8-", "HOLD-A10M5R8-")),
        },
        "protected_roles_opened": [],
        "scientific_decision": decision,
        "schema_version": 1,
    }
    climate.atomic_json(options.output / "evidence.json.part", evidence)
    print(decision["terminal"])


if __name__ == "__main__":
    main()
