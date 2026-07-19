#!/usr/bin/env python3
"""Prepare immutable A10M5R4R2 assets and six frozen toolkit wrappers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
ROWS = (
    ("capacity-p1-s147031", "P1", 147031),
    ("frontier-k0-s271828", "P1", 271828),
    ("frontier-k0-s314159", "P1", 314159),
    ("capacity-p2-s147031", "P2", 147031),
    ("frontier-k1-s271828", "P2", 271828),
    ("frontier-k1-s314159", "P2", 314159),
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def wrapper(row_id: str, capacity: str, seed: int) -> str:
    return f'''#!/bin/sh
set -eu
umask 077
role={row_id}
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/{row_id}
target=${{TMPDIR:-/tmp}}/a10m5r4r2-{row_id}-$SLURM_JOB_ID
mkdir -p -- "$output" "$target"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{{"attempt_index":0,"job_id":"%s","node":"%s","role":"%s","run_id":"%s"}}\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{{print $1}}')
device=$(stat -c %d "$target")
uid=$(id -u)
set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" ./run_model.sh {row_id} {capacity} {seed} "$target"
status=$?
set -e
cleanup=false
[ ! -e "$target" ] && cleanup=true
/usr/bin/python3 - "$output/streams.json" "$role" "$status" <<'PY'
import json, os, sys
path, role, status = sys.argv[1:]
if not os.path.exists(path):
    temporary=path+'.promote'
    with open(temporary,'w',encoding='utf-8') as stream:
        json.dump({'schema_version':1,'row_id':role,'streams':[],'valid':False,'absent_reason':'model role exited before stream publication','exit_code':int(status)},stream,indent=2,sort_keys=True)
        stream.write('\n')
    os.replace(temporary,path)
PY
/usr/bin/python3 - "$output/evidence.json.part" "$output/evidence.json" "$status" "$cleanup" "$target" "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" "$uid" "$device" "$marker_sha" <<'PY'
import json, os, sys
partial, final, status, cleanup, target, job, node, role, run_id, uid, device, marker_sha = sys.argv[1:]
if os.path.exists(partial):
    with open(partial, encoding='utf-8') as stream: value=json.load(stream)
else:
    value={{'classification':'a10m5r4r2-development-only-realized-temporal-streams','row_id':role,'gates':{{'compute_completed':False}}}}
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--canonical-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve()
    cache = options.canonical_cache.resolve()
    root.mkdir(parents=True, exist_ok=True)
    canonical = ("runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar")
    for name in canonical:
        if not (cache / name).is_file():
            raise RuntimeError(f"canonical asset absent: {name}")
    jobs = ("generate.py", "temporal_metrics.py", "run_model.sh")
    for name in jobs:
        shutil.copyfile(PACKAGE / "artifacts/jobs" / name, root / name)
    predecessor = REPO / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/jobs"
    shutil.copyfile(predecessor / "screen_core_v2.py", root / "screen_core_v2.py")
    shutil.copyfile(predecessor / "train.py", root / "train.py")
    legacy = REPO / "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py"
    shutil.copyfile(legacy, root / "legacy_core.py")
    for name in ("temporal-contract.json", "sites.json"):
        shutil.copyfile(PACKAGE / "artifacts" / name, root / name)
    for source_name, target_name in (("recover_job_local_v2.sh", "recover-job-local-v2.sh"), ("supervise_v2.sh", "supervise-v2.sh")):
        shutil.copyfile(REPO / "research/a10/lemhi_toolkit/remote" / source_name, root / target_name)
    wrappers = []
    for row_id, capacity, seed in ROWS:
        name = f"job-{row_id}.sh"
        (root / name).write_text(wrapper(row_id, capacity, seed), encoding="utf-8")
        wrappers.append(name)
    recovery = {"invoked": False, "reason": "all primary jobs own supervised job-local cleanup"}
    (root / "recovery.json").write_text(json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    generated = (*jobs, "screen_core_v2.py", "train.py", "legacy_core.py", "temporal-contract.json", "sites.json", "recover-job-local-v2.sh", "supervise-v2.sh", "recovery.json", *wrappers)
    for name in generated:
        if name.endswith((".sh", ".py")):
            (root / name).chmod(0o700)
    assets = {name: identity(cache / name) for name in canonical}
    for name in generated:
        assets[name] = identity(root / name)
    manifest = {"schema_version": 1, "source_commit": options.source_commit, "protected_roles_opened": [], "assets": assets}
    (root / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
