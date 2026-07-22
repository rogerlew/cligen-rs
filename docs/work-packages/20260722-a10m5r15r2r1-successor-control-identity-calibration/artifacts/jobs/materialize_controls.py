#!/usr/bin/env python3
"""Capture frozen R14 control identities on the R15 successor corpus."""

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


STATIC_FIELDS = (
    "capacity_id",
    "family",
    "hidden_size",
    "parameter_count",
    "row_id",
    "training_seed",
)
DYNAMIC_FIELDS = (
    "checkpoint_epoch",
    "checkpoint_global_step",
    "checkpoint_payload_bytes",
    "checkpoint_payload_sha256",
    "corpus_cursor_epoch_order_sha256",
    "corpus_cursor_next_batch",
    "model_record_sha256",
    "validation_primary_nll",
    "validation_stability",
    "validation_tail_score",
)


def actual_identity(output: Path) -> dict[str, Any]:
    checkpoint = portfolio.read_json(output / "checkpoint-record.json")
    export = portfolio.read_json(output / "export-metadata.json")
    return {
        "capacity_id": export["capacity_id"],
        "checkpoint_epoch": checkpoint["epoch"],
        "checkpoint_global_step": checkpoint["global_step"],
        "checkpoint_payload_bytes": (output / "checkpoint.pt").stat().st_size,
        "checkpoint_payload_sha256": portfolio.digest(output / "checkpoint.pt"),
        "corpus_cursor_epoch_order_sha256": checkpoint["corpus_cursor"][
            "epoch_order_sha256"
        ],
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


def verify_static_identity(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    if set(actual) != set(STATIC_FIELDS) | set(DYNAMIC_FIELDS):
        raise RuntimeError("control calibration identity field drift")
    for key in STATIC_FIELDS:
        if expected.get(key) != actual[key]:
            raise RuntimeError(
                f"static control identity mismatch for {expected.get('row_id')}: "
                f"{key}: expected={expected.get(key)!r} actual={actual[key]!r}"
            )
    for key in DYNAMIC_FIELDS:
        value = actual[key]
        if key.endswith("sha256"):
            if not isinstance(value, str) or len(value) != 64:
                raise RuntimeError(f"malformed control digest: {key}")
        elif isinstance(value, float):
            if not torch.isfinite(torch.tensor(value, dtype=torch.float64)):
                raise RuntimeError(f"non-finite control value: {key}")
        elif not isinstance(value, int):
            raise RuntimeError(f"malformed control value: {key}")


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
    expected_observed = int(
        contract["calendar"]["representative_window"]["core_observed_rows"]
    )
    if any(
        int(window.valid_index.sum()) != expected_observed
        for item in (*fit_calendar, *validation_calendar)
        for window in item.windows
    ):
        raise RuntimeError("eligible window observed-row drift")

    identity_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    selections = [(index, 0) for index in range(len(validation_calendar))]
    for expected in contract["controls"]["models"]:
        capacity = expected["capacity_id"]
        seed = int(expected["training_seed"])
        model_output = options.output / f"{capacity}-s{seed}"
        subprocess.run(
            [
                sys.executable,
                str(options.run_root / "train.py"),
                "--row-id",
                expected["row_id"],
                "--family",
                contract["controls"]["amount_family"],
                "--capacity",
                capacity,
                "--seed",
                str(seed),
                "--corpus",
                str(options.corpus),
                "--output",
                str(model_output),
            ],
            check=True,
        )
        actual = actual_identity(model_output)
        verify_static_identity(expected, actual)
        export_sha256 = portfolio.digest(model_output / "model-export.pt")
        provenance = {
            "checkpoint_record_sha256": portfolio.digest(
                model_output / "checkpoint-record.json"
            ),
            "export_metadata_sha256": portfolio.digest(
                model_output / "export-metadata.json"
            ),
            "export_sha256": export_sha256,
            "model_record_sha256": portfolio.digest(
                model_output / "model-record.json"
            ),
        }
        identity_rows.append(
            {
                "actual": actual,
                "dynamic_differs_from_parent": any(
                    expected.get(key) != actual[key] for key in DYNAMIC_FIELDS
                ),
                "parent_expected": expected,
                "static_identity_exact": True,
                "successor_record_provenance": provenance,
            }
        )
        model = torch.jit.load(
            str(model_output / "model-export.pt"), map_location=device
        ).eval()
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
        summary_rows.append(
            {
                "capacity_id": capacity,
                "checkpoint_sha256": actual["checkpoint_payload_sha256"],
                "export_sha256": export_sha256,
                "hidden_size": actual["hidden_size"],
                "model_directory": model_output.name,
                "parameter_count": actual["parameter_count"],
                "row_id": actual["row_id"],
                "score": score,
                "training_seed": seed,
            }
        )
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
    identity = {
        "all_static_identities_exact": all(
            row["static_identity_exact"] for row in identity_rows
        ),
        "candidate_output_accessed": False,
        "models": identity_rows,
        "protected_roles_opened": [],
        "schema_version": 1,
        "successor_control_identity_calibration": True,
    }
    summary = {
        "calendar_preflight_sha256": portfolio.digest(
            options.output / "calendar-preflight.json"
        ),
        "candidate_output_accessed": False,
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
        "classification": "a10m5r15r2r1-successor-control-identity-calibration",
        "gates": {
            "calendar_preflight": preflight["valid"],
            "calendar_surface_complete": (
                len(fit_calendar) == 1200 and len(validation_calendar) == 240
            ),
            "candidate_output_absent": True,
            "control_matrix_complete": (
                len(summary_rows) == 6 and actual_pairs == expected_pairs
            ),
            "fit_validation_gradient_free": True,
            "parent_identity_drift_reproduced": any(
                row["dynamic_differs_from_parent"] for row in identity_rows
            ),
            "protected_roles_sealed": True,
            "static_control_identities_exact": identity[
                "all_static_identities_exact"
            ],
        },
        "protected_roles_opened": [],
        "schema_version": 1,
    }
    portfolio.atomic_json(options.output / "evidence.json.part", evidence)
    print("A10M5R15R2R1-SUCCESSOR-CONTROL-IDENTITIES-CAPTURED")


if __name__ == "__main__":
    main()
