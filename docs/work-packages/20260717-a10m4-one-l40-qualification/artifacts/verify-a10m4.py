#!/usr/bin/env python3
"""Static verification for the prospective A10M4 scaffold."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
JOBS = PACKAGE / "artifacts/jobs"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    contract = json.loads(
        (
            REPO
            / "docs/work-packages/20260717-a10m3-model-training-generation-selector-freeze/"
            "artifacts/model-training-generation-v1.json"
        ).read_text()
    )
    configuration = json.loads(
        (
            REPO
            / "research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v1.json"
        ).read_text()
    )
    selected = next(
        row
        for row in contract["screen"]["configurations"]
        if row["id"] == "N0-l32-w128-d2-lognormal"
    )
    assert selected == {
        "id": "N0-l32-w128-d2-lognormal",
        "pooling": "N0_complete",
        "latent_dim": 32,
        "width": 128,
        "depth": 2,
        "tail_head": "lognormal",
    }
    assert configuration["configuration_id"] == "lemhi-a10-py311-l40-v1"
    assert configuration["configuration_semantic_sha256"] == (
        "0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179"
    )
    schema = json.loads((JOBS / "evidence.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert schema["properties"]["configuration_id"]["const"] == configuration["configuration_id"]
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(JOBS / "qualify.py"), str(PACKAGE / "artifacts/environment/build-assets.py")],
        check=True,
    )
    subprocess.run(["sh", "-n", str(JOBS / "qualify.sh")], check=True)
    text = (JOBS / "qualify.py").read_text()
    assert "confirmation" not in text.lower()
    assert "candidate_fit" in text and "fit_validation" in text
    assert "0x6627E8D5" in text and "0x9B00DBD8" in text
    print("A10M4 prospective scaffold: PASS")
    print(
        json.dumps(
            {
                "configuration": selected["id"],
                "evidence_schema_sha256": sha256(JOBS / "evidence.schema.json"),
                "requested_gpu_minutes": 120,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
