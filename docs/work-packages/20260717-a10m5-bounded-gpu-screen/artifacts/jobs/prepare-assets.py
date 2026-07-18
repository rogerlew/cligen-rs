#!/usr/bin/env python3
"""Prepare exact A10M5 wrapper assets around the attested canonical cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
BASE_COMMIT = "37a2127"
CONFIGURATIONS = (
    "N0-l32-w128-d2-lognormal", "N0-l32-w128-d2-gpd",
    "N0-l64-w128-d2-lognormal", "N0-l64-w128-d2-gpd",
    "N0-l64-w128-d3-lognormal", "N0-l64-w128-d3-gpd",
    "N1-l32-w128-d2-lognormal", "N1-l32-w128-d2-gpd",
    "N1-l64-w128-d2-lognormal", "N1-l64-w128-d2-gpd",
    "N1-l64-w128-d3-lognormal", "N1-l64-w128-d3-gpd",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--canonical-cache", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    options = parser.parse_args()
    root = options.asset_root.resolve(); root.mkdir(parents=True, exist_ok=True)
    cache = options.canonical_cache.resolve()
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", f"{BASE_COMMIT}..{options.source_commit}", "--", "crates", "Cargo.toml", "Cargo.lock"],
        cwd=REPO, check=False,
    ).returncode == 0
    if not unchanged:
        raise RuntimeError("faithful Rust changed after the attested source archive")
    names = (
        "runtime.tar.gz", "wheelhouse.tar", "requirements.lock",
        "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz", "corpus.tar",
        "source.tar.gz", "cargo-vendor.tar.gz", "selected-parameters-v1.tar.gz",
    )
    for name in names:
        if not (cache / name).is_file():
            raise RuntimeError(f"canonical cache asset absent: {name}")
    for name in ("screen.py", "screen-job.sh"):
        shutil.copyfile(PACKAGE / "artifacts/jobs" / name, root / name)
    (root / "screen-job.sh").chmod(0o700)
    recovery = REPO / "research/a10/lemhi_toolkit/remote/recover_job_local_v2.sh"
    shutil.copyfile(recovery, root / "recover-job-local-v2.sh")
    (root / "recover-job-local-v2.sh").chmod(0o700)
    supervisor = REPO / "research/a10/lemhi_toolkit/remote/supervise_v2.sh"
    shutil.copyfile(supervisor, root / "supervise-v2.sh")
    (root / "supervise-v2.sh").chmod(0o700)
    wrappers = []
    for configuration in CONFIGURATIONS:
        slug = configuration.lower()
        name = f"job-{slug}.sh"
        path = root / name
        path.write_text("""#!/bin/sh
set -eu
umask 077
configuration='%s'
slug=$(printf '%%s' "$configuration" | tr '[:upper:]' '[:lower:]')
role=screen-$slug
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/$slug
target=${TMPDIR:-/tmp}/a10m5-$slug-$SLURM_JOB_ID
mkdir -p -- "$output" "$target"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{"attempt_index":0,"job_id":"%%s","node":"%%s","role":"%%s","run_id":"%%s"}\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{print $1}')
device=$(stat -c %%d "$target")
uid=$(id -u)
set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" ./screen-job.sh "$configuration" "$target"
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
    value={'classification':'a10m5-development-only-fit-validation-screen','configuration_id':role[7:] if role.startswith('screen-') else role,'valid':False,'gates':{'compute_completed':False}}
value.setdefault('gates',{})['job_local_cleanup']=cleanup=='true'
value['gates']['offline_hash_install']=os.path.exists(partial)
value['exit_code']=int(status)
if cleanup!='true':
    value['recovery_target']={'device':int(device),'job_id':job,'marker_sha256':marker_sha,'node':node,'target':target,'uid':int(uid)}
value['verdict']='PASS' if int(status)==0 and all(value['gates'].values()) else 'FAIL'
temporary=final+'.promote'
with open(temporary,'w',encoding='utf-8') as stream: json.dump(value,stream,indent=2,sort_keys=True); stream.write('\n')
os.replace(temporary,final)
if os.path.exists(partial): os.unlink(partial)
PY
exit "$status"
""" % configuration, encoding="utf-8")
        path.chmod(0o700)
        wrappers.append(name)
    assets = {name: identity(cache / name) for name in names}
    for name in ("screen.py", "screen-job.sh", "recover-job-local-v2.sh", "supervise-v2.sh", *wrappers):
        assets[name] = identity(root / name)
    manifest = {
        "schema_version": 1, "source_commit": options.source_commit,
        "faithful_source_commit": BASE_COMMIT, "faithful_source_unchanged": True,
        "assets": assets,
    }
    (root / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
