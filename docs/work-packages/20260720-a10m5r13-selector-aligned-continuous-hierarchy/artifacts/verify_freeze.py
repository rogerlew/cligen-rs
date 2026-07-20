#!/usr/bin/env python3
"""Fail closed on the frozen R13 scientific and operational scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import subprocess
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
PARENT = ROOT / "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy"
parser = argparse.ArgumentParser()
parser.add_argument(
    "--science-python", type=Path,
    help="Python with pinned NumPy/Torch for calendar and differentiable science tests",
)
options = parser.parse_args()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


manifest = read(PACKAGE / "artifacts/inheritance-manifest.json")
if (
    manifest.get("campaign_predecessor_commit")
    != "4ebc8c6124e5d024dc74327789cd01a3cf5f0d2e"
    or manifest.get("campaign_predecessor_package")
    != "20260720-a10m5r12r2-collection-ceiling-reconciliation"
    or manifest.get("campaign_predecessor_terminal")
    != "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
):
    raise RuntimeError("campaign predecessor identity drift")
for name, expected in manifest["sources"].items():
    if name.startswith("../"):
        path = ROOT / "docs/work-packages" / name[3:]
    else:
        path = PARENT / name
    if digest(path) != expected:
        raise RuntimeError(f"inherited source drift: {name}")

science = read(PACKAGE / "artifacts/science-contract.json")
window = science["training_window"]
if (window["axis_rows"], window["observed_rows"], window["eligible_origins_per_point"]) != (5844, 5840, 13):
    raise RuntimeError("long-window calendar freeze drift")
if window["leap_year_structural_null_date"] != "December 31":
    raise RuntimeError("Daymet leap-year null drift")
annual = science["annual_loss"]
if not annual["families_equal_weight"] or not annual["replaces_inherited_annual_location_and_dispersion"]:
    raise RuntimeError("annual replacement/equal-family freeze drift")
if annual["location_components"] != ["precipitation_mean", "precipitation_q95", "tmax_mean", "tmin_mean"]:
    raise RuntimeError("annual q95 is not in location family")
shared = science["candidates"][1]
if shared["additional_ou_state_dimension"] != 0 or shared["remaining_flexible_slow_state_dimension"] != 3:
    raise RuntimeError("shared arm stochastic dimension drift")
if shared["shared_injection_heads"] != ["precipitation_occurrence", "positive_amount_location", "temperature_mean_location", "log_dtr_location"]:
    raise RuntimeError("shared arm generator head semantics drift")

parent_temporal = read(PARENT / "artifacts/temporal-contract.json")
temporal = read(PACKAGE / "artifacts/temporal-contract.json")
for name in ("generation", "observation", "metrics", "scoring", "solar", "protected_roles_opened"):
    if temporal[name] != parent_temporal[name]:
        raise RuntimeError(f"ratified temporal selector section drift: {name}")
if temporal["predecessor_terminal"] != "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE":
    raise RuntimeError("campaign predecessor terminal drift")
resources = temporal["resources"]
if (resources["control_minutes"], resources["candidate_minutes_each"], resources["recovery_minutes"], resources["gpu_minute_ceiling"], resources["maximum_concurrent_candidates"]) != (30, 240, 5, 515, 2):
    raise RuntimeError("resource/concurrency freeze drift")
portfolio_contract = read(PACKAGE / "artifacts/portfolio-contract.json")
if portfolio_contract["terminals"] != {
    "ready": "A10M5R13-TEMPORAL-READY",
    "single": "A10M5R13-TEMPORAL-READY",
    "none": "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
}:
    raise RuntimeError("R13 terminal registry drift")
capacity = read(PACKAGE / "artifacts/job-local-capacity-contract.json")
if (
    capacity["package_id"] != "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
    or capacity["predecessor_terminal"] != "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
    or capacity["resources"]["candidate_minutes_each"] != 240
    or capacity["resources"]["total_gpu_minute_ceiling"] != 515
    or capacity["admission"]["maximum_live_candidate_jobs"] != 2
):
    raise RuntimeError("job-local capacity/admission contract drift")
replay_pin = read(PACKAGE / "artifacts/replay-predecessor-pin.json")
if (
    digest(PACKAGE / "artifacts/replay-predecessor-pin.json")
    != "b6a2119eed0d042052d2d606628c4698d9937cce029896f0a5785c54a11c9670"
    or replay_pin["campaign_predecessor_commit"]
    != manifest["campaign_predecessor_commit"]
    or replay_pin["campaign_predecessor_package"]
    != manifest["campaign_predecessor_package"]
    or replay_pin["terminal"] != manifest["campaign_predecessor_terminal"]
    or replay_pin["data_root_tree"]
    != {"file_count": 2773, "semantic_sha256": "2eac4cb53a6e3fb218f7ee33dfb0b369f828a31c188591ea4509602fe655c1ad"}
    or len(replay_pin["prism_provenance"]) != 6
    or replay_pin["prism_provenance"]["p+3275_-08325"]["normals_sha256"]
    != "329f94f51f5cd6da03200a0ca0a50e645b677f93e3b723ab4223b2af4d1b7e85"
):
    raise RuntimeError("replay predecessor/data-root/PRISM pin drift")

profile = ROOT / "research/a10/lemhi_toolkit/profiles/lemhi-v2-large-evidence.json"
binding = read(PACKAGE / "artifacts/evidence-profile.json")
if digest(profile) != binding["profile_sha256"] or binding["estimated_stream_evidence_bytes"] > binding["max_evidence_expanded_bytes"]:
    raise RuntimeError("published large-evidence profile binding drift")

source = (PACKAGE / "artifacts/jobs/continuous_core.py").read_text(encoding="utf-8")
required = (
    "self.shared_field_vector", "slow[..., 0]", "slow[..., 1:]",
    "inherited.score_candidate = score_candidate", "inherited.score_candidate = original_score",
    "inherited_blocks.pop(\"annual_location\")",
    "inherited_blocks.pop(\"annual_interannual_dispersion\")",
)
if any(token not in source for token in required):
    raise RuntimeError("candidate implementation freeze incomplete")
if "self.shared_state =" in source or "nn.Linear(self.slow_dim, 1" in source:
    raise RuntimeError("shared arm added a forbidden fifth state projection")

for path in (PACKAGE / "artifacts/jobs").glob("*.py"):
    py_compile.compile(str(path), doraise=True)

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
            raise RuntimeError(f"materialized contract is stale: {name}")

for script in (
    "test_builder.py", "test_prepare_assets.py", "test_admission_wrapper.py",
    "test_replay_contract.py",
):
    subprocess.run(["python3", str(PACKAGE / "artifacts" / script)], check=True)
if options.science_python is None:
    print("A10M5R13-SCIENCE-TESTS-NOT-RUN (supply --science-python)")
else:
    for script in (
        "test_calendar.py", "test_selector_loss.py",
        "test_staged_continuous_core.py",
    ):
        subprocess.run(
            [str(options.science_python), str(PACKAGE / "artifacts" / script)],
            check=True,
        )
print("A10M5R13-FREEZE-VERIFY-PASS")
