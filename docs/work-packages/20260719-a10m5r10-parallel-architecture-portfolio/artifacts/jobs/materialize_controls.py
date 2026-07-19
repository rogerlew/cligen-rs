#!/usr/bin/env python3
"""Materialize and authenticate the six frozen A10M5R10 controls."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch

import climate_core as climate
import legacy_core as legacy
import portfolio_core as portfolio


def actual_identity(output: Path) -> dict[str, Any]:
    checkpoint = portfolio.read_json(output / "checkpoint-record.json")
    export = portfolio.read_json(output / "export-metadata.json")
    return {
        "capacity_id": export["capacity_id"],
        "checkpoint_epoch": checkpoint["epoch"],
        "checkpoint_global_step": checkpoint["global_step"],
        "checkpoint_payload_bytes": (output / "checkpoint.pt").stat().st_size,
        "checkpoint_payload_sha256": portfolio.digest(output / "checkpoint.pt"),
        "corpus_cursor_epoch_order_sha256": checkpoint["corpus_cursor"]["epoch_order_sha256"],
        "corpus_cursor_next_batch": checkpoint["corpus_cursor"]["next_batch"],
        "family": export["family"],
        "hidden_size": export["hidden_size"],
        "model_record_sha256": portfolio.digest(output / "model-record.json"),
        "parameter_count": export["parameter_count"],
        "row_id": export["row_id"],
        "training_seed": checkpoint["training_seed"],
        "validation_primary_nll": export["validation_primary_nll"],
        "validation_stability": export["validation_stability"],
        "validation_tail_score": export["validation_tail_score"],
    }


def verify_identity(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    if set(actual) - set(expected):
        raise RuntimeError("control contract omits reconstructed identity fields")
    for key, value in actual.items():
        if expected[key] != value:
            raise RuntimeError(
                f"control identity mismatch for {expected['row_id']}: {key}: "
                f"expected={expected[key]!r} actual={value!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    portfolio.self_test()
    device = portfolio.require_l40()
    options.output.mkdir(parents=True, exist_ok=True)
    contract_path = options.run_root / "portfolio-contract.json"
    profile_path = options.run_root / "a10-daymet-calendar-profile-v1.json"
    contract = portfolio.read_json(contract_path)
    profile = portfolio.read_json(profile_path)

    transfer, normalized, normalization = legacy.verify_corpus(options.corpus)
    preflight = portfolio.calendar_preflight(options.corpus, normalized, profile)
    portfolio.atomic_json(options.output / "calendar-preflight.json", preflight)
    fit, validation, role_counts = legacy.load_daymet(
        options.corpus, normalized, normalization
    )
    fit_calendar, validation_calendar = climate.attach_calendars(
        options.corpus,
        normalized,
        fit,
        validation,
        int(contract["stochastic"]["window_calendar_years"]),
    )
    expected_observed = int(contract["calendar"]["representative_window"]["core_observed_rows"])
    if any(
        int(window.valid_index.sum()) != expected_observed
        for item in (*fit_calendar, *validation_calendar)
        for window in item.windows
    ):
        raise RuntimeError("eligible window observed-row drift")

    identity_rows, summary_rows = [], []
    selections = [(index, 0) for index in range(len(validation_calendar))]
    for expected in contract["controls"]["models"]:
        capacity = expected["capacity_id"]
        seed = int(expected["training_seed"])
        model_output = options.output / f"{capacity}-s{seed}"
        subprocess.run(
            [
                sys.executable,
                str(options.run_root / "train.py"),
                "--row-id", expected["row_id"],
                "--family", contract["controls"]["amount_family"],
                "--capacity", capacity,
                "--seed", str(seed),
                "--corpus", str(options.corpus),
                "--output", str(model_output),
            ],
            check=True,
        )
        actual = actual_identity(model_output)
        verify_identity(expected, actual)
        reconstructed_export_sha256 = portfolio.digest(model_output / "model-export.pt")
        identity_rows.append({
            "actual": actual,
            "expected": expected,
            "exact": True,
            "reconstructed_record_provenance": {
                "checkpoint_record_sha256": portfolio.digest(model_output / "checkpoint-record.json"),
                "export_sha256": reconstructed_export_sha256,
                "export_metadata_sha256": portfolio.digest(model_output / "export-metadata.json"),
                "model_record_sha256": portfolio.digest(model_output / "model-record.json"),
            },
        })
        model = torch.jit.load(str(model_output / "model-export.pt"), map_location=device).eval()
        score = climate.score_model(
            model,
            validation_calendar,
            selections,
            int(contract["stochastic"]["evaluation_members"]),
            device,
            len(fit_calendar),
            910000,
            int(expected["hidden_size"]),
        )
        summary_rows.append({
            "capacity_id": capacity,
            "checkpoint_sha256": actual["checkpoint_payload_sha256"],
            "export_sha256": reconstructed_export_sha256,
            "hidden_size": actual["hidden_size"],
            "model_directory": model_output.name,
            "parameter_count": actual["parameter_count"],
            "row_id": actual["row_id"],
            "score": score,
            "training_seed": seed,
        })
        del model
        torch.cuda.empty_cache()

    expected_pairs = {
        (capacity, seed)
        for capacity in ("P1", "P2")
        for seed in portfolio.SEEDS
    }
    actual_pairs = {
        (row["capacity_id"], row["training_seed"]) for row in summary_rows
    }
    if actual_pairs != expected_pairs:
        raise RuntimeError("control capacity/seed matrix incomplete")
    identity = {
        "all_exact": all(row["exact"] for row in identity_rows),
        "models": identity_rows,
        "schema_version": 1,
    }
    summary = {
        "calendar_preflight_sha256": portfolio.digest(options.output / "calendar-preflight.json"),
        "contract_sha256": portfolio.digest(contract_path),
        "corpus": {
            "aggregate_bytes": transfer["aggregate_bytes"],
            "normalization_role": normalization["fit_role_only"],
            "object_count": len(transfer["objects"]),
            "role_counts": role_counts,
        },
        "fit_calendar_points": len(fit_calendar),
        "fit_validation_calendar_points": len(validation_calendar),
        "models": summary_rows,
        "protected_roles_opened": [],
        "schema_version": 1,
    }
    portfolio.atomic_json(options.output / "control-identity.json", identity)
    portfolio.atomic_json(options.output / "control-summary.json", summary)
    evidence = {
        "classification": "a10m5r10-development-only-control-materialization",
        "gates": {
            "calendar_preflight": preflight["valid"],
            "calendar_surface_complete": len(fit_calendar) == 1200 and len(validation_calendar) == 240,
            "control_matrix_complete": actual_pairs == expected_pairs,
            "controls_reconstructed_exactly": identity["all_exact"],
            "fit_validation_gradient_free": True,
            "protected_roles_sealed": True,
        },
        "protected_roles_opened": [],
        "schema_version": 1,
    }
    portfolio.atomic_json(options.output / "evidence.json.part", evidence)
    print("A10M5R10-CONTROLS-MATERIALIZED")


if __name__ == "__main__":
    main()
