#!/usr/bin/env python3
"""Execute the repaired callee result through the inherited caller composition."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

path = Path(__file__).resolve().parent / "jobs/parameter_accounting.py"
spec = importlib.util.spec_from_file_location("r14r2_parameter_accounting", path)
assert spec and spec.loader
accounting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounting)

ceiling = 330000
for candidate, expected_total in accounting.EXPECTED_TOTALS.items():
    adapter = expected_total - accounting.CONTROL_PARAMETER_COUNT
    inherited_result = {
        "candidate_adapter_parameter_count": adapter,
        "parameter_count": expected_total,
    }
    repaired = accounting.repair(inherited_result, candidate, adapter)
    # This is the exact inherited continuous_candidate_experiment composition.
    candidate_parameters = int(repaired["parameter_count"])
    caller_total = candidate_parameters + accounting.CONTROL_PARAMETER_COUNT
    assert candidate_parameters == adapter
    assert repaired["total_parameter_count"] == caller_total == expected_total
    assert caller_total <= ceiling
    assert caller_total != expected_total + accounting.CONTROL_PARAMETER_COUNT

# The frozen experiment publishes this plain (non-self-authenticated) shape.
process_path = Path(__file__).resolve().parent / "jobs/portfolio_candidate_process.py"
process_spec = importlib.util.spec_from_file_location("r14r2_candidate_process", process_path)
assert process_spec and process_spec.loader
process = importlib.util.module_from_spec(process_spec)
process_spec.loader.exec_module(process)
with tempfile.TemporaryDirectory(prefix="a10m5r14r2-training-promotion-") as raw:
    target = Path(raw) / "training.json"
    original = {
        "architecture": "centered_location_ou",
        "capacity": "K2",
        "schema_version": 1,
        "seeds": [
            {
                "candidate_adapter_parameter_count": 1740,
                "parameter_accounting_interface": "adapter-only-parameter_count-plus-explicit-total",
                "parameter_count": 1740,
                "seed": 147031,
                "total_parameter_count": 278667,
            }
        ],
    }
    target.write_text(json.dumps(original, indent=2, sort_keys=True) + "\n")
    promoted = process.authenticate_training(
        target, "centered_location_ou", "K2"
    )
    semantic = dict(promoted)
    semantic.pop("record_sha256")
    assert semantic == original
    assert promoted["record_sha256"]
    promoted["seeds"][0]["parameter_count"] = 278667
    assert promoted["record_sha256"] != process.hashlib.sha256(
        process.canonical({key: value for key, value in promoted.items() if key != "record_sha256"})
    ).hexdigest()

print("A10M5R14R2-PARAMETER-ACCOUNTING-COMPOSITION-PASS")
