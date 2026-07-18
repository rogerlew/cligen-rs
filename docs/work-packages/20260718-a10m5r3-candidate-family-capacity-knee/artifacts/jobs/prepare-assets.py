#!/usr/bin/env python3
"""Prepare the exact committed R3 assets and eighteen frozen wrappers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
FAMILIES = (("lognormal", "lognormal_wet_v2"), ("gamma", "gamma_wet_v2"), ("splice", "lognormal_body_gpd_excess_v2"))
SEEDS = (147031, 271828, 314159)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""): value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def wrapper(row_id: str, phase: str, family: str, capacity: str, seed: int) -> str:
    return f'''#!/bin/sh
set -eu
umask 077
role={row_id}
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/{row_id}
target=${{TMPDIR:-/tmp}}/a10m5r3-{row_id}-$SLURM_JOB_ID
mkdir -p -- "$output" "$target"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{{"attempt_index":0,"job_id":"%s","node":"%s","role":"%s","run_id":"%s"}}\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{{print $1}}')
device=$(stat -c %d "$target")
uid=$(id -u)
set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" ./screen-job.sh {row_id} {phase} {family} {capacity} {seed} "$target"
status=$?
set -e
cleanup=false
[ ! -e "$target" ] && cleanup=true
/usr/bin/python3 - "$output/evidence.json.part" "$output/evidence.json" "$status" "$cleanup" "$target" "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" "$uid" "$device" "$marker_sha" <<'PY'
import json, os, sys
partial, final, status, cleanup, target, job, node, role, run_id, uid, device, marker_sha = sys.argv[1:]
if os.path.exists(partial):
    with open(partial, encoding='utf-8') as stream: value=json.load(stream)
else:
    value={{'classification':'a10m5r3-development-only-family-capacity-screen','phase':'{phase}','row_id':role,'valid':False,'gates':{{'compute_completed':False}}}}
value.setdefault('gates',{{}})['job_local_cleanup']=cleanup=='true'
value['gates']['offline_hash_install']=os.path.exists(partial)
value['exit_code']=int(status)
value['valid']=int(status)==0 and all(value['gates'].values())
value['verdict']='PASS' if value['valid'] else 'FAIL'
if cleanup!='true': value['recovery_target']={{'device':int(device),'job_id':job,'marker_sha256':marker_sha,'node':node,'target':target,'uid':int(uid)}}
temporary=final+'.promote'
with open(temporary,'w',encoding='utf-8') as stream: json.dump(value,stream,indent=2,sort_keys=True); stream.write('\n')
os.replace(temporary,final)
if os.path.exists(partial): os.unlink(partial)
PY
exit "$status"
'''


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--asset-root", type=Path, required=True); parser.add_argument("--canonical-cache", type=Path, required=True); parser.add_argument("--source-commit", required=True)
    options = parser.parse_args(); root = options.asset_root.resolve(); root.mkdir(parents=True, exist_ok=True); cache = options.canonical_cache.resolve()
    canonical = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz", "corpus.tar", "source.tar.gz", "cargo-vendor.tar.gz", "selected-parameters-v1.tar.gz")
    for name in canonical:
        if not (cache / name).is_file(): raise RuntimeError(f"canonical asset absent: {name}")
    jobs = ("screen_core_v2.py", "train.py", "cpu_worker.py", "finalize.py", "resolve.py", "screen-job.sh")
    for name in jobs: shutil.copyfile(PACKAGE / "artifacts/jobs" / name, root / name)
    shutil.copyfile(REPO / "research/a10/m5r3_contract.py", root / "m5r3_contract.py")
    predecessor = REPO / "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py"
    shutil.copyfile(predecessor, root / "legacy_core.py")
    for source_name, target_name in (("recover_job_local_v2.sh", "recover-job-local-v2.sh"), ("supervise_v2.sh", "supervise-v2.sh")):
        shutil.copyfile(REPO / "research/a10/lemhi_toolkit/remote" / source_name, root / target_name); (root / target_name).chmod(0o700)
    wrappers = []
    for short, family in FAMILIES:
        for seed in SEEDS:
            row_id = f"family-{short}-s{seed}"; name = f"job-{row_id}.sh"; (root / name).write_text(wrapper(row_id, "family", family, "FAMILY", seed), encoding="utf-8"); (root / name).chmod(0o700); wrappers.append(name)
    for slot in range(5):
        row_id = f"capacity-p{slot}-s147031"; name = f"job-{row_id}.sh"; (root / name).write_text(wrapper(row_id, "capacity", "AUTO", str(slot), 147031), encoding="utf-8"); (root / name).chmod(0o700); wrappers.append(name)
    for slot in range(4):
        seed = SEEDS[1 + slot % 2]; row_id = f"frontier-k{slot//2}-s{seed}"; name = f"job-{row_id}.sh"; (root / name).write_text(wrapper(row_id, "frontier", "AUTO", str(slot), seed), encoding="utf-8"); (root / name).chmod(0o700); wrappers.append(name)
    recovery = {"invoked": False, "reason": "all primary jobs own supervised job-local cleanup"}
    (root / "recovery.json").write_text(json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "toolkit-recovery.0.out").write_text("recovery not invoked\n", encoding="utf-8"); (root / "toolkit-recovery.0.err").write_text("recovery not invoked\n", encoding="utf-8")
    for executable in (*jobs, "recover-job-local-v2.sh", "supervise-v2.sh", *wrappers):
        if executable.endswith((".sh", ".py")): (root / executable).chmod(0o700)
    assets = {name: identity(cache / name) for name in canonical}
    generated = (*jobs, "m5r3_contract.py", "legacy_core.py", "recover-job-local-v2.sh", "supervise-v2.sh", "recovery.json", "toolkit-recovery.0.out", "toolkit-recovery.0.err", *wrappers)
    for name in generated: assets[name] = identity(root / name)
    manifest = {"schema_version": 1, "source_commit": options.source_commit, "protected_roles_opened": [], "assets": assets}
    (root / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__": main()
