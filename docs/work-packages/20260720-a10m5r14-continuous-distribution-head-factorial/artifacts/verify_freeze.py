#!/usr/bin/env python3
"""Fail closed on the frozen R14 scientific and operational scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
PARENT = ROOT / "docs/work-packages/20260720-a10m5r13r1-admission-controller-materialization-remedy"
parser = argparse.ArgumentParser()
parser.add_argument("--science-python", type=Path)
parser.add_argument("--parent-assets", type=Path)
options = parser.parse_args()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


science = read(PACKAGE / "artifacts/science-contract.json")
inheritance = read(PACKAGE / "artifacts/inheritance-manifest.json")
if (
    inheritance["campaign_predecessor_commit"]
    != "4720ea5764fe02c55a3707f94bb6805f5886b812"
    or
    inheritance["campaign_predecessor_terminal"]
    != "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
    or inheritance["executed_parent_assets"]["asset_manifest_sha256"]
    != "eddd17045a8347ac2b9c919ecba0ce30ca49dbe47e236664e45969fea76f09c9"
    or inheritance["inherited_contracts"] != {
        "portfolio_contract_sha256": digest(PARENT / "artifacts/portfolio-contract.json"),
        "temporal_contract_sha256": digest(PARENT / "artifacts/temporal-contract.json"),
    }
):
    raise RuntimeError("R13 inheritance identity drift")
if [
    (row["smooth_uncentered_climatology"], row["centered_scale_ou"])
    for row in science["candidates"]
] != [(False, False), (True, False), (False, True), (True, True)]:
    raise RuntimeError("factorial freeze drift")
if science["continuous_process"] != {
    "calendar_boundary_resets": False,
    "daily_transition": "exact_stationary_continuous_time_ou_discretization",
    "location_head_indices": [0, 1, 3, 5],
    "medium_state_dimension": 8,
    "medium_time_scale_days": [14.0, 180.0],
    "scale_head_indices": [2, 4, 6],
    "slow_state_dimension": 4,
    "slow_time_scale_days": [180.0, 1460.0],
}:
    raise RuntimeError("daily continuous process freeze drift")

parent_temporal = read(PARENT / "artifacts/temporal-contract.json")
temporal = read(PACKAGE / "artifacts/temporal-contract.json")
for name in ("generation", "observation", "metrics", "scoring", "solar", "protected_roles_opened"):
    if temporal[name] != parent_temporal[name]:
        raise RuntimeError(f"ratified R13 temporal protocol drift: {name}")
if temporal["predecessor_terminal"] != "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE":
    raise RuntimeError("R13 predecessor terminal drift")

coverage = read(PACKAGE / "artifacts/objective-selector-coverage.json")
if coverage["counts"] != {
    "annual": 13, "monthly_precipitation": 108,
    "monthly_temperature": 60, "occurrence": 7, "total": 188,
}:
    raise RuntimeError("objective-selector coverage count drift")
if any(set(row["trainable_head_reachability"]) != {"A", "B", "C", "D"} for row in coverage["metrics"]):
    raise RuntimeError("objective-selector head reachability drift")
subprocess.run(["python3", str(PACKAGE / "artifacts/build_objective_coverage.py")], check=True)

profile = ROOT / "research/a10/lemhi_toolkit/profiles/lemhi-v2-xlarge-evidence.json"
binding = read(PACKAGE / "artifacts/evidence-profile.json")
if (
    digest(profile) != binding["profile_sha256"]
    or read(profile)["max_evidence_expanded_bytes"] != 256000000
    or binding["estimated_stream_evidence_bytes"] > binding["max_evidence_expanded_bytes"]
):
    raise RuntimeError("xlarge evidence profile binding drift")

source = (PACKAGE / "artifacts/jobs/continuous_core.py").read_text(encoding="utf-8")
required = (
    "self.climatology_heads", "self.medium_scale_loadings",
    "smooth_climatology_basis", "nn.Linear(", "bias=False",
    "SCALE_HEAD_INDICES = (2, 4, 6)", "scale = scale - scale.mean",
    "location_ou_offsets", "scale_ou_offsets", "climatology_offsets",
    "medium_daily_states", "slow_daily_states", "len(components) != 188",
)
if any(token not in source for token in required):
    raise RuntimeError("candidate/fixed-regularization implementation incomplete")
if "portfolio.regularization(diagnostics)" in source:
    raise RuntimeError("dynamic diagnostic-key regularization reintroduced")
if any(token in source for token in (
    "nn.Sequential(nn.Linear(5, 16)", "squared=True",
    "climatology_head_bounds", "torch.tanh(self.climatology_heads",
)):
    raise RuntimeError("obsolete climatology transform or squared training loss reintroduced")

for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
replay = PACKAGE / "artifacts/run_temporal_replay.py"
compile(replay.read_text(encoding="utf-8"), str(replay), "exec")

with tempfile.TemporaryDirectory() as scratch:
    output = Path(scratch)
    subprocess.run([
        "python3", str(PACKAGE / "artifacts/materialize_contracts.py"),
        "--parent-portfolio", str(PARENT / "artifacts/portfolio-contract.json"),
        "--parent-temporal", str(PARENT / "artifacts/temporal-contract.json"),
        "--output-dir", str(output),
    ], check=True)
    for name in ("portfolio-contract.json", "temporal-contract.json"):
        if (output / name).read_bytes() != (PACKAGE / "artifacts" / name).read_bytes():
            raise RuntimeError(f"materialized contract stale: {name}")

for script in ("test_contracts.py", "test_replay_authentication.py"):
    subprocess.run(["python3", str(PACKAGE / "artifacts" / script)], check=True)
if options.parent_assets is not None:
    spec_path = PACKAGE / "artifacts/jobs/prepare_assets.py"
    namespace: dict[str, object] = {}
    exec(compile(spec_path.read_bytes(), str(spec_path), "exec"), namespace)
    namespace["verify_parent_assets"](options.parent_assets)
if options.science_python is None:
    print("A10M5R14-SCIENCE-TESTS-NOT-RUN (supply --science-python)")
else:
    for script in (
        "test_calendar.py", "test_aligned_objective.py",
        "test_staged_continuous_core.py",
    ):
        subprocess.run([str(options.science_python), "-B", str(PACKAGE / "artifacts" / script)], check=True)
print("A10M5R14-FREEZE-VERIFY-PASS")
