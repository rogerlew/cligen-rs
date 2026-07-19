#!/usr/bin/env python3
"""Fail closed on A10M5R4R2R1's prospective corrective freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
R2 = REPO / "docs/work-packages/20260718-a10m5r4r2-realized-temporal-adjudication"
R3 = REPO / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/toolkit-recovered/evidence/results"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


contract = read(PACKAGE / "artifacts/reconstruction-contract.json")
evaluation = read(PACKAGE / "artifacts/evaluation-contract.json")
assert contract["r2_temporal_contract_sha256"] == digest(R2 / "artifacts/temporal-contract.json")
assert contract["r2_sites_sha256"] == digest(R2 / "artifacts/sites.json")
assert "EXECUTED-HOLD-MODEL-RECONSTRUCTION-IDENTITY" in (R2 / "package.md").read_text(encoding="utf-8")
assert len(contract["models"]) == 6
assert evaluation["bootstrap"] == {
    "candidate_stream_order": "training_seed ascending, then member_id ascending",
    "candidate_stream_resample": "24 draws with replacement from the paired 3-seed by 8-member order; one index vector shared by P1 and P2",
    "comparator_stream_order": "stochastic_burn_counts order",
    "comparator_stream_resample": "8 draws with replacement; one index vector shared by faithful and stochastic_prism_localized_par_v1",
    "observation_resample": "30 calendar-year blocks with replacement independently by site; inter-block transition pairs and cross-boundary spells excluded",
    "replicates": 1000,
    "seed": 410542,
}
assert len({row["row_id"] for row in contract["models"]}) == 6
assert {row["capacity_id"] for row in contract["models"]} == {"P1", "P2"}
for expected in contract["models"]:
    root = R3 / expected["row_id"]
    checkpoint = read(root / "checkpoint-record.json")
    metadata = read(root / "export-metadata.json")
    assert checkpoint["payload_bytes"] == expected["checkpoint_payload_bytes"]
    assert checkpoint["payload_sha256"] == expected["checkpoint_payload_sha256"]
    assert checkpoint["epoch"] == expected["checkpoint_epoch"]
    assert checkpoint["global_step"] == expected["checkpoint_global_step"]
    assert checkpoint["training_seed"] == expected["training_seed"]
    assert checkpoint["corpus_cursor"]["epoch_order_sha256"] == expected["corpus_cursor_epoch_order_sha256"]
    assert checkpoint["corpus_cursor"]["next_batch"] == expected["corpus_cursor_next_batch"]
    assert metadata["model_record_sha256"] == expected["model_record_sha256"]
    assert metadata["export_sha256"] == expected["non_gating_accepted_export_sha256"]
    for name in ("capacity_id", "family", "hidden_size", "parameter_count", "validation_primary_nll", "validation_stability", "validation_tail_score"):
        assert metadata[name] == expected[name]
source = (PACKAGE / "artifacts/jobs/prepare_assets.py").read_text(encoding="utf-8")
assert "stream.write('\\\\n')" in source
assert "accepted_export_exact" not in (PACKAGE / "artifacts/jobs/generate.py").read_text(encoding="utf-8")
compile((PACKAGE / "artifacts/jobs/evaluate.py").read_text(encoding="utf-8"), "evaluate.py", "exec")
print("A10M5R4R2R1-FREEZE-READY")
