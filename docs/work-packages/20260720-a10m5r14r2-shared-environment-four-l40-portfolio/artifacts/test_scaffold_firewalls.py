#!/usr/bin/env python3
"""Verify publication-time fail-closed gates and portfolio wrapper surfaces."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
JOBS = PACKAGE / "artifacts/jobs"

prepare_spec = importlib.util.spec_from_file_location("r14r2_prepare", JOBS / "prepare_assets.py")
assert prepare_spec and prepare_spec.loader
prepare = importlib.util.module_from_spec(prepare_spec)
prepare_spec.loader.exec_module(prepare)
predecessor = prepare.verify_predecessor(PACKAGE)
assert predecessor["actual_gpu_minutes"] == 88
assert predecessor["plan_id"] == "dc11173b0d4bbad54e3361a5ecbee0b092f7996e0862c0839f82fdfa5f30992d"
assert predecessor["ledger"]["head_sha256"] == "a2e529b36005a585ca52a637a816c9521132c6155f2bc93c2b57641e5067eeaa"
assert predecessor["matrix_stop"]["record_sha256"] == "44737476b606bbc072d42a4b0a349cdf0be95d1f3e37c22423710653dea6633a"
assert predecessor["terminal"]["remote_absent"] is True
assert predecessor["terminal"]["job_local_cleanup"] == "verified_absent"
assert {row["actual_gpu_minutes"] for row in predecessor["failures"].values()} == {2, 31, 36}

launcher = (JOBS / "portfolio_launcher.py").read_text()
candidate = (JOBS / "portfolio_candidate_process.py").read_text()
runner = (JOBS / "run_portfolio.sh").read_text()
wrapper = (JOBS / "job-continuous-distribution-head-factorial-portfolio.sh").read_text()
admission = (JOBS / "admission_checker.py").read_text()
materializer = (JOBS / "materialize_admission.py").read_text()
builder = (JOBS / "build_control_records.py").read_text()
preparer = (JOBS / "prepare_assets.py").read_text()

for forbidden in ("torchrun", "DistributedDataParallel", "init_process_group"):
    assert forbidden not in launcher
    assert forbidden not in candidate
assert 'tokens = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")' in launcher
assert 'len(set(tokens)) == 4' in launcher
assert 'torch.cuda.device_count()' in launcher
assert 'torch.cuda.device_count()' in candidate
assert 'device_name == "NVIDIA L40"' in candidate
assert 'process.wait()' in launcher
assert 'signal.signal(signal.SIGTERM' in launcher
assert 'shared_before == shared_after' in launcher
assert 'chmod -R a-w -- "$environment" "$shared_corpus"' in runner
assert 'chmod -R u+w -- "$environment" "$shared_corpus"' in runner
assert "cleanup-permissions.json" in runner
assert 'test "$available_kb" -ge 16777216' in runner
assert "all_role_directories_retained" in wrapper
assert "all_role_records_authenticated" in wrapper
assert "parent_portfolio_admission_authenticated" in wrapper
assert "portfolio_launcher_authenticated" in wrapper
assert "submission_admission_authenticated" in wrapper
assert "job_local_cleanup" in wrapper
assert "os.makedirs(os.path.dirname(child_path), exist_ok=True)" in wrapper
assert "#SBATCH --nodelist=node03" in wrapper
assert "--states=RUNNING,COMPLETING,CONFIGURING" in admission
assert "immediate_node03_four_l40_idle" in admission
assert "occupancy_receipt" in admission
assert "age <= 60" in materializer
assert "authenticated(process)" in launcher
assert "authenticated(evidence)" in launcher
assert "exact_authenticated_role_map" in launcher
assert "setup_record_authenticated" in launcher
assert "portfolio_admission_authenticated" in launcher
assert "control_gate_receipt_sha256" in admission
assert 'target = option("--role")' in admission
assert 'target = option("--target")' not in admission
assert admission.index("inherited admission checker asset identity drift") < admission.index("spec.loader.exec_module(parent)")
assert '"admissions/{role}.json"' in builder
assert '"temporal_select.py"' in preparer

print("A10M5R14R2-SCAFFOLD-FIREWALLS-PASS")
