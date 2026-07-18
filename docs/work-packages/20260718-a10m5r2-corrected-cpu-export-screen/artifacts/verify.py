#!/usr/bin/env python3
"""Fail-closed prospective and terminal verifier for A10M5R2."""

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
from research.a10.m5_screen import CONFIGURATION_IDS, select_promotions  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    jobs = PACKAGE / "artifacts/jobs"
    for path in jobs.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ast.parse((PACKAGE / "artifacts/aggregate.py").read_text(encoding="utf-8"))
    shell = (jobs / "screen-job.sh").read_text(encoding="utf-8")
    for token in (
        "trainer-exited.marker", "/usr/bin/time -v", "CUDA_VISIBLE_DEVICES=",
        "cpu_worker.py", "finalize.py", "VmHWM", "VmRSS",
    ):
        source = shell + (jobs / "cpu_worker.py").read_text() + (jobs / "finalize.py").read_text()
        require(token in source, f"corrected process token absent: {token}")

    cache = Path("/Users/roger/.cache/cligen-rs/a10-python311-smoke/assets")
    if cache.is_dir():
        with tempfile.TemporaryDirectory(prefix="a10m5r2-assets-") as temporary:
            root = Path(temporary)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
            ).strip()
            subprocess.run(
                [
                    sys.executable, str(jobs / "prepare-assets.py"),
                    "--asset-root", str(root), "--canonical-cache", str(cache),
                    "--source-commit", commit,
                ],
                cwd=REPO,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            expected = json.loads((root / "expected-predecessors.json").read_text())
            require(set(expected) == set(CONFIGURATION_IDS), "predecessor configuration set drift")
            require(all(len(row["identities"]) == 12 for row in expected.values()), "predecessor identities incomplete")
            require(
                (root / "screen_core.py").read_bytes()
                == (REPO / "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py").read_bytes(),
                "frozen trainer core drift",
            )
            for configuration in CONFIGURATION_IDS:
                wrapper = (root / f"job-{configuration.lower()}.sh").read_text()
                finalizer = wrapper.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
                ast.parse(finalizer, filename=f"wrapper-{configuration}")

    results_path = PACKAGE / "artifacts/screen-results.json"
    if results_path.exists():
        rows = json.loads(results_path.read_text())["configurations"]
        require(len(rows) == 12, "terminal screen row count")
        decision = select_promotions(rows)
        recorded = json.loads((PACKAGE / "artifacts/promotion-trace.json").read_text())
        require(recorded["promotions"] == decision["promotions"], "promotion identity drift")
        require(recorded["ordering"] == decision["ordering"], "promotion ordering drift")
        for row in rows:
            root = PACKAGE / "artifacts/toolkit/evidence/results" / row["configuration_id"].lower()
            evidence = json.loads((root / "evidence.json").read_text())
            require(evidence["valid"] is True and all(evidence["gates"].values()), "invalid retained row")
            require(evidence["worker_vmhwm_bytes"] <= 2_147_483_648, "worker VmHWM limit")
            require(evidence["external_maximum_rss_bytes"] <= 2_147_483_648, "external RSS limit")
            require(evidence["gates"]["candidate_identity_exact"] is True, "predecessor stream drift")
            validate_model_record(json.loads((root / "model-record.json").read_text()))
            validate_checkpoint_record(json.loads((root / "checkpoint-record.json").read_text()))
    print("A10M5R2 verifier: PASS")


if __name__ == "__main__":
    main()
