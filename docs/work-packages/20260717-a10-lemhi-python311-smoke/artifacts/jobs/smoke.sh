#!/bin/sh
#SBATCH --export=NONE
set -eu
umask 077

run_root=$PWD
runtime_root=$run_root/runtime/cpython
environment=$run_root/runtime/environment
job_local=${TMPDIR:-/tmp}/a10-python311-smoke-$SLURM_JOB_ID
partial=$run_root/evidence.json.part
final=$run_root/evidence.json

unset PYTHONPATH PYTHONHOME LD_LIBRARY_PATH
export PYTHONNOUSERSITE=1
export PIP_NO_INDEX=1
export PATH=/usr/bin:/bin

rm -rf -- "$run_root/runtime"
mkdir -p -- "$runtime_root" "$job_local"
tar -xzf "$run_root/runtime.tar.gz" --strip-components=1 -C "$runtime_root"
test "$($runtime_root/bin/python3 --version 2>&1)" = "Python 3.11.15"
"$runtime_root/bin/python3" -m venv --copies "$environment"
tar -xf "$run_root/wheelhouse.tar" -C "$job_local"
"$environment/bin/python" -m pip install --disable-pip-version-check --no-index --require-hashes \
  --find-links "$job_local/wheelhouse" -r "$run_root/requirements.lock" >"$job_local/pip-install.log" 2>&1
"$environment/bin/python" -m pip check >"$job_local/pip-check.log" 2>&1
"$environment/bin/python" "$run_root/smoke.py" \
  --checkpoint "$run_root/checkpoint/smoke.pt" --output "$partial"
rm -rf -- "$job_local"
test ! -e "$job_local"
"$environment/bin/python" - "$partial" "$final" <<'PY'
import json
import os
import sys

partial, final = sys.argv[1:]
with open(partial, encoding="utf-8") as stream:
    evidence = json.load(stream)
evidence["gates"]["job_local_cleanup"] = True
evidence["gates"]["offline_hash_install"] = True
temporary = final + ".promote"
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(evidence, stream, indent=2, sort_keys=True)
    stream.write("\n")
os.replace(temporary, final)
os.unlink(partial)
PY
printf '%s\n' A10-PY311-SMOKE-PASS
