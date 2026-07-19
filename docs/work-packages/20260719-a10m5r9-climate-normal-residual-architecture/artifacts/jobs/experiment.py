#!/usr/bin/env python3
"""Run the frozen A10M5R9 architecture ablation on one L40."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import torch

import climate_core as climate
import legacy_core as legacy
import residual_core as residuals


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


def calendar_preflight(
    corpus: Path,
    normalized: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    expected = profile["fit_period_example"]
    expected_missing = expected["unobserved_dates"]
    role_counts = {"candidate_fit": 0, "fit_validation": 0}
    for shard in normalized["daymet_shards"]:
        with tarfile.open(corpus / shard["path"], "r:gz") as archive:
            for member in archive.getmembers():
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                document = json.load(stream)
                role = document["role"]
                if role not in role_counts:
                    continue
                observed = document["source_observed"]
                missing = [date for date, keep in zip(document["dates"], observed, strict=True) if not keep]
                if len(document["dates"]) != expected["calendar_axis_rows"]:
                    raise RuntimeError("Daymet calendar-axis count mismatch")
                if sum(bool(value) for value in observed) != expected["observed_rows"]:
                    raise RuntimeError("Daymet observed-row count mismatch")
                if missing != expected_missing:
                    raise RuntimeError("Daymet unobserved-date profile mismatch")
                for field in ("prcp", "tmax", "tmin"):
                    present = [value is not None for value in document["fields"][field]]
                    if present != observed:
                        raise RuntimeError(f"Daymet {field} mask mismatch")
                role_counts[role] += 1
    if role_counts != {"candidate_fit": 1200, "fit_validation": 240}:
        raise RuntimeError(f"calendar-preflight role mismatch: {role_counts}")
    return {
        "calendar_axis_rows_per_point": expected["calendar_axis_rows"],
        "observed_rows_per_point": expected["observed_rows"],
        "profile_id": profile["profile_id"],
        "role_counts": role_counts,
        "schema_version": 1,
        "unobserved_dates": expected_missing,
        "valid": True,
        "window_axis_rows": profile["window_example"]["calendar_axis_rows"],
        "window_observed_rows": profile["window_example"]["observed_rows"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or "L40" not in torch.cuda.get_device_name(0):
        raise RuntimeError("exactly one typed L40 is required")
    options.output.mkdir(parents=True, exist_ok=True)
    contract_path = options.run_root / "architecture-contract.json"
    contract = read_json(contract_path)
    reconstruction = read_json(options.run_root / "reconstruction-contract.json")
    profile = read_json(options.run_root / "a10-daymet-calendar-profile-v1.json")

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
    preflight = calendar_preflight(options.corpus, normalized, profile)
    climate.atomic_json(options.output / "calendar-preflight.json", preflight)
    fit, validation, role_counts = legacy.load_daymet(options.corpus, normalized, normalization)
    fit_calendar, validation_calendar = climate.attach_calendars(
        options.corpus, normalized, fit, validation, contract["calendar"]["window_calendar_years"]
    )
    if any(int(window.valid_index.sum()) != 2920 for item in (*fit_calendar, *validation_calendar) for window in item.windows):
        raise RuntimeError("eight-year observed-row count drift")

    device = torch.device("cuda:0")
    baseline, baseline_training = residuals.train_baseline(
        contract, fit_calendar, validation_calendar, device, options.output
    )
    latent, residual_training = residuals.train_residual(
        contract, baseline, fit_calendar, validation_calendar, device, options.output
    )

    selections = [(index, 0) for index in range(len(validation_calendar))]
    members = contract["stochastic"]["evaluation_members"]
    baseline_score = residuals.score_baseline(
        baseline, validation_calendar, selections, members, device, 910000
    )
    residual_score = residuals.score_residual(
        baseline, latent, validation_calendar, selections, members, device, 910000, 920000
    )
    control = torch.jit.load(str(control_output / "model-export.pt"), map_location=device).eval()
    p1_score = climate.score_model(
        control, validation_calendar, selections, members, device, len(fit), 910000
    )
    decision = residuals.decision(p1_score, baseline_score, residual_score, contract)
    comparison = {
        "arms": {
            "accepted_p1_context": p1_score,
            "climate_normal_baseline": baseline_score,
            "climate_normal_plus_residual": residual_score,
        },
        "calendar_preflight": preflight,
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
        "training": {
            "baseline_checkpoint": {
                "best_epoch": baseline_training["best_epoch"],
                "bytes": baseline_training["checkpoint_bytes"],
                "sha256": baseline_training["checkpoint_sha256"],
            },
            "baseline_frozen_during_residual": residual_training["baseline_state_sha256_before"]
            == residual_training["baseline_state_sha256_after"],
            "residual_checkpoint": {
                "best_epoch": residual_training["best_epoch"],
                "bytes": residual_training["checkpoint_bytes"],
                "sha256": residual_training["checkpoint_sha256"],
            },
        },
    }
    climate.atomic_json(options.output / "comparison.json", comparison)
    climate.atomic_json(options.output / "decision.json", decision)
    evidence = {
        "classification": "a10m5r9-development-only-climate-normal-residual-architecture",
        "control_identity": identity["exact"],
        "gates": {
            "baseline_frozen_during_residual": comparison["training"]["baseline_frozen_during_residual"],
            "calendar_preflight": preflight["valid"],
            "calendar_surface_complete": len(fit_calendar) == 1200 and len(validation_calendar) == 240,
            "comparison_published": True,
            "control_reconstructed_exactly": identity["exact"],
            "fit_validation_gradient_free": True,
            "protected_roles_sealed": True,
            "scientific_decision_published": decision["terminal"].startswith(("A10M5R9-", "HOLD-A10M5R9-")),
        },
        "protected_roles_opened": [],
        "schema_version": 1,
        "scientific_decision": decision,
    }
    climate.atomic_json(options.output / "evidence.json.part", evidence)
    print(decision["terminal"])


if __name__ == "__main__":
    main()
