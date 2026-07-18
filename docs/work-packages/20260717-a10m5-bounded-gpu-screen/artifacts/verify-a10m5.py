#!/usr/bin/env python3
"""Fail-closed prospective and completed-result checks for A10M5."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(REPO))

from research.a10.m3_contract import validate_checkpoint_record, validate_model_record  # noqa: E402
from research.a10.m5_screen import CONFIGURATION_BY_ID, CONFIGURATION_IDS, select_promotions  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    m3 = json.loads((REPO / "docs/work-packages/20260717-a10m3-model-training-generation-selector-freeze/artifacts/model-training-generation-v1.json").read_text())
    frozen = m3["screen"]["configurations"]
    require(tuple(row["id"] for row in frozen) == CONFIGURATION_IDS, "configuration order drift")
    for row in frozen:
        local = CONFIGURATION_BY_ID[row["id"]]
        require(local["pooling_class"] == row["pooling"], "pooling drift")
        for key in ("latent_dim", "width", "depth", "tail_head"):
            require(local[key] == row[key], f"architecture drift: {row['id']}/{key}")
    require(m3["screen"]["screen_training_seed"] == 147031, "screen seed drift")
    require(m3["resources"]["m5_screen_gpu_hours"] == 160, "screen ceiling drift")
    for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
    screen = (PACKAGE / "artifacts/jobs/screen.py").read_text()
    for token in ("candidate_fit", "fit_validation", "CUBLAS_WORKSPACE_CONFIG"):
        require(token in screen or token in (PACKAGE / "artifacts/jobs/screen-job.sh").read_text(), f"missing freeze token: {token}")
    require("147031" in screen, "training seed absent")
    require("range(100)" in screen and ">= 20" in screen and ">= 10" in screen, "early stopping drift")
    require("range(12)" in screen and "range(64)" in screen, "epoch/batch drift")
    with tempfile.TemporaryDirectory(prefix="a10m5-wrapper-check-") as temporary:
        root = Path(temporary)
        command = [
            sys.executable,
            str(PACKAGE / "artifacts/jobs/prepare-assets.py"),
            "--asset-root", str(root),
            "--canonical-cache", "/Users/roger/.cache/cligen-rs/a10-python311-smoke/assets",
            "--source-commit", "b396b72",
        ]
        if Path(command[-3]).is_dir():
            subprocess.run(command, cwd=REPO, check=True, stdout=subprocess.DEVNULL)
            wrapper = (root / "job-n0-l32-w128-d2-lognormal.sh").read_text()
            finalizer = wrapper.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
            ast.parse(finalizer, filename="generated-wrapper-finalizer")

    results_path = PACKAGE / "artifacts/screen-results.json"
    if results_path.exists():
        results = json.loads(results_path.read_text())
        records = results["configurations"]
        decision = select_promotions(records)
        require(decision == json.loads((PACKAGE / "artifacts/promotion-trace.json").read_text()), "promotion trace mismatch")
        for record in records:
            evidence_root = PACKAGE / "artifacts/toolkit/evidence/results" / record["configuration_id"].lower()
            evidence = json.loads((evidence_root / "evidence.json").read_text())
            require(evidence["configuration_id"] == record["configuration_id"], "evidence identity mismatch")
            validate_model_record(json.loads((evidence_root / "model-record.json").read_text()))
            validate_checkpoint_record(json.loads((evidence_root / "checkpoint-record.json").read_text()))
    print("A10M5 verification: PASS")


if __name__ == "__main__":
    main()
